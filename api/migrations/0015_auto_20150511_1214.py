# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_userlocation_tellzone'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tellcard',
            options={'ordering': ('user_source', '-viewed_at', '-saved_at'), 'verbose_name': 'Tellcard', 'verbose_name_plural': 'Tellcards'},
        ),
        migrations.RemoveField(
            model_name='tellcard',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='tellcard',
            name='saved_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Favorited At', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tellcard',
            name='viewed_at',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='Viewed At', blank=True),
            preserve_default=True,
        ),
    ]
