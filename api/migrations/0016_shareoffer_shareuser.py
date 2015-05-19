# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_auto_20150511_1214'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShareOffer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('object', models.ForeignKey(related_name='+', to='api.Offer')),
                ('user_destination', models.ForeignKey(related_name='+', to='api.User')),
                ('user_source', models.ForeignKey(related_name='+', to='api.User')),
            ],
            options={
                'ordering': ('-timestamp',),
                'db_table': 'api_shares_offers',
                'verbose_name': 'Shares Offer',
                'verbose_name_plural': 'Shares Offers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShareUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('object', models.ForeignKey(related_name='+', to='api.User')),
                ('user_destination', models.ForeignKey(related_name='+', to='api.User')),
                ('user_source', models.ForeignKey(related_name='+', to='api.User')),
            ],
            options={
                'ordering': ('-timestamp',),
                'db_table': 'api_shares_users',
                'verbose_name': 'Shares User',
                'verbose_name_plural': 'Shares Users',
            },
            bases=(models.Model,),
        ),
    ]
