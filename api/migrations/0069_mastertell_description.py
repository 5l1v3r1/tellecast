# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0068_mastertell_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastertell',
            name='description',
            field=models.TextField(db_index=True, null=True, verbose_name='Description', blank=True),
        ),
    ]
