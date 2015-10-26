# -*- coding: utf-8 -*-

from collections import OrderedDict
from traceback import print_exc

from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.six import string_types
from django.utils.translation import ugettext_lazy
from drf_extra_fields.geo_fields import PointField
from geopy.distance import vincenty
from rest_framework.fields import SkipField
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DictField,
    EmailField,
    FloatField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    ValidationError,
)
from rollbar import report_exc_info
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import loads

from api import models

BooleanField.FALSE_VALUES = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False, ''))


def to_representation(self, value):
    if self.format is None:
        return value
    if self.format.lower() == 'iso-8601':
        value = value.isoformat()
        if value.endswith('+00:00'):
            value = value[:-6] + 'Z'
        if len(value) == 19:
            value = value + '.000000'
        return value
    return value.strftime(self.format)

DateTimeField.to_representation = to_representation


def to_internal_value(self, value):
    if value in (None, '', [], (), {}):
        return None
    if isinstance(value, string_types):
        try:
            value = loads(value.replace("'", '"'))
        except ValueError:
            raise ValidationError(self.error_messages['invalid'])
    if value and type(value) is dict:
        longitude = value.get('longitude')
        latitude = value.get('latitude')
        if longitude and latitude:
            return Point(longitude, latitude)

PointField.to_internal_value = to_internal_value


def get_user_id(context):
    request = context.get('request', None)
    if request is None:
        return 0
    if not request.user.is_authenticated():
        return 0
    return request.user.id


class Null(Serializer):
    pass


class Ad(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'slot',
            'type',
            'source',
            'target',
            'inserted_at',
            'updated_at',
        )
        model = models.Ad


class Category(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'name',
        )
        model = models.Category


