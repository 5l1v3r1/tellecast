# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from contextlib import closing

from django.db import connection, migrations
from jsonfield.fields import JSONField
from ujson import dumps


def transfer_users_settings(applications, schema):
    with closing(connection.cursor()) as cursor:
        cursor.execute('SELECT id AS id FROM api_users')
        users = cursor.fetchall()
        for user in users:
            settings = {}
            cursor.execute('SELECT key, value FROM api_users_settings WHERE user_id = %s', (user[0],))
            user_settings = cursor.fetchall()
            for user_setting in user_settings:
                settings[user_setting[0]] = 'True' if user_setting[1] == 'True' else 'False'
            cursor.execute('UPDATE api_users SET settings = %s WHERE id = %s', (dumps(settings), user[0],))


def transfer_users_social_profiles(applications, schema):
    with closing(connection.cursor()) as cursor:
        cursor.execute('SELECT id AS id FROM api_users')
        users = cursor.fetchall()
        for user in users:
            social_profiles = []
            cursor.execute('SELECT netloc, url FROM api_users_social_profiles WHERE user_id = %s', (user[0],))
            user_social_profiles = cursor.fetchall()
            for user_social_profile in user_social_profiles:
                social_profiles.append({
                    'netloc': user_social_profile[0],
                    'url': user_social_profile[1],
                })
            cursor.execute(
                'UPDATE api_users SET social_profiles = %s WHERE id = %s', (dumps(social_profiles), user[0],),
            )


def transfer_tellzones_social_profiles(applications, schema):
    with closing(connection.cursor()) as cursor:
        cursor.execute('SELECT id AS id FROM api_tellzones')
        tellzones = cursor.fetchall()
        for tellzone in tellzones:
            social_profiles = []
            cursor.execute(
                'SELECT netloc, url FROM api_tellzones_social_profiles WHERE tellzone_id = %s', (tellzone[0],),
            )
            tellzone_social_profiles = cursor.fetchall()
            for tellzone_social_profile in tellzone_social_profiles:
                social_profiles.append({
                    'netloc': tellzone_social_profile[0],
                    'url': tellzone_social_profile[1],
                })
            cursor.execute(
                'UPDATE api_tellzones SET social_profiles = %s WHERE id = %s', (dumps(social_profiles), tellzone[0],),
            )


def transfer_messages_attachments(applications, schema):
    with closing(connection.cursor()) as cursor:
        cursor.execute('SELECT id AS id FROM api_messages')
        messages = cursor.fetchall()
        for message in messages:
            attachments = []
            cursor.execute(
                'SELECT string, position FROM api_messages_attachments WHERE message_id = %s', (message[0],),
            )
            message_attachments = cursor.fetchall()
            for message_attachment in message_attachments:
                attachments.append({
                    'string': message_attachment[0],
                    'position': message_attachment[1],
                })
            cursor.execute('UPDATE api_messages SET attachments = %s WHERE id = %s', (dumps(attachments), message[0],))


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0083_auto_20160611_0119'),
    ]

    operations = [
        migrations.AddField(
            field=JSONField(blank=True, null=True, verbose_name='Settings'),
            model_name='user',
            name='settings',
        ),
        migrations.AddField(
            field=JSONField(blank=True, null=True, verbose_name='Social Profiles'),
            model_name='user',
            name='social_profiles',
        ),
        migrations.AddField(
            field=JSONField(blank=True, null=True, verbose_name='Social Profiles'),
            model_name='tellzone',
            name='social_profiles',
        ),
        migrations.AddField(
            field=JSONField(blank=True, null=True, verbose_name='Attachments'),
            model_name='message',
            name='attachments',
        ),
        migrations.RunPython(transfer_users_settings),
        migrations.RunPython(transfer_users_social_profiles),
        migrations.RunPython(transfer_tellzones_social_profiles),
        migrations.RunPython(transfer_messages_attachments),
        migrations.RemoveField(model_name='usersetting', name='user'),
        migrations.DeleteModel(name='UserSetting'),
        migrations.RemoveField(model_name='usersocialprofile', name='user'),
        migrations.DeleteModel(name='UserSocialProfile'),
        migrations.RemoveField(model_name='TellzoneSocialProfile', name='tellzone'),
        migrations.DeleteModel(name='TellzoneSocialProfile'),
        migrations.RemoveField(model_name='messageattachment', name='message'),
        migrations.DeleteModel(name='MessageAttachment'),
        migrations.AlterField(
            field=JSONField(blank=True, null=True, verbose_name='Contents'),
            model_name='notification',
            name='contents',
        ),
    ]
