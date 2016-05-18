# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0080_auto_20160518_0520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzonestatus',
            name='title',
            field=models.CharField(unique=True, max_length=255, verbose_name='Title', db_index=True),
        ),
        migrations.AlterField(
            model_name='tellzonetype',
            name='title',
            field=models.CharField(unique=True, max_length=255, verbose_name='Title', db_index=True),
        ),
    ]
