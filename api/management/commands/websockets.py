# -*- coding: utf-8 -*-

from contextlib import closing
from copy import deepcopy
from datetime import datetime
from logging import CRITICAL, DEBUG, Formatter, StreamHandler, getLogger

from celery import current_app
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from geopy.distance import vincenty
from itsdangerous import TimestampSigner
from numpy import array_split
from pika import TornadoConnection, URLParameters
from rollbar import init, report_exc_info, report_message
from tornado.gen import coroutine, Return
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from ujson import dumps, loads

from api import serializers

formatter = Formatter('%(asctime)s [%(levelname)8s] %(message)s')

stream_handler = StreamHandler()
stream_handler.setLevel(DEBUG)
stream_handler.setFormatter(formatter)

logger = getLogger(__name__)
logger.setLevel(DEBUG)
logger.addHandler(stream_handler)

init(
    settings.ROLLBAR['access_token'],
    branch=settings.ROLLBAR['branch'],
    environment=settings.ROLLBAR['environment'],
    root=settings.ROLLBAR['root'],
)


class RabbitMQ(object):

    @coroutine
    def __init__(self, *args, **kwargs):
        try:
            self.connection = TornadoConnection(
                parameters=URLParameters(settings.BROKER),
                on_close_callback=self.on_connection_close,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
            )
        except Exception:
            report_exc_info()

    def on_connection_open(self, connection):
        try:
            self.channel = connection.channel(on_open_callback=self.on_channel_open)
        except Exception:
            report_exc_info()

    def on_connection_open_error(self, connection, error_message):
        report_message(error_message)

    def on_connection_close(self, connection, reply_code, reply_text):
        report_message(reply_text)

    def on_channel_open(self, channel):
        try:
            self.channel.exchange_declare(
                self.on_channel_exchange_declare, durable=True, exchange='api.management.commands.websockets',
            )
        except Exception:
            report_exc_info()

    def on_channel_exchange_declare(self, frame):
        try:
            self.channel.queue_declare(
                self.on_channel_queue_declare, durable=True, queue='api.management.commands.websockets',
            )
        except Exception:
            report_exc_info()

    def on_channel_queue_declare(self, frame):
        try:
            self.channel.queue_bind(
                self.on_channel_queue_bind,
                'api.management.commands.websockets',
                'api.management.commands.websockets',
                routing_key='api.management.commands.websockets',
            )
        except Exception:
            report_exc_info()

    def on_channel_queue_bind(self, frame):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                self.on_channel_basic_consume, queue='api.management.commands.websockets', no_ack=False,
            )
        except Exception:
            report_exc_info()

    @coroutine
    def on_channel_basic_consume(self, channel, method, properties, body):
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        try:
            message = loads(body)['args'][0]
        except Exception:
            report_exc_info()
        if not message or 'subject' not in message or 'body' not in message:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [   ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='RabbitMQ', subject='if not message',
            ))
            raise Return(None)
        try:
            start = datetime.now()
            if message['subject'] == 'blocks':
                yield self.blocks(message['body'])
            elif message['subject'] == 'master_tells':
                user_ids = body['user_ids']
                del body['user_ids']
                for user in [key for key, value in IOLoop.current().clients.items() if value in user_ids]:
                    user.write_message(dumps(message))
            elif message['subject'] == 'messages':
                if 'users' in message:
                    for user in [key for key, value in IOLoop.current().clients.items() if value in message['users']]:
                        user.write_message(dumps({
                            'subject': message['subject'],
                            'body': message['body'],
                            'action': message['action'],
                        }))
                else:
                    yield self.messages(message['body'])
            elif message['subject'] == 'notifications':
                yield self.notifications(message['body'])
            elif message['subject'] == 'posts':
                user_ids = body['user_ids']
                del body['user_ids']
                for user in [key for key, value in IOLoop.current().clients.items() if value in user_ids]:
                    user.write_message(dumps(message))
            elif message['subject'] == 'profile':
                yield self.profile(message['body'])
            elif message['subject'] == 'users_locations':
                yield self.users_locations(message['body'])
            logger.log(DEBUG, '[{clients:>3d}] [{source:>9s}] [IN ] [{seconds:>9.2f}] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()),
                source='RabbitMQ',
                seconds=(datetime.now() - start).total_seconds(),
                subject=message['subject'],
            ))
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def blocks(self, id):
        block = yield self.get_block(id)
        if not block:
            raise Return(None)
        for user in [key for key, value in IOLoop.current().clients.items() if value == block['user_destination_id']]:
            user.write_message(dumps({
                'subject': 'blocks',
                'body': block['user_source_id'],
            }))
        raise Return(None)

    @coroutine
    def messages(self, id):
        message = yield self.get_message(id)
        if not message:
            raise Return(None)
        for user in [key for key, value in IOLoop.current().clients.items() if value == message['user_source_id']]:
            body = deepcopy(message)
            body['user_destination']['email'] = (
                body['user_destination']['email']
                if body['user_destination']['settings']['show_email'] == 'True' else None
            )
            body['user_destination']['last_name'] = (
                body['user_destination']['last_name']
                if body['user_destination']['settings']['show_last_name'] == 'True' else None
            )
            body['user_destination']['phone'] = (
                body['user_destination']['phone']
                if body['user_destination']['settings']['show_phone'] == 'True' else None
            )
            body['user_destination']['photo_original'] = (
                body['user_destination']['photo_original']
                if body['user_destination']['settings']['show_photo'] == 'True' else None
            )
            body['user_destination']['photo_preview'] = (
                body['user_destination']['photo_preview']
                if body['user_destination']['settings']['show_photo'] == 'True' else None
            )
            del body['user_source']['settings']
            del body['user_destination']['settings']
            user.write_message(dumps({
                'subject': 'messages',
                'body': body,
            }))
        for user in [key for key, value in IOLoop.current().clients.items() if value == message['user_destination_id']]:
            body = deepcopy(message)
            body['user_source']['email'] = (
                body['user_source']['email']
                if body['user_source']['settings']['show_email'] == 'True' else None
            )
            body['user_source']['last_name'] = (
                body['user_source']['last_name']
                if body['user_source']['settings']['show_last_name'] == 'True' else None
            )
            body['user_source']['phone'] = (
                body['user_source']['phone']
                if body['user_source']['settings']['show_phone'] == 'True' else None
            )
            body['user_source']['photo_original'] = (
                body['user_source']['photo_original']
                if body['user_source']['settings']['show_photo'] == 'True' else None
            )
            body['user_source']['photo_preview'] = (
                body['user_source']['photo_preview']
                if body['user_source']['settings']['show_photo'] == 'True' else None
            )
            del body['user_source']['settings']
            del body['user_destination']['settings']
            user.write_message(dumps({
                'subject': 'messages',
                'body': body,
            }))
        raise Return(None)

    @coroutine
    def notifications(self, id):
        notification = yield self.get_notification(id)
        if not notification:
            raise Return(None)
        for user in [key for key, value in IOLoop.current().clients.items() if value == notification['user_id']]:
            user.write_message(dumps({
                'subject': 'notifications',
                'body': notification,
            }))
        raise Return(None)

    @coroutine
    def profile(self, id):
        profile = yield self.get_profile(id)
        if not profile:
            raise Return(None)
        for user in [key for key, value in IOLoop.current().clients.items() if value in profile['ids']]:
            user.write_message(dumps({
                'subject': 'profile',
                'body': profile['id'],
            }))
        raise Return(None)

    @coroutine
    def users_locations(self, data):
        users_locations = yield self.get_user_locations(data)
        if not users_locations:
            raise Return(None)
        for user in [
            key for key, value in IOLoop.current().clients.items() if value == users_locations[0]['user_id']
        ]:
            body = yield self.get_radar_post(users_locations[0])
            user.write_message(dumps({
                'subject': 'users_locations_post',
                'body': body,
            }))
        users = yield self.get_users(users_locations[0]['user_id'], users_locations[0]['point'], 999999999, True)
        if not users:
            raise Return(None)
        blocks = {}
        users_ids = tuple([user['id'] for user in users])
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT user_source_id, user_destination_id
                FROM api_blocks
                WHERE user_source_id IN %s OR user_destination_id IN %s
                ''',
                (users_ids, users_ids,)
            )
            for record in cursor.fetchall():
                if not record[0] in blocks:
                    blocks[record[0]] = []
                blocks[record[0]].append(record[1])
                if not record[1] in blocks:
                    blocks[record[1]] = []
                blocks[record[1]].append(record[0])
        for user in users:
            for k, v in IOLoop.current().clients.items():
                if v == user['id']:
                    body = yield self.get_radar_get(
                        user,
                        [
                            u
                            for u in deepcopy(users[:])
                            if u['id'] != user['id'] and u['id'] not in blocks.get(user['id'], [])
                        ],
                    )
                    k.write_message(dumps({
                        'subject': 'users_locations_get',
                        'body': body,
                    }))
        if len(users_locations) == 1:
            raise Return(None)
        if not vincenty(
            (users_locations[0]['point']['longitude'], users_locations[0]['point']['latitude']),
            (users_locations[1]['point']['longitude'], users_locations[1]['point']['latitude'])
        ).ft > 999999999:
            raise Return(None)
        users = yield self.get_users(users_locations[1]['user_id'], users_locations[1]['point'], 999999999, False)
        for user in users:
            for k, v in IOLoop.current().clients.items():
                if v == user['id']:
                    body = yield self.get_radar_get(
                        user,
                        [
                            u
                            for u in deepcopy(users[:])
                            if u['id'] != user['id'] and u['id'] not in blocks.get(user['id'], [])
                        ],
                    )
                    k.write_message(dumps({
                        'subject': 'users_locations_get',
                        'body': body,
                    }))
        raise Return(None)

    @coroutine
    def get_block(self, id):
        block = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute('SELECT user_source_id, user_destination_id FROM api_blocks WHERE id = %s', (id,))
                record = cursor.fetchone()
                if record:
                    block = {
                        'user_source_id': record[0],
                        'user_destination_id': record[1],
                    }
        except Exception:
            report_exc_info()
        raise Return(block)

    @coroutine
    def get_message(self, id):
        message = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        api_messages.id AS message_id,
                        api_messages.user_source_id AS message_user_source_id,
                        api_messages.user_source_is_hidden AS message_user_source_is_hidden,
                        api_messages.user_destination_id AS message_user_destination_id,
                        api_messages.user_destination_is_hidden AS message_user_destination_is_hidden,
                        api_messages.post_id AS message_post_id,
                        api_messages.type AS message_type,
                        api_messages.contents AS message_contents,
                        api_messages.status AS message_status,
                        api_messages.inserted_at AS message_inserted_at,
                        api_messages.updated_at AS message_updated_at,
                        api_messages_attachments.id AS message_attachment_id,
                        api_messages_attachments.string AS message_attachment_string,
                        api_messages_attachments.position AS message_attachment_position,
                        api_users_source.email AS user_source_email,
                        api_users_source.photo_original AS user_source_photo_original,
                        api_users_source.photo_preview AS user_source_photo_preview,
                        api_users_source.first_name AS user_source_first_name,
                        api_users_source.last_name AS user_source_last_name,
                        api_users_source.date_of_birth AS user_source_date_of_birth,
                        api_users_source.gender AS user_source_gender,
                        api_users_source.location AS user_source_location,
                        api_users_source.description AS user_source_description,
                        api_users_source.phone AS user_source_phone,
                        api_users_settings_source.key AS user_setting_source_key,
                        api_users_settings_source.value AS user_setting_source_value,
                        api_users_destination.email AS user_destination_email,
                        api_users_destination.photo_original AS user_destination_photo_original,
                        api_users_destination.photo_preview AS user_destination_photo_preview,
                        api_users_destination.first_name AS user_destination_first_name,
                        api_users_destination.last_name AS user_destination_last_name,
                        api_users_destination.date_of_birth AS user_destination_date_of_birth,
                        api_users_destination.gender AS user_destination_gender,
                        api_users_destination.location AS user_destination_location,
                        api_users_destination.description AS user_destination_description,
                        api_users_destination.phone AS user_destination_phone,
                        api_users_settings_destination.key AS user_setting_destination_key,
                        api_users_settings_destination.value AS user_setting_destination_value,
                        api_users_statuses.id AS user_status_id,
                        api_users_statuses.string AS user_status_string,
                        api_users_statuses.title AS user_status_title,
                        api_users_statuses.url AS user_status_url,
                        api_users_statuses.notes AS user_status_notes,
                        api_users_statuses_attachments.id AS user_status_attachment_id,
                        api_users_statuses_attachments.string_original AS user_status_attachment_string_original,
                        api_users_statuses_attachments.string_preview AS user_status_attachment_string_preview,
                        api_users_statuses_attachments.position AS user_status_attachment_position,
                        api_master_tells.id AS master_tell_id,
                        api_master_tells.created_by_id AS master_tell_created_by_id,
                        api_master_tells.owned_by_id AS master_tell_owned_by_id,
                        api_master_tells.contents AS master_tell_contents,
                        api_master_tells.position AS master_tell_position,
                        api_master_tells.is_visible AS master_tell_is_visible,
                        api_master_tells.inserted_at AS master_tell_inserted_at,
                        api_master_tells.updated_at AS master_tell_updated_at
                    FROM api_messages
                    LEFT OUTER JOIN api_messages_attachments
                        ON api_messages_attachments.message_id = api_messages.id
                    INNER JOIN api_users AS api_users_source
                        ON api_users_source.id = api_messages.user_source_id
                    LEFT OUTER JOIN api_users_settings AS api_users_settings_source
                        ON api_users_settings_source.user_id = api_messages.user_source_id
                    INNER JOIN api_users AS api_users_destination
                        ON api_users_destination.id = api_messages.user_destination_id
                    LEFT OUTER JOIN api_users_settings AS api_users_settings_destination
                        ON api_users_settings_destination.user_id = api_messages.user_destination_id
                    LEFT OUTER JOIN api_users_statuses
                        ON api_users_statuses.id = api_messages.user_status_id
                    LEFT OUTER JOIN api_users_statuses_attachments
                        ON api_users_statuses_attachments.user_status_id = api_messages.user_status_id
                    LEFT OUTER JOIN api_master_tells
                        ON api_master_tells.id = api_messages.master_tell_id
                    WHERE api_messages.id = %s
                    ''',
                    (id,),
                )
                columns = [column.name for column in cursor.description]
                for record in cursor.fetchall():
                    record = dict(zip(columns, record))
                    if 'id' not in message:
                        message['id'] = record['message_id']
                    if 'user_source_id' not in message:
                        message['user_source_id'] = record['message_user_source_id']
                    if 'user_source_is_hidden' not in message:
                        message['user_source_is_hidden'] = record['message_user_source_is_hidden']
                    if 'user_destination_id' not in message:
                        message['user_destination_id'] = record['message_user_destination_id']
                    if 'user_destination_is_hidden' not in message:
                        message['user_destination_is_hidden'] = record['message_user_destination_is_hidden']
                    if 'post_id' not in message:
                        message['post_id'] = record['message_post_id']
                    if 'type' not in message:
                        message['type'] = record['message_type']
                    if 'contents' not in message:
                        message['contents'] = record['message_contents']
                    if 'status' not in message:
                        message['status'] = record['message_status']
                    if 'inserted_at' not in message:
                        message['inserted_at'] = record['message_inserted_at'].isoformat()
                    if 'updated_at' not in message:
                        message['updated_at'] = record['message_updated_at'].isoformat()
                    if 'attachments' not in message:
                        message['attachments'] = {}
                    if record['message_attachment_id']:
                        if record['message_attachment_id'] not in message['attachments']:
                            message['attachments'][record['message_attachment_id']] = {
                                'id': record['message_attachment_id'],
                                'string': record['message_attachment_string'],
                                'position': record['message_attachment_position'],
                            }
                    if 'user_source' not in message:
                        message['user_source'] = {
                            'id': record['message_user_source_id'],
                            'email': record['user_source_email'],
                            'photo_original': record['user_source_photo_original'],
                            'photo_preview': record['user_source_photo_preview'],
                            'first_name': record['user_source_first_name'],
                            'last_name': record['user_source_last_name'],
                            'date_of_birth': record['user_source_date_of_birth'].isoformat()
                            if record['user_source_date_of_birth'] else None,
                            'gender': record['user_source_gender'],
                            'location': record['user_source_location'],
                            'description': record['user_source_description'],
                            'phone': record['user_source_phone'],
                        }
                    if 'settings' not in message['user_source']:
                        message['user_source']['settings'] = {}
                    if record['user_setting_source_key']:
                        if record['user_setting_source_key'] not in message['user_source']['settings']:
                            message['user_source']['settings'][
                                record['user_setting_source_key']
                            ] = record['user_setting_source_value']
                    if 'user_destination' not in message:
                        message['user_destination'] = {
                            'id': record['message_user_destination_id'],
                            'email': record['user_destination_email'],
                            'photo_original': record['user_destination_photo_original'],
                            'photo_preview': record['user_destination_photo_preview'],
                            'first_name': record['user_destination_first_name'],
                            'last_name': record['user_destination_last_name'],
                            'date_of_birth': record['user_destination_date_of_birth'].isoformat()
                            if record['user_destination_date_of_birth'] else None,
                            'gender': record['user_destination_gender'],
                            'location': record['user_destination_location'],
                            'description': record['user_destination_description'],
                            'phone': record['user_destination_phone'],
                        }
                    if 'settings' not in message['user_destination']:
                        message['user_destination']['settings'] = {}
                    if record['user_setting_destination_key']:
                        if record['user_setting_destination_key'] not in message['user_destination']['settings']:
                            message['user_destination']['settings'][
                                record['user_setting_destination_key']
                            ] = record['user_setting_destination_value']
                    if 'master_tell' not in message:
                        message['master_tell'] = {}
                    if record['master_tell_id']:
                        if 'id' not in message['master_tell']:
                            message['master_tell']['id'] = record['master_tell_id']
                        if 'created_by_id' not in message['master_tell']:
                            message['master_tell']['created_by_id'] = record['master_tell_created_by_id']
                        if 'owned_by_id' not in message['master_tell']:
                            message['master_tell']['owned_by_id'] = record['master_tell_owned_by_id']
                        if 'contents' not in message['master_tell']:
                            message['master_tell']['contents'] = record['master_tell_contents']
                        if 'position' not in message['master_tell']:
                            message['master_tell']['position'] = record['master_tell_position']
                        if 'is_visible' not in message['master_tell']:
                            message['master_tell']['is_visible'] = record['master_tell_is_visible']
                        if 'inserted_at' not in message['master_tell']:
                            message['master_tell']['inserted_at'] = record['master_tell_inserted_at'].isoformat()
                        if 'updated_at' not in message['master_tell']:
                            message['master_tell']['updated_at'] = record['master_tell_updated_at'].isoformat()
                    if 'user_status' not in message:
                        message['user_status'] = {}
                    if record['user_status_id']:
                        if 'id' not in message['user_status']:
                            message['user_status']['id'] = record['user_status_id']
                        if 'string' not in message['user_status']:
                            message['user_status']['string'] = record['user_status_string']
                        if 'title' not in message['user_status']:
                            message['user_status']['title'] = record['user_status_title']
                        if 'url' not in message['user_status']:
                            message['user_status']['url'] = record['user_status_url']
                        if 'notes' not in message['user_status']:
                            message['user_status']['notes'] = record['user_status_notes']
                        if 'attachments' not in message['user_status']:
                            message['user_status']['attachments'] = {}
                        if record['user_status_attachment_id'] not in message['user_status']['attachments']:
                            message['user_status']['attachments'][record['user_status_attachment_id']] = {
                                'id': record['user_status_attachment_id'],
                                'string_original': record['user_status_attachment_string_original'],
                                'string_preview': record['user_status_attachment_string_preview'],
                                'position': record['user_status_attachment_position'],
                            }
        except Exception:
            report_exc_info()
        if message:
            if 'attachments' in message:
                message['attachments'] = sorted(message['attachments'].values(), key=lambda item: item['position'])
            if 'user_status' in message:
                if 'attachments' in message['user_status']:
                    message['user_status']['attachments'] = sorted(
                        message['user_status']['attachments'].values(), key=lambda item: item['position'],
                    )
        raise Return(message)

    @coroutine
    def get_notification(self, id):
        notification = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    'SELECT id, user_id, type, contents, status, timestamp FROM api_notifications WHERE id = %s',
                    (id,),
                )
                record = cursor.fetchone()
                if record:
                    notification = {
                        'id': record[0],
                        'user_id': record[1],
                        'type': record[2],
                        'contents': loads(record[3]),
                        'status': record[4],
                        'timestamp': record[5].isoformat(' '),
                    }
        except Exception:
            report_exc_info()
        raise Return(notification)

    @coroutine
    def get_profile(self, id):
        profile = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute('SELECT user_source_id FROM api_tellcards WHERE user_destination_id = %s', (id,))
                for record in cursor.fetchall():
                    if 'id' not in profile:
                        profile['id'] = id
                    if 'ids' not in profile:
                        profile['ids'] = []
                    profile['ids'].append(record[0])
        except Exception:
            report_exc_info()
        raise Return(profile)

    @coroutine
    def get_user_locations(self, data):
        user_locations = []
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        api_users_locations_1.user_id,
                        api_users_locations_1.network_id,
                        api_users_locations_1.tellzone_id,
                        ST_AsGeoJSON(api_users_locations_1.point)
                    FROM api_users_locations api_users_locations_1
                    INNER JOIN (
                        SELECT user_id FROM api_users_locations WHERE id = %s
                    ) api_users_locations_2 ON api_users_locations_1.user_id = api_users_locations_2.user_id
                    ORDER BY api_users_locations_1.id DESC LIMIT 2
                    ''',
                    (data,)
                )
                for record in cursor.fetchall():
                    point = loads(record[3])
                    user_location = {
                        'user_id': record[0],
                        'network_id': record[1],
                        'tellzone_id': record[2],
                        'point': {
                            'latitude': point['coordinates'][1],
                            'longitude': point['coordinates'][0],
                        },
                    }
                    user_locations.append(user_location)
        except Exception:
            report_exc_info()
        raise Return(user_locations)

    @coroutine
    def get_radar_get(self, user, users):
        for key, value in enumerate(users):
            users[key]['photo_original'] = (
                users[key]['photo_original'] if users[key]['settings']['show_photo'] == 'True' else None
            )
            users[key]['photo_preview'] = (
                users[key]['photo_preview'] if users[key]['settings']['show_photo'] == 'True' else None
            )
            del users[key]['settings']
            users[key]['distance'] = vincenty(
                (user['point']['longitude'], user['point']['latitude']),
                (users[key]['point']['longitude'], users[key]['point']['latitude']),
            ).ft
            del users[key]['point']
            users[key]['group'] = 1
            if user['tellzone_id']:
                if users[key]['tellzone_id']:
                    if user['tellzone_id'] == users[key]['tellzone_id']:
                        users[key]['group'] = 1
                    else:
                        users[key]['group'] = 2
                else:
                    if users[key]['distance'] <= 300.0:
                        users[key]['group'] = 1
                    else:
                        users[key]['group'] = 2
            else:
                if users[key]['distance'] <= 300.0:
                    users[key]['group'] = 1
                else:
                    users[key]['group'] = 2
            del users[key]['network_id']
            del users[key]['tellzone_id']
        users = sorted(users, key=lambda item: (item['distance'], item['id'],))
        raise Return(
            [
                {
                    'hash': '-'.join(map(str, [item['id'] for item in items])),
                    'items': items,
                    'position': position + 1,
                }
                for position, items in enumerate([u.tolist() for u in array_split(users, len(users) or 1)])
            ]
        )

    @coroutine
    def get_radar_post(self, user_location):
        point = 'POINT({longitude} {latitude})'.format(
            longitude=user_location['point']['longitude'], latitude=user_location['point']['latitude'],
        )
        tellzones = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        api_tellzones.id AS api_tellzones_id,
                        api_tellzones.name AS api_tellzones_name,
                        ST_AsGeoJSON(api_tellzones.point) AS point,
                        ST_Distance(
                            ST_Transform(api_tellzones.point, 2163),
                            ST_Transform(ST_GeomFromText(%s, 4326), 2163)
                        ) * 3.28084 AS distance,
                        api_networks.id AS api_networks_id,
                        api_networks.name AS api_networks_name
                    FROM api_tellzones
                    LEFT OUTER JOIN api_networks_tellzones ON api_networks_tellzones.tellzone_id = api_tellzones.id
                    LEFT OUTER JOIN api_networks ON api_networks.id = api_networks_tellzones.network_id
                    WHERE ST_DWithin(
                        ST_Transform(api_tellzones.point, 2163),
                        ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                        91.44
                    )
                    ''',
                    (point, point,),
                )
                records = cursor.fetchall()
                if not records:
                    cursor.execute(
                        '''
                        SELECT
                            api_tellzones.id AS api_tellzones_id,
                            api_tellzones.name AS api_tellzones_name,
                            ST_AsGeoJSON(api_tellzones.point) AS point,
                            ST_Distance(
                                ST_Transform(api_tellzones.point, 2163),
                                ST_Transform(ST_GeomFromText(%s, 4326), 2163)
                            ) * 3.28084 AS distance,
                            api_networks.id AS api_networks_id,
                            api_networks.name AS api_networks_name
                        FROM api_tellzones
                        LEFT OUTER JOIN api_networks_tellzones ON
                            api_networks_tellzones.tellzone_id = api_tellzones.id
                        LEFT OUTER JOIN api_networks ON
                            api_networks.id = api_networks_tellzones.network_id
                        WHERE
                            api_networks_tellzones.network_id IN (
                                SELECT DISTINCT api_networks.id
                                FROM api_tellzones
                                INNER JOIN api_networks_tellzones ON
                                    api_networks_tellzones.tellzone_id = api_tellzones.id
                                INNER JOIN api_networks ON
                                    api_networks.id = api_networks_tellzones.network_id
                                WHERE ST_DWithin(
                                    ST_Transform(api_tellzones.point, 2163),
                                    ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                                    8046.72
                                )
                                ORDER BY api_networks.id ASC
                            )
                            AND
                            api_tellzones.status = %s
                        ''',
                        (point, point, 'Public',),
                    )
                    records = cursor.fetchall()
                for record in records:
                    if record[0] not in tellzones:
                        point = loads(record[2])
                        tellzones[record[0]] = {
                            'id': record[0],
                            'name': record[1],
                            'latitude': point['coordinates'][1],
                            'longitude': point['coordinates'][0],
                            'distance': record[3],
                            'networks': {},
                        }
                    if record[4] and record[5]:
                        if record[4] not in tellzones[record[0]]['networks']:
                            tellzones[record[0]]['networks'][record[4]] = {
                                'id': record[4],
                                'name': record[5],
                            }
            for key, value in tellzones.items():
                tellzones[key]['networks'] = sorted(
                    tellzones[key]['networks'].values(), key=lambda network: (network['name'], -network['id'],),
                )
            tellzones = sorted(tellzones.values(), key=lambda tellzone: (tellzone['distance'], -tellzone['id'],))
            for index, _ in enumerate(tellzones):
                del tellzones[index]['distance']
                del tellzones[index]['latitude']
                del tellzones[index]['longitude']
        except Exception:
            report_exc_info()
            from traceback import print_exc
            print_exc()
        raise Return(tellzones)

    @coroutine
    def get_users(self, user_id, point, radius, status):
        point = 'POINT({longitude} {latitude})'.format(longitude=point['longitude'], latitude=point['latitude'])
        users = {}
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT
                        api_users_locations.network_id AS network_id,
                        api_users_locations.tellzone_id AS tellzone_id,
                        ST_AsGeoJSON(api_users_locations.point) AS point,
                        api_users.id AS id,
                        api_users.photo_original AS photo_original,
                        api_users.photo_preview AS photo_preview,
                        api_users_settings.key AS user_setting_key,
                        api_users_settings.value AS user_setting_value
                    FROM api_users_locations
                    INNER JOIN (
                        SELECT MAX(api_users_locations.id) AS id
                        FROM api_users_locations
                        WHERE api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
                        GROUP BY api_users_locations.user_id
                    ) api_users_locations_ ON api_users_locations_.id = api_users_locations.id
                    INNER JOIN api_users ON api_users.id = api_users_locations.user_id
                    LEFT OUTER JOIN api_users_settings AS api_users_settings
                        ON api_users_settings.user_id = api_users.id
                    WHERE
                        (api_users_locations.user_id != %s OR %s = true)
                        AND
                        ST_DWithin(
                            ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                            ST_Transform(api_users_locations.point, 2163),
                            %s
                        )
                        AND
                        api_users_locations.is_casting IS TRUE
                        AND
                        api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
                        AND
                        api_users.is_signed_in IS TRUE
                        AND
                        api_users_settings.key = 'show_photo'
                    ORDER BY api_users_locations.user_id ASC
                    ''',
                    (user_id, status, point, radius,),
                )
                columns = [column.name for column in cursor.description]
                for record in cursor.fetchall():
                    record = dict(zip(columns, record))
                    record['point'] = loads(record['point'])
                    if record['id'] not in users:
                        users[record['id']] = {}
                    if 'id' not in users[record['id']]:
                        users[record['id']]['id'] = record['id']
                    if 'photo_original' not in users[record['id']]:
                        users[record['id']]['photo_original'] = record['photo_original']
                    if 'photo_preview' not in users[record['id']]:
                        users[record['id']]['photo_preview'] = record['photo_preview']
                    if 'settings' not in users[record['id']]:
                        users[record['id']]['settings'] = {}
                    if record['user_setting_key']:
                        if record['user_setting_key'] not in users[record['id']]['settings']:
                            users[record['id']]['settings'][record['user_setting_key']] = record['user_setting_value']
                    if 'point' not in users[record['id']]:
                        users[record['id']]['point'] = {
                            'latitude': record['point']['coordinates'][1],
                            'longitude': record['point']['coordinates'][0],
                        }
                    if 'network_id' not in users[record['id']]:
                        users[record['id']]['network_id'] = record['network_id']
                    if 'tellzone_id' not in users[record['id']]:
                        users[record['id']]['tellzone_id'] = record['tellzone_id']
        except Exception:
            report_exc_info()
        users = sorted(users.values(), key=lambda item: item['id'])
        raise Return(users)


class WebSocket(WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):
        self.stream.set_nodelay(True)

    def write_message(self, message, binary=False):
        try:
            message = loads(message)
            logger.log(DEBUG, '[{clients:>3d}] [{source:>9s}] [OUT] [         ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='WebSocket', subject=message['subject'],
            ))
        except Exception:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [OUT] [         ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='WebSocket', subject=message['subject'],
            ))
            report_exc_info()
        super(WebSocket, self).write_message(message, binary=binary)

    def on_close(self):
        del IOLoop.current().clients[self]

    @coroutine
    def on_message(self, message):
        try:
            message = loads(message)
        except Exception:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [IN ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='WebSocket', subject='message = loads(message)',
            ))
            report_exc_info()
        if not message:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [IN ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='WebSocket', subject='if not message',
            ))
            raise Return(None)
        if 'subject' not in message or 'body' not in message:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [IN ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()),
                source='WebSocket',
                subject='if \'subject\' not in message or \'body\' not in message',
            ))
            raise Return(None)
        try:
            start = datetime.now()
            if message['subject'] == 'messages':
                yield self.messages(message['body'])
            elif message['subject'] == 'users':
                yield self.users(message['body'])
            elif message['subject'] == 'users_locations_post':
                yield self.users_locations_post(message['body'])
            logger.log(DEBUG, '[{clients:>3d}] [{source:>9s}] [IN ] [{seconds:>9.2f}] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()),
                source='WebSocket',
                seconds=(datetime.now() - start).total_seconds(),
                subject=message['subject'],
            ))
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def messages(self, data):
        if self not in IOLoop.current().clients:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'if self not in clients',
                },
            }))
            raise Return(None)
        yield self.set_messages(IOLoop.current().clients[self], data)
        raise Return(None)

    @coroutine
    def users(self, data):
        id = data.split('.')[0]
        if str(id) != TimestampSigner(settings.SECRET_KEY).unsign(data):
            self.write_message(dumps({
                'subject': 'users',
                'body': False,
            }))
            raise Return(None)
        id = yield self.get_id(id)
        if not id:
            self.write_message(dumps({
                'subject': 'users',
                'body': False,
            }))
            raise Return(None)
        IOLoop.current().clients[self] = id
        self.write_message(dumps({
            'subject': 'users',
            'body': True,
        }))
        raise Return(None)

    @coroutine
    def users_locations_post(self, data):
        if self not in IOLoop.current().clients:
            self.write_message(dumps({
                'subject': 'users_locations_post',
                'body': {
                    'errors': 'if self not in IOLoop.current().clients',
                },
            }))
            raise Return(None)
        yield self.set_users_locations(IOLoop.current().clients[self], data)
        raise Return(None)

    @coroutine
    def get_blocks(self, one, two):
        blocks = 0
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT COUNT(id)
                    FROM api_blocks
                    WHERE
                        (user_source_id = %s AND user_destination_id = %s)
                        OR
                        (user_source_id = %s AND user_destination_id = %s)
                    ''',
                    (one, two, two, one,)
                )
                blocks = cursor.fetchone()[0]
        except Exception:
            report_exc_info()
        raise Return(blocks)

    @coroutine
    def get_id(self, id):
        id_ = None
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute('SELECT id FROM api_users WHERE id = %s', (id,))
                record = cursor.fetchone()
                if record:
                    id_ = record[0]
        except Exception:
            report_exc_info()
        raise Return(id_)

    @coroutine
    def get_message(self, one, two):
        message = None
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT user_source_id, user_destination_id, type
                    FROM api_messages
                    WHERE (
                        (user_source_id = %s AND user_destination_id = %s)
                        OR
                        (user_source_id = %s AND user_destination_id = %s)
                    ) AND post_id IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                    OFFSET 0
                    ''',
                    (one, two, two, one,)
                )
                record = cursor.fetchone()
                if record:
                    message = {
                        'user_source_id': record[0],
                        'user_destination_id': record[1],
                        'type': record[2],
                    }
        except Exception:
            report_exc_info()
        raise Return(message)

    @coroutine
    def get_messages(self, one, two):
        messages = 0
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT COUNT(id)
                    FROM api_messages
                    WHERE
                        (
                            (user_source_id = %s AND user_destination_id = %s)
                            OR
                            (user_source_id = %s AND user_destination_id = %s)
                        )
                        AND
                        post_id IS NULL
                        AND
                        type IN ('Response - Accepted', 'Response - Rejected', 'Message', 'Ask')
                    ''',
                    (one, two, two, one,)
                )
                messages = cursor.fetchone()[0]
        except Exception:
            report_exc_info()
        raise Return(messages)

    @coroutine
    def set_message(self, user_id, data):
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    INSERT INTO api_messages (
                        user_source_id,
                        user_source_is_hidden,
                        user_destination_id,
                        user_destination_is_hidden,
                        user_status_id,
                        master_tell_id,
                        post_id,
                        type,
                        contents,
                        status,
                        is_suppressed,
                        inserted_at,
                        updated_at
                    ) VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NOW(),
                        NOW()
                    ) RETURNING id
                    ''',
                    (
                        user_id,
                        data['user_source_is_hidden'] if 'user_source_is_hidden' in data else False,
                        data['user_destination_id'] if 'user_destination_id' in data else False,
                        data['user_destination_is_hidden'] if 'user_destination_is_hidden' in data else False,
                        data['user_status_id'] if 'user_status_id' in data else None,
                        data['master_tell_id'] if 'master_tell_id' in data else None,
                        data['post_id'] if 'post_id' in data else None,
                        data['type'] if 'type' in data else None,
                        data['contents'] if 'contents' in data else None,
                        data['status'] if 'status' in data else 'Unread',
                        False,
                    )
                )
                connection.commit()
                message_id = cursor.fetchone()[0]
                if 'attachments' in data:
                    for position, _ in enumerate(data['attachments']):
                        cursor.execute(
                            '''
                            INSERT INTO api_messages_attachments (message_id, string, position) VALUES (%s, %s, %s)
                            ''',
                            (message_id, data['attachments'][position]['string'], position + 1,)
                        )
                        connection.commit()
                if 'type' in data:
                    if data['type'] == 'Response - Blocked':
                        cursor.execute(
                            '''
                            INSERT INTO api_blocks (user_source_id, user_destination_id, timestamp)
                            VALUES (%s, %s, NOW())
                             RETURNING id
                            ''',
                            (user_id, data['user_destination_id'],)
                        )
                        connection.commit()
                        block_id = cursor.fetchone()[0]
                        current_app.send_task(
                            'api.management.commands.websockets',
                            (
                                {
                                    'subject': 'blocks',
                                    'body': block_id,
                                },
                            ),
                            queue='api.management.commands.websockets',
                            routing_key='api.management.commands.websockets',
                            serializer='json',
                        )
                    if data['type'] in ['Response - Rejected', 'Response - Blocked']:
                        cursor.execute('UPDATE api_messages SET is_suppressed = %s WHERE id = %s', (True, message_id,))
                        connection.commit()
                        cursor.execute(
                            '''
                            SELECT id, type
                            FROM api_messages
                            WHERE
                                id < %s
                                AND
                                (
                                    (user_source_id = %s AND user_destination_id = %s)
                                    OR
                                    (user_source_id = %s AND user_destination_id = %s)
                                )
                            ORDER BY id DESC
                            ''',
                            (
                                message_id,
                                user_id,
                                data['user_destination_id'] if 'user_destination_id' in data else False,
                                data['user_destination_id'] if 'user_destination_id' in data else False,
                                user_id,
                            )
                        )
                        records = cursor.fetchall()
                        for record in records:
                            if record[1] == 'Request':
                                cursor.execute(
                                    'UPDATE api_messages SET is_suppressed = %s WHERE id = %s', (True, record[0],)
                                )
                                connection.commit()
                                break
                    notify = False
                    if data['type'] in ['Request', 'Response - Accepted']:
                        cursor.execute(
                            'SELECT COUNT(id) FROM api_users_settings WHERE user_id = %s AND key = %s AND value = %s',
                            (data['user_destination_id'], 'notifications_invitations', 'True',)
                        )
                        if cursor.fetchone()[0]:
                            notify = True
                    if data['type'] in ['Ask', 'Message']:
                        cursor.execute(
                            'SELECT COUNT(id) FROM api_users_settings WHERE user_id = %s AND key = %s AND value = %s',
                            (data['user_destination_id'], 'notifications_messages', 'True',)
                        )
                        if cursor.fetchone()[0]:
                            notify = True
                    if notify:
                        badge = 0
                        cursor.execute(
                            'SELECT COUNT(id) FROM api_messages WHERE user_destination_id = %s AND status = %s',
                            (data['user_destination_id'], 'Unread',)
                        )
                        badge += cursor.fetchone()[0]
                        cursor.execute(
                            'SELECT COUNT(id) FROM api_notifications WHERE user_id = %s AND status = %s',
                            (data['user_destination_id'], 'Unread',)
                        )
                        badge += cursor.fetchone()[0]
                        if data['type'] in ['Ask', 'Message']:
                            cursor.execute('SELECT first_name, last_name FROM api_users WHERE id = %s', (user_id,))
                            user_source = cursor.fetchone()
                            body = u'{first_name:s} {last_name:s}: {contents:s}'.format(
                                first_name=user_source[0],
                                last_name=user_source[1],
                                contents=data['contents'],
                            )
                        else:
                            body = data['contents']
                        current_app.send_task(
                            'api.tasks.push_notifications',
                            (
                                data['user_destination_id'],
                                {
                                    'aps': {
                                        'alert': {
                                            'body': body,
                                            'title': 'New message from user',
                                        },
                                        'badge': badge,
                                    },
                                    'type': 'message',
                                    'user_source_id': user_id,
                                    'post_id': data['post_id'] if 'post_id' in data else None,
                                },
                            ),
                            queue='api.tasks.push_notifications',
                            routing_key='api.tasks.push_notifications',
                            serializer='json',
                        )
                current_app.send_task(
                    'api.management.commands.websockets',
                    (
                        {
                            'subject': 'messages',
                            'body': message_id,
                        },
                    ),
                    queue='api.management.commands.websockets',
                    routing_key='api.management.commands.websockets',
                    serializer='json',
                )
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def set_messages(self, user_id, data):
        serializer = serializers.MessagesPostRequest(data=data)
        if not serializer.is_valid(raise_exception=False):
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': serializer.errors,
                },
            }))
            raise Return(None)
        data = serializer.validated_data
        if user_id == data['user_destination_id']:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'Invalid `user_destination_id`',
                },
            }))
            raise Return(None)
        blocks = yield self.get_blocks(user_id, data['user_destination_id'])
        if blocks:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'Invalid `user_destination_id`',
                },
            }))
            raise Return(None)
        if 'post_id' not in data or not data['post_id']:
            messages = yield self.get_messages(user_id, data['user_destination_id'])
            if not messages:
                message = yield self.get_message(user_id, data['user_destination_id'])
                if message:
                    if message['user_source_id'] == user_id:
                        if message['type'] == 'Request':
                            self.write_message(dumps({
                                'subject': 'messages',
                                'body': {
                                    'errors': 'HTTP_409_CONFLICT',
                                },
                            }))
                            raise Return(None)
                        if message['type'] == 'Response - Blocked':
                            self.write_message(dumps({
                                'subject': 'messages',
                                'body': {
                                    'errors': 'HTTP_403_FORBIDDEN',
                                },
                            }))
                            raise Return(None)
                    if message['user_destination_id'] == user_id:
                        if message['type'] == 'Request' and data['type'] in ['Message', 'Ask']:
                            self.write_message(dumps({
                                'subject': 'messages',
                                'body': {
                                    'errors': 'HTTP_403_FORBIDDEN',
                                },
                            }))
                            raise Return(None)
                        if message['type'] == 'Response - Blocked':
                            self.write_message(dumps({
                                'subject': 'messages',
                                'body': {
                                    'errors': 'HTTP_403_FORBIDDEN',
                                },
                            }))
                            raise Return(None)
                else:
                    if not data['type'] == 'Request':
                        self.write_message(dumps({
                            'subject': 'messages',
                            'body': {
                                'errors': 'HTTP_403_FORBIDDEN',
                            },
                        }))
                        raise Return(None)
        yield self.set_message(user_id, data)
        raise Return(None)

    @coroutine
    def set_user_location(self, user_id, data):
        if not data['point'] or not data['point'].x or not data['point'].y:
            raise Return(None)
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    INSERT INTO api_users_locations (
                        user_id,
                        network_id,
                        tellzone_id,
                        location,
                        point,
                        accuracies_horizontal,
                        accuracies_vertical,
                        bearing,
                        is_casting,
                        timestamp
                    ) VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s, %s, %s, NOW()) RETURNING id
                    ''',
                    (
                        user_id,
                        data['network_id'] if 'network_id' in data else None,
                        data['tellzone_id'] if 'tellzone_id' in data else None,
                        data['location'] if 'location' in data else None,
                        'POINT({longitude} {latitude})'.format(longitude=data['point'].x, latitude=data['point'].y),
                        data['accuracies_horizontal'] if 'accuracies_horizontal' in data else 0.00,
                        data['accuracies_vertical'] if 'accuracies_vertical' in data else 0.00,
                        data['bearing'] if 'bearing' in data else 0,
                        data['is_casting'] if 'is_casting' in data else False,
                    )
                )
                id = cursor.fetchone()[0]
                current_app.send_task(
                    'api.management.commands.websockets',
                    (
                        {
                            'subject': 'users_locations',
                            'body': id,
                        },
                    ),
                    queue='api.management.commands.websockets',
                    routing_key='api.management.commands.websockets',
                    serializer='json',
                )
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def set_users_locations(self, user_id, data):
        serializer = serializers.RadarPostRequest(data=data)
        if not serializer.is_valid(raise_exception=False):
            self.write_message(dumps({
                'subject': 'users_locations_post',
                'body': {
                    'errors': serializer.errors,
                },
            }))
            raise Return(None)
        yield self.set_user_location(user_id, serializer.validated_data)
        raise Return(None)


class Command(BaseCommand):

    help = 'WebSockets'

    def handle(self, *args, **kwargs):
        server = HTTPServer(
            Application([('/websockets/', WebSocket)], autoreload=settings.DEBUG, debug=settings.DEBUG),
        )
        server.listen(settings.TORNADO['port'], address=settings.TORNADO['address'])
        IOLoop.current().clients = {}
        IOLoop.current().add_callback(RabbitMQ)
        IOLoop.current().start()
