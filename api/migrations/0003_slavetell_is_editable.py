# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_message_messageattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='slavetell',
            name='is_editable',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is Editable?'),
            preserve_default=False,
        ),
    ]
