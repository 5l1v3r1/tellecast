# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0049_auto_20151101_2340'),
    ]

    operations = [
        migrations.CreateModel(
            name='TellzoneSocialProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('netloc', models.CharField(db_index=True, max_length=255, verbose_name='Network Location', choices=[(b'facebook.com', b'facebook.com'), (b'google.com', b'google.com'), (b'instagram.com', b'instagram.com'), (b'linkedin.com', b'linkedin.com'), (b'twitter.com', b'twitter.com')])),
                ('url', models.CharField(max_length=255, verbose_name='URL', db_index=True)),
                ('tellzone', models.ForeignKey(related_name='social_profiles', to='api.Tellzone')),
            ],
            options={
                'ordering': ('-id',),
                'db_table': 'api_tellzones_social_profiles',
                'verbose_name': 'Tellzones :: Social Profile',
                'verbose_name_plural': 'Tellzones :: Social Profiles',
            },
        ),
        migrations.AlterUniqueTogether(
            name='tellzonesocialprofile',
            unique_together=set([('tellzone', 'netloc')]),
        ),
    ]
