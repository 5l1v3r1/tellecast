# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0032_recommendedtell'),
    ]

    operations = [
        migrations.AddField(
            model_name='tellcard',
            name='location',
            field=models.CharField(default=None, max_length=255, blank=True, null=True, verbose_name='Location', db_index=True),
        ),
        migrations.AddField(
            model_name='tellcard',
            name='tellzone',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to='api.Tellzone', null=True),
        ),
    ]
