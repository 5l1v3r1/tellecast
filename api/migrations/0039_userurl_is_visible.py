# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0038_auto_20150912_2312'),
    ]

    operations = [
        migrations.AddField(
            model_name='userurl',
            name='is_visible',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Visible?'),
        ),
    ]
