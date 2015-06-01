# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_auto_20150527_0952'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='userlocation',
            table='api_users_locations',
        ),
    ]
