# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0076_version'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('access_code', models.CharField(unique=True, max_length=255, verbose_name='Access Code', db_index=True)),
                ('tellzone', models.ForeignKey(related_name='campaigns', to='api.Tellzone')),
            ],
            options={
                'ordering': ('access_code',),
                'db_table': 'api_campaigns',
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
            },
        ),
    ]
