# -*- coding: utf-8 -*-

from traceback import print_exc

from django.conf import settings
from django.core.management.base import BaseCommand
from pika import TornadoConnection, URLParameters
from tornado.gen import coroutine
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from ujson import dumps, loads

from api import models, serializers

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
        print 'error_message', error_message

    def on_connection_close(self, connection, reply_code, reply_text):
        print 'RabbitMQHandler.on_connection_close()'
        print 'reply_code', reply_code
        print 'reply_text', reply_text

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
            if message['subject'] == 'notifications':
                notification = models.Notification.objects.get_queryset().filter(id=message['body']).first()
                if notification:
                    if notification.user_id in clients:
                        print 'clients[notification.user_id].write_message()'
                        clients[notification.user_id].write_message(
                            dumps({
                                'subject': 'notifications',
                                'body': serializers.NotificationsGetResponse(
                                    notification,
                                    context={},
                                ).data,
                            })
                        )
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
        print 'args', args
        print 'kwargs', kwargs

    def write_message(self, message, binary=False):
        super(WebSocketHandler, self).write_message(message, binary)
        print 'WebSocketHandler.write_message()'
        print 'message', message

    def on_close(self):
        print 'WebSocketHandler.on_close()'
        for key, value in clients.items():
            if value is self:
                del clients[key]
                return

    def on_connection_close(self):
        super(WebSocketHandler, self).on_connection_close()
        print 'WebSocketHandler.on_connection_close()'

    def on_pong(self, data):
        print 'WebSocketHandler.on_pong()'
        print 'data', data

    def get_id(self):
        print 'WebSocketHandler.get_id()'
        for key, value in clients.items():
            if value is self:
                return key
        return 0

    @coroutine
    def on_message(self, message):
        print 'WebSocketHandler.on_message()'
        print 'message', message
        try:
            message = loads(message)
            if message['subject'] == 'token':
                user = None
                try:
                    user = models.User.objects.filter(id=message['body'].split('.')[0]).first()
                except Exception:
                    self.write_message(dumps({
                        'subject': 'token',
                        'body': False,
                    }))
                    print_exc()
                    return
                if not user:
                    self.write_message(dumps({
                        'subject': 'token',
                        'body': False,
                    }))
                    print 'if not user'
                    return
                if not user.is_valid(message['body']):
                    self.write_message(dumps({
                        'subject': 'token',
                        'body': False,
                    }))
                    print 'if not user.is_valid(message[\'token\'])'
                    return
                if user.id not in clients:
                    self.write_message(dumps({
                        'subject': 'token',
                        'body': True,
                    }))
                    clients[user.id] = self
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
