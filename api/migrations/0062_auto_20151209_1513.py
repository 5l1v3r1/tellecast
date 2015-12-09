# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0061_tellzone_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='api.User', null=True),
        ),
        migrations.AddField(
            model_name='tellzone',
            name='user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='api.User', null=True),
        ),
    ]
