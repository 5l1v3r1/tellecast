# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0073_auto_20160408_1841'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellzone',
            name='description',
            field=models.TextField(db_index=True, null=True, verbose_name='Description', blank=True),
        ),
    ]
