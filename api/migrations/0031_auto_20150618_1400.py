# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_auto_20150614_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_signed_in',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Signed In?'),
        ),
    ]
