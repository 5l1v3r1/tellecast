# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_auto_20150929_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='type',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Type', choices=[(b'Ask', b'Ask'), (b'Message', b'Message'), (b'Request', b'Request'), (b'Response - Accepted', b'Response - Accepted'), (b'Response - Blocked', b'Response - Blocked'), (b'Response - Rejected', b'Response - Rejected')]),
        ),
    ]
