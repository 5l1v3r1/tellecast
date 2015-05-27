# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_auto_20150526_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceapns',
            name='registration_id',
            field=models.CharField(unique=True, max_length=255, verbose_name='Registration ID', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='devicegcm',
            name='registration_id',
            field=models.TextField(unique=True, max_length=255, verbose_name='Registration ID', db_index=True),
            preserve_default=True,
        ),
    ]
