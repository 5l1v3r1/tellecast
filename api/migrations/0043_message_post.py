# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0042_auto_20151009_1652'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='post',
            field=models.ForeignKey(related_name='+', blank=True, to='api.Post', null=True),
        ),
    ]
