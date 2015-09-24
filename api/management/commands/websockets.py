# -*- coding: utf-8 -*-

from datetime import datetime
from logging import CRITICAL, DEBUG, Formatter, StreamHandler, getLogger

from django.conf import settings
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.test.client import RequestFactory
from geopy.distance import vincenty
from pika import TornadoConnection, URLParameters
from rest_framework.request import Request
from rollbar import init, report_exc_info, report_message
from tornado.gen import coroutine, Return, sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from ujson import dumps, loads

from api import models, serializers

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
    def __init__(self, application, *args, **kwargs):
        self.application = application
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
            logger.log(CRITICAL, '{clients:>3d} {source:>9s} [   ] {subject:s}'.format(
                clients=len(self.application.clients.values()), source='RabbitMQ', subject='if not message',
            ))
            raise Return(None)
        try:
            start = datetime.now()
            if message['subject'] == 'blocks':
                yield self.blocks(message['body'])
            elif message['subject'] == 'messages':
                yield self.messages(message['body'])
            elif message['subject'] == 'notifications':
                yield self.notifications(message['body'])
            elif message['subject'] == 'profile':
                yield self.profile(message['body'])
            elif message['subject'] == 'users_locations':
                yield self.users_locations(message['body'])
            logger.log(DEBUG, '{clients:>3d} {source:>9s} [IN ] [{seconds:>9.2f}] {subject:s}'.format(
                clients=len(self.application.clients.values()),
                source='RabbitMQ',
                seconds=(datetime.now() - start).total_seconds(),
                subject=message['subject'],
            ))
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def blocks(self, data):
        instance = yield self.get_instance(models.Block, id=data)
        if not instance:
            raise Return(None)
        for user in [key for key, value in self.application.clients.items() if value == instance.user_destination_id]:
            user.write_message(dumps({
                'subject': 'blocks',
                'body': instance.user_source_id,
            }))
        raise Return(None)

    @coroutine
    def messages(self, data):
        instance = yield self.get_instance(models.Message, id=data)
        if not instance:
            raise Return(None)
        for user in [key for key, value in self.application.clients.items() if value == instance.user_source_id]:
            body = yield self.get_message(instance, instance.user_source)
            user.write_message(dumps({
                'subject': 'messages',
                'body': body,
            }))
        for user in [key for key, value in self.application.clients.items() if value == instance.user_destination_id]:
            body = yield self.get_message(instance, instance.user_destination)
            user.write_message(dumps({
                'subject': 'messages',
                'body': body,
            }))
        raise Return(None)

    @coroutine
    def notifications(self, data):
        instance = yield self.get_instance(models.Notification, id=data)
        if not instance:
            raise Return(None)
        for user in [key for key, value in self.application.clients.items() if value == instance.user_id]:
            body = yield self.get_notification(instance)
            user.write_message(dumps({
                'subject': 'notifications',
                'body': body,
            }))
        raise Return(None)

    @coroutine
    def profile(self, data):
        instance = yield self.get_instance(models.User, id=data)
        if not instance:
            raise Return(None)
        ids = yield self.get_tellcard_ids(instance.id)
        for user in [key for key, value in self.application.clients.items() if value in ids]:
            user.write_message(dumps({
                'subject': 'profile',
                'body': instance.id,
            }))
        raise Return(None)

    @coroutine
    def users_locations(self, data):
        users_locations_new = yield self.get_instance(models.UserLocation, id=data)
        if not users_locations_new:
            raise Return(None)
        if not users_locations_new.point:
            raise Return(None)
        for user in [key for key, value in self.application.clients.items() if value == users_locations_new.user_id]:
            body = yield self.get_radar_post(users_locations_new)
            user.write_message(dumps({
                'subject': 'users_locations_post',
                'body': body,
            }))
        users = yield self.get_users(users_locations_new.user.id, users_locations_new.point, 999999999, True)
        for key, value in users.items():
            for k, v in self.application.clients.items():
                if v == key:
                    body = yield self.get_radar_get(key, value, users)
                    k.write_message(dumps({
                        'subject': 'users_locations_get',
                        'body': body,
                    }))
        users_locations_old = yield self.get_user_location(data, users_locations_new.user_id)
        if not users_locations_old:
            raise Return(None)
        if not vincenty(
            (users_locations_new.point.x, users_locations_new.point.y),
            (users_locations_old.point.x, users_locations_old.point.y)
        ).m > 999999999:
            raise Return(None)
        users = yield self.get_users(users_locations_old.user.id, users_locations_old.point, 999999999, False)
        for key, value in users.items():
            for k, v in self.application.clients.items():
                if v == key:
                    body = yield self.get_radar_get(key, value, users)
                    k.write_message(dumps({
                        'subject': 'users_locations_get',
                        'body': body,
                    }))
        raise Return(None)

    @coroutine
    def get_instance(self, model, id):
        attempts = 0
        while True:
            instance = model.objects.get_queryset().filter(id=id).first()
            if instance:
                raise Return(instance)
            attempts += 1
            if attempts >= 3:
                raise Return(None)
            yield sleep(1)
        raise Return(None)

    @coroutine
    def get_message(self, instance, user):
        data = serializers.MessagesGetResponse(instance, context=get_context(user)).data
        raise Return(data)

    @coroutine
    def get_notification(self, instance):
        data = serializers.NotificationsGetResponse(instance, context=get_context(instance.user)).data
        raise Return(data)

    @coroutine
    def get_radar_get(self, key, value, users):
        data = serializers.RadarGetResponse(
            [
                {
                    'hash': models.get_hash(items),
                    'items': items,
                    'position': position + 1,
                }
                for position, items in enumerate(
                    models.get_items([user[0] for user in users.values() if user[0].id != key], 5)
                )
            ],
            context=get_context(value[0]),
            many=True,
        ).data
        raise Return(data)

    @coroutine
    def get_radar_post(self, user_location):
        data = serializers.RadarPostResponse(
            models.Tellzone.objects.get_queryset().filter(
                point__distance_lte=(user_location.point, D(ft=models.Tellzone.radius())),
            ).distance(user_location.point),
            context=get_context(user_location.user),
            many=True,
        ).data
        raise Return(data)

    @coroutine
    def get_tellcard_ids(self, id):
        ids = models.Tellcard.objects.get_queryset().filter(
            user_destination_id=id,
        ).values_list('user_source_id', flat=True)
        raise Return(ids)

    @coroutine
    def get_users(self, user_id, point, radius, status):
        users = models.get_users(user_id, point, radius, status)
        raise Return(users)

    @coroutine
    def get_user_location(self, one, two):
        user_location = models.UserLocation.objects.get_queryset().filter(id__lt=one, user_id=two).first()
        raise Return(user_location)


