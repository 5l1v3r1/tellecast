# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import push_notifications.fields


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_auto_20150611_1338'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offer',
            name='tellzone',
        ),
        migrations.RemoveField(
            model_name='shareoffer',
            name='object',
        ),
        migrations.RemoveField(
            model_name='shareoffer',
            name='user_destination',
        ),
        migrations.RemoveField(
            model_name='shareoffer',
            name='user_source',
        ),
        migrations.RemoveField(
            model_name='useroffer',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='useroffer',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='ad',
            options={'ordering': ('-id',), 'verbose_name': 'Ad', 'verbose_name_plural': 'Ads'},
        ),
        migrations.AlterModelOptions(
            name='block',
            options={'ordering': ('-id',), 'verbose_name': 'Block', 'verbose_name_plural': 'Blocks'},
        ),
        migrations.AlterModelOptions(
            name='deviceapns',
            options={'ordering': ('-id',), 'verbose_name': 'Devices :: APNS', 'verbose_name_plural': 'Devices :: APNS'},
        ),
        migrations.AlterModelOptions(
            name='devicegcm',
            options={'ordering': ('-id',), 'verbose_name': 'Devices :: GCM', 'verbose_name_plural': 'Devices :: GCM'},
        ),
        migrations.AlterModelOptions(
            name='mastertell',
            options={'ordering': ('-id',), 'verbose_name': 'Master Tell', 'verbose_name_plural': 'Master Tells'},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('-id',), 'verbose_name': 'Message', 'verbose_name_plural': 'Messages'},
        ),
        migrations.AlterModelOptions(
            name='messageattachment',
            options={'ordering': ('-id',), 'verbose_name': 'Messages :: Attachment', 'verbose_name_plural': 'Messages :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ('-id',), 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ('-id',), 'verbose_name': 'Report', 'verbose_name_plural': 'Reports'},
        ),
        migrations.AlterModelOptions(
            name='shareuser',
            options={'ordering': ('-id',), 'verbose_name': 'Shares :: User', 'verbose_name_plural': 'Shares :: Users'},
        ),
        migrations.AlterModelOptions(
            name='slavetell',
            options={'ordering': ('-id',), 'verbose_name': 'Slave Tell', 'verbose_name_plural': 'Slave Tells'},
        ),
        migrations.AlterModelOptions(
            name='tellcard',
            options={'ordering': ('-id',), 'verbose_name': 'Tellcard', 'verbose_name_plural': 'Tellcards'},
        ),
        migrations.AlterModelOptions(
            name='tellzone',
            options={'ordering': ('-id',), 'verbose_name': 'Tellzone', 'verbose_name_plural': 'Tellzones'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('-id',), 'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
        migrations.AlterModelOptions(
            name='userlocation',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Location', 'verbose_name_plural': 'Users :: Locations'},
        ),
        migrations.AlterModelOptions(
            name='userphoto',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Photo', 'verbose_name_plural': 'Users :: Photos'},
        ),
        migrations.AlterModelOptions(
            name='usersetting',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Setting', 'verbose_name_plural': 'Users :: Settings'},
        ),
        migrations.AlterModelOptions(
            name='usersocialprofile',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Social Profile', 'verbose_name_plural': 'Users :: Social Profiles'},
        ),
        migrations.AlterModelOptions(
            name='userstatus',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Status', 'verbose_name_plural': 'Users :: Statuses'},
        ),
        migrations.AlterModelOptions(
            name='userstatusattachment',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Statuses :: Attachment', 'verbose_name_plural': 'Users :: Statuses :: Attachments'},
        ),
        migrations.AlterModelOptions(
            name='usertellzone',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: Tellzone', 'verbose_name_plural': 'Users :: Tellzones'},
        ),
        migrations.AlterModelOptions(
            name='userurl',
            options={'ordering': ('-id',), 'verbose_name': 'Users :: URL', 'verbose_name_plural': 'Users :: URLs'},
        ),
        migrations.AlterField(
            model_name='ad',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='ad',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Timestamp', db_index=True),
        ),
        migrations.AlterField(
            model_name='devicegcm',
            name='device_id',
            field=push_notifications.fields.HexIntegerField(verbose_name='Device ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='mastertell',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='mastertell',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Timestamp', db_index=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Timestamp', db_index=True),
        ),
        migrations.AlterField(
            model_name='shareuser',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Timestamp', db_index=True),
        ),
        migrations.AlterField(
            model_name='slavetell',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='slavetell',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='tellzone',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.AlterField(
            model_name='userlocation',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Timestamp', db_index=True),
        ),
        migrations.AlterField(
            model_name='usersetting',
            name='inserted_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Inserted At', db_index=True),
        ),
        migrations.AlterField(
            model_name='usersetting',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At', db_index=True),
        ),
        migrations.DeleteModel(
            name='Offer',
        ),
        migrations.DeleteModel(
            name='ShareOffer',
        ),
        migrations.DeleteModel(
            name='UserOffer',
        ),
    ]
