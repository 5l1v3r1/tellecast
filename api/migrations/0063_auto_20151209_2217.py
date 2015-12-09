# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0062_auto_20151209_1513'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellzone',
            name='ended_at',
            field=models.DateTimeField(null=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AddField(
            model_name='tellzone',
            name='started_at',
            field=models.DateTimeField(null=True, verbose_name='Inserted At', db_index=True),
        ),
    ]
