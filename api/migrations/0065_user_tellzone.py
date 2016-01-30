# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0064_auto_20151222_2246'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='tellzone',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to='api.Tellzone', null=True),
        ),
    ]
