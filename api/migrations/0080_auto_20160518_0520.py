# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0079_auto_20160517_0959'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tellzonestatus',
            options={'ordering': ('position',), 'verbose_name': 'Tellzone :: Status', 'verbose_name_plural': 'Tellzones :: Statuses'},
        ),
        migrations.AlterModelOptions(
            name='tellzonetype',
            options={'ordering': ('position',), 'verbose_name': 'Tellzone :: Type', 'verbose_name_plural': 'Tellzones :: Types'},
        ),
    ]
