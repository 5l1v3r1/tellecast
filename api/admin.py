# -*- coding: utf-8 -*-

from django.apps import apps
from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.admin import UserAdmin as AdministratorAdmin
from django.contrib.auth.models import User as Administrator
from django.utils.translation import ugettext_lazy
from social.apps.django_app.default.admin import UserSocialAuthOption
from social.apps.django_app.default.models import UserSocialAuth

from api import models


class User(ModelAdmin):

    fields = (
        'email',
        'email_status',
        'photo',
        'first_name',
        'last_name',
        'date_of_birth',
        'gender',
        'location',
        'description',
        'phone',
        'phone_status',

    )
    list_display = (
        'id',
        'email',
        'first_name',
        'last_name',
        'master_tells_',
        'slave_tells_',
        'inserted_at',
        'updated_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'email',
        'first_name',
        'last_name',
        'inserted_at',
        'updated_at',
    )
    list_select_related = (
        'social',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'email',
        'first_name',
        'last_name',
    )

    def master_tells_(self, instance):
        return instance.master_tells.get_queryset().count()

    master_tells_.allow_tags = True
    master_tells_.short_description = 'Master Tells'

    def slave_tells_(self, instance):
        return instance.slave_tells.get_queryset().count()

    slave_tells_.allow_tags = True
    slave_tells_.short_description = 'Slave Tells'

site.register(models.User, User)


class UserPhoto(ModelAdmin):

    fields = (
        'user',
        'string',
        'position',
    )
    list_display = (
        'id',
        'user',
        'string',
        'position',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'string',
        'position',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'string',
        'position',
    )

site.register(models.UserPhoto, UserPhoto)


class UserSocialProfile(ModelAdmin):

    fields = (
        'user',
        'netloc',
        'url',
    )
    list_display = (
        'id',
        'user',
        'netloc',
        'url',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'netloc',
        'url',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'netloc',
        'url',
    )

site.register(models.UserSocialProfile, UserSocialProfile)


class UserStatus(ModelAdmin):

    fields = (
        'user',
        'string',
        'title',
        'url',
        'notes',
    )
    list_display = (
        'id',
        'user',
        'string',
        'title',
        'url',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'string',
        'title',
        'url',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'string',
        'title',
        'url',
        'notes',
    )

site.register(models.UserStatus, UserStatus)


class UserStatusAttachment(ModelAdmin):

    fields = (
        'user_status',
        'string',
        'position',
    )
    list_display = (
        'id',
        'user_status',
        'string',
        'position',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user_status',
        'string',
        'position',
    )
    list_select_related = (
        'user_status',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'user_status',
        'string',
        'position',
    )

site.register(models.UserStatusAttachment, UserStatusAttachment)


class UserURL(ModelAdmin):

    fields = (
        'user',
        'string',
        'position',
    )
    list_display = (
        'id',
        'user',
        'string',
        'position',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'string',
        'position',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'string',
        'position',
    )

site.register(models.UserURL, UserURL)


class MasterTell(ModelAdmin):

    fields = (
        'created_by',
        'owned_by',
        'contents',
        'position',
    )
    list_display = (
        'id',
        'created_by',
        'owned_by',
        'position',
        'slave_tells',
        'inserted_at',
        'updated_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'created_by',
        'owned_by',
        'position',
        'slave_tells',
        'inserted_at',
        'updated_at',
    )
    list_select_related = (
        'created_by',
        'owned_by',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'position',
        'inserted_at',
        'updated_at',
    )

    def slave_tells_(self, instance):
        return instance.slave_tells.get_queryset().count()

    slave_tells_.allow_tags = True
    slave_tells_.short_description = 'Slave Tells'

site.register(models.MasterTell, MasterTell)


class SlaveTell(ModelAdmin):

    fields = (
        'master_tell',
        'created_by',
        'owned_by',
        'contents',
        'position',
    )
    list_display = (
        'id',
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'position',
        'inserted_at',
        'updated_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'position',
        'inserted_at',
        'updated_at',
    )
    list_select_related = (
        'master_tell',
        'created_by',
        'owned_by',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'type',
        'position',
        'inserted_at',
        'updated_at',
    )

site.register(models.SlaveTell, SlaveTell)

site.unregister(Administrator)

delattr(AdministratorAdmin, 'form')

AdministratorAdmin.fieldsets = ()
AdministratorAdmin.fields = (
    'username',
    'email',
    'first_name',
    'last_name',
    'is_active',
    'is_staff',
    'is_superuser',
)
AdministratorAdmin.list_display = (
    'id',
    'username',
    'email',
    'first_name',
    'last_name',
    'is_active',
    'is_staff',
    'is_superuser',
    'last_login',
)
AdministratorAdmin.list_display_links = (
    'id',
)
AdministratorAdmin.list_filter = (
    'id',
    'username',
    'email',
    'first_name',
    'last_name',
    'is_active',
    'is_staff',
    'is_superuser',
    'last_login',
)
AdministratorAdmin.ordering = (
    'id',
)
AdministratorAdmin.search_fields = (
    'username',
    'email',
    'first_name',
    'last_name',
)

site.register(Administrator, AdministratorAdmin)

site.unregister(UserSocialAuth)

UserSocialAuthOption.fields = (
    'uid',
    'user',
    'provider',
    'extra_data',
)
UserSocialAuthOption.list_display = (
    'id',
    'uid',
    'user',
    'provider',
)
UserSocialAuthOption.list_display_links = (
    'id',
)
UserSocialAuthOption.list_filter = (
    'id',
    'uid',
    'user',
    'provider',
)
UserSocialAuthOption.list_select_related = (
    'user',
)
UserSocialAuthOption.ordering = (
    'id',
)
UserSocialAuthOption.search_fields = (
    'uid',
    'user',
    'provider',
    'extra_data',
)

site.register(UserSocialAuth, UserSocialAuthOption)

apps.get_app_config('api').verbose_name = ugettext_lazy('API')
apps.get_app_config('auth').verbose_name = ugettext_lazy('Django')
apps.get_app_config('default').verbose_name = ugettext_lazy('Social')
