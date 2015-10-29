# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0047_auto_20151022_1405'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-id',), 'verbose_name': 'Post', 'verbose_name_plural': 'Posts'},
        ),
    ]
