# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_auto_20150611_1107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='email_status',
        ),
        migrations.RemoveField(
            model_name='user',
            name='phone_status',
        ),
    ]
