# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'Message', b'Message'), (b'Request', b'Request'), (b'Response - Accepted', b'Response - Accepted'), (b'Response - Blocked', b'Response - Blocked'), (b'Response - Deferred', b'Response - Deferred'), (b'Response - Rejected', b'Response - Rejected')])),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('status', models.CharField(db_index=True, max_length=255, verbose_name='Status', choices=[(b'Read', b'Read'), (b'Unread', b'Unread')])),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('master_tell', models.ForeignKey(related_name='+', blank=True, to='api.MasterTell', null=True)),
                ('user_destination', models.ForeignKey(related_name='+', to='api.User')),
                ('user_source', models.ForeignKey(related_name='+', to='api.User')),
                ('user_status', models.ForeignKey(related_name='+', blank=True, to='api.UserStatus', null=True)),
            ],
            options={
                'ordering': ('-inserted_at',),
                'db_table': 'api_messages',
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessageAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('message', models.ForeignKey(related_name='attachments', to='api.Message')),
            ],
            options={
                'ordering': ('message', 'position'),
                'db_table': 'api_messages_attachments',
                'verbose_name': 'Message Attachment',
                'verbose_name_plural': 'Message Attachments',
            },
            bases=(models.Model,),
        ),
    ]
