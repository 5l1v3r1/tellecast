# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy
from os import environ, remove
from os.path import getsize
from tempfile import mkstemp
from uuid import uuid4

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.ses import connect_to_region
from celery import Celery, current_app
from celery.signals import task_failure
from celery.utils.log import get_task_logger
from django.conf import settings
from kombu import Exchange, Queue
from PIL import Image
from pilkit.processors import ProcessorPipeline, ResizeToFit, Transpose
from raven import Client
from requests import request

environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from api import models  # noqa

celery = Celery('api.tasks')
celery.conf.update(
    BROKER_POOL_LIMIT=0,
    CELERY_ACCEPT_CONTENT=[
        'json',
    ],
    CELERY_ACKS_LATE=True,
    CELERY_QUEUES=(
        Queue(
            'api.tasks.email_notifications',
            Exchange('api.tasks.email_notifications'),
            routing_key='api.tasks.email_notifications',
        ),
        Queue(
            'api.tasks.push_notifications',
            Exchange('api.tasks.push_notifications'),
            routing_key='api.tasks.push_notifications',
        ),
        Queue(
            'api.tasks.reports',
            Exchange('api.tasks.reports'),
            routing_key='api.tasks.reports',
        ),
        Queue(
            'api.tasks.thumbnails',
            Exchange('api.tasks.thumbnails'),
            routing_key='api.tasks.thumbnails',
        ),
    ),
    CELERY_IGNORE_RESULT=True,
    CELERY_RESULT_SERIALIZER='json',
    CELERY_ROUTES={
        'api.tasks.email_notifications': {
            'queue': 'api.tasks.email_notifications',
        },
        'api.tasks.push_notifications': {
            'queue': 'api.tasks.push_notifications',
        },
        'api.tasks.reports': {
            'queue': 'api.tasks.reports',
        },
        'api.tasks.thumbnails_1': {
            'queue': 'api.tasks.thumbnails',
        },
        'api.tasks.thumbnails_2': {
            'queue': 'api.tasks.thumbnails',
        },
    },
    CELERY_TASK_SERIALIZER='json',
    CELERYD_LOG_FORMAT='[%(asctime)s: %(levelname)s] %(message)s',
    CELERYD_POOL_RESTARTS=True,
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERYD_TASK_SOFT_TIME_LIMIT=3600,
    CELERYD_TASK_TIME_LIMIT=7200,
)

client = Client(settings.RAVEN_CONFIG['dsn'])

logger = get_task_logger(__name__)


@task_failure.connect
def handle_task_failure(**kwargs):
    client.captureException(extra=kwargs)


@celery.task
def email_notifications(id, type):
    user = models.User.objects.get_queryset().filter(id=id).first()
    if not user:
        return
    if type == 'reset_password':
        connect_to_region(
            settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        ).send_email(
            settings.AWS_EMAIL,
            'Reset Password',
            u'''
Hi {first_name:s},

Please use the following link to reset your password.

https://invite.tellzone.com/reset-password/{id:d}/{hash:s}/

From,
Tellzone
            '''.strip().format(first_name=user.first_name, id=user.id, hash=user.hash),
            [
                user.email,
            ],
        )
    if type == 'verify':
        connect_to_region(
            settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        ).send_email(
            settings.AWS_EMAIL,
            'Verify',
            u'''
Hi {first_name:s},

Please use the following link to verify.

https://invite.tellzone.com/verify/{id:d}/{hash:s}/

From,
Tellzone
            '''.strip().format(first_name=user.first_name, id=user.id, hash=user.hash),
            [
                user.email,
            ],
        )


@celery.task
def push_notifications(user_id, json):
    for device in models.DeviceAPNS.objects.get_queryset().filter(user_id=user_id):
        device.send_message(deepcopy(json))
    for device in models.DeviceGCM.objects.get_queryset().filter(user_id=user_id):
        device.send_message(deepcopy(json))


@celery.task
def reports(id):
    instance = models.Block.objects.get_queryset().filter(id=id).first()
    if not instance:
        return
    body = '''
    {source_name:s} ({source_email:s}) has reported {destination_name:s} ({destination_email:s}) in {domain:s}
    '''.strip().format(
        source_name=get_name(instance.user_source.first_name, instance.user_source.last_name),
        source_email=instance.user_source.email,
        destination_name=get_name(instance.user_destination.first_name, instance.user_destination.last_name),
        destination_email=instance.user_destination.email,
        domain=settings.DESK_COM['domain'],
    )
    json = {
        'id': uuid4().__str__(),
        'priority': 10,
        'status': 'new',
        'type': 'email',
        'custom_fields': {
            'domain': settings.DESK_COM['domain'],
            'user_destination': {
                'id': instance.user_destination.id,
                'email': instance.user_destination.email,
                'first_name': instance.user_destination.first_name,
                'last_name': instance.user_destination.last_name,
            },
            'user_source': {
                'id': instance.user_source.id,
                'email': instance.user_source.email,
                'first_name': instance.user_source.first_name,
                'last_name': instance.user_source.last_name,
            },
            'timestamp': instance.timestamp.isoformat(),
        },
        'message': {
            'body': body,
            'direction': 'in',
            'from': instance.user_source.email,
            'name': get_name(instance.user_source.first_name, instance.user_source.last_name),
            'subject': 'Report',
            'to': settings.DESK_COM['username'],
        },
        '_links': {
            'assigned_group': {
                'class': 'group',
                'href': '/api/v2/groups/616498',
            },
        },
    }
    request(
        'POST',
        'https://{subdomain:s}.desk.com/api/v2/cases'.format(subdomain=settings.DESK_COM['subdomain']),
        auth=(settings.DESK_COM['username'], settings.DESK_COM['password']),
        json=json,
    )


