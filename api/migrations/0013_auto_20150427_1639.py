# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_report'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceapns',
            name='device_id',
            field=django_extensions.db.fields.UUIDField(db_index=True, max_length=255, editable=False, blank=True),
            preserve_default=True,
        ),
    ]
