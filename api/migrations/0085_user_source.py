# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0084_auto_20160619_1508'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='source',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Source', blank=True),
        ),
    ]
