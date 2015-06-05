# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_auto_20150601_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlocation',
            name='accuracies_horizontal',
            field=models.FloatField(db_index=True, null=True, verbose_name='Accuracies :: Horizontal', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userlocation',
            name='accuracies_vertical',
            field=models.FloatField(db_index=True, null=True, verbose_name='Accuracies :: Vertical', blank=True),
            preserve_default=True,
        ),
    ]
