# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0072_user_access_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Verified?'),
        ),
        migrations.AddField(
            model_name='user',
            name='password',
            field=models.CharField(db_index=True, max_length=255, null=True, verbose_name='Password', blank=True),
        ),
    ]
