# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0077_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.TextField(db_index=True, null=True, verbose_name='Description', blank=True),
        ),
        migrations.AddField(
            model_name='category',
            name='display_type',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Display Type', blank=True),
        ),
    ]
