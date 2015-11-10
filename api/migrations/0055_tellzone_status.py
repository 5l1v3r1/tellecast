# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_tellcard_network'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellzone',
            name='status',
            field=models.CharField(default=b'Public', max_length=255, verbose_name='Status', db_index=True, choices=[(b'Public', b'Public'), (b'Private', b'Private')]),
        ),
    ]
