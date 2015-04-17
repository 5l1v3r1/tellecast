# -*- coding: utf-8 -*-

from django.apps import apps
from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.admin import UserAdmin as AdministratorAdmin
from django.contrib.auth.models import User as Administrator
from django.utils.translation import ugettext_lazy
from social.apps.django_app.default.admin import UserSocialAuthOption
from social.apps.django_app.default.models import UserSocialAuth

from api import models


class Tellzone(ModelAdmin):

    fields = (
        'name',
        'photo',
        'location',
        'phone',
        'url',
        'hours',
        'point',
    )
    list_display = (
        'id',
        'name',
        'location',
        'phone',
        'url',
        'point',
        'offers_',
        'users_',
        'inserted_at',
        'updated_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'name',
        'location',
        'phone',
        'url',
        'inserted_at',
        'updated_at',
    )
    list_select_related = (
        'offers',
        'users',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'name',
        'photo',
        'location',
        'phone',
        'url',
    )

    def offers_(self, instance):
        return instance.offers.get_queryset().count()

    offers_.allow_tags = True
    offers_.short_description = 'Offers'

    def users_(self, instance):
        return instance.users.get_queryset().count()

    users_.allow_tags = True
    users_.short_description = 'Users'

site.register(models.Tellzone, Tellzone)


class Offer(ModelAdmin):

    fields = (
        'tellzone',
        'name',
        'description',
        'photo',
        'code',
        'expires_at',
    )
    list_display = (
        'id',
        'tellzone',
        'name',
        'code',
        'users_',
        'inserted_at',
        'updated_at',
        'expires_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'tellzone',
        'name',
        'code',
        'inserted_at',
        'updated_at',
        'expires_at',
    )
    list_select_related = (
        'tellzone',
        'users',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'tellzone',
        'name',
        'photo',
        'location',
        'phone',
        'url',
    )

    def users_(self, instance):
        return instance.users.get_queryset().count()

    users_.allow_tags = True
    users_.short_description = 'Users'

site.register(models.Offer, Offer)


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
        'point',
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
        'user',
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
        'user',
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
        'user',
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
        'user',
        'string',
        'position',
    )

site.register(models.UserURL, UserURL)


class UserTellzone(ModelAdmin):

    fields = (
        'user',
        'tellzone',
        'viewed_at',
        'favorited_at',
    )
    list_display = (
        'id',
        'user',
        'tellzone',
        'viewed_at',
        'favorited_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'tellzone',
        'viewed_at',
        'favorited_at',
    )
    list_select_related = (
        'user',
        'tellzone',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'user',
        'tellzone',
    )

site.register(models.UserTellzone, UserTellzone)


class UserOffer(ModelAdmin):

    fields = (
        'user',
        'offer',
    )
    list_display = (
        'id',
        'user',
        'offer',
        'timestamp',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'offer',
        'timestamp',
    )
    list_select_related = (
        'user',
        'offer',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'user',
        'offer',
    )

site.register(models.UserOffer, UserOffer)


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
        'slave_tells_',
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
        'created_by',
        'owned_by',
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
        'photo',
        'first_name',
        'last_name',
        'type',
        'is_editable',
        'contents',
        'description',
        'position',
    )
    list_display = (
        'id',
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'is_editable',
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
        'is_editable',
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
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'is_editable',
        'position',
        'inserted_at',
        'updated_at',
    )

site.register(models.SlaveTell, SlaveTell)


class Message(ModelAdmin):

    fields = (
        'user_source',
        'user_source_is_hidden',
        'user_destination',
        'user_destination_is_hidden',
        'user_status',
        'master_tell',
        'type',
        'contents',
        'status',
    )
    list_display = (
        'id',
        'user_source',
        'user_source_is_hidden',
        'user_destination',
        'user_destination_is_hidden',
        'user_status',
        'master_tell',
        'type',
        'status',
        'attachments_',
        'inserted_at',
        'updated_at',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user_source',
        'user_source_is_hidden',
        'user_destination',
        'user_destination_is_hidden',
        'user_status',
        'master_tell',
        'type',
        'status',
        'inserted_at',
        'updated_at',
    )
    list_select_related = (
        'user_source',
        'user_destination',
        'user_status',
        'master_tell',
    )
    ordering = (
        '-inserted_at',
    )
    search_fields = (
        'user_source',
        'user_destination',
        'user_status',
        'master_tell',
        'type',
        'contents',
        'status',
        'inserted_at',
        'updated_at',
    )

    def attachments_(self, instance):
        return instance.attachments.get_queryset().count()

    attachments_.allow_tags = True
    attachments_.short_description = 'Slave Tells'

site.register(models.Message, Message)


class MessageAttachment(ModelAdmin):

    fields = (
        'message',
        'string',
        'position',
    )
    list_display = (
        'id',
        'message',
        'string',
        'position',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'message',
        'string',
        'position',
    )
    list_select_related = (
        'message',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'message',
        'string',
        'position',
    )

site.register(models.MessageAttachment, MessageAttachment)


class DeviceAPNS(ModelAdmin):

    fields = (
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_display = (
        'id',
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'user',
        'name',
        'device_id',
        'registration_id',
    )

site.register(models.DeviceAPNS, DeviceAPNS)


class DeviceGCM(ModelAdmin):

    fields = (
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_display = (
        'id',
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_display_links = (
        'id',
    )
    list_filter = (
        'id',
        'user',
        'name',
        'device_id',
        'registration_id',
    )
    list_select_related = (
        'user',
    )
    ordering = (
        'id',
    )
    search_fields = (
        'user',
        'name',
        'device_id',
        'registration_id',
    )

site.register(models.DeviceGCM, DeviceGCM)

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
