# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_mastertell_is_visible'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='Point', db_index=True)),
                ('bearing', models.IntegerField(verbose_name='Bearing', db_index=True)),
                ('is_casting', models.BooleanField(default=True, db_index=True, verbose_name='Is Casting?')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('user', models.ForeignKey(related_name='locations', to='api.User')),
            ],
            options={
                'ordering': ('user', '-timestamp'),
                'db_table': 'api_locations',
                'verbose_name': 'User Location',
                'verbose_name_plural': 'User Locations',
            },
            bases=(models.Model,),
        ),
    ]
