# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_auto_20151020_1459'),
    ]

    operations = [
        migrations.AlterField(
            model_name='posttellzone',
            name='post',
            field=models.ForeignKey(related_name='posts_tellzones', to='api.Post'),
        ),
        migrations.AlterField(
            model_name='posttellzone',
            name='tellzone',
            field=models.ForeignKey(related_name='posts_tellzones', to='api.Tellzone'),
        ),
    ]
