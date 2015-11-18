# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0055_tellzone_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tellzonesocialprofile',
            name='netloc',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Network Location', choices=[(b'facebook.com', b'facebook.com'), (b'google.com', b'google.com'), (b'instagram.com', b'instagram.com'), (b'linkedin.com', b'linkedin.com'), (b'twitter.com', b'twitter.com'), (b'yelp.com', b'yelp.com')]),
        ),
    ]
