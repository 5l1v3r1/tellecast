# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0058_auto_20151119_2035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='contents',
            field=models.TextField(db_index=True, verbose_name='Contents', blank=True),
        ),
    ]
