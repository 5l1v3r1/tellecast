# -*- coding: utf-8 -*-

from os import remove
from tempfile import mkstemp
from traceback import print_exc

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image
from pilkit.processors import ProcessorPipeline, ResizeToFit, Transpose
from rollbar import report_exc_info

from api import models


class Command(BaseCommand):

    help = 'Thumbnails'

    def __init__(self, *args, **kwargs):
        self.bucket = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY).get_bucket('tellecast')
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **kwargs):
        for slave_tell in models.SlaveTell.objects.get_queryset():
            log(0, 'slave_tells :: {id} :: photo'.format(id=slave_tell.id))
            self.process(
                slave_tell.photo,
                'image/*',
                (
                    {
                        'name': 'large',
                        'width': 1920,
                    },
                    {
                        'name': 'small',
                        'width': 320,
                    },
                ),
            )
            if slave_tell.type.startswith('image'):
                log(0, 'slave_tells :: {id} :: contents'.format(id=slave_tell.id))
                self.process(
                    slave_tell.contents,
                    slave_tell.type,
                    (
                        {
                            'name': 'large',
                            'width': 1920,
                        },
                        {
                            'name': 'small',
                            'width': 685,
                        },
                    ),
                )
        for user in models.User.objects.get_queryset():
            log(0, 'users :: {id} :: photo'.format(id=user.id))
            self.process(
                user.photo,
                'image/*',
                (
                    {
                        'name': 'large',
                        'width': 1920,
                    },
                    {
                        'name': 'small',
                        'width': 320,
                    },
                ),
            )
        for user_photo in models.UserPhoto.objects.get_queryset():
            log(
                0,
                'users :: {users_id} :: photos :: {users_photos_id} :: string'.format(
                    users_id=user_photo.user_id,
                    users_photos_id=user_photo.id,
                ),
            )
            self.process(
                user_photo.string,
                'image/*',
                (
                    {
                        'name': 'large',
                        'width': 1920,
                    },
                    {
                        'name': 'small',
                        'width': 320,
                    },
                ),
            )
        for user_status_attachment in models.UserStatusAttachment.objects.get_queryset():
            log(
                0,
                (
                    'users :: {users_id} :: statuses :: {users_statuses_id} :: attachments :: '
                    '{users_statuses_attachments_id} :: string'
                ).format(
                    users_id=user_status_attachment.user_status.user_id,
                    users_statuses_id=user_status_attachment.user_status_id,
                    users_statuses_attachments_id=user_status_attachment.id,
                ),
            )
            self.process(
                user_status_attachment.string,
                'image/*',
                (
                    {
                        'name': 'large',
                        'width': 1920,
                    },
                    {
                        'name': 'small',
                        'width': 685,
                    },
                ),
            )

    def process(self, name, type, items):
        if not name:
            log(1, 'not name (#1)')
            return
        name = name.split('/')[-1]
        if not name:
            log(1, 'not name (#2)')
            return
        log(1, 'name = {name}'.format(name=name))
        log(1, 'type = {type}'.format(type=type))
        key = self.bucket.get_key(name)
        if not key:
            log(1, 'not key')
            return
        _, source = mkstemp()
        key.get_contents_to_filename(source)
        for item in items:
            n = '{prefix}_{suffix}'.format(prefix=item['name'], suffix=name)
            log(1, n)
            k = self.bucket.get_key(n)
            if k:
                log(2, 'Success (#1)')
            else:
                destination = None
                try:
                    destination = self.get_thumbnail(source, name, type, item['width'])
                except Exception:
                    print_exc()
                    report_exc_info()
                if destination:
                    k = Key(self.bucket)
                    k.key = n
                    k.set_contents_from_filename(destination)
                    remove(destination)
                    log(2, 'Success (#2)')
                else:
                    log(2, 'Failure')
        remove(source)

    def get_thumbnail(self, source, name, type, width):
        if type.startswith('image'):
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
            ProcessorPipeline([
                Transpose(),
                ResizeToFit(width=width, upscale=False),
            ]).process(
                Image.open(source)
            ).save(destination, format=format, quality=75)
            return destination


def log(level, message):
    if isinstance(message, basestring):
        message = message.rstrip()
    print '{level}{message}'.format(level=' ' * 4 * level, message=message)
