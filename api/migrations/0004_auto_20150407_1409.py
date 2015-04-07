# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_slavetell_is_editable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slavetell',
            name='is_editable',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Editable?'),
            preserve_default=True,
        ),
    ]
