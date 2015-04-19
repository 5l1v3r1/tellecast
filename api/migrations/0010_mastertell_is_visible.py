# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_tellcard'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastertell',
            name='is_visible',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Visible?'),
            preserve_default=True,
        ),
    ]
