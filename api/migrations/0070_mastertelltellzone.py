# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_mastertell_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='MasterTellTellzone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('master_tell', models.ForeignKey(related_name='master_tells_tellzones', to='api.MasterTell')),
                ('tellzone', models.ForeignKey(related_name='master_tells_tellzones', to='api.Tellzone')),
            ],
            options={
                'ordering': ('-id',),
                'db_table': 'api_master_tells_tellzones',
                'verbose_name': 'Master Tells :: Tellzone',
                'verbose_name_plural': 'Master Tells :: Tellzones',
            },
        ),
    ]