class DeviceAPNS(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS

    def insert_or_update(self):
        return models.DeviceAPNS.insert_or_update(get_user_id(self.context), self.validated_data)


class DeviceGCM(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM

    def insert_or_update(self):
        return models.DeviceGCM.insert_or_update(get_user_id(self.context), self.validated_data)


class Notification(ModelSerializer):

    contents = DictField()

    class Meta:

        fields = (
            'id',
            'type',
            'contents',
            'status',
            'timestamp',
        )
        model = models.Notification


class RecommendedTell(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'type',
            'contents',
            'photo',
        )
        model = models.RecommendedTell


class UserPhoto(ModelSerializer):

    string_preview = CharField(allow_blank=True, required=False)
    description = CharField(allow_blank=True, required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string_original',
            'string_preview',
            'description',
            'position',
        )
        model = models.UserPhoto


class UserLocation(ModelSerializer):

    tellzone_id = IntegerField(allow_null=True, default=None)
    location = CharField(allow_blank=True, required=False)
    point = PointField()
    accuracies_horizontal = FloatField(default=0.00)
    accuracies_vertical = FloatField(default=0.00)
    bearing = IntegerField(default=0)
    is_casting = BooleanField(default=False)

    class Meta:

        fields = (
            'tellzone_id',
            'location',
            'point',
            'accuracies_horizontal',
            'accuracies_vertical',
            'bearing',
            'is_casting',
        )
        model = models.UserLocation

    def insert(self):
        return models.UserLocation.insert(get_user_id(self.context), self.validated_data)


class UserSetting(Serializer):

    show_last_name = BooleanField()
    show_photo = BooleanField()
    show_email = BooleanField()
    show_phone = BooleanField()
    show_photos = BooleanField()
    notifications_invitations = BooleanField()
    notifications_messages = BooleanField()
    notifications_saved_you = BooleanField()
    notifications_shared_profiles = BooleanField()


class UserSocialProfile(ModelSerializer):

    url = CharField(allow_blank=True, required=False)

    class Meta:

        fields = (
            'id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatusAttachment(ModelSerializer):

    string_preview = CharField(allow_blank=True, required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string_original',
            'string_preview',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatus(ModelSerializer):

    url = CharField(allow_blank=True, required=False)
    notes = CharField(allow_blank=True, required=False)
    attachments = UserStatusAttachment(help_text='List of Users :: Statuses :: Attachments', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'title',
            'url',
            'notes',
            'attachments',
        )
        model = models.UserStatus


class UserTellzone(ModelSerializer):

    user_id = IntegerField()
    tellzone_id = IntegerField()
    action = ChoiceField(
        choices=(
            ('View', 'View',),
            ('Favorite', 'Favorite',),
        ),
    )

    class Meta:

        fields = (
            'id',
            'user_id',
            'tellzone_id',
            'viewed_at',
            'favorited_at',
            'action',
        )
        model = models.UserTellzone

    def insert_or_update(self):
        return models.UserTellzone.insert_or_update(get_user_id(self.context), self.validated_data)

    def delete(self):
        return models.UserTellzone.remove(get_user_id(self.context), self.validated_data)


class UserURL(ModelSerializer):

    position = IntegerField(required=False)
    is_visible = BooleanField(default=True, required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
            'is_visible',
        )
        model = models.UserURL


class SlaveTell(ModelSerializer):

    master_tell_id = IntegerField()
    created_by_id = IntegerField()
    owned_by_id = IntegerField()
    contents_preview = CharField(allow_blank=True, required=False)
    is_editable = BooleanField(default=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'master_tell_id',
            'created_by_id',
            'owned_by_id',
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents_original',
            'contents_preview',
            'description',
            'position',
            'is_editable',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell

    def insert(self):
        return models.SlaveTell.insert(get_user_id(self.context), self.validated_data)

    def update(self):
        return self.instance.update(self.validated_data)


class MasterTell(ModelSerializer):

    created_by_id = IntegerField()
    owned_by_id = IntegerField()
    position = IntegerField(required=False)
    is_visible = BooleanField(default=True, required=False)
    slave_tells = SlaveTell(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'contents',
            'position',
            'is_visible',
            'inserted_at',
            'updated_at',
            'slave_tells',
        )
        model = models.MasterTell

    def insert(self):
        return models.MasterTell.insert(get_user_id(self.context), self.validated_data)

    def update(self):
        return self.instance.update(self.validated_data)


class User(ModelSerializer):

    photo_original = CharField(allow_blank=True, required=False)
    photo_preview = CharField(allow_blank=True, required=False)
    first_name = CharField(allow_blank=True, required=False)
    last_name = CharField(allow_blank=True, required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(allow_blank=True, required=False)
    location = CharField(allow_blank=True, required=False)
    description = CharField(allow_blank=True, required=False)
    phone = CharField(allow_blank=True, required=False)
    point = PointField(required=False)
    photos = UserPhoto(help_text='List of Users :: Photos', many=True, required=False)
    settings = UserSetting(help_text='Users :: Settings', required=False)
    social_profiles = UserSocialProfile(help_text='List of Users :: Social Profiles', many=True, required=False)
    status = UserStatus(help_text='Users :: Status', required=False)
    urls = UserURL(help_text='List of Users :: URLs', many=True, required=False)
    master_tells = MasterTell(help_text='List of Master Tells', many=True, required=False)
    messages = IntegerField()
    is_tellcard = BooleanField()
    posts = IntegerField()

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'photos',
            'settings',
            'social_profiles',
            'status',
            'urls',
            'master_tells',
            'messages',
            'token',
            'is_tellcard',
            'posts',
        )
        model = models.User

    def insert(self):
        return models.User.insert(self.validated_data)

    def update(self):
        return self.instance.update(self.validated_data)

    def to_representation(self, instance):
        id = get_user_id(self.context)
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'email':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_email']:
                    dictionary[field.field_name] = instance.email
                continue
            if field.field_name == 'photo_original':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_photo']:
                    dictionary[field.field_name] = instance.photo_original
                continue
            if field.field_name == 'photo_preview':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_photo']:
                    dictionary[field.field_name] = instance.photo_preview
                continue
            if field.field_name == 'last_name':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_last_name']:
                    dictionary[field.field_name] = instance.last_name
                continue
            if field.field_name == 'phone':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_phone']:
                    dictionary[field.field_name] = instance.phone
                continue
            if field.field_name == 'settings':
                dictionary[field.field_name] = instance.settings_
                continue
            if field.field_name == 'master_tells':
                dictionary[field.field_name] = [
                    MasterTell(master_tell, context=self.context).data
                    for master_tell in instance.master_tells.get_queryset().filter(is_visible=True)
                ]
                continue
            if field.field_name == 'messages':
                dictionary[field.field_name] = instance.get_messages(id)
                continue
            if field.field_name == 'token':
                dictionary[field.field_name] = instance.token
                continue
            if field.field_name == 'is_tellcard':
                dictionary[field.field_name] = instance.is_tellcard(id)
                continue
            if field.field_name == 'posts':
                dictionary[field.field_name] = instance.get_posts()
                continue
            attribute = None
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            if attribute is None:
                dictionary[field.field_name] = None
            else:
                dictionary[field.field_name] = field.to_representation(attribute)
        return dictionary


class PostAttachment(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'type',
            'string_original',
            'string_preview',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.PostAttachment


class UsersProfile(User):

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'photos',
            'social_profiles',
            'status',
            'urls',
            'master_tells',
            'messages',
            'is_tellcard',
            'posts',
        )
        model = models.User


class BlockUser(User):

    class Meta:

        fields = (
            'id',
            'photo_original',
            'photo_preview',
            'first_name',
            'last_name',
            'location',
        )
        model = models.User


class Block(ModelSerializer):

    user_destination_id = IntegerField()
    user = BlockUser(source='user_destination')
    report = BooleanField(default=False)

    class Meta:

        fields = (
            'id',
            'user_destination_id',
            'user',
            'timestamp',
            'report',
        )
        model = models.Block

    def insert_or_update(self):
        return models.Block.insert_or_update(
            get_user_id(self.context), self.validated_data['user_destination_id'], self.validated_data['report'],
        )

    def delete(self):
        return models.Block.remove(get_user_id(self.context), self.validated_data['user_destination_id'])


class DevicesAPNSRequest(DeviceAPNS):

    class Meta:

        fields = (
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS


class DevicesAPNSResponse(DeviceAPNS):

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS


class DevicesGCMRequest(DeviceGCM):

    class Meta:

        fields = (
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM


class DevicesGCMResponse(DeviceGCM):

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM


class ShareUser(ModelSerializer):

    user_destination_id = IntegerField(default=None)
    user = UsersProfile()
    object_id = IntegerField()
    object = UsersProfile()

    class Meta:

        fields = (
            'user_destination_id',
            'user',
            'object_id',
            'object',
            'timestamp',
        )
        model = models.ShareUser

    def to_representation(self, instance):
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'user':
                request = self.context.get('request', None)
                if request:
                    if 'type' in request.QUERY_PARAMS:
                        if request.QUERY_PARAMS['type'] == 'Source':
                            dictionary[field.field_name] = field.to_representation(instance.user_destination)
                            continue
                        if request.QUERY_PARAMS['type'] == 'Destination':
                            dictionary[field.field_name] = field.to_representation(instance.user_source)
                            continue
                dictionary[field.field_name] = field.to_representation(instance.user_destination)
                continue
            attribute = None
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            if attribute is None:
                dictionary[field.field_name] = None
            else:
                dictionary[field.field_name] = field.to_representation(attribute)
        return dictionary

    def insert(self):
        return models.ShareUser.insert(
            get_user_id(self.context), self.validated_data['user_destination_id'], self.validated_data['object_id'],
        )


class TellzonePostUser(User):

    class Meta:

        fields = (
            'id',
            'photo_original',
            'photo_preview',
            'first_name',
            'last_name',
            'location',
        )
        model = models.User


class TellzonePost(ModelSerializer):

    user = TellzonePostUser()
    category = Category()
    attachments = PostAttachment(many=True)

    class Meta:

        fields = (
            'id',
            'user',
            'category',
            'title',
            'contents',
            'inserted_at',
            'updated_at',
            'expired_at',
            'attachments',
        )
        model = models.Post


class Tellzone(ModelSerializer):

    hours = DictField()
    point = PointField()
    views = IntegerField()
    favorites = IntegerField()
    distance = FloatField()
    connections = UsersProfile(many=True, required=False)
    tellecasters = IntegerField()
    is_viewed = BooleanField()
    is_favorited = BooleanField()
    posts = TellzonePost(many=True)

    class Meta:

        fields = (
            'id',
            'name',
            'photo',
            'location',
            'phone',
            'url',
            'hours',
            'point',
            'inserted_at',
            'updated_at',
            'views',
            'favorites',
            'distance',
            'connections',
            'tellecasters',
            'is_viewed',
            'is_favorited',
            'posts',
        )
        model = models.Tellzone

    def to_representation(self, instance):
        id = get_user_id(self.context)
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'distance':
                try:
                    dictionary[field.field_name] = getattr(instance.distance, 'ft', 0.00)
                    continue
                except AttributeError:
                    point = self.context.get('point', None)
                    if not instance.point or not point:
                        dictionary[field.field_name] = 0.00
                        continue
                    dictionary[field.field_name] = vincenty(
                        (instance.point.x, instance.point.y), (point.x, point.y)
                    ).ft
                    continue
            if field.field_name == 'connections':
                dictionary[field.field_name] = instance.get_connections(id)
                continue
            if field.field_name == 'is_viewed':
                dictionary[field.field_name] = instance.is_viewed(id)
                continue
            if field.field_name == 'is_favorited':
                dictionary[field.field_name] = instance.is_favorited(id)
                continue
            attribute = None
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            if attribute is None:
                dictionary[field.field_name] = None
            else:
                dictionary[field.field_name] = field.to_representation(attribute)
        return dictionary


class TellcardTellzone(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
            'photo',
            'location',
            'phone',
            'url',
            'hours',
            'point',
            'inserted_at',
            'updated_at',
        )
        model = models.Tellzone


class Tellcard(ModelSerializer):

    user_destination_id = IntegerField()
    user = UsersProfile()
    tellzone_id = IntegerField(required=False)
    tellzone = TellcardTellzone(required=False)
    location = CharField(allow_blank=True, required=False)
    action = ChoiceField(
        choices=(
            ('View', 'View',),
            ('Save', 'Save',),
        ),
    )

    class Meta:

        fields = (
            'id',
            'user_destination_id',
            'user',
            'tellzone_id',
            'tellzone',
            'location',
            'viewed_at',
            'saved_at',
            'action',
        )
        model = models.Tellcard

    def to_representation(self, instance):
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'user':
                request = self.context.get('request', None)
                if request:
                    if 'type' in request.QUERY_PARAMS:
                        if request.QUERY_PARAMS['type'] == 'Source':
                            dictionary[field.field_name] = field.to_representation(instance.user_destination)
                            continue
                        if request.QUERY_PARAMS['type'] == 'Destination':
                            dictionary[field.field_name] = field.to_representation(instance.user_source)
                            continue
                dictionary[field.field_name] = field.to_representation(instance.user_destination)
                continue
            attribute = None
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue
            if attribute is None:
                dictionary[field.field_name] = None
            else:
                dictionary[field.field_name] = field.to_representation(attribute)
        return dictionary

    def insert_or_update(self):
        return models.Tellcard.insert_or_update(get_user_id(self.context), self.validated_data)

    def delete(self):
        return models.Tellcard.remove(get_user_id(self.context), self.validated_data)


class PostUser(User):

    class Meta:

        fields = (
            'id',
            'photo_original',
            'photo_preview',
            'first_name',
            'last_name',
            'location',
        )
        model = models.User


class PostTellzone(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
            'photo',
            'location',
            'phone',
            'url',
            'hours',
            'point',
            'inserted_at',
            'updated_at',
            'views',
            'favorites',
            'distance',
            'connections',
            'tellecasters',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone


class Post(ModelSerializer):

    user_id = IntegerField()
    user = PostUser()
    category_id = IntegerField()
    category = Category()
    title = CharField(required=False)
    attachments = PostAttachment(many=True)
    tellzones = PostTellzone(many=True)

    class Meta:

        fields = (
            'id',
            'category',
            'title',
            'contents',
            'inserted_at',
            'updated_at',
            'expired_at',
            'attachments',
            'tellzones',
        )
        model = models.Post

    def insert(self):
        return models.Post.insert(get_user_id(self.context), self.validated_data)

    def update(self):
        return self.instance.update(self.validated_data)


class MessageUser(User):

    class Meta:

        fields = (
            'id',
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
        model = models.User


class MessageUserStatus(UserStatus):

    class Meta:

        fields = (
            'id',
            'string',
            'title',
            'url',
            'notes',
            'attachments',
        )
        model = models.UserStatus


class MessageMasterTell(MasterTell):

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'contents',
            'position',
            'is_visible',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class MessageAttachment(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.MessageAttachment


class Message(ModelSerializer):

    user_source_id = IntegerField()
    user_source = MessageUser()
    user_source_is_hidden = BooleanField(default=False)
    user_destination_id = IntegerField()
    user_destination = MessageUser()
    user_destination_is_hidden = BooleanField(default=False)
    user_status_id = IntegerField(allow_null=True, required=False)
    user_status = MessageUserStatus(required=False)
    master_tell_id = IntegerField(allow_null=True, required=False)
    master_tell = MessageMasterTell(required=False)
    post_id = IntegerField(allow_null=True, required=False)
    attachments = MessageAttachment(help_text='List of Messages :: Attachments', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'user_source_id',
            'user_source',
            'user_source_is_hidden',
            'user_destination_id',
            'user_destination',
            'user_destination_is_hidden',
            'user_status',
            'master_tell',
            'post_id',
            'type',
            'contents',
            'status',
            'inserted_at',
            'updated_at',
            'attachments',
        )
        model = models.Message


class Ads(Ad):
    pass


class AuthenticateRequest(Serializer):

    access_token = CharField(help_text='OAuth 2 `access_token`')


class AuthenticateResponse(User):

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'token',
        )
        model = models.User


class BlocksRequest(Block):

    class Meta:

        fields = (
            'user_destination_id',
            'report',
        )
        model = models.Block


class BlocksResponse(Block):

    class Meta:

        fields = (
            'id',
            'user',
            'timestamp',
        )
        model = models.Block


class Categories(Category):
    pass


class DeauthenticateRequest(Serializer):

    type = CharField(allow_blank=True, required=False)
    device_id = CharField(allow_blank=True, required=False)
    registration_id = CharField(allow_blank=True, required=False)

    def process(self):
        if 'type' not in self.validated_data:
            return
        if self.validated_data['type'] == 'APNS':
            if 'registration_id' in self.validated_data and self.validated_data['registration_id']:
                models.DeviceAPNS.objects.get_queryset().filter(
                    user_id=get_user_id(self.context),
                    registration_id=self.validated_data['registration_id']
                ).delete()
        if self.validated_data['type'] == 'GCM':
            if 'device_id' in self.validated_data and self.validated_data['device_id']:
                models.DeviceGCM.objects.get_queryset().filter(
                    user_id=get_user_id(self.context),
                    device_id=self.validated_data['device_id']
                ).delete()


class DeauthenticateResponse(Null):
    pass


class HomeRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    dummy = ChoiceField(
        choices=(
            ('No', 'No',),
            ('Yes', 'Yes',),
        ),
        default='No',
        required=False,
    )


class HomeConnectionsRequest(HomeRequest):
    pass


class HomeConnectionsResponseItemsUser(User):

    class Meta:

        fields = (
            'id',
            'photo_original',
            'photo_preview',
            'first_name',
            'last_name',
            'location',
            'description',
            'point',
            'photos',
            'status',
            'master_tells',
            'is_tellcard',
            'posts',
        )
        model = models.User


class HomeConnectionsResponseItemsTellzone(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
            'photo',
            'location',
            'phone',
            'url',
            'hours',
            'point',
            'inserted_at',
            'updated_at',
        )
        model = models.Tellzone


class HomeConnectionsResponseItems(Serializer):

    user = HomeConnectionsResponseItemsUser()
    tellzone = HomeConnectionsResponseItemsTellzone(required=False)
    location = CharField(allow_blank=True, required=False)
    point = PointField()
    timestamp = DateTimeField()


class HomeConnectionsResponse(Serializer):

    days = DictField(child=IntegerField())
    trailing_24_hours = IntegerField()
    users = HomeConnectionsResponseItems(many=True, required=False)


class HomeStatisticsFrequentRequest(HomeRequest):
    pass


class HomeStatisticsFrequentResponseViews(Serializer):

    today = IntegerField()
    total = IntegerField()


class HomeStatisticsFrequentResponseSaves(Serializer):

    today = IntegerField()
    total = IntegerField()


class HomeStatisticsFrequentResponseUsers(Serializer):

    near = IntegerField()
    area = IntegerField()


class HomeStatisticsFrequentResponse(Serializer):

    views = HomeStatisticsFrequentResponseViews()
    saves = HomeStatisticsFrequentResponseSaves()
    users = HomeStatisticsFrequentResponseUsers()


class HomeStatisticsInfrequentRequest(HomeRequest):
    pass


class HomeStatisticsInfrequentResponseViews(Serializer):

    days = DictField(child=IntegerField())
    weeks = DictField(child=IntegerField())
    months = DictField(child=IntegerField())


class HomeStatisticsInfrequentResponseSaves(Serializer):

    days = DictField(child=IntegerField())
    weeks = DictField(child=IntegerField())
    months = DictField(child=IntegerField())


class HomeStatisticsInfrequentResponse(Serializer):

    views = HomeStatisticsInfrequentResponseViews()
    saves = HomeStatisticsInfrequentResponseSaves()


class HomeTellzonesRequest(HomeRequest):
    pass


class HomeTellzonesResponse(Tellzone):
    pass


class MasterTellsRequest(MasterTell):

    class Meta:

        fields = (
            'contents',
            'position',
            'is_visible',
        )
        model = models.MasterTell


class MasterTellsResponse(MasterTell):

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'contents',
            'position',
            'is_visible',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class MasterTellsGetRequest(Serializer):

    inserted_at = DateTimeField(required=False)
    updated_at = DateTimeField(required=False)


class MasterTellsGetResponse(MasterTellsResponse):
    pass


class MessagesGetRequest(Serializer):

    recent = BooleanField(default=False)
    user_id = IntegerField(required=False)
    user_status_id = IntegerField(required=False)
    master_tell_id = IntegerField(required=False)
    post_id = IntegerField(required=False)
    since_id = IntegerField(required=False)
    max_id = IntegerField(required=False)
    limit = IntegerField(required=False)


class MessagesGetResponse(Message):
    pass


class MessagesPostRequestAttachment(MessageAttachment):

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.MessageAttachment


class MessagesPostRequest(Message):

    attachments = MessagesPostRequestAttachment(help_text='List of Messages :: Attachments', many=True, required=False)

    class Meta:

        fields = (
            'user_source_is_hidden',
            'user_destination_id',
            'user_destination_is_hidden',
            'user_status_id',
            'master_tell_id',
            'post_id',
            'type',
            'contents',
            'status',
            'attachments',
        )
        model = models.Message

    def insert(self):
        return models.Message.insert(get_user_id(self.context), self.validated_data)

    def validate(self, attrs):
        if 'user_status_id' in attrs:
            if not attrs['user_status_id']:
                del attrs['user_status_id']
        if 'master_tell_id' in attrs:
            if not attrs['master_tell_id']:
                del attrs['master_tell_id']
        if 'post_id' in attrs:
            if not attrs['post_id']:
                del attrs['post_id']
        return attrs


class MessagesPostResponse(Message):
    pass


class MessagesPatchRequest(Message):

    class Meta:

        fields = (
            'user_source_is_hidden',
            'user_destination_is_hidden',
            'status',
        )
        model = models.Message

    def update(self):
        return self.instance.update(self.validated_data)


class MessagesPatchResponse(Message):
    pass


class MessagesBulkRequest(Serializer):

    user_id = IntegerField()


class MessagesBulkResponse(Message):
    pass


class Notifications(Notification):
    pass


class NotificationsGetRequest(Serializer):

    since_id = IntegerField(required=False)
    max_id = IntegerField(required=False)
    limit = IntegerField(required=False)


class NotificationsGetResponse(Notifications):
    pass


class RadarGetRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    radius = FloatField()


class RadarGetResponseItems(User):

    class Meta:

        fields = (
            'id',
            'photo_original',
            'photo_preview',
            'first_name',
            'last_name',
            'gender',
            'location',
            'description',
            'photos',
            'status',
            'master_tells',
            'is_tellcard',
            'posts',
        )
        model = models.User


class RadarGetResponse(Serializer):

    hash = CharField()
    items = RadarGetResponseItems(many=True, required=False)
    position = IntegerField()


class RadarPostRequest(UserLocation):
    pass


class RadarPostResponse(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
        )
        model = models.Tellzone


class RegisterRequestUserPhoto(UserPhoto):

    class Meta:

        fields = (
            'string_original',
            'string_preview',
            'description',
            'position',
        )
        model = models.UserPhoto


class RegisterRequestUserSocialProfile(Serializer):

    access_token = CharField(allow_blank=True, required=False)
    netloc = ChoiceField(
        choices=(
            ('facebook.com', 'facebook.com',),
            ('google.com', 'google.com',),
            ('instagram.com', 'instagram.com',),
            ('linkedin.com', 'linkedin.com',),
            ('twitter.com', 'twitter.com',),
        ),
    )
    url = CharField(allow_blank=True, required=False)

    def validate(self, data):
        if data['netloc'] in ['facebook.com', 'linkedin.com']:
            if 'access_token' not in data or not data['access_token']:
                raise ValidationError(ugettext_lazy('Invalid `access_token` - #1'))
        return data


class RegisterRequestUserStatusAttachment(UserStatusAttachment):

    class Meta:

        fields = (
            'string_original',
            'string_preview',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterRequestUserStatus(UserStatus):

    attachments = RegisterRequestUserStatusAttachment(
        help_text='List of Users :: Status :: Attachments',
        many=True,
        required=False,
    )

    class Meta:

        fields = (
            'string',
            'title',
            'url',
            'notes',
            'attachments',
        )
        model = models.UserStatus


class RegisterRequestUserURL(UserURL):

    class Meta:

        fields = (
            'string',
            'position',
            'is_visible',
        )
        model = models.UserURL


class RegisterRequestSlaveTell(SlaveTell):

    class Meta:

        fields = (
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
        model = models.SlaveTell


class RegisterRequestMasterTell(MasterTell):

    slave_tells = RegisterRequestSlaveTell(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'contents',
            'position',
            'is_visible',
            'slave_tells',
        )
        model = models.MasterTell


class RecommendedTellsRequest(RecommendedTell):

    class Meta:

        fields = (
            'type',
        )
        model = models.RecommendedTell


class RecommendedTellsResponse(RecommendedTell):

    class Meta:

        fields = (
            'id',
            'contents',
            'photo',
        )
        model = models.RecommendedTell


class RegisterRequest(User):

    email = EmailField()
    photo_original = CharField(allow_blank=True, required=False)
    photo_preview = CharField(allow_blank=True, required=False)
    first_name = CharField(allow_blank=True, required=False)
    last_name = CharField(allow_blank=True, required=False)
    date_of_birth = DateField(required=False)
    gender = ChoiceField(
        allow_null=True,
        choices=(
            ('Female', 'Female',),
            ('Male', 'Male',),
        ),
        required=False,
    )
    location = CharField(allow_blank=True, required=False)
    description = CharField(allow_blank=True, required=False)
    phone = CharField(allow_blank=True, required=False)
    point = PointField(required=False)
    settings = UserSetting(help_text='Users :: Settings')
    photos = RegisterRequestUserPhoto(help_text='List of Users :: Photos', many=True, required=False)
    social_profiles = RegisterRequestUserSocialProfile(
        help_text='List of Users :: Social Profiles',
        many=True,
        required=False,
    )
    status = RegisterRequestUserStatus(help_text='Users :: Status', required=False)
    urls = RegisterRequestUserURL(help_text='List of Users :: URLs', many=True, required=False)
    master_tells = RegisterRequestMasterTell(help_text='List of Master Tells', many=True, required=False)

    class Meta:

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
            'settings',
            'photos',
            'social_profiles',
            'status',
            'urls',
            'master_tells',
        )
        model = models.User

    def is_valid_(self, data):
        if 'social_profiles' not in data:
            return False
        if not data['social_profiles']:
            return False
        for social_profile in data['social_profiles']:
            if social_profile['netloc'] == 'facebook.com':
                response = None
                try:
                    response = get_backend(
                        settings.AUTHENTICATION_BACKENDS, 'facebook',
                    )(
                        strategy=DjangoStrategy(storage=DjangoStorage())
                    ).user_data(
                        social_profile['access_token']
                    )
                except Exception:
                    print_exc()
                    report_exc_info()
                uid = response['id'] if response and 'id' in response else ''
                if not uid:
                    return False
                if not UserSocialAuth.objects.get_queryset().filter(provider='facebook', uid=uid).count():
                    return True
            if social_profile['netloc'] == 'linkedin.com':
                response = None
                try:
                    response = get_backend(
                        settings.AUTHENTICATION_BACKENDS, 'linkedin-oauth2',
                    )(
                        strategy=DjangoStrategy(storage=DjangoStorage())
                    ).user_data(
                        social_profile['access_token']
                    )
                except Exception:
                    print_exc()
                    report_exc_info()
                uid = response['id'] if response and 'id' in response else ''
                if not uid:
                    return False
                if not UserSocialAuth.objects.get_queryset().filter(provider='linkedin-oauth2', uid=uid).count():
                    return True
        return False


class RegisterResponse(User):

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'settings',
            'photos',
            'social_profiles',
            'status',
            'urls',
            'master_tells',
            'token',
        )
        model = models.User


class SharesUsersGet(ShareUser):

    class Meta:

        fields = (
            'user',
            'object',
            'timestamp',
        )
        model = models.ShareUser


class SharesUsersPostRequest(ShareUser):

    class Meta:

        fields = (
            'user_destination_id',
            'object_id',
        )
        model = models.ShareUser


class SharesUsersPostResponseEmail(Serializer):

    subject = CharField()
    body = CharField()


class SharesUsersPostResponse(Serializer):

    email = SharesUsersPostResponseEmail()
    sms = CharField()
    facebook_com = CharField()
    twitter_com = CharField()


class SlaveTellsRequest(SlaveTell):

    class Meta:

        fields = (
            'master_tell_id',
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
        model = models.SlaveTell


class SlaveTellsResponse(SlaveTell):
    pass


class SlaveTellsGetRequest(Serializer):

    inserted_at = DateTimeField(required=False)
    updated_at = DateTimeField(required=False)


class SlaveTellsGetResponse(SlaveTellsResponse):
    pass


class TellcardsRequest(Tellcard):

    class Meta:

        fields = (
            'user_destination_id',
            'tellzone_id',
            'location',
            'action',
        )
        model = models.Tellcard


class TellcardsResponse(Tellcard):

    class Meta:

        fields = (
            'id',
            'user',
            'tellzone',
            'location',
            'viewed_at',
            'saved_at',
        )
        model = models.Tellcard


class TellzonesRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    radius = FloatField()


class TellzonesResponse(Tellzone):
    pass


class TellzonesMasterTells(MasterTell):

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'contents',
            'position',
            'is_visible',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class UsersRequest(User):

    class Meta:

        fields = (
            'id',
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
            'photos',
            'settings',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User


class UsersResponse(User):

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'photos',
            'settings',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User


class UsersTellzonesGet(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
            'photo',
            'location',
            'phone',
            'url',
            'hours',
            'point',
            'inserted_at',
            'updated_at',
            'views',
            'favorites',
            'distance',
            'connections',
            'tellecasters',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone


class UsersTellzonesRequest(UserTellzone):

    class Meta:

        fields = (
            'tellzone_id',
            'action',
        )
        model = models.UserTellzone


class UsersTellzonesResponse(UserTellzone):

    class Meta:

        fields = (
            'id',
            'user_id',
            'tellzone_id',
            'viewed_at',
            'favorited_at',
        )
        model = models.UserTellzone


class PostsRequestAttachment(PostAttachment):

    class Meta:

        fields = (
            'type',
            'string_original',
            'string_preview',
            'position',
        )
        model = models.PostAttachment


class PostsRequest(Post):

    attachments = PostsRequestAttachment(many=True, required=False)
    tellzones = ListField(child=IntegerField(), required=False)

    class Meta:

        fields = (
            'category_id',
            'title',
            'contents',
            'attachments',
            'tellzones',
        )
        model = models.Post


class PostsResponse(Post):

    attachments = PostAttachment(many=True)

    class Meta:

        fields = (
            'id',
            'user',
            'category',
            'title',
            'contents',
            'inserted_at',
            'updated_at',
            'expired_at',
            'attachments',
            'tellzones',
        )
        model = models.Post


class PostsSearch(Post):

    attachments = PostAttachment(many=True)

    class Meta:

        fields = (
            'id',
            'user',
            'category',
            'title',
            'contents',
            'inserted_at',
            'updated_at',
            'expired_at',
            'attachments',
        )
        model = models.Post


class ProfilesRequest(Serializer):

    ids = ListField(child=IntegerField())


class ProfilesResponse(UsersProfile):
    pass
