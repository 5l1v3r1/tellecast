# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_auto_20150601_1312'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useroffer',
            options={'ordering': ('user', 'offer', '-id'), 'verbose_name': 'User Offer', 'verbose_name_plural': 'User Offers'},
        ),
        migrations.RemoveField(
            model_name='useroffer',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='useroffer',
            name='redeemed_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Redeemed At', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='useroffer',
            name='saved_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Saved At', blank=True),
            preserve_default=True,
        ),
    ]
