# -*- coding: utf-8 -*-

from django.apps import apps
from django.contrib.admin import ModelAdmin, site

from api import models


class User(ModelAdmin):
    exclude = (
        'password',
        'inserted_at',
        'updated_at',
        'signed_in_at',
    )
    list_display = (
        'email',
        'inserted_at',
        'updated_at',
        'signed_in_at',
        'is_staff',
        'is_superuser',
        'is_active',
    )
    list_filter = ('email', 'is_staff', 'is_superuser', 'is_active',)
    ordering = ('-inserted_at',)
    search_fields = ('email', 'first_name', 'last_name',)

site.register(models.User, User)

apps.get_app_config('api').verbose_name = 'API'
