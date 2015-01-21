# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='Email', db_index=True)),
                ('password', models.CharField(max_length=255, verbose_name='Password', db_index=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='First Name', db_index=True)),
                ('last_name', models.CharField(max_length=255, verbose_name='Last Name', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Updated At', db_index=True)),
                ('signed_in_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Signed In At', db_index=True)),
                ('is_staff', models.BooleanField(default=False, db_index=True, verbose_name='Is Staff?')),
                ('is_superuser', models.BooleanField(default=False, db_index=True, verbose_name='Is Superuser?')),
                ('is_active', models.BooleanField(default=True, db_index=True, verbose_name='Is Active?')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
    ]
