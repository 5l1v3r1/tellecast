# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0071_auto_20160308_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='access_code',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Access Code', blank=True),
        ),
    ]
