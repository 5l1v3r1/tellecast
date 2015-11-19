# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0057_auto_20151119_2030'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mastertell',
            options={'ordering': ('-owned_by_id', 'position'), 'verbose_name': 'Master Tell', 'verbose_name_plural': 'Master Tells'},
        ),
        migrations.AlterModelOptions(
            name='messageattachment',
            options={'ordering': ('-message_id', 'position'), 'verbose_name': 'Messages :: Attachment', 'verbose_name_plural': 'Messages :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='postattachment',
            options={'ordering': ('-post_id', 'position'), 'verbose_name': 'Posts :: Attachment', 'verbose_name_plural': 'Posts :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='slavetell',
            options={'ordering': ('-master_tell_id', 'position'), 'verbose_name': 'Slave Tell', 'verbose_name_plural': 'Slave Tells'},
        ),
        migrations.AlterModelOptions(
            name='userphoto',
            options={'ordering': ('-user_id', 'position'), 'verbose_name': 'Users :: Photo', 'verbose_name_plural': 'Users :: Photos'},
        ),
        migrations.AlterModelOptions(
            name='userstatusattachment',
            options={'ordering': ('-user_status_id', 'position'), 'verbose_name': 'Users :: Statuses :: Attachment', 'verbose_name_plural': 'Users :: Statuses :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='userurl',
            options={'ordering': ('-user_id', 'position'), 'verbose_name': 'Users :: URL', 'verbose_name_plural': 'Users :: URLs'},
        ),
    ]
