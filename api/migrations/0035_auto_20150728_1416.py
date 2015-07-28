# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_userlocation_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceapns',
            name='device_id',
            field=django_extensions.db.fields.UUIDField(auto=False, max_length=255, verbose_name='Device ID', db_index=True),
        ),
    ]
