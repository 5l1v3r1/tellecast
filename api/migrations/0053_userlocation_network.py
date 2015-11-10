# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_auto_20151110_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlocation',
            name='network',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to='api.Network', null=True),
        ),
    ]
