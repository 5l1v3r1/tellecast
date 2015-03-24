# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MasterTell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('owned_by', 'position'),
                'db_table': 'api_master_tells',
                'verbose_name': 'Master Tell',
                'verbose_name_plural': 'Master Tells',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SlaveTell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Photo', blank=True)),
                ('first_name', models.CharField(db_index=True, max_length=255, null=True, verbose_name='First Name', blank=True)),
                ('last_name', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Last Name', blank=True)),
                ('type', models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'application/pdf', b'application/pdf'), (b'audio/*', b'audio/*'), (b'audio/aac', b'audio/aac'), (b'audio/mp4', b'audio/mp4'), (b'audio/mpeg', b'audio/mpeg'), (b'audio/mpeg3', b'audio/mpeg3'), (b'audio/x-mpeg3', b'audio/x-mpeg3'), (b'image/*', b'image/*'), (b'image/bmp', b'image/bmp'), (b'image/gif', b'image/gif'), (b'image/jpeg', b'image/jpeg'), (b'image/png', b'image/png'), (b'text/plain', b'text/plain'), (b'video/*', b'video/*'), (b'video/3gpp', b'video/3gpp'), (b'video/mp4', b'video/mp4'), (b'video/mpeg', b'video/mpeg'), (b'video/x-mpeg', b'video/x-mpeg')])),
                ('contents', models.TextField(verbose_name='Contents', db_index=True)),
                ('description', models.TextField(db_index=True, null=True, verbose_name='Description', blank=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('owned_by', 'master_tell', 'position'),
                'db_table': 'api_slave_tells',
                'verbose_name': 'Slave Tell',
                'verbose_name_plural': 'Slave Tells',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name='Email', db_index=True)),
                ('email_status', models.CharField(default=b'Private', max_length=255, verbose_name='Email Status', db_index=True, choices=[(b'Private', b'Private'), (b'Public', b'Public')])),
                ('photo', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Photo', blank=True)),
                ('first_name', models.CharField(db_index=True, max_length=255, null=True, verbose_name='First Name', blank=True)),
                ('last_name', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Last Name', blank=True)),
                ('date_of_birth', models.DateField(db_index=True, null=True, verbose_name='Date of Birth', blank=True)),
                ('gender', models.CharField(choices=[(b'Female', b'Female'), (b'Male', b'Male')], max_length=255, blank=True, null=True, verbose_name='Gender', db_index=True)),
                ('location', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Location', blank=True)),
                ('description', models.TextField(db_index=True, null=True, verbose_name='Description', blank=True)),
                ('phone', models.CharField(db_index=True, max_length=255, null=True, verbose_name='Phone', blank=True)),
                ('phone_status', models.CharField(default=b'Private', max_length=255, verbose_name='Phone Status', db_index=True, choices=[(b'Private', b'Private'), (b'Public', b'Public')])),
                ('inserted_at', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='Inserted At', db_index=True)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='Updated At', db_index=True)),
            ],
            options={
                'ordering': ('-inserted_at',),
                'db_table': 'api_users',
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user', models.ForeignKey(related_name='photos', to='api.User')),
            ],
            options={
                'ordering': ('user', 'position'),
                'db_table': 'api_users_photos',
                'verbose_name': 'User Photo',
                'verbose_name_plural': 'User Photos',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSocialProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('netloc', models.CharField(db_index=True, max_length=255, verbose_name='Network Location', choices=[(b'facebook.com', b'facebook.com'), (b'google.com', b'google.com'), (b'instagram.com', b'instagram.com'), (b'linkedin.com', b'linkedin.com'), (b'twitter.com', b'twitter.com')])),
                ('url', models.CharField(max_length=255, verbose_name='URL', db_index=True)),
                ('user', models.ForeignKey(related_name='social_profiles', to='api.User')),
            ],
            options={
                'ordering': ('user', 'netloc'),
                'db_table': 'api_users_social_profiles',
                'verbose_name': 'User Social Profile',
                'verbose_name_plural': 'User Social Profiles',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title', db_index=True)),
                ('url', models.CharField(db_index=True, max_length=255, null=True, verbose_name='URL', blank=True)),
                ('notes', models.TextField(db_index=True, null=True, verbose_name='Notes', blank=True)),
                ('user', models.OneToOneField(related_name='status', to='api.User')),
            ],
            options={
                'ordering': ('user', 'string'),
                'db_table': 'api_users_statuses',
                'verbose_name': 'User Status',
                'verbose_name_plural': 'User Statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStatusAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user_status', models.ForeignKey(related_name='attachments', to='api.UserStatus')),
            ],
            options={
                'ordering': ('user_status', 'position'),
                'db_table': 'api_users_statuses_attachments',
                'verbose_name': 'User Status Attachment',
                'verbose_name_plural': 'User Status Attachments',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserURL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('string', models.CharField(max_length=255, verbose_name='String', db_index=True)),
                ('position', models.IntegerField(verbose_name='Position', db_index=True)),
                ('user', models.ForeignKey(related_name='urls', to='api.User')),
            ],
            options={
                'ordering': ('user', 'position'),
                'db_table': 'api_users_urls',
                'verbose_name': 'User URL',
                'verbose_name_plural': 'User URLs',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='usersocialprofile',
            unique_together=set([('user', 'netloc')]),
        ),
        migrations.AddField(
            model_name='slavetell',
            name='created_by',
            field=models.ForeignKey(related_name='+', to='api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='slavetell',
            name='master_tell',
            field=models.ForeignKey(related_name='slave_tells', to='api.MasterTell'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='slavetell',
            name='owned_by',
            field=models.ForeignKey(related_name='slave_tells', to='api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mastertell',
            name='created_by',
            field=models.ForeignKey(related_name='+', to='api.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mastertell',
            name='owned_by',
            field=models.ForeignKey(related_name='master_tells', to='api.User'),
            preserve_default=True,
        ),
    ]
