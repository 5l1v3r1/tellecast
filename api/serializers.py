# -*- coding: utf-8 -*-

from collections import OrderedDict
from traceback import print_exc

from django.conf import settings
from django.utils.translation import ugettext_lazy
from drf_extra_fields.geo_fields import PointField
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
    ModelSerializer,
    Serializer,
    ValidationError,
)
from rollbar import report_exc_info
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy

from api import models


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


def get_user_id(context):
    request = context.get('request', None)
    if request is None:
        return 0
    if not request.user.is_authenticated():
        return 0
    return request.user.id


class Null(Serializer):
    pass


class Notification(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'type',
            'contents',
            'status',
            'timestamp',
        )
        model = models.Notification


class UserPhoto(ModelSerializer):

    user_id = IntegerField()
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSetting(Serializer):

    show_last_name = BooleanField()
    show_photo = BooleanField()
    show_email = BooleanField()
    show_phone = BooleanField()
    notifications_invitations = BooleanField()
    notifications_messages = BooleanField()
    notifications_saved_you = BooleanField()
    notifications_shared_profiles = BooleanField()


class UserSocialProfile(ModelSerializer):

    user_id = IntegerField()

    class Meta:

        fields = (
            'id',
            'user_id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatusAttachment(ModelSerializer):

    user_status_id = IntegerField()
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_status_id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatus(ModelSerializer):

    user_id = IntegerField()
    url = CharField(required=False)
    notes = CharField(required=False)
    attachments = UserStatusAttachment(help_text='List of Users :: Statuses :: Attachments', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'title',
            'url',
            'notes',
            'attachments',
        )
        model = models.UserStatus


class UserURL(ModelSerializer):

    user_id = IntegerField()
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'position',
        )
        model = models.UserURL


class SlaveTell(ModelSerializer):

    master_tell_id = IntegerField()
    created_by_id = IntegerField()
    owned_by_id = IntegerField()
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
            'contents',
            'description',
            'position',
            'is_editable',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell

    def insert(self):
        return models.SlaveTell.insert(get_user_id(self.context), self.validated_data)

    def update(self, instance):
        return instance.update(self.validated_data)


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

    def update(self, instance):
        return instance.update(self.validated_data)


class User(ModelSerializer):

    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(required=False)
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    point = PointField(required=False)
    photos = UserPhoto(help_text='List of Photos', many=True, required=False)
    settings = UserSetting(help_text='Settings', required=False)
    social_profiles = UserSocialProfile(help_text='List of Social Profiles', many=True, required=False)
    status = UserStatus(help_text='Status', required=False)
    urls = UserURL(help_text='List of URLs', many=True, required=False)
    master_tells = MasterTell(help_text='List of Master Tells', many=True, required=False)
    messages = BooleanField()
    is_tellcard = BooleanField()

    class Meta:

        fields = (
            'id',
            'email',
            'photo',
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
        )
        model = models.User

    def insert(self):
        return models.User.insert(self.validated_data)

    def update(self, instance):
        return instance.update(self.validated_data)

    def to_representation(self, instance):
        id = get_user_id(self.context)
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'email':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_email']:
                    dictionary[field.field_name] = instance.email
                continue
            if field.field_name == 'photo':
                dictionary[field.field_name] = None
                if id == instance.id or instance.settings_['show_photo']:
                    dictionary[field.field_name] = instance.photo
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


class UsersProfile(User):

    class Meta:

        fields = (
            'id',
            'email',
            'photo',
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
        )
        model = models.User


