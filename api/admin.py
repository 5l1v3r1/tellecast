# -*- coding: utf-8 -*-

from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField, ReadOnlyPasswordHashWidget,
)
from django.utils.translation import ugettext_lazy

from models import User


class UserAdmin(admin.ModelAdmin):
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

admin.site.register(User, UserAdmin)

apps.get_app_config('api').verbose_name = 'API'
