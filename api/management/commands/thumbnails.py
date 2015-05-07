# -*- coding: utf-8 -*-

from os import remove
from tempfile import mkstemp

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image
from pilkit.processors import ProcessorPipeline, ResizeToFit, Transpose

from api import models


class Command(BaseCommand):

    help = 'Thumbnails'

    def __init__(self, *args, **kwargs):
        self.bucket = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY).get_bucket('tellecast')
        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **kwargs):
        for user in models.User.objects.all():
            print 'user.photo', user.id
            self.process(user.photo, 'image/*', (1920, 320,))
            for photo in user.photos.get_queryset().all():
                print 'user.photos[].string', photo.id
                self.process(photo.string, 'image/*', (1920, 320,))
        for slave_tell in models.SlaveTell.objects.all():
            print 'slave_tell.photo', slave_tell.id
            self.process(slave_tell.photo, 'image/*', (1920, 320,))
            if slave_tell.type.startswith('audio'):
                continue
            if slave_tell.type == 'text/plain':
                continue
            print 'slave_tell.contents', slave_tell.id
            self.process(slave_tell.contents, slave_tell.type, (1920, 685,))

    def process(self, name, type, widths):
        if not name:
            return
        name = name.split('/')[-1]
        if not name:
            return
        print '    ', name
        print '    ', type
        key = self.bucket.get_key(name)
        if not key:
            print '        ', 'if not key'
            return
        _, source = mkstemp()
        key.get_contents_to_filename(source)
        print '        ', 'large'
        name_large = 'large_%(name)s' % {
            'name': name,
        }
        key_large = self.bucket.get_key(name_large)
        if key_large:
            print '            ', 'Success (#1)'
        else:
            destination = None
            try:
                destination = self.get_thumbnail(source, type, name, widths[0])
            except Exception:
                from traceback import print_exc
                print_exc()
            if destination:
                key_large = Key(self.bucket)
                key_large.key = name_large
                key_large.set_contents_from_filename(destination)
                remove(destination)
                print '            ', 'Success (#2)'
            else:
                print '            ', 'Failure'
        print '        ', 'small'
        name_small = 'small_%(name)s' % {
            'name': name,
        }
        key_small = self.bucket.get_key(name_small)
        if key_small:
            print '            ', 'Success (#1)'
        else:
            destination = None
            try:
                destination = self.get_thumbnail(source, type, name, widths[1])
            except Exception:
                from traceback import print_exc
                print_exc()
            if destination:
                key_small = Key(self.bucket)
                key_small.key = name_small
                key_small.set_contents_from_filename(destination)
                remove(destination)
                print '            ', 'Success (#2)'
            else:
                print '            ', 'Failure'
        remove(source)

    def get_thumbnail(self, source, type, name, width):
        if type.startswith('application'):
            pass
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
            _, destination = mkstemp()
            ProcessorPipeline([
                Transpose(),
                ResizeToFit(width=width, upscale=False),
            ]).process(
                Image.open(source)
            ).save(destination, format=format)
            return destination
        if type.startswith('video'):
            pass
