# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_auto_20150710_2141'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlocation',
            name='location',
            field=models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Location', db_index=True),
        ),
    ]