@celery.task
def thumbnails_1(table, id):
    if table == 'User':
        instance = models.User.objects.get_queryset().filter(id=id).first()
        if not instance:
            logger.critical('{table:s}/{id:d}: if not instance'.format(table=table, id=id))
            raise thumbnails_1.retry(countdown=1)
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo_original, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo_original, 'image/*', 'small', 320, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo_preview, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo_preview, 'image/*', 'small', 320, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        return
    if table == 'UserPhoto':
        instance = models.UserPhoto.objects.get_queryset().filter(id=id).first()
        if not instance:
            logger.critical('{table:s}/{id:d}: if not instance'.format(table=table, id=id))
            raise thumbnails_1.retry(countdown=1)
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_original, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_original, 'image/*', 'small', 320, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_preview, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_preview, 'image/*', 'small', 320, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        return
    if table == 'UserStatusAttachment':
        instance = models.UserStatusAttachment.objects.get_queryset().filter(id=id).first()
        if not instance:
            logger.critical('{table:s}/{id:d}: if not instance'.format(table=table, id=id))
            raise thumbnails_1.retry(countdown=1)
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_original, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_original, 'image/*', 'small', 685, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_preview, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.string_preview, 'image/*', 'small', 685, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        return
    if table == 'SlaveTell':
        instance = models.SlaveTell.objects.get_queryset().filter(id=id).first()
        if not instance:
            logger.critical('{table:s}/{id:d}: if not instance'.format(table=table, id=id))
            raise thumbnails_1.retry(countdown=1)
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo, 'image/*', 'large', 1920, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        current_app.send_task(
            'api.tasks.thumbnails_2',
            (instance.photo, 'image/*', 'small', 320, None,),
            queue='api.tasks.thumbnails',
            routing_key='api.tasks.thumbnails',
            serializer='json',
        )
        if instance.type.startswith('image'):
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.contents_original, instance.type, 'large', 1920, 1048576,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.contents_original, instance.type, 'small', 685, 524288,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.contents_preview, instance.type, 'large', 1920, 1048576,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.contents_preview, instance.type, 'small', 685, 524288,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
        return
    if table == 'PostAttachment':
        instance = models.PostAttachment.objects.get_queryset().filter(id=id).first()
        if not instance:
            logger.critical('{table:s}/{id:d}: if not instance'.format(table=table, id=id))
            raise thumbnails_1.retry(countdown=1)
        if instance.type.startswith('image'):
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.string_original, instance.type, 'large', 1920, None,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.string_original, instance.type, 'small', 685, None,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.string_preview, instance.type, 'large', 1920, None,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
            current_app.send_task(
                'api.tasks.thumbnails_2',
                (instance.string_preview, instance.type, 'small', 685, None,),
                queue='api.tasks.thumbnails',
                routing_key='api.tasks.thumbnails',
                serializer='json',
            )
        return


@celery.task
def thumbnails_2(name, type, prefix, width, bytes):
    bucket = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY).get_bucket(settings.AWS_BUCKET)
    if not name:
        logger.critical('{name:s}: if not name (#1)'.format(name=name))
        return
    name = name.split('/')[-1]
    if not name:
        logger.critical('{name:s}: if not name (#2)'.format(name=name))
        return
    key = bucket.get_key(name)
    if not key:
        logger.critical('{name:s}: if not key'.format(name=name))
        return
    n = '{prefix:s}_{suffix:s}'.format(prefix=prefix, suffix=name)
    k = bucket.get_key(n)
    if k:
        logger.info('{name:s}: Success (#1)'.format(name=n))
        return
    _, source = mkstemp()
    key.get_contents_to_filename(source)
    destination = None
    try:
        destination = get_destination(source, name, type, width, bytes)
    except Exception:
        client.captureException()
    if not destination:
        logger.critical('{name:s}: Failure'.format(name=n))
        return
    k = Key(bucket)
    k.key = n
    k.set_contents_from_filename(destination)
    remove(destination)
    remove(source)
    logger.info('{name:s}: Success (#2)'.format(name=n))
    return


def get_destination(source, name, type, width, bytes):
    if not type.startswith('image'):
        return
    format = type.split('/')[1]
    if format == '*':
        format = ''
        try:
            format = name.split('.')[-1].lower()
        except Exception:
            pass
        if not format:
            format = 'png'
        if format == 'jpg':
            format = 'jpeg'
    _, destination = mkstemp()
    quality = 75
    while True:
        try:
            ProcessorPipeline([
                Transpose(),
                ResizeToFit(width=width, upscale=False),
            ]).process(
                Image.open(source),
            ).save(
                destination, format=format, optimize=True, quality=quality,
            )
        except IOError:
            break
        if not bytes:
            break
        if getsize(destination) <= bytes:
            break
        if quality <= 5:
            break
        quality = quality - 5
    return destination


def get_name(first_name, last_name):
    return ' '.join(filter(None, [first_name, last_name]))
