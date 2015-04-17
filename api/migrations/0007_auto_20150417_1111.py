# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20150413_1641'),
    ]

    operations = [
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
                ('description', models.TextField(verbose_name='Description', db_index=True)),
                ('photo', models.CharField(max_length=255, verbose_name='Photo', db_index=True)),
                ('code', models.CharField(max_length=255, verbose_name='Code', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('expires_at', models.DateTimeField(db_index=True, null=True, verbose_name='Expires At', blank=True)),
            ],
            options={
                'ordering': ('-inserted_at',),
                'db_table': 'api_offers',
                'verbose_name': 'Offer',
                'verbose_name_plural': 'Offers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tellzone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name', db_index=True)),
                ('photo', models.CharField(max_length=255, verbose_name='Photo', db_index=True)),
                ('location', models.CharField(max_length=255, verbose_name='Location', db_index=True)),
                ('phone', models.CharField(max_length=255, verbose_name='Phone', db_index=True)),
                ('url', models.CharField(max_length=255, verbose_name='URL', db_index=True)),
                ('hours', models.TextField(verbose_name='Hours')),
                ('point', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='Point', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('-inserted_at',),
                'db_table': 'api_tellzones',
                'verbose_name': 'Tellzone',
                'verbose_name_plural': 'Tellzones',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserOffer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Timestamp', db_index=True)),
                ('offer', models.ForeignKey(related_name='users', to='api.Offer')),
                ('user', models.ForeignKey(related_name='offers', to='api.User')),
            ],
            options={
                'ordering': ('user', 'offer', '-timestamp'),
                'db_table': 'api_users_offers',
                'verbose_name': 'User Offer',
                'verbose_name_plural': 'User Offers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserTellzone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('viewed_at', models.DateTimeField(db_index=True, null=True, verbose_name='Viewed At', blank=True)),
                ('favorited_at', models.DateTimeField(db_index=True, null=True, verbose_name='Favorited At', blank=True)),
                ('tellzone', models.ForeignKey(related_name='users', to='api.Tellzone')),
                ('user', models.ForeignKey(related_name='tellzones', to='api.User')),
            ],
            options={
                'ordering': ('user', 'tellzone', '-viewed_at', '-favorited_at'),
                'db_table': 'api_users_tellzones',
                'verbose_name': 'User Tellzone',
                'verbose_name_plural': 'User Tellzones',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='offer',
            name='tellzone',
            field=models.ForeignKey(related_name='offers', to='api.Tellzone'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='point',
            field=django.contrib.gis.db.models.fields.PointField(db_index=True, srid=4326, null=True, verbose_name='Point', blank=True),
            preserve_default=True,
        ),
    ]
