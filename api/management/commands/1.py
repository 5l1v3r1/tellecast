# -*- coding: utf-8 -*-

from datetime import datetime
from logging import CRITICAL, DEBUG, Formatter, StreamHandler, getLogger
from traceback import print_exc

from celery import current_app
from django.conf import settings
from django.core.management.base import BaseCommand
from pika import TornadoConnection, URLParameters
from tornado.gen import coroutine, Return
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from ujson import dumps, loads

formatter = Formatter('%(asctime)s [%(levelname)8s] %(message)s')

stream_handler = StreamHandler()
stream_handler.setLevel(DEBUG)
stream_handler.setFormatter(formatter)

logger = getLogger(__name__)
logger.setLevel(DEBUG)
logger.addHandler(stream_handler)


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
            print_exc()

    def on_connection_open(self, connection):
        try:
            self.channel = connection.channel(on_open_callback=self.on_channel_open)
        except Exception:
            print_exc()

    def on_connection_open_error(self, connection, error_message):
        print error_message

    def on_connection_close(self, connection, reply_code, reply_text):
        print reply_text

    def on_channel_open(self, channel):
        try:
            self.channel.exchange_declare(
                self.on_channel_exchange_declare, durable=True, exchange='ws',
            )
        except Exception:
            print_exc()

    def on_channel_exchange_declare(self, frame):
        try:
            self.channel.queue_declare(
                self.on_channel_queue_declare, durable=True, queue='ws',
            )
        except Exception:
            print_exc()

    def on_channel_queue_declare(self, frame):
        try:
            self.channel.queue_bind(self.on_channel_queue_bind, 'ws', 'ws', routing_key='ws')
        except Exception:
            print_exc()

    def on_channel_queue_bind(self, frame):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(self.on_channel_basic_consume, queue='ws', no_ack=False)
        except Exception:
            print_exc()

    @coroutine
    def on_channel_basic_consume(self, channel, method, properties, body):
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        try:
            message = loads(body)['args'][0]
        except Exception:
            print_exc()
        if not message or 'subject' not in message or 'body' not in message:
            logger.log(CRITICAL, '[{clients:>3d}] [{source:>9s}] [   ] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()), source='RabbitMQ', subject='if not message',
            ))
            raise Return(None)
        try:
            start = datetime.now()
            if message['subject'] == 'users_locations':
                yield self.users_locations(message['body'])
            logger.log(DEBUG, '[{clients:>3d}] [{source:>9s}] [IN ] [{seconds:>9.2f}] {subject:s}'.format(
                clients=len(IOLoop.current().clients.values()),
                source='RabbitMQ',
                seconds=(datetime.now() - start).total_seconds(),
                subject=message['subject'],
            ))
        except Exception:
            print_exc()
        raise Return(None)

    @coroutine
    def users_locations(self, data):
        data = loads(data)
        for user in [key for key, value in IOLoop.current().clients.items() if value == data['user_id']]:
            user.write_message(dumps({
                'subject': 'users_locations_post',
                'body': dumps(data),
            }))
        for k, v in IOLoop.current().clients.items():
            k.write_message(dumps({
                'subject': 'users_locations_get',
                'body': dumps(data),
            }))
        for k, v in IOLoop.current().clients.items():
            k.write_message(dumps({
                'subject': 'users_locations_get',
                'body': dumps(data),
            }))
        raise Return(None)


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
            print_exc()
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
            print_exc()
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
            if message['subject'] == 'users':
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
            print_exc()
        raise Return(None)

    @coroutine
    def users(self, data):
        IOLoop.current().clients[self] = data
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
                    'errors': 'if self not in clients',
                },
            }))
            raise Return(None)
        current_app.send_task(
            'ws',
            (
                {
                    'subject': 'users_locations',
                    'body': dumps(data),
                },
            ),
            queue='ws',
            routing_key='ws',
            serializer='json',
        )
        raise Return(None)


class Command(BaseCommand):

    help = 'WebSockets'

    def handle(self, *args, **kwargs):
        server = HTTPServer(
            Application([('/websockets/', WebSocket)], autoreload=True, debug=True),
        )
        server.listen(settings.TORNADO['port'] + 1, address=settings.TORNADO['address'])
        IOLoop.current().clients = {}
        IOLoop.current().add_callback(RabbitMQ)
        IOLoop.current().start()
