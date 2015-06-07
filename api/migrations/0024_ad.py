# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_auto_20150605_1626'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slot', models.CharField(default=b'Example #1', choices=[(b'Example #1', b'Example #1'), (b'Example #2', b'Example #2'), (b'Example #3', b'Example #3')], max_length=255, help_text='(...to be finalized...)', verbose_name='Slot', db_index=True)),
                ('type', models.CharField(default=b'Photo', max_length=255, verbose_name='Type', db_index=True, choices=[(b'Photo', b'Photo'), (b'Video', b'Video')])),
                ('source', models.CharField(help_text='...URL of the Photo/Video', max_length=255, verbose_name='Source', db_index=True)),
                ('target', models.CharField(help_text='...only applicable if Type is Photo. Examples: http://..., https://..., tellecast://...', max_length=255, verbose_name='Target', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_ads',
                'verbose_name': 'Ad',
                'verbose_name_plural': 'Ads',
            },
            bases=(models.Model,),
        ),
    ]
