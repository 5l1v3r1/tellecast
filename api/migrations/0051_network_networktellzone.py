# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_auto_20151104_1301'),
    ]

    operations = [
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
            ],
            options={
                'ordering': ('-id',),
                'db_table': 'api_networks',
                'verbose_name': 'Network',
                'verbose_name_plural': 'Networks',
            },
        ),
        migrations.CreateModel(
            name='NetworkTellzone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('network', models.ForeignKey(related_name='networks_tellzones', to='api.Network')),
                ('tellzone', models.ForeignKey(related_name='networks_tellzones', to='api.Tellzone')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_networks_tellzones',
                'verbose_name': 'Networks :: Tellzone',
                'verbose_name_plural': 'Networks :: Tellzones',
            },
        ),
    ]
