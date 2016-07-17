# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0085_user_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastertelltellzone',
            name='status',
            field=models.CharField(default=b'Published', max_length=255, verbose_name='Status', db_index=True, choices=[(b'Published', b'Published'), (b'In Review', b'In Review')]),
        ),
        migrations.AddField(
            model_name='tellzone',
            name='are_pinned_tells_queued',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Queue Pinned Tells?'),
        ),
    ]
