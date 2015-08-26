# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_userphoto_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='slavetell',
            old_name='contents',
            new_name='contents_original',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='photo',
            new_name='photo_original',
        ),
        migrations.RenameField(
            model_name='userphoto',
            old_name='string',
            new_name='string_original',
        ),
        migrations.RenameField(
            model_name='userstatusattachment',
            old_name='string',
            new_name='string_original',
        ),
        migrations.AlterField(
            model_name='slavetell',
            name='contents_original',
            field=models.TextField(db_index=True, null=True, verbose_name='Contents :: Original', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='photo_original',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Photo :: Original', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userphoto',
            name='string_original',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='String :: Original', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userstatusattachment',
            name='string_original',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='String :: Original', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='slavetell',
            name='contents_preview',
            field=models.TextField(db_index=True, null=True, verbose_name='Contents :: Preview', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='photo_preview',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Photo :: Preview', blank=True),
        ),
        migrations.AddField(
            model_name='userphoto',
            name='string_preview',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='String :: Preview', blank=True),
        ),
        migrations.AddField(
            model_name='userstatusattachment',
            name='string_preview',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='String :: Preview', blank=True),
        ),
    ]
