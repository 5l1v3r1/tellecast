# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0044_message_is_suppressed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postattachment',
            name='contents',
        ),
        migrations.AddField(
            model_name='postattachment',
            name='contents_original',
            field=models.TextField(default='', verbose_name='Contents :: Original', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='postattachment',
            name='contents_preview',
            field=models.TextField(default='', verbose_name='Contents :: Preview', db_index=True),
            preserve_default=False,
        ),
    ]
