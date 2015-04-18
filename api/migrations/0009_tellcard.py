# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_block'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tellcard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('user_destination', models.ForeignKey(related_name='+', to='api.User')),
                ('user_source', models.ForeignKey(related_name='+', to='api.User')),
            ],
            options={
                'ordering': ('user_source', '-timestamp'),
                'db_table': 'api_tellcards',
                'verbose_name': 'Tellcard',
                'verbose_name_plural': 'Tellcards',
            },
            bases=(models.Model,),
        ),
    ]
