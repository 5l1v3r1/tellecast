# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


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
                ('photo', models.CharField(db_index=True, max_length=255, verbose_name='Photo', blank=True)),
                ('first_name', models.CharField(db_index=True, max_length=255, verbose_name='First Name', blank=True)),
                ('last_name', models.CharField(db_index=True, max_length=255, verbose_name='Last Name', blank=True)),
                ('location', models.CharField(db_index=True, max_length=255, verbose_name='Location', blank=True)),
                ('description', models.TextField(db_index=True, verbose_name='Description', blank=True)),
                ('phone', models.CharField(db_index=True, max_length=255, verbose_name='Phone', blank=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('signed_in_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Signed In At', db_index=True)),
                ('is_staff', models.BooleanField(default=False, db_index=True, verbose_name='Is Staff?')),
                ('is_superuser', models.BooleanField(default=False, db_index=True, verbose_name='Is Superuser?')),
                ('is_active', models.BooleanField(default=True, db_index=True, verbose_name='Is Active?')),
            ],
            options={
                'ordering': ('-inserted_at',),
                'db_table': 'api_users',
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MasterTell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('created_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('owned_by', models.ForeignKey(related_name='master_tells', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_master_tells',
                'verbose_name': 'master tell',
                'verbose_name_plural': 'master tells',
                'get_latest_by': 'position',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SlaveTell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', models.CharField(db_index=True, max_length=255, verbose_name='Photo', blank=True)),
                ('first_name', models.CharField(db_index=True, max_length=255, verbose_name='First Name', blank=True)),
                ('last_name', models.CharField(db_index=True, max_length=255, verbose_name='Last Name', blank=True)),
                ('type', models.CharField(max_length=255, verbose_name='Type', db_index=True)),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
                ('created_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('master_tell', models.ForeignKey(related_name='slave_tells', to='api.MasterTell')),
                ('owned_by', models.ForeignKey(related_name='slave_tells', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_slave_tells',
                'verbose_name': 'slave tell',
                'verbose_name_plural': 'slave tells',
                'get_latest_by': 'position',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user', models.ForeignKey(related_name='photos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_users_photos',
                'verbose_name': 'user photo',
                'verbose_name_plural': 'user photos',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSocialProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('netloc', models.CharField(max_length=255, verbose_name='Network Location', db_index=True)),
                ('url', models.CharField(max_length=255, verbose_name='URL', db_index=True)),
                ('user', models.ForeignKey(related_name='social_profiles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('netloc',),
                'db_table': 'api_users_social_profiles',
                'verbose_name': 'user social profile',
                'verbose_name_plural': 'user social profiles',
                'get_latest_by': 'netloc',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title', db_index=True)),
                ('url', models.CharField(db_index=True, max_length=255, verbose_name='URL', blank=True)),
                ('notes', models.TextField(db_index=True, verbose_name='Notes', blank=True)),
                ('user', models.OneToOneField(related_name='status', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_users_statuses',
                'verbose_name': 'user status',
                'verbose_name_plural': 'user statuses',
                'get_latest_by': 'id',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStatusAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user_status', models.ForeignKey(related_name='attachments', db_column=b'user_status_id', to='api.UserStatus')),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_users_statuses_attachments',
                'verbose_name': 'user status attachment',
                'verbose_name_plural': 'user status attachments',
                'get_latest_by': 'position',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserURL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user', models.ForeignKey(related_name='urls', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('position',),
                'db_table': 'api_users_urls',
                'verbose_name': 'user url',
                'verbose_name_plural': 'user urls',
                'get_latest_by': 'position',
            },
            bases=(models.Model,),
        ),
    ]
