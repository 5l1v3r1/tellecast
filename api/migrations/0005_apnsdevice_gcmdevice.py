# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuidfield.fields
import push_notifications.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20150407_1409'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceAPNS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
                ('device_id', uuidfield.fields.UUIDField(max_length=32, db_index=True)),
                ('registration_id', models.CharField(max_length=255, verbose_name='Registration ID', db_index=True)),
                ('user', models.ForeignKey(related_name='+', to='api.User')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_devices_apns',
                'verbose_name': 'APNS Device',
                'verbose_name_plural': 'APNS Devices',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DeviceGCM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
                ('device_id', push_notifications.fields.HexIntegerField(max_length=255, verbose_name='Device ID', db_index=True)),
                ('registration_id', models.TextField(max_length=255, verbose_name='Registration ID', db_index=True)),
                ('user', models.ForeignKey(related_name='+', to='api.User')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_devices_gcm',
                'verbose_name': 'GCM Device',
                'verbose_name_plural': 'GCM Devices',
            },
            bases=(models.Model,),
        ),
    ]
