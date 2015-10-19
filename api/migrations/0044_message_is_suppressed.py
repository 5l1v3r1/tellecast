# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0043_message_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_suppressed',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Is Suppressed?'),
        ),
    ]
