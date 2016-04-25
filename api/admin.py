# -*- coding: utf-8 -*-

from uuid import uuid4

from bcrypt import gensalt, hashpw
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from celery import current_app
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers, ModelAdmin, site, widgets
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import model_ngettext, unquote
from django.contrib.auth.admin import UserAdmin as AdministratorAdmin
from django.contrib.auth.models import User as Administrator
from django.contrib.gis.forms.widgets import BaseGeometryWidget
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms import ModelForm
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext_lazy
from social.apps.django_app.default.admin import UserSocialAuthOption
from social.apps.django_app.default.models import UserSocialAuth
from ujson import loads

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
                _(u'Successfully deleted {count:d} {items:s}.').format(
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
            u'admin/{app_label:s}/{model_name:s}/delete_selected_confirmation.html'.format(
                app_label=modeladmin.model._meta.app_label, model_name=modeladmin.model._meta.model_name,
            ),
            u'admin/{app_label:s}/delete_selected_confirmation.html'.format(
                app_label=modeladmin.model._meta.app_label,
            ),
            u'admin/delete_selected_confirmation.html',
        ],
        context,
    )

delete_selected.short_description = ugettext_lazy('Delete selected %(verbose_name_plural)s')


def delete_view(self, request, object_id, extra_context=None):
    to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
    if to_field and not self.to_field_allowed(request, to_field):
        raise DisallowedModelAdminToField(u'The field {to_field:s} cannot be referenced.'.format(to_field=to_field))
    object = self.get_object(request, unquote(object_id), to_field)
    if not self.has_delete_permission(request, object):
        raise PermissionDenied
    if object is None:
        raise Http404(_(u'{name:} object with primary key {key:s} does not exist.').format(
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
        return u'SRID={srid};POINT ({coords_0:.14f}, {coords_1:.14f})'.format(
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
AdministratorAdmin.list_per_page = 10
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
UserSocialAuthOption.list_per_page = 10
UserSocialAuthOption.search_fields = (
    'uid',
)

site.register(Administrator, AdministratorAdmin)
site.register(UserSocialAuth, UserSocialAuthOption)


class AdminFileWidget(widgets.AdminFileWidget):

    def render(self, name, value, attrs=None):
        output = []
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        if value:
            output.append(u'<br>')
            output.append(u'<a href="{photo:s}" target="_blank">{photo:s}</a>'.format(photo=value))
        return mark_safe(u''.join(output))


class Form(ModelForm):

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self.fields['photo'].widget = AdminFileWidget()
        if self.instance.pk:
            self.fields['photo'].required = False
        self.fields['user'].required = False
        self.fields['type'].required = False
        self.fields['phone'].required = False
        self.fields['url'].required = False
        self.fields['hours'].required = False
        self.fields['status'].required = False
        self.fields['started_at'].required = False
        self.fields['ended_at'].required = False

    def clean_hours(self):
        try:
            return loads(self.data.get('hours'))
        except Exception:
            pass
        return {}

    def clean_photo(self):
        if self.instance.pk:
            if 'photo' not in self.files:
                return self.instance.photo
        if self.files['photo'].content_type not in ['image/gif', 'image/jpeg', 'image/jpg', 'image/png']:
            raise ValidationError('Invalid Photo')
        uuid = u'{prefix:s}.{suffix:s}'.format(
            prefix=str(uuid4()), suffix=self.files['photo'].content_type.split('/')[-1],
        )
        try:
            photo = Key(
                S3Connection(
                    settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY,
                ).get_bucket(
                    settings.AWS_BUCKET,
                )
            )
            photo.content_type = self.files['photo'].content_type
            photo.key = uuid
            photo.set_contents_from_string(self.files['photo'].read())
            return u'https://d2k6ktnea3auzx.cloudfront.net/{uuid:s}'.format(uuid=uuid)
        except Exception:
            pass
        raise ValidationError('Invalid Photo')


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
    list_per_page = 10
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
    list_per_page = 10
    list_filter = (
        'user_source',
        'user_destination',
        'timestamp',
    )
    search_fields = ()

Block.delete_view = delete_view


class Category(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'name',
        'photo',
        'position',
    )
    list_display = (
        'id',
        'name',
        'position',
    )
    list_filter = ()
    list_per_page = 10
    search_fields = (
        'name',
        'photo',
        'position',
    )

Category.delete_view = delete_view


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
    list_per_page = 10
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
    list_per_page = 10
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
        'category',
        'contents',
        'description',
        'position',
        'is_visible',
    )
    list_display = (
        'id',
        'created_by',
        'owned_by',
        'category',
        'position',
        'is_visible',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'created_by',
        'owned_by',
        'category',
        'is_visible',
        'inserted_at',
        'updated_at',
    )
    list_per_page = 10
    search_fields = (
        'contents',
        'description',
    )

MasterTell.delete_view = delete_view


class MasterTellTellzone(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'master_tell',
        'tellzone',
    )
    list_display = (
        'id',
        'master_tell',
        'master_tell_created_by',
        'master_tell_contents',
        'tellzone',
        'tellzone_user',
    )
    list_filter = (
        'master_tell',
        'tellzone',
    )
    list_per_page = 10
    search_fields = ()

    def master_tell_created_by(self, instance):
        return instance.master_tell.created_by

    master_tell_created_by.short_description = 'Master tell :: Created by'

    def master_tell_contents(self, instance):
        return instance.master_tell.contents

    master_tell_contents.short_description = 'Master tell :: Contents'

    def tellzone_user(self, instance):
        return instance.tellzone.user

    tellzone_user.short_description = 'Tellzone :: User'

MasterTellTellzone.delete_view = delete_view


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
        'is_suppressed',
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
        'is_suppressed',
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
        'is_suppressed',
        'inserted_at',
        'updated_at',
    )
    list_per_page = 10
    search_fields = (
        'contents',
    )

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
    list_per_page = 10
    search_fields = (
        'string',
    )

MessageAttachment.delete_view = delete_view


class Network(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user',
        'name',
    )
    list_display = (
        'id',
        'user',
        'name',
    )
    list_filter = (
        'user',
    )
    list_per_page = 10
    search_fields = (
        'name',
    )

Network.delete_view = delete_view


class NetworkTellzone(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'network',
        'tellzone',
    )
    list_display = (
        'id',
        'network',
        'tellzone',
    )
    list_filter = (
        'network',
        'tellzone',
    )
    list_per_page = 10
    search_fields = ()

NetworkTellzone.delete_view = delete_view


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
    list_per_page = 10
    search_fields = (
        'contents',
    )

Notification.delete_view = delete_view


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
    list_per_page = 10
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
        'string_original',
        'string_preview',
        'position',
    )
    list_display = (
        'id',
        'post',
        'type',
        'string_original',
        'string_preview',
        'position',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'post',
        'type',
    )
    list_per_page = 10
    search_fields = (
        'string_original',
        'string_preview',
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
    list_per_page = 10
    search_fields = ()

PostTellzone.delete_view = delete_view


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
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
        'network',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    list_display = (
        'id',
        'user_source',
        'user_destination',
        'network',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    list_filter = (
        'user_source',
        'user_destination',
        'network',
        'tellzone',
        'location',
        'viewed_at',
        'saved_at',
    )
    list_per_page = 10
    search_fields = ()

Tellcard.delete_view = delete_view


class Tellzone(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user',
        'type',
        'name',
        'description',
        'photo',
        'location',
        'phone',
        'url',
        'hours',
        'point',
        'status',
        'started_at',
        'ended_at',
    )
    form = Form
    list_display = (
        'id',
        'user',
        'type',
        'name_',
        'location',
        'phone',
        'url',
        'point',
        'status',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'user',
        'status',
        'inserted_at',
        'updated_at',
    )
    list_per_page = 10
    search_fields = (
        'type',
        'name',
        'description',
        'photo',
        'location',
        'phone',
        'url',
        'hours',
    )

    def name_(self, instance):
        return u'<a href="{photo:s}" target="_blank">{name:s}</a>'.format(photo=instance.photo, name=instance.name)

    name_.allow_tags = True

    def save_model(self, request, tellzone, form, change):
        tellzone.hours = form.cleaned_data.get('hours')
        tellzone.photo = form.cleaned_data.get('photo')
        tellzone.save()


Tellzone.delete_view = delete_view


class TellzoneSocialProfile(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'tellzone',
        'netloc',
        'url',
    )
    list_display = (
        'id',
        'tellzone',
        'netloc',
        'url',
    )
    list_filter = (
        'tellzone',
        'netloc',
    )
    list_per_page = 10
    search_fields = (
        'url',
    )

TellzoneSocialProfile.delete_view = delete_view


class User(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'tellzone',
        'type',
        'email',
        'password',
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
        'is_verified',
        'is_signed_in',
    )
    list_display = (
        'id',
        'tellzone',
        'type',
        'email',
        'first_name',
        'last_name',
        'is_verified',
        'is_signed_in',
        'inserted_at',
        'updated_at',
        'token',
        'access_code',
    )
    list_filter = (
        'tellzone',
        'type',
        'is_verified',
        'is_signed_in',
        'inserted_at',
        'updated_at',
        'access_code',
    )
    list_per_page = 10
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
        'access_code',
    )

    def save_model(self, request, user, form, change):
        if 'password' in form.changed_data:
            if user.password:
                user.password = hashpw(user.password.encode('utf-8'), gensalt(10))
        user.save()
        if not user.is_verified:
            current_app.send_task(
                'api.tasks.email_notifications',
                (user.id, 'verify',),
                queue='api.tasks.email_notifications',
                routing_key='api.tasks.email_notifications',
                serializer='json',
            )

User.delete_view = delete_view


class UserLocation(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'user',
        'network',
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
        'network',
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
        'network',
        'tellzone',
        'is_casting',
        'timestamp',
    )
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
    list_per_page = 10
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
        'favorited_at',
        'pinned_at',
        'viewed_at',
    )
    list_display = (
        'id',
        'user',
        'tellzone',
        'favorited_at',
        'pinned_at',
        'viewed_at',
    )
    list_filter = (
        'user',
        'tellzone',
        'favorited_at',
        'pinned_at',
        'viewed_at',
    )
    list_per_page = 10
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
    list_per_page = 10
    search_fields = (
        'string',
    )

