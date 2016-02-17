# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0067_usertellzone_pinned_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastertell',
            name='category',
            field=models.ForeignKey(related_name='master_tells', to='api.Category', null=True),
        ),
    ]
