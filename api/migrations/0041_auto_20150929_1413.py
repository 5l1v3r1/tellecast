# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_category_post_posttellzone'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'application/pdf', b'application/pdf'), (b'audio/*', b'audio/*'), (b'audio/aac', b'audio/aac'), (b'audio/mp4', b'audio/mp4'), (b'audio/mpeg', b'audio/mpeg'), (b'audio/mpeg3', b'audio/mpeg3'), (b'audio/x-mpeg3', b'audio/x-mpeg3'), (b'image/*', b'image/*'), (b'image/bmp', b'image/bmp'), (b'image/gif', b'image/gif'), (b'image/jpeg', b'image/jpeg'), (b'image/png', b'image/png'), (b'text/plain', b'text/plain'), (b'video/*', b'video/*'), (b'video/3gpp', b'video/3gpp'), (b'video/mp4', b'video/mp4'), (b'video/mpeg', b'video/mpeg'), (b'video/x-mpeg', b'video/x-mpeg')])),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('inserted_at', models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True)),
                ('post', models.ForeignKey(related_name='attachments', to='api.Post')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_posts_attachments',
                'verbose_name': 'Posts :: Attachment',
                'verbose_name_plural': 'Posts :: Attachments',
            },
        ),
        migrations.RemoveField(
            model_name='post',
            name='description',
        ),
        migrations.RemoveField(
            model_name='post',
            name='type',
        ),
    ]
