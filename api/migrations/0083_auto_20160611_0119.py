# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0082_auto_20160518_0601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzone',
            name='user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='api.User', null=True),
        ),
    ]
