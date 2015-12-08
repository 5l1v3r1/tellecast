# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0059_auto_20151201_1521'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(default=b'Regular', max_length=255, verbose_name='Type', db_index=True, choices=[(b'Root', b'Root'), (b'Network', b'Network'), (b'Regular', b'Regular')]),
        ),
    ]
