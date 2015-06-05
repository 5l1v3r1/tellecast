# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_auto_20150605_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shareoffer',
            name='user_destination',
            field=models.ForeignKey(related_name='+', blank=True, to='api.User', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='shareuser',
            name='user_destination',
            field=models.ForeignKey(related_name='+', blank=True, to='api.User', null=True),
            preserve_default=True,
        ),
    ]
