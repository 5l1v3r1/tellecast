# -*- coding: utf-8 -*-

from contextlib import closing
from traceback import print_exc

from django.conf import settings
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.test.client import RequestFactory
from geopy.distance import vincenty
from pika import TornadoConnection, URLParameters
from rest_framework.request import Request
from tornado.gen import coroutine
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from ujson import dumps, loads

from api import models, serializers, views

clients = {}


class RabbitMQHandler(object):

    @coroutine
    def __init__(self):
        try:
            self.connection = TornadoConnection(
                parameters=URLParameters(settings.BROKER),
                on_close_callback=self.on_connection_close,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
            )
        except Exception:
            print_exc()

    def on_connection_open(self, connection):
        print 'RabbitMQHandler.on_connection_open()'
        try:
            self.channel = connection.channel(on_open_callback=self.on_channel_open)
        except Exception:
            print_exc()

    def on_connection_open_error(self, connection, error_message):
        print 'RabbitMQHandler.on_connection_open_error()'
        try:
            print 'error_message', error_message
        except Exception:
            print_exc()

    def on_connection_close(self, connection, reply_code, reply_text):
        print 'RabbitMQHandler.on_connection_close()'
        try:
            print 'reply_code', reply_code
            print 'reply_text', reply_text
        except Exception:
            print_exc()

    def on_channel_open(self, channel):
        print 'RabbitMQHandler.on_channel_open()'
        try:
            self.channel.exchange_declare(
                self.on_channel_exchange_declare,
                durable=True,
                exchange='api.management.commands.websockets',
            )
        except Exception:
            print_exc()

    def on_channel_exchange_declare(self, frame):
        print 'RabbitMQHandler.on_channel_exchange_declare()'
        try:
            self.channel.queue_declare(
                self.on_channel_queue_declare,
                durable=True,
                queue='api.management.commands.websockets',
            )
        except Exception:
            print_exc()

    def on_channel_queue_declare(self, frame):
        print 'RabbitMQHandler.on_channel_queue_declare()'
        try:
            self.channel.queue_bind(
                self.on_channel_queue_bind,
                'api.management.commands.websockets',
                'api.management.commands.websockets',
                routing_key='api.management.commands.websockets',
            )
        except Exception:
            print_exc()

    def on_channel_queue_bind(self, frame):
        print 'RabbitMQHandler.on_channel_queue_bind()'
        try:
            self.channel.basic_consume(
                self.on_channel_basic_consume,
                queue='api.management.commands.websockets',
                no_ack=False,
            )
        except Exception:
            print_exc()

    def on_channel_basic_consume(self, channel, method, properties, body):
        print 'RabbitMQHandler.on_channel_basic_consume()'
        try:
            message = loads(body)['args'][0]
            print 'message', message
            if message['subject'] == 'messages':
                instance = models.Message.objects.get_queryset().filter(id=message['body']).first()
                if instance:
                    for key, value in clients.items():
                        if value == instance.user_source_id:
                            key.write_message(
                                dumps({
                                    'subject': 'messages',
                                    'body': serializers.MessagesGetResponse(
                                        instance,
                                        context=get_context(instance.user_source),
                                    ).data,
                                })
                            )
                            print 'key.write_message()'
                        if value == instance.user_destination_id:
                            key.write_message(
                                dumps({
                                    'subject': 'messages',
                                    'body': serializers.MessagesGetResponse(
                                        instance,
                                        context=get_context(instance.user_destination),
                                    ).data,
                                })
                            )
                            print 'key.write_message()'
            if message['subject'] == 'notifications':
                instance = models.Notification.objects.get_queryset().filter(id=message['body']).first()
                if instance:
                    for key, value in clients.items():
                        if value == instance.user_id:
                            key.write_message(
                                dumps({
                                    'subject': 'notifications',
                                    'body': serializers.NotificationsGetResponse(
                                        instance,
                                        context=get_context(instance.user),
                                    ).data,
                                })
                            )
                            print 'key.write_message()'
            if message['subject'] == 'users_locations':
                users_locations_new = models.UserLocation.objects.get_queryset().filter(id=message['body']).first()
                if users_locations_new:
                    if users_locations_new.point:
                        for key, value in clients.items():
                            if value == users_locations_new.user_id:
                                key.write_message(
                                    dumps({
                                        'subject': 'users_locations_post',
                                        'body': serializers.RadarPostResponse(
                                            models.Tellzone.objects.get_queryset().filter(
                                                point__distance_lte=(
                                                    users_locations_new.point, D(ft=models.Tellzone.radius()),
                                                ),
                                            ).distance(
                                                users_locations_new.point,
                                            ),
                                            context=get_context(users_locations_new.user),
                                            many=True,
                                        ).data,
                                    })
                                )
                                print 'key.write_message()'
                    users = models.get_users(
                        users_locations_new.user.id,
                        users_locations_new.point,
                        models.Tellzone.radius(),
                        True,
                    )
                    for key, value in users.items():
                        for k, v in clients.items():
                            if v == key:
                                k.write_message(
                                    dumps({
                                        'subject': 'users_locations_get',
                                        'body': serializers.RadarGetResponse(
                                            [
                                                {
                                                    'items': items,
                                                    'position': position + 1,
                                                }
                                                for position, items in enumerate(
                                                    models.get_items(
                                                        [
                                                            user[0]
                                                            for user in sorted(
                                                                users.values(),
                                                                key=lambda user: (user[2], user[0].id,)
                                                            )
                                                            if user[0].id != key
                                                        ],
                                                        5
                                                    )
                                                )
                                            ],
                                            context=get_context(value[0]),
                                            many=True,
                                        ).data,
                                    })
                                )
                                print 'k.write_message()'
                    users_locations_old = models.UserLocation.objects.get_queryset().filter(
                        id__lt=message['body'],
                        user_id=users_locations_new.user_id
                    ).first()
                    if users_locations_old:
                        if vincenty(
                            (users_locations_new.point.x, users_locations_new.point.y),
                            (users_locations_old.point.x, users_locations_old.point.y)
                        ).m > models.Tellzone.radius():
                            users = models.get_users(
                                users_locations_old.user.id,
                                users_locations_old.point,
                                models.Tellzone.radius(),
                                include_user_id=False
                            )
                            for key, value in users.items():
                                for k, v in clients.items():
                                    if v == key:
                                        k.write_message(
                                            dumps({
                                                'subject': 'users_locations_get',
                                                'body': serializers.RadarGetResponse(
                                                    [
                                                        {
                                                            'items': items,
                                                            'position': position + 1,
                                                        }
                                                        for position, items in enumerate(
                                                            models.get_items(
                                                                [
                                                                    user[0]
                                                                    for user in sorted(
                                                                        users.values(),
                                                                        key=lambda user: (user[2], user[0].id,)
                                                                    )
                                                                    if user[0].id != key
                                                                ],
                                                                5
                                                            )
                                                        )
                                                    ],
                                                    context=get_context(value[0]),
                                                    many=True,
                                                ).data,
                                            })
                                        )
                                        print 'k.write_message()'
            self.channel.basic_ack(method.delivery_tag)
        except Exception:
            print_exc()