UserURL.delete_view = delete_view


class Version(ModelAdmin):

    actions = [delete_selected]
    fields = (
        'platform',
        'number',
    )
    list_display = (
        'id',
        'platform',
        'number',
        'inserted_at',
        'updated_at',
    )
    list_filter = (
        'platform',
        'inserted_at',
        'updated_at',
    )
    list_per_page = 10
    search_fields = (
        'number',
    )

Version.delete_view = delete_view

apps.get_app_config('api').verbose_name = ugettext_lazy('API')
apps.get_app_config('auth').verbose_name = ugettext_lazy('Django')
apps.get_app_config('default').verbose_name = ugettext_lazy('Social')

site.register(models.Ad, Ad)
site.register(models.Block, Block)
site.register(models.Category, Category)
site.register(models.DeviceAPNS, DeviceAPNS)
site.register(models.DeviceGCM, DeviceGCM)
site.register(models.MasterTell, MasterTell)
site.register(models.MasterTellTellzone, MasterTellTellzone)
site.register(models.Message, Message)
site.register(models.MessageAttachment, MessageAttachment)
site.register(models.Network, Network)
site.register(models.NetworkTellzone, NetworkTellzone)
site.register(models.Notification, Notification)
site.register(models.Post, Post)
site.register(models.PostAttachment, PostAttachment)
site.register(models.PostTellzone, PostTellzone)
site.register(models.RecommendedTell, RecommendedTell)
site.register(models.Report, Report)
site.register(models.ShareUser, ShareUser)
site.register(models.SlaveTell, SlaveTell)
site.register(models.Tellcard, Tellcard)
site.register(models.Tellzone, Tellzone)
site.register(models.TellzoneSocialProfile, TellzoneSocialProfile)
site.register(models.User, User)
site.register(models.UserLocation, UserLocation)
site.register(models.UserPhoto, UserPhoto)
site.register(models.UserSetting, UserSetting)
site.register(models.UserSocialProfile, UserSocialProfile)
site.register(models.UserStatus, UserStatus)
site.register(models.UserStatusAttachment, UserStatusAttachment)
site.register(models.UserTellzone, UserTellzone)
site.register(models.UserURL, UserURL)
site.register(models.Version, Version)
