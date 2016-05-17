# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0078_auto_20160509_0605'),
    ]

    operations = [
        migrations.CreateModel(
            name='TellzoneStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='Name', db_index=True)),
                ('title', models.CharField(unique=True, max_length=255, verbose_name='Name', db_index=True)),
                ('description', models.TextField(db_index=True, null=True, verbose_name='Description', blank=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_tellzones_statuses',
                'verbose_name': 'Tellzone Status',
                'verbose_name_plural': 'Tellzones Statuses',
            },
        ),
        migrations.CreateModel(
            name='TellzoneType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='Name', db_index=True)),
                ('title', models.CharField(unique=True, max_length=255, verbose_name='Name', db_index=True)),
                ('description', models.TextField(db_index=True, null=True, verbose_name='Description', blank=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_tellzones_types',
                'verbose_name': 'Tellzone Type',
                'verbose_name_plural': 'Tellzones Types',
            },
        ),
        migrations.RemoveField(model_name='tellzone', name='type'),
        migrations.RemoveField(model_name='tellzone', name='status'),
        migrations.AddField(
            model_name='tellzone',
            name='status',
            field=models.ForeignKey(related_name='tellzones', to='api.TellzoneStatus', null=True),
        ),
        migrations.AddField(
            model_name='tellzone',
            name='type',
            field=models.ForeignKey(related_name='tellzones', to='api.TellzoneType', null=True),
        ),
    ]
