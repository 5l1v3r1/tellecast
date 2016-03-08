# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def positions(apps, schema_editor):
    Category = apps.get_model('api', 'Category')
    position = 0
    for category in Category.objects.get_queryset().order_by('name').all():
        position += 1
        category.position = position
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0070_mastertelltellzone'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('position',), 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AddField(
            model_name='category',
            name='position',
            field=models.IntegerField(default=1, verbose_name='Position', db_index=True),
            preserve_default=False,
        ),
        migrations.RunPython(positions),
    ]
