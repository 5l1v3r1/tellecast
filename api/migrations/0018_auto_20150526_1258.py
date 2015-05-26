# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255, verbose_name='Key', db_index=True)),
                ('value', models.CharField(max_length=255, verbose_name='Value', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('user', models.ForeignKey(related_name='settings', to='api.User')),
            ],
            options={
                'ordering': ('user', 'key'),
                'db_table': 'api_users_settings',
                'verbose_name': 'user setting',
                'verbose_name_plural': 'user settings',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='usersetting',
            unique_together=set([('user', 'key')]),
        ),
    ]
