# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_ad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceapns',
            name='registration_id',
            field=models.CharField(max_length=255, verbose_name='Registration ID', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='devicegcm',
            name='registration_id',
            field=models.TextField(max_length=255, verbose_name='Registration ID', db_index=True),
            preserve_default=True,
        ),
    ]
