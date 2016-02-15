# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0065_user_tellzone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzone',
            name='hours',
            field=jsonfield.fields.JSONField(null=True, verbose_name='Hours', blank=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='location',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Location', blank=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='phone',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Phone', blank=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='photo',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Photo', blank=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='url',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='URL', blank=True),
        ),
    ]
