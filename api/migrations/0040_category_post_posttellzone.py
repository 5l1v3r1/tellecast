# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0039_userurl_is_visible'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='Name', db_index=True)),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_categories',
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, null=True, verbose_name='Title', db_index=True)),
                ('type', models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'application/pdf', b'application/pdf'), (b'audio/*', b'audio/*'), (b'audio/aac', b'audio/aac'), (b'audio/mp4', b'audio/mp4'), (b'audio/mpeg', b'audio/mpeg'), (b'audio/mpeg3', b'audio/mpeg3'), (b'audio/x-mpeg3', b'audio/x-mpeg3'), (b'image/*', b'image/*'), (b'image/bmp', b'image/bmp'), (b'image/gif', b'image/gif'), (b'image/jpeg', b'image/jpeg'), (b'image/png', b'image/png'), (b'text/plain', b'text/plain'), (b'video/*', b'video/*'), (b'video/3gpp', b'video/3gpp'), (b'video/mp4', b'video/mp4'), (b'video/mpeg', b'video/mpeg'), (b'video/x-mpeg', b'video/x-mpeg')])),
                ('description', models.TextField(verbose_name='Description', db_index=True)),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('inserted_at', models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True)),
                ('expired_at', models.DateTimeField(verbose_name='Expired At', db_index=True)),
                ('category', models.ForeignKey(related_name='posts', to='api.Category', null=True)),
                ('user', models.ForeignKey(related_name='posts', to='api.User')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_posts',
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
            },
        ),
        migrations.CreateModel(
            name='PostTellzone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('post', models.ForeignKey(related_name='+', to='api.Post')),
                ('tellzone', models.ForeignKey(related_name='+', to='api.Tellzone')),
            ],
            options={
                'ordering': ('id',),
                'db_table': 'api_posts_tellzones',
                'verbose_name': 'Posts :: Tellzone',
                'verbose_name_plural': 'Posts :: Tellzones',
            },
        ),
    ]
