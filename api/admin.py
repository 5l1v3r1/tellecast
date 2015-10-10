# -*- coding: utf-8 -*-

from django.apps import apps
from django.contrib import messages
from django.contrib.admin import helpers, ModelAdmin, site
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.utils import model_ngettext, unquote
from django.contrib.auth.admin import UserAdmin as AdministratorAdmin
from django.contrib.auth.models import User as Administrator
from django.contrib.gis.forms.widgets import BaseGeometryWidget
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.translation import ugettext as _, ugettext_lazy
from social.apps.django_app.default.admin import UserSocialAuthOption
from social.apps.django_app.default.models import UserSocialAuth

from api import models

BaseGeometryWidget.display_raw = True


def delete_selected(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied
    if request.POST.get('post'):
        count = queryset.count()
        if count:
            for object in queryset:
                modeladmin.log_deletion(request, object, force_text(object))
            queryset.delete()
            modeladmin.message_user(
                request,
                _('Successfully deleted {count} {items}.').format(
                    count=count, items=model_ngettext(modeladmin.opts, count),
                ),
                messages.SUCCESS,
            )
        return None
    context = dict(
        modeladmin.admin_site.each_context(request),
        action_checkbox_name=helpers.ACTION_CHECKBOX_NAME,
        objects_name=force_text(modeladmin.model._meta.verbose_name)
        if len(queryset) == 1 else force_text(modeladmin.model._meta.verbose_name_plural),
        opts=modeladmin.model._meta,
        queryset=queryset,
        title=_('Are you sure?'),
    )
    request.current_app = modeladmin.admin_site.name
    return TemplateResponse(
        request,
        modeladmin.delete_selected_confirmation_template or [
            'admin/{app_label}/{model_name}/delete_selected_confirmation.html'.format(
                app_label=modeladmin.model._meta.app_label, model_name=modeladmin.model._meta.model_name,
            ),
            'admin/{app_label}/delete_selected_confirmation.html'.format(app_label=modeladmin.model._meta.app_label),
            'admin/delete_selected_confirmation.html',
        ],
        context,
    )

delete_selected.short_description = ugettext_lazy('Delete selected %(verbose_name_plural)s')


def delete_view(self, request, object_id, extra_context=None):
    to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
    if to_field and not self.to_field_allowed(request, to_field):
        raise DisallowedModelAdminToField('The field {to_field} cannot be referenced.'.format(to_field=to_field))
    object = self.get_object(request, unquote(object_id), to_field)
    if not self.has_delete_permission(request, object):
        raise PermissionDenied
    if object is None:
        raise Http404(_('{name} object with primary key {key} does not exist.').format(
            name=force_text(self.model._meta.verbose_name), key=escape(object_id),
        ))
    if request.POST:
        object_display = force_text(object)
        self.log_deletion(request, object, object_display)
        self.delete_model(request, object)
        return self.response_delete(
            request,
            object_display,
            object.serializable_value(str(to_field) if to_field else self.model._meta.pk.attname),
        )
    context = dict(
        self.admin_site.each_context(request),
        app_label=self.model._meta.app_label,
        is_popup=IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
        object=object,
        object_name=force_text(self.model._meta.verbose_name),
        opts=self.model._meta,
        preserved_filters=self.get_preserved_filters(request),
        title=_('Are you sure?'),
        to_field=to_field,
    )
    context.update(extra_context or {})
    return self.render_delete_form(request, context)


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

AdministratorAdmin.actions = [delete_selected]
AdministratorAdmin.delete_view = delete_view
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

UserSocialAuthOption.actions = [delete_selected]
UserSocialAuthOption.delete_view = delete_view
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

    actions = [delete_selected]
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

Ad.delete_view = delete_view


class Block(ModelAdmin):

    actions = [delete_selected]
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

Block.delete_view = delete_view


class DeviceAPNS(ModelAdmin):

    actions = [delete_selected]
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

DeviceAPNS.delete_view = delete_view


class DeviceGCM(ModelAdmin):

    actions = [delete_selected]
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

DeviceGCM.delete_view = delete_view


class MasterTell(ModelAdmin):

    actions = [delete_selected]
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

MasterTell.delete_view = delete_view


class Message(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user_source',
        'user_source_is_hidden',
        'user_destination',
        'user_destination_is_hidden',
        'user_status',
        'master_tell',
        'post',
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
        'post',
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
        'post',
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

Message.delete_view = delete_view


class MessageAttachment(ModelAdmin):

    actions = [delete_selected]
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

MessageAttachment.delete_view = delete_view


class Notification(ModelAdmin):

    actions = [delete_selected]
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

Notification.delete_view = delete_view


class RecommendedTell(ModelAdmin):

    actions = [delete_selected]
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

RecommendedTell.delete_view = delete_view


class Report(ModelAdmin):

    actions = [delete_selected]
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

Report.delete_view = delete_view


class ShareUser(ModelAdmin):

    actions = [delete_selected]
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

ShareUser.delete_view = delete_view


class SlaveTell(ModelAdmin):

    actions = [delete_selected]
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

SlaveTell.delete_view = delete_view


class Tellcard(ModelAdmin):

    actions = [delete_selected]
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

Tellcard.delete_view = delete_view


class Tellzone(ModelAdmin):

    actions = [delete_selected]
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

Tellzone.delete_view = delete_view


class User(ModelAdmin):

    actions = [delete_selected]
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
        'token',
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

User.delete_view = delete_view


class UserLocation(ModelAdmin):

    actions = [delete_selected]
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

UserLocation.delete_view = delete_view


class UserPhoto(ModelAdmin):

    actions = [delete_selected]
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

UserPhoto.delete_view = delete_view


class UserSetting(ModelAdmin):

    actions = [delete_selected]
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

UserSetting.delete_view = delete_view


class UserSocialProfile(ModelAdmin):

    actions = [delete_selected]
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

UserSocialProfile.delete_view = delete_view


class UserStatus(ModelAdmin):

    actions = [delete_selected]
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

UserStatus.delete_view = delete_view


class UserStatusAttachment(ModelAdmin):

    actions = [delete_selected]
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

UserStatusAttachment.delete_view = delete_view


class UserTellzone(ModelAdmin):

    actions = [delete_selected]
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

UserTellzone.delete_view = delete_view


class UserURL(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user',
        'string',
        'position',
        'is_visible',
    )
    list_display = (
        'id',
        'user',
        'string',
        'position',
        'is_visible',
    )
    list_filter = (
        'user',
        'is_visible',
    )
    search_fields = (
        'string',
    )

UserURL.delete_view = delete_view


class Category(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'name',
    )
    list_display = (
        'id',
        'name',
    )
    list_filter = ()
    search_fields = (
        'name',
    )

Category.delete_view = delete_view


class Post(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user',
        'category',
        'title',
        'contents',
    )
    list_display = (
        'id',
        'user',
        'category',
        'title',
        'inserted_at',
        'updated_at',
        'expired_at',
    )
    list_filter = (
        'user',
        'category',
    )
    search_fields = (
        'title',
        'contents',
    )

Post.delete_view = delete_view


class PostAttachment(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'post',
        'type',
        'contents',
        'position',
    )
    list_display = (
        'id',
        'post',
        'type',
        'contents',
        'position',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'post',
        'type',
    )
    search_fields = (
        'contents',
    )

PostAttachment.delete_view = delete_view


class PostTellzone(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'post',
        'tellzone',
    )
    list_display = (
        'id',
        'post',
        'tellzone',
    )
    list_filter = (
        'post',
        'tellzone',
    )
    search_fields = ()

PostTellzone.delete_view = delete_view


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
site.register(models.Category, Category)
site.register(models.Post, Post)
site.register(models.PostAttachment, PostAttachment)
site.register(models.PostTellzone, PostTellzone)
