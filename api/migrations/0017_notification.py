# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_shareoffer_shareuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'A', b'A'), (b'B', b'B'), (b'C', b'C'), (b'D', b'D'), (b'E', b'E'), (b'F', b'F'), (b'G', b'G'), (b'H', b'H')])),
                ('contents', jsonfield.fields.JSONField(verbose_name='Contents')),
                ('status', models.CharField(db_index=True, max_length=255, verbose_name='Status', choices=[(b'Read', b'Read'), (b'Unread', b'Unread')])),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('user', models.ForeignKey(related_name='notifications', to='api.User')),
            ],
            options={
                'ordering': ('-timestamp',),
                'db_table': 'api_notifications',
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
            bases=(models.Model,),
        ),
    ]