class MessageUser(User):

    class Meta:

        fields = (
            'id',
            'email',
            'photo',
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
            'user_id',
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
    user_source_is_hidden = BooleanField(default=False, required=False)
    user_destination_id = IntegerField()
    user_destination = MessageUser()
    user_destination_is_hidden = BooleanField(default=False, required=False)
    user_status_id = IntegerField(required=False)
    user_status = MessageUserStatus(required=False)
    master_tell_id = IntegerField(required=False)
    master_tell = MessageMasterTell(required=False)
    contents = CharField()
    status = ChoiceField(
        choices=(
            ('Read', 'Read',),
            ('Unread', 'Unread',),
        ),
        default='Unread',
        required=False,
    )
    attachments = MessageAttachment(help_text='List of Message Attachments', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'user_source',
            'user_source_is_hidden',
            'user_destination',
            'user_destination_is_hidden',
            'user_status',
            'master_tell',
            'type',
            'contents',
            'status',
            'inserted_at',
            'updated_at',
            'attachments',
        )
        model = models.Message


class Tellzone(ModelSerializer):

    hours = DictField(child=CharField())
    point = PointField()
    views = IntegerField()
    favorites = IntegerField()
    tellecasters = IntegerField()
    distance = FloatField()
    is_viewed = BooleanField()
    is_favorited = BooleanField()
    connections = UsersProfile(many=True, required=False)

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
            'distance',
            'connections',
            'tellecasters',
            'views',
            'favorites',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone

    def to_representation(self, instance):
        id = get_user_id(self.context)
        dictionary = OrderedDict()
        for field in [field for field in self.fields.values() if not field.write_only]:
            if field.field_name == 'distance':
                dictionary[field.field_name] = getattr(instance.distance, 'ft', 0.00)
                continue
            if field.field_name == 'connections':
                dictionary[field.field_name] = instance.get_connections(id)
                continue
            if field.field_name == 'tellecasters':
                dictionary[field.field_name] = instance.get_tellecasters(id)
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


class Ads(ModelSerializer):

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


class AuthenticateRequest(Serializer):

    access_token = CharField(help_text='OAuth 2 access token')


class AuthenticateResponse(User):

    class Meta:

        fields = (
            'id',
            'email',
            'photo',
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


class BlocksRequest(Serializer):

    user_destination_id = IntegerField()
    report = BooleanField(default=False, required=False)

    def insert_or_update(self):
        return models.Block.insert_or_update(
            get_user_id(self.context), self.validated_data['user_destination_id'], self.validated_data['report'],
        )

    def delete(self):
        return models.Block.delete(get_user_id(self.context), self.validated_data['user_destination_id'])


class BlocksResponseUser(User):

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'location',
        )
        model = models.User


class BlocksResponse(ModelSerializer):

    user = BlocksResponseUser(source='user_destination')

    class Meta:

        fields = (
            'id',
            'user',
            'timestamp',
        )
        model = models.Block


class DevicesAPNSRequest(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS

    def insert_or_update(self):
        return models.DeviceAPNS.insert_or_update(get_user_id(self.context), self.validated_data)


class DevicesAPNSResponse(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS


class DevicesGCMRequest(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM

    def insert_or_update(self):
        return models.DeviceGCM.insert_or_update(get_user_id(self.context), self.validated_data)


class DevicesGCMResponse(ModelSerializer):

    device_id = CharField()

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM


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


class HomeConnectionsResponseUser(User):

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'location',
            'description',
            'point',
            'photos',
            'status',
            'master_tells',
            'is_tellcard',
        )
        model = models.User


class HomeConnectionsResponseTellzone(Tellzone):

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


class HomeConnectionsResponse(Serializer):

    user = HomeConnectionsResponseUser()
    tellzone = HomeConnectionsResponseTellzone(required=False)
    point = PointField()
    timestamp = DateTimeField()


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


class MessagesGetResponse(Message):
    pass


class MessagesPostRequestAttachment(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.MessageAttachment


class MessagesPostRequest(Message):

    attachments = MessagesPostRequestAttachment(help_text='List of Message Attachments', many=True, required=False)

    class Meta:

        fields = (
            'user_source_is_hidden',
            'user_destination_id',
            'user_destination_is_hidden',
            'user_status_id',
            'master_tell_id',
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
        return attrs


class MessagesPostResponse(Message):
    pass


class MessagesPatchRequest(Serializer):

    user_source_is_hidden = BooleanField(default=False, required=False)
    user_destination_is_hidden = BooleanField(default=False, required=False)
    status = ChoiceField(
        choices=(
            ('Read', 'Read',),
            ('Unread', 'Unread',),
        ),
        required=False,
    )

    def update(self, instance):
        return instance.update(self.validated_data)


class MessagesPatchResponse(Message):
    pass


class MessagesBulkRequest(Serializer):

    user_id = IntegerField()


class MessagesBulkResponse(Message):
    pass


class Notifications(Notification):
    pass


class RadarGetRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    radius = FloatField()
    widths_radar = IntegerField()
    widths_group = IntegerField()


class RadarGetResponseUsersItems(User):

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'location',
            'description',
            'photos',
            'status',
            'master_tells',
            'is_tellcard',
        )
        model = models.User


class RadarGetResponseUsers(Serializer):

    degrees = FloatField()
    radius = FloatField()
    items = RadarGetResponseUsersItems(many=True, required=False)


class RadarGetResponse(Serializer):

    users = RadarGetResponseUsers(many=True, required=False)


class RadarPostRequest(ModelSerializer):

    tellzone_id = IntegerField(allow_null=True, required=False)
    point = PointField()
    accuracies_horizontal = FloatField(required=False)
    accuracies_vertical = FloatField(required=False)
    bearing = IntegerField()
    is_casting = BooleanField(required=False)

    class Meta:

        fields = (
            'tellzone_id',
            'point',
            'accuracies_horizontal',
            'accuracies_vertical',
            'bearing',
            'is_casting',
        )
        model = models.UserLocation

    def insert(self):
        return models.UserLocation.insert(get_user_id(self.context), self.validated_data)


class RadarPostResponse(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'name',
        )
        model = models.Tellzone


class RegisterRequestUserPhoto(UserPhoto):

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserPhoto


class RegisterRequestUserSocialProfile(Serializer):

    access_token = CharField(required=False)
    netloc = ChoiceField(
        choices=(
            ('facebook.com', 'facebook.com',),
            ('google.com', 'google.com',),
            ('instagram.com', 'instagram.com',),
            ('linkedin.com', 'linkedin.com',),
            ('twitter.com', 'twitter.com',),
        ),
    )
    url = CharField()

    def validate(self, data):
        if data['netloc'] in ['facebook.com', 'linkedin.com']:
            if 'access_token' not in data or not data['access_token']:
                raise ValidationError(ugettext_lazy('Invalid `access_token` - #1'))
        return data


class RegisterRequestUserStatusAttachment(UserStatusAttachment):

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterRequestUserStatus(UserStatus):

    url = CharField(required=False)
    notes = CharField(required=False)
    attachments = RegisterRequestUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
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
        )
        model = models.UserURL


class RegisterRequestSlaveTell(SlaveTell):

    class Meta:

        fields = (
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
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


class RegisterRequest(User):

    email = EmailField()
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = ChoiceField(
        allow_null=True,
        choices=(
            ('Female', 'Female',),
            ('Male', 'Male',),
        ),
        required=False,
    )
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    point = PointField(required=False)
    photos = RegisterRequestUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = RegisterRequestUserSocialProfile(
        help_text='List of User Social Profiles',
        many=True,
        required=False,
    )
    status = RegisterRequestUserStatus(help_text='User Status', required=False)
    urls = RegisterRequestUserURL(help_text='List of User URLs', many=True, required=False)
    master_tells = RegisterRequestMasterTell(help_text='List of Master Tells', many=True, required=False)

    class Meta:

        fields = (
            'email',
            'photo',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'location',
            'description',
            'phone',
            'point',
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
            'photo',
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
            'social_profiles',
            'status',
            'urls',
            'master_tells',
            'token',
        )
        model = models.User


class SharesUsersGet(ModelSerializer):

    user = UsersProfile()
    object = UsersProfile()

    class Meta:

        fields = (
            'user',
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


class SharesUsersPostRequest(ModelSerializer):

    user_destination_id = IntegerField(required=False)
    object_id = IntegerField()

    class Meta:

        fields = (
            'user_destination_id',
            'object_id',
        )
        model = models.ShareUser

    def insert(self):
        return models.ShareUser.insert(
            get_user_id(self.context), self.validated_data['user_destination_id'], self.validated_data['object_id'],
        )


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
            'contents',
            'description',
            'position',
            'is_editable',
        )
        model = models.SlaveTell


class SlaveTellsResponse(SlaveTell):
    pass


class TellcardsRequest(Serializer):

    user_destination_id = IntegerField()
    action = ChoiceField(
        choices=(
            ('View', 'View',),
            ('Save', 'Save',),
        ),
    )

    def insert_or_update(self):
        return models.Tellcard.insert_or_update(get_user_id(self.context), self.validated_data)

    def delete(self):
        return models.Tellcard.delete(get_user_id(self.context), self.validated_data)


class TellcardsResponse(ModelSerializer):

    user = UsersProfile()

    class Meta:

        fields = (
            'id',
            'user',
            'viewed_at',
            'saved_at',
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
            'connections',
            'tellecasters',
            'views',
            'favorites',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone


class UsersTellzonesRequest(ModelSerializer):

    tellzone_id = IntegerField()
    action = ChoiceField(
        choices=(
            ('View', 'View',),
            ('Favorite', 'Favorite',),
        ),
    )

    class Meta:

        fields = (
            'tellzone_id',
            'action',
        )
        model = models.UserTellzone

    def insert_or_update(self):
        return models.UserTellzone.insert_or_update(get_user_id(self.context), self.validated_data)

    def delete(self):
        return models.UserTellzone.delete(get_user_id(self.context), self.validated_data)


class UsersTellzonesResponse(ModelSerializer):

    user_id = IntegerField()
    tellzone_id = IntegerField()

    class Meta:

        fields = (
            'id',
            'user_id',
            'tellzone_id',
            'viewed_at',
            'favorited_at',
        )
        model = models.UserTellzone


class UsersRequest(User):

    class Meta:

        fields = (
            'id',
            'email',
            'photo',
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
            'photo',
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
