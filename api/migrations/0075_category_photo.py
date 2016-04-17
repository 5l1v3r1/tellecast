# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0074_tellzone_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='photo',
            field=models.CharField(default='', max_length=255, verbose_name='Photo', db_index=True),
            preserve_default=False,
        ),
    ]
