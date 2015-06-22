# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0031_auto_20150618_1400'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendedTell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'Hobby', max_length=255, verbose_name='Type', db_index=True, choices=[(b'Hobby', b'Hobby'), (b'Mind', b'Mind'), (b'Passion', b'Passion')])),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('photo', models.CharField(max_length=255, verbose_name='Photo', db_index=True)),
                ('inserted_at', models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('-id',),
                'db_table': 'api_recommended_tells',
                'verbose_name': 'Recommended Tell',
                'verbose_name_plural': 'Recommended Tells',
            },
        ),
    ]
