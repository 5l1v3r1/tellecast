# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0066_auto_20160215_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertellzone',
            name='pinned_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Pinned At', blank=True),
        ),
    ]
