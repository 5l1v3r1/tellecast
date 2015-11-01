# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0048_auto_20151029_2002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postattachment',
            name='string_preview',
            field=models.TextField(db_index=True, null=True, verbose_name='String :: Preview', blank=True),
        ),
    ]
