# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_auto_20150611_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceapns',
            name='device_id',
            field=django_extensions.db.fields.UUIDField(db_index=True, verbose_name='Device ID', max_length=255, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='tellcard',
            name='saved_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Saved At', blank=True),
            preserve_default=True,
        ),
    ]
