# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0081_auto_20160518_0522'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellzonestatus',
            name='icon',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Icon', blank=True),
        ),
        migrations.AddField(
            model_name='tellzonetype',
            name='icon',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Icon', blank=True),
        ),
    ]
