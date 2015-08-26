# -*- coding: utf-8 -*-

from django.apps import apps
from django.contrib.admin import ModelAdmin, site
from django.contrib.auth.admin import UserAdmin as AdministratorAdmin
from django.contrib.auth.models import User as Administrator
from django.contrib.gis.forms.widgets import BaseGeometryWidget
from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import ugettext_lazy
from social.apps.django_app.default.admin import UserSocialAuthOption
from social.apps.django_app.default.models import UserSocialAuth

from api import models

BaseGeometryWidget.display_raw = True


@property
def ewkt(self):
    if self.get_srid():
        return 'SRID={srid};POINT ({coords_0:.14f}, {coords_1:.14f})'.format(
            srid=self.srid, coords_0=self.coords[0], coords_1=self.coords[1],
        )
    return 'N/A'

GEOSGeometry.ewkt = ewkt

site.unregister(Administrator)
site.unregister(UserSocialAuth)

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
AdministratorAdmin.list_filter = (
    'username',
    'email',
    'first_name',
    'last_name',
    'is_active',
    'is_staff',
    'is_superuser',
    'last_login',
)
AdministratorAdmin.search_fields = ()

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
UserSocialAuthOption.list_filter = (
    'user',
    'provider',
)
UserSocialAuthOption.search_fields = (
    'uid',
)

site.register(Administrator, AdministratorAdmin)
site.register(UserSocialAuth, UserSocialAuthOption)


class Ad(ModelAdmin):

    fields = (
        'slot',
        'type',
        'source',
        'target',
    )
    list_display = (
        'id',
        'slot',
        'type',
        'source',
        'target',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'slot',
        'type',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'source',
        'target',
    )


class Block(ModelAdmin):

    fields = (
        'user_source',
        'user_destination',
    )
    list_display = (
        'id',
        'user_source',
        'user_destination',
        'timestamp',
    )
    list_filter = (
        'user_source',
        'user_destination',
        'timestamp',
    )
    search_fields = ()


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
    list_filter = (
        'user',
    )
    search_fields = (
        'name',
        'device_id',
        'registration_id',
    )


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
    list_filter = (
        'user',
    )
    search_fields = (
        'name',
        'device_id',
        'registration_id',
    )


