# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_apnsdevice_gcmdevice'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='user_destination_is_hidden',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Is Hidden?'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='user_source_is_hidden',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Is Hidden?'),
            preserve_default=True,
        ),
    ]
