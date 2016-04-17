# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0075_category_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('platform', models.CharField(default=b'Android', max_length=255, verbose_name='Slot', db_index=True, choices=[(b'Android', b'Android'), (b'iOS', b'iOS')])),
                ('number', models.CharField(max_length=255, verbose_name='Number', db_index=True)),
                ('inserted_at', models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('-id',),
                'db_table': 'api_versions',
                'verbose_name': 'Version',
                'verbose_name_plural': 'Version',
            },
        ),
    ]
