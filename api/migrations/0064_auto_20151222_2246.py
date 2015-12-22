# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0063_auto_20151209_2217'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzone',
            name='ended_at',
            field=models.DateTimeField(null=True, verbose_name='Ended At', db_index=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='started_at',
            field=models.DateTimeField(null=True, verbose_name='Started At', db_index=True),
        ),
    ]
