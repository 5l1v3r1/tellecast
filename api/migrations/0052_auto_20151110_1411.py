# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0051_network_networktellzone'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('-id',), 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='networktellzone',
            options={'ordering': ('-id',), 'verbose_name': 'Networks :: Tellzone', 'verbose_name_plural': 'Networks :: Tellzones'},
        ),
        migrations.AlterModelOptions(
            name='postattachment',
            options={'ordering': ('-id',), 'verbose_name': 'Posts :: Attachment', 'verbose_name_plural': 'Posts :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='posttellzone',
            options={'ordering': ('-id',), 'verbose_name': 'Posts :: Tellzone', 'verbose_name_plural': 'Posts :: Tellzones'},
        ),
    ]
