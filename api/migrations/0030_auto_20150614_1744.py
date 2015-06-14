# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_auto_20150614_1644'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzone',
            name='hours',
            field=jsonfield.fields.JSONField(verbose_name='Hours'),
        ),
    ]