class MasterTell(ModelAdmin):

    fields = (
        'created_by',
        'owned_by',
        'contents',
        'position',
        'is_visible',
    )
    list_display = (
        'id',
        'created_by',
        'owned_by',
        'position',
        'is_visible',
        'slave_tells_',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'created_by',
        'owned_by',
        'is_visible',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'contents',
    )

    def slave_tells_(self, instance):
        return instance.slave_tells.get_queryset().count()

    slave_tells_.allow_tags = True
    slave_tells_.short_description = 'Slave Tells'


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
    list_filter = (
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
    search_fields = (
        'contents',
    )

    def attachments_(self, instance):
        return instance.attachments.get_queryset().count()

    attachments_.allow_tags = True
    attachments_.short_description = 'Slave Tells'


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
    list_filter = (
        'message',
    )
    search_fields = (
        'string',
    )


class Notification(ModelAdmin):

    fields = (
        'user',
        'type',
        'contents',
        'status',
    )
    list_display = (
        'id',
        'user',
        'type',
        'status',
        'timestamp',
    )
    list_filter = (
        'user',
        'type',
        'status',
        'timestamp',
    )
    search_fields = (
        'contents',
    )


class RecommendedTell(ModelAdmin):

    fields = (
        'type',
        'contents',
        'photo',
    )
    list_display = (
        'id',
        'type',
        'contents',
        'photo',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'type',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'contents',
        'photo',
    )


class Report(ModelAdmin):

    fields = (
        'user_source',
        'user_destination',
    )
    list_display = (
        'id',
        'user_source',
        'user_destination',
        'timestamp',
    )
    list_filter = (
        'user_source',
        'user_destination',
        'timestamp',
    )
    search_fields = ()


class ShareUser(ModelAdmin):

    fields = (
        'user_source',
        'user_destination',
        'object',
    )
    list_display = (
        'id',
        'user_source',
        'user_destination',
        'object',
        'timestamp',
    )
    list_filter = (
        'user_source',
        'user_destination',
        'object',
        'timestamp',
    )
    search_fields = ()


class SlaveTell(ModelAdmin):

    fields = (
        'master_tell',
        'created_by',
        'owned_by',
        'photo',
        'first_name',
        'last_name',
        'type',
        'contents_original',
        'contents_preview',
        'description',
        'position',
        'is_editable',
    )
    list_display = (
        'id',
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'position',
        'is_editable',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'master_tell',
        'created_by',
        'owned_by',
        'type',
        'is_editable',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'photo',
        'first_name',
        'last_name',
        'contents_original',
        'contents_preview',
        'description',
    )


class Tellcard(ModelAdmin):

    fields = (
        'user_source',
        'user_destination',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    list_display = (
        'id',
        'user_source',
        'user_destination',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    list_filter = (
        'user_source',
        'user_destination',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    search_fields = ()


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
        'users_',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'name',
        'photo',
        'location',
        'phone',
        'url',
        'hours',
    )

    def users_(self, instance):
        return instance.users.get_queryset().count()

    users_.allow_tags = True
    users_.short_description = 'Users'


class User(ModelAdmin):

    fields = (
        'email',
        'photo_original',
        'photo_preview',
        'first_name',
        'last_name',
        'date_of_birth',
        'gender',
        'location',
        'description',
        'phone',
        'point',
        'is_signed_in',
    )
    list_display = (
        'id',
        'email',
        'first_name',
        'last_name',
        'master_tells_',
        'slave_tells_',
        'is_signed_in',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'is_signed_in',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'email',
        'photo_original',
        'photo_preview',
        'first_name',
        'last_name',
        'date_of_birth',
        'gender',
        'location',
        'description',
        'phone',
    )

    def master_tells_(self, instance):
        return instance.master_tells.get_queryset().count()

    master_tells_.allow_tags = True
    master_tells_.short_description = 'Master Tells'

    def slave_tells_(self, instance):
        return instance.slave_tells.get_queryset().count()

    slave_tells_.allow_tags = True
    slave_tells_.short_description = 'Slave Tells'


class UserLocation(ModelAdmin):

    fields = (
        'user',
        'tellzone',
        'location',
        'point',
        'accuracies_horizontal',
        'accuracies_vertical',
        'bearing',
        'is_casting',
    )
    list_display = (
        'id',
        'user',
        'tellzone',
        'location',
        'point',
        'accuracies_horizontal',
        'accuracies_vertical',
        'bearing',
        'is_casting',
        'timestamp',
    )
    list_filter = (
        'user',
        'tellzone',
        'is_casting',
        'timestamp',
    )
    search_fields = (
        'location',
    )


class UserPhoto(ModelAdmin):

    fields = (
        'user',
        'string_original',
        'string_preview',
        'description',
        'position',
    )
    list_display = (
        'id',
        'user',
        'string_original',
        'string_preview',
        'description',
        'position',
    )
    list_filter = (
        'user',
    )
    search_fields = (
        'string_original',
        'string_preview',
    )


class UserSetting(ModelAdmin):

    fields = (
        'user',
        'key',
        'value',
    )
    list_display = (
        'id',
        'user',
        'key',
        'value',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'user',
        'key',
        'inserted_at',
        'updated_at',
    )
    search_fields = (
        'value',
    )


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
    list_filter = (
        'user',
        'netloc',
    )
    search_fields = (
        'url',
    )


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
    list_filter = (
        'user',
    )
    search_fields = (
        'string',
        'title',
        'url',
        'notes',
    )


class UserStatusAttachment(ModelAdmin):

    fields = (
        'user_status',
        'string_original',
        'string_preview',
        'position',
    )
    list_display = (
        'id',
        'user_status',
        'string_original',
        'string_preview',
        'position',
    )
    list_filter = (
        'user_status',
    )
    search_fields = (
        'string_original',
        'string_preview',
    )


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
    list_filter = (
        'user',
        'tellzone',
        'viewed_at',
        'favorited_at',
    )
    search_fields = ()


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
    list_filter = (
        'user',
    )
    search_fields = (
        'string',
    )


apps.get_app_config('api').verbose_name = ugettext_lazy('API')
apps.get_app_config('auth').verbose_name = ugettext_lazy('Django')
apps.get_app_config('default').verbose_name = ugettext_lazy('Social')

site.register(models.Ad, Ad)
site.register(models.Block, Block)
site.register(models.DeviceAPNS, DeviceAPNS)
site.register(models.DeviceGCM, DeviceGCM)
site.register(models.MasterTell, MasterTell)
site.register(models.Message, Message)
site.register(models.MessageAttachment, MessageAttachment)
site.register(models.Notification, Notification)
site.register(models.RecommendedTell, RecommendedTell)
site.register(models.Report, Report)
site.register(models.ShareUser, ShareUser)
site.register(models.SlaveTell, SlaveTell)
site.register(models.Tellcard, Tellcard)
site.register(models.Tellzone, Tellzone)
site.register(models.User, User)
site.register(models.UserLocation, UserLocation)
site.register(models.UserPhoto, UserPhoto)
site.register(models.UserSetting, UserSetting)
site.register(models.UserSocialProfile, UserSocialProfile)
site.register(models.UserStatus, UserStatus)
site.register(models.UserStatusAttachment, UserStatusAttachment)
site.register(models.UserTellzone, UserTellzone)
site.register(models.UserURL, UserURL)
