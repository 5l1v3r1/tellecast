# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0060_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellzone',
            name='type',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Type', blank=True),
        ),
    ]