class WebSocket(WebSocketHandler):

    def __init__(self, application, request, **kwargs):
        self.application = application
        super(WebSocket, self).__init__(application, request, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        self.stream.set_nodelay(True)

    def write_message(self, message, binary=False):
        try:
            message = loads(message)
            logger.log(DEBUG, '{clients:>3d} {source:>9s} [OUT] [         ] {subject:s}'.format(
                clients=len(self.application.clients.values()), source='WebSocket', subject=message['subject']),
            )
        except Exception:
            logger.log(CRITICAL, '{clients:>3d} {source:>9s} [OUT] [         ] {subject:s}'.format(
                clients=len(self.application.clients.values()), source='WebSocket', subject=message['subject']),
            )
            report_exc_info()
        super(WebSocket, self).write_message(message, binary=binary)

    def on_close(self):
        del self.application.clients[self]

    @coroutine
    def on_message(self, message):
        try:
            message = loads(message)
        except Exception:
            logger.log(CRITICAL, '{clients:>3d} {source:>9s} [IN ] {subject:s}'.format(
                clients=len(self.application.clients.values()), source='WebSocket', subject='message = loads(message)',
            ))
            report_exc_info()
        if not message:
            logger.log(CRITICAL, '{clients:>3d} {source:>9s} [IN ] {subject:s}'.format(
                clients=len(self.application.clients.values()), source='WebSocket', subject='if not message',
            ))
            raise Return(None)
        if 'subject' not in message or 'body' not in message:
            logger.log(CRITICAL, '{clients:>3d} {source:>9s} [IN ] {subject:s}'.format(
                clients=len(self.application.clients.values()),
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
            logger.log(DEBUG, '{clients:>3d} {source:>9s} [IN ] [{seconds:>9.2f}] {subject:s}'.format(
                clients=len(self.application.clients.values()),
                source='WebSocket',
                seconds=(datetime.now() - start).total_seconds(),
                subject=message['subject'],
            ))
        except Exception:
            report_exc_info()
        raise Return(None)

    @coroutine
    def messages(self, data):
        if self not in self.application.clients:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'if self not in clients',
                },
            }))
            raise Return(None)
        user = yield self.get_user(self.application.clients[self])
        if not user:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'if not user',
                },
            }))
            raise Return(None)
        yield self.set_messages(user, data)
        raise Return(None)

    @coroutine
    def users(self, data):
        user = models.User.objects.filter(id=data.split('.')[0]).first()
        if not user:
            self.write_message(dumps({
                'subject': 'users',
                'body': False,
            }))
            raise Return(None)
        if not user.is_valid(data):
            self.write_message(dumps({
                'subject': 'users',
                'body': False,
            }))
            raise Return(None)
        self.application.clients[self] = user.id
        self.write_message(dumps({
            'subject': 'users',
            'body': True,
        }))
        raise Return(None)

    @coroutine
    def users_locations_post(self, data):
        if self not in self.application.clients:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'if self not in self.application.clients',
                },
            }))
            raise Return(None)
        user = yield self.get_user(self.application.clients[self])
        if not user:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'if not user',
                },
            }))
            raise Return(None)
        yield self.set_users_locations_post(user, data)
        raise Return(None)

    @coroutine
    def get_blocks(self, one, two):
        count = models.Block.objects.get_queryset().filter(
            Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
        ).count()
        raise Return(count)

    @coroutine
    def get_messages(self, one, two):
        count = models.Message.objects.get_queryset().filter(
            Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
            type__in=['Response - Accepted', 'Response - Rejected', 'Message'],
        ).count()
        raise Return(count)

    @coroutine
    def get_message(self, one, two):
        message = models.Message.objects.get_queryset().filter(
            Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
        ).order_by('-inserted_at', '-id').first()
        raise Return(message)

    @coroutine
    def get_user(self, id):
        user = models.User.objects.filter(id=id).first()
        raise Return(user)

    @coroutine
    def set_message(self, user_id, data):
        message = models.Message.objects.create(
            user_source_id=user_id,
            user_source_is_hidden=data['user_source_is_hidden'] if 'user_source_is_hidden' in data else None,
            user_destination_id=data['user_destination_id'],
            user_destination_is_hidden=data['user_destination_is_hidden']
            if 'user_destination_is_hidden' in data else None,
            user_status_id=data['user_status_id'] if 'user_status_id' in data else None,
            master_tell_id=data['master_tell_id'] if 'master_tell_id' in data else None,
            type=data['type'] if 'type' in data else None,
            contents=data['contents'] if 'contents' in data else None,
            status=data['status'] if 'status' in data else 'Unread',
        )
        raise Return(message)

    @coroutine
    def set_message_attachment(self, message_id, attachment):
        models.MessageAttachment.insert(message_id, attachment)
        raise Return(None)

    @coroutine
    def set_messages(self, user, data):
        serializer = serializers.MessagesPostRequest(context=get_context(user), data=data)
        if not serializer.is_valid(raise_exception=False):
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': serializer.errors,
                },
            }))
            raise Return(None)
        data = serializer.validated_data
        if user.id == data['user_destination_id']:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'Invalid `user_destination_id`',
                },
            }))
            raise Return(None)
        count = yield self.get_blocks(user.id, data['user_destination_id'])
        if count:
            self.write_message(dumps({
                'subject': 'messages',
                'body': {
                    'errors': 'Invalid `user_destination_id`',
                },
            }))
            raise Return(None)
        count = yield self.get_messages(user.id, data['user_destination_id'])
        if not count:
            message = yield self.get_message(user.id, data['user_destination_id'])
            if message:
                if message.user_source_id == user.id:
                    if message.type == 'Request':
                        self.write_message(dumps({
                            'subject': 'messages',
                            'body': {
                                'errors': 'HTTP_409_CONFLICT',
                            },
                        }))
                        raise Return(None)
                    if message.type == 'Response - Blocked':
                        self.write_message(dumps({
                            'subject': 'messages',
                            'body': {
                                'errors': 'HTTP_403_FORBIDDEN',
                            },
                        }))
                        raise Return(None)
                if message.user_destination_id == user.id:
                    if message.type == 'Request' and data['type'] == 'Message':
                        self.write_message(dumps({
                            'subject': 'messages',
                            'body': {
                                'errors': 'HTTP_403_FORBIDDEN',
                            },
                        }))
                        raise Return(None)
                    if message.type == 'Response - Blocked':
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
        message = yield self.set_message(user.id, data)
        if 'attachments' in data:
            for attachment in data['attachments']:
                yield self.set_message_attachment(message.id, attachment)
        raise Return(None)

    @coroutine
    def set_user_location(self, user_id, data):
        models.UserLocation.objects.create(
            user_id=user_id,
            tellzone_id=data['tellzone_id'] if 'tellzone_id' in data else None,
            location=data['location'] if 'location' in data else None,
            point=data['point'] if 'point' in data else None,
            accuracies_horizontal=data['accuracies_horizontal'] if 'accuracies_horizontal' in data else None,
            accuracies_vertical=data['accuracies_vertical'] if 'accuracies_vertical' in data else None,
            bearing=data['bearing'] if 'bearing' in data else None,
            is_casting=data['is_casting'] if 'is_casting' in data else None,
        )
        raise Return(None)

    @coroutine
    def set_users_locations_post(self, user, data):
        serializer = serializers.RadarPostRequest(context=get_context(user), data=data)
        if not serializer.is_valid(raise_exception=False):
            self.write_message(dumps({
                'subject': 'users_locations_post',
                'body': {
                    'errors': serializer.errors,
                },
            }))
            raise Return(None)
        yield self.set_user_location(user.id, serializer.validated_data)
        raise Return(None)


class Command(BaseCommand):

    help = 'WebSockets'

    def handle(self, *args, **kwargs):
        application = Application(
            [
                ('/websockets/', WebSocket),
            ],
            autoreload=settings.DEBUG,
            debug=settings.DEBUG,
        )
        application.clients = {}
        server = HTTPServer(application)
        server.listen(settings.TORNADO['port'], address=settings.TORNADO['address'])
        '''
        if settings.DEBUG:
            server.listen(settings.TORNADO['port'], address=settings.TORNADO['address'])
        else:
            server.bind(settings.TORNADO['port'], address=settings.TORNADO['address'])
            server.start(0)
        '''
        IOLoop.current().add_callback(RabbitMQ, application)
        IOLoop.instance().start()


def get_context(user):
    request = Request(RequestFactory().get('/'))
    request.user = user
    return {
        'request': request,
    }