class WebSocketHandler(WebSocketHandler):

    def check_origin(self, origin):
        print 'WebSocketHandler.check_origin()'
        return True

    def open(self):
        print 'WebSocketHandler.open()'
        self.stream.set_nodelay(True)

    def send_error(self, *args, **kwargs):
        super(WebSocketHandler, self).send_error(*args, **kwargs)
        print 'WebSocketHandler.send_error()'
        try:
            print 'args', args
            print 'kwargs', kwargs
            print 'status_code', args[0]
            print 'exc_info', kwargs['exc_info']
        except Exception:
            print_exc()

    def write_message(self, message, binary=False):
        super(WebSocketHandler, self).write_message(message, binary)
        print 'WebSocketHandler.write_message()'
        try:
            print 'message', message
        except Exception:
            print_exc()

    def on_close(self):
        print 'WebSocketHandler.on_close()'
        del clients[self]

    def on_connection_close(self):
        super(WebSocketHandler, self).on_connection_close()
        print 'WebSocketHandler.on_connection_close()'

    def on_pong(self, data):
        print 'WebSocketHandler.on_pong()'
        try:
            print 'data', data
        except Exception:
            print_exc()

    @coroutine
    def on_message(self, message):
        print 'WebSocketHandler.on_message()'
        try:
            print 'message', message
        except Exception:
            print_exc()
        try:
            message = loads(message)
            if message['subject'] == 'messages':
                if self not in clients:
                    print 'if self not in clients'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'if self not in clients',
                        },
                    }))
                    print 'self.write_message()'
                    return
                user = models.User.objects.filter(id=clients[self]).first()
                if not user:
                    print 'if not user'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'if not user',
                        },
                    }))
                    print 'self.write_message()'
                    return
                serializer = serializers.MessagesPostRequest(context=get_context(user), data=message['body'])
                if not serializer.is_valid(raise_exception=False):
                    print 'if not serializer.is_valid(raise_exception=False)'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': serializer.errors,
                        },
                    }))
                    print 'self.write_message()'
                    return
                if views.is_blocked(user.id, serializer.validated_data['user_destination_id']):
                    print 'if is_blocked()'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'Invalid `user_destination_id`',
                        },
                    }))
                    print 'self.write_message()'
                    return
                if user.id == serializer.validated_data['user_destination_id']:
                    print 'if user.id == serializer.validated_data[\'user_destination_id\']'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'Invalid `user_destination_id`',
                        },
                    }))
                    print 'self.write_message()'
                    return
                if not models.Message.objects.get_queryset().filter(
                    Q(user_source_id=user.id, user_destination_id=serializer.validated_data['user_destination_id']) |
                    Q(user_source_id=serializer.validated_data['user_destination_id'], user_destination_id=user.id),
                    type__in=[
                        'Response - Accepted',
                        'Response - Deferred',
                        'Response - Rejected',
                        'Message',
                    ],
                ).count():
                    message = models.Message.objects.get_queryset().filter(
                        Q(
                            user_source_id=user.id,
                            user_destination_id=serializer.validated_data['user_destination_id'],
                        ) |
                        Q(
                            user_source_id=serializer.validated_data['user_destination_id'],
                            user_destination_id=user.id,
                        ),
                    ).order_by(
                        '-inserted_at',
                        '-id',
                    ).first()
                    if message:
                        if message.user_source_id == user.id:
                            if message.type == 'Request':
                                print 'if message.type == \'Request\''
                                self.write_message(dumps({
                                    'subject': 'messages',
                                    'body': {
                                        'errors': 'HTTP_409_CONFLICT',
                                    },
                                }))
                                print 'self.write_message()'
                                return
                            if message.type == 'Response - Blocked':
                                print 'if message.type == \'Response - Blocked\''
                                self.write_message(dumps({
                                    'subject': 'messages',
                                    'body': {
                                        'errors': 'HTTP_403_FORBIDDEN',
                                    },
                                }))
                                print 'self.write_message()'
                                return
                        if message.user_destination_id == user.id:
                            if message.type == 'Request' and serializer.validated_data['type'] == 'Message':
                                print (
                                    'if message.type == \'Request\' and '
                                    'serializer.validated_data[\'type\'] == \'Message\''
                                )
                                self.write_message(dumps({
                                    'subject': 'messages',
                                    'body': {
                                        'errors': 'HTTP_403_FORBIDDEN',
                                    },
                                }))
                                print 'self.write_message()'
                                return
                            if message.type == 'Response - Blocked':
                                print 'if message.type == \'Response - Blocked\''
                                self.write_message(dumps({
                                    'subject': 'messages',
                                    'body': {
                                        'errors': 'HTTP_403_FORBIDDEN',
                                    },
                                }))
                                print 'self.write_message()'
                                return
                    else:
                        if not serializer.validated_data['type'] == 'Request':
                            print 'if not serializer.validated_data[\'type\'] == \'Request\''
                            self.write_message(dumps({
                                'subject': 'messages',
                                'body': {
                                    'errors': 'HTTP_403_FORBIDDEN',
                                },
                            }))
                            print 'self.write_message()'
                            return
                serializer.insert()
                return
            if message['subject'] == 'users':
                user = None
                try:
                    user = models.User.objects.filter(id=message['body'].split('.')[0]).first()
                except Exception:
                    print 'except Exception'
                    print_exc()
                    self.write_message(dumps({
                        'subject': 'users',
                        'body': False,
                    }))
                    print 'self.write_message()'
                    return
                if not user:
                    print 'if not user'
                    self.write_message(dumps({
                        'subject': 'users',
                        'body': False,
                    }))
                    print 'self.write_message()'
                    return
                if not user.is_valid(message['body']):
                    print 'if not user.is_valid(message[\'body\'])'
                    self.write_message(dumps({
                        'subject': 'users',
                        'body': False,
                    }))
                    print 'self.write_message()'
                    return
                clients[self] = user.id
                self.write_message(dumps({
                    'subject': 'users',
                    'body': True,
                }))
                print 'self.write_message()'
                return
            if message['subject'] == 'users_locations_post':
                if self not in clients:
                    print 'if self not in clients'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'if self not in clients',
                        },
                    }))
                    print 'if self not in clients'
                    return
                user = models.User.objects.filter(id=clients[self]).first()
                if not user:
                    print 'if not user'
                    self.write_message(dumps({
                        'subject': 'messages',
                        'body': {
                            'errors': 'if not user',
                        },
                    }))
                    print 'self.write_message()'
                    return
                serializer = serializers.RadarPostRequest(context=get_context(user), data=message['body'])
                if not serializer.is_valid(raise_exception=False):
                    print 'if not serializer.is_valid(raise_exception=False)'
                    self.write_message(dumps({
                        'subject': 'users_locations_post',
                        'body': {
                            'errors': serializer.errors,
                        },
                    }))
                    print 'self.write_message()'
                    return
                serializer.insert()
                return
        except Exception:
            print_exc()


class Command(BaseCommand):

    help = 'WebSockets'

    def handle(self, *args, **kwargs):
        server = HTTPServer(
            Application(
                [
                    ('/websockets/', WebSocketHandler),
                ],
                autoreload=settings.DEBUG,
                debug=settings.DEBUG,
            )
        )
        server.listen(settings.TORNADO['port'], address=settings.TORNADO['address'])
        IOLoop.current().add_callback(RabbitMQHandler)
        IOLoop.instance().start()


def get_context(user):
    request = Request(RequestFactory().get('/'))
    request.user = user
    return {
        'request': request,
    }
