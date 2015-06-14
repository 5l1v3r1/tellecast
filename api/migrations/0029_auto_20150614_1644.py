# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_auto_20150613_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_signed_in',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Is Signed In?'),
        ),
        migrations.AlterField(
            model_name='message',
            name='status',
            field=models.CharField(default=b'Unread', max_length=255, verbose_name='Status', db_index=True, choices=[(b'Read', b'Read'), (b'Unread', b'Unread')]),
        ),
        migrations.AlterField(
            model_name='notification',
            name='status',
            field=models.CharField(default=b'Unread', max_length=255, verbose_name='Status', db_index=True, choices=[(b'Read', b'Read'), (b'Unread', b'Unread')]),
        ),
    ]
