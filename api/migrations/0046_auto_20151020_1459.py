# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_auto_20151020_1323'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postattachment',
            name='contents_original',
        ),
        migrations.RemoveField(
            model_name='postattachment',
            name='contents_preview',
        ),
        migrations.AddField(
            model_name='postattachment',
            name='string_original',
            field=models.TextField(default='', verbose_name='String :: Original', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='postattachment',
            name='string_preview',
            field=models.TextField(default='', verbose_name='String :: Preview', db_index=True),
            preserve_default=False,
        ),
    ]
