# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20150427_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlocation',
            name='tellzone',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to='api.Tellzone', null=True),
            preserve_default=True,
        ),
    ]
