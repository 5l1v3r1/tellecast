# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils.translation import ugettext_lazy
from drf_extra_fields.geo_fields import PointField
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
    SerializerMethodField,
    ValidationError,
)
from rest_framework.validators import UniqueValidator
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps, loads

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


class Offer(ModelSerializer):

    is_saved = SerializerMethodField()
    is_redeemed = SerializerMethodField()

    class Meta:

        fields = (
            'id',
            'name',
            'description',
            'photo',
            'code',
            'inserted_at',
            'updated_at',
            'expires_at',
            'is_saved',
            'is_redeemed',
        )
        model = models.Offer

    def get_is_saved(self, instance):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        if not models.UserOffer.objects.filter(user_id=user_id, offer_id=instance.id, saved_at__isnull=False).count():
            return False
        return True

    def get_is_redeemed(self, instance):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        if not models.UserOffer.objects.filter(
            user_id=user_id, offer_id=instance.id, redeemed_at__isnull=False,
        ).count():
            return False
        return True


class Tellzone(ModelSerializer):

    hours = SerializerMethodField()
    point = PointField()
    offers = Offer(many=True)
    distance = SerializerMethodField()
    tellecasters = SerializerMethodField()
    connections = SerializerMethodField()
    views = SerializerMethodField()
    favorites = SerializerMethodField()
    is_viewed = SerializerMethodField()
    is_favorited = SerializerMethodField()

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
            'offers',
            'distance',
            'tellecasters',
            'connections',
            'views',
            'favorites',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone

    def get_hours(self, instance):
        try:
            return loads(instance.hours)
        except Exception:
            pass
        return {}

    def get_distance(self, instance):
        return getattr(instance.distance, 'ft')

    def get_users(self, instance):
        users = []
        for user_location in models.UserLocation.objects.filter(
            ~Q(user_id=get_user_id(self.context)),
            point__distance_lte=(instance.point, D(ft=models.Tellzone.radius())),
            timestamp__gt=datetime.now() - timedelta(minutes=1),
        ).select_related(
            'user',
        ).order_by(
            '-timestamp',
        ).all():
            users.append(user_location.user)
        return users

    def get_tellecasters(self, instance):
        return [UsersProfile(user, context=self.context).data for user in self.get_users(instance)]

    def get_connections(self, instance):
        connections = []
        user_id = get_user_id(self.context)
        if not user_id:
            return connections
        user_ids = [user.id for user in self.get_users(instance)]
        for tellcard in models.Tellcard.objects.filter(
            Q(user_source_id=user_id, user_destination_id__in=user_ids) |
            Q(user_source_id__in=user_ids, user_destination_id=user_id),
            saved_at__isnull=False,
        ).select_related(
            'user_source',
            'user_destination',
        ).order_by(
            '-saved_at',
        ).all():
            if tellcard.user_source.id == user_id:
                connections.append(UsersProfile(tellcard.user_destination, context=self.context).data)
            if tellcard.user_destination.id == user_id:
                connections.append(UsersProfile(tellcard.user_source, context=self.context).data)
        return connections

    def get_views(self, instance):
        return models.UserTellzone.objects.filter(tellzone_id=instance.id, viewed_at__isnull=False).count()

    def get_favorites(self, instance):
        return models.UserTellzone.objects.filter(tellzone_id=instance.id, favorited_at__isnull=False).count()

    def get_is_viewed(self, instance):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        if not models.UserTellzone.objects.filter(
            user_id=user_id, tellzone_id=instance.id, viewed_at__isnull=False,
        ).count():
            return False
        return True

    def get_is_favorited(self, instance):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        if not models.UserTellzone.objects.filter(
            user_id=user_id, tellzone_id=instance.id, favorited_at__isnull=False,
        ).count():
            return False
        return True


class User(ModelSerializer):

    id = IntegerField(required=False)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(required=False)
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    phone_status = CharField(required=False)
    point = PointField(required=False)

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
        )
        model = models.User


class UserPhoto(ModelSerializer):

    id = IntegerField(required=False)
    user_id = IntegerField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSocialProfile(ModelSerializer):

    id = IntegerField(required=False)
    user_id = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatus(ModelSerializer):

    id = IntegerField(required=False)
    user_id = IntegerField(required=False)
    url = CharField(required=False)
    notes = CharField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'title',
            'url',
            'notes',
        )
        model = models.UserStatus


class UserStatusAttachment(ModelSerializer):

    id = IntegerField(required=False)
    user_status_id = IntegerField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_status_id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserURL(ModelSerializer):

    id = IntegerField(required=False)
    user_id = IntegerField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'user_id',
            'string',
            'position',
        )
        model = models.UserURL


class Notification(ModelSerializer):

    contents = SerializerMethodField()

    class Meta:

        fields = (
            'id',
            'type',
            'contents',
            'status',
            'timestamp',
        )
        model = models.Notification

    def get_contents(self, instance):
        return instance.contents


class DeviceAPNS(ModelSerializer):

    id = IntegerField(required=False)
    name = CharField()
    device_id = CharField()
    registration_id = CharField(validators=[UniqueValidator(queryset=models.DeviceAPNS.objects.all())])

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceAPNS


class DeviceGCM(ModelSerializer):

    id = IntegerField(required=False)
    name = CharField()
    device_id = CharField()
    registration_id = CharField(validators=[UniqueValidator(queryset=models.DeviceGCM.objects.all())])

    class Meta:

        fields = (
            'id',
            'name',
            'device_id',
            'registration_id',
        )
        model = models.DeviceGCM


class MasterTell(ModelSerializer):

    id = IntegerField(required=False)
    created_by_id = IntegerField(required=False)
    owned_by_id = IntegerField(required=False)
    is_visible = BooleanField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'is_visible',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class SlaveTell(ModelSerializer):

    id = IntegerField(required=False)
    master_tell_id = IntegerField(required=False)
    created_by_id = IntegerField(required=False)
    owned_by_id = IntegerField(required=False)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    is_editable = BooleanField(required=False)
    description = CharField(required=False)
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
            'is_editable',
            'contents',
            'description',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class MessageAttachment(ModelSerializer):

    id = IntegerField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.MessageAttachment


class Message(ModelSerializer):

    id = IntegerField(required=False)
    user_source = User()
    user_source_is_hidden = BooleanField(default=False, required=False)
    user_destination = User()
    user_destination_is_hidden = BooleanField(default=False, required=False)
    user_status = UserStatus(required=False)
    master_tell = MasterTell(required=False)
    type = CharField()
    contents = CharField()
    status = CharField()
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


class BlockUser(ModelSerializer):

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'photo',
            'location',
        )
        model = models.User


class Block(ModelSerializer):

    user = BlockUser(source='user_destination')

    class Meta:

        fields = (
            'id',
            'user',
            'timestamp',
        )
        model = models.Block


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


class Null(Serializer):
    pass


class RegisterRequestUserPhoto(ModelSerializer):

    position = IntegerField(required=False)

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
                raise ValidationError(ugettext_lazy('Invalid `access_token`'))
        return data


class RegisterRequestUserStatusAttachment(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterRequestUserStatus(ModelSerializer):

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


class RegisterRequestUserURL(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserURL


class RegisterRequestSlaveTell(ModelSerializer):

    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    is_editable = BooleanField(required=False)
    description = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'photo',
            'first_name',
            'last_name',
            'type',
            'is_editable',
            'contents',
            'description',
            'position',
        )
        model = models.SlaveTell


class RegisterRequestMasterTell(ModelSerializer):

    is_visible = BooleanField(required=False)
    position = IntegerField(required=False)
    slave_tells = RegisterRequestSlaveTell(help_text='List of Slave Tells', many=True)

    class Meta:

        fields = (
            'is_visible',
            'contents',
            'position',
            'slave_tells',
        )
        model = models.MasterTell


class RegisterRequest(Serializer):

    email = EmailField()
    email_status = ChoiceField(
        choices=(
            ('Private', 'Private',),
            ('Public', 'Public',),
        ),
    )
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
    phone_status = ChoiceField(
        choices=(
            ('Private', 'Private',),
            ('Public', 'Public',),
        ),
        required=False,
    )
    point = PointField(required=False)
    photos = RegisterRequestUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = RegisterRequestUserSocialProfile(
        help_text='List of User Social Profiles', many=True, required=False,
    )
    status = RegisterRequestUserStatus(help_text='User Status', required=False)
    urls = RegisterRequestUserURL(help_text='List of User URLs', many=True, required=False)
    master_tells = RegisterRequestMasterTell(help_text='List of Master Tells', many=True, required=False)

    def create(self, data):
        user = models.User.objects.create(
            email=data['email'],
            email_status=data['email_status'],
            photo=data['photo'] if 'photo' in data else None,
            first_name=data['first_name'] if 'first_name' in data else None,
            last_name=data['last_name'] if 'last_name' in data else None,
            date_of_birth=data['date_of_birth'] if 'date_of_birth' in data else None,
            gender=data['gender'] if 'gender' in data else None,
            location=data['location'] if 'location' in data else None,
            description=data['description'] if 'description' in data else None,
            phone=data['phone'] if 'phone' in data else None,
            point=data['point'] if 'point' in data else None,
        )
        if 'phone_status' in data:
            user.phone_status = data['phone_status']
            user.save()
        if 'status' in data:
            attachments = []
            if 'attachments' in data['status']:
                attachments = data['status']['attachments']
                del data['status']['attachments']
            user_status = models.UserStatus.objects.create(user=user, **data['status'])
            for attachment in attachments:
                models.UserStatusAttachment.objects.create(user_status=user_status, **attachment)
        if 'urls' in data:
            for url in data['urls']:
                models.UserURL.objects.create(user=user, **url)
        if 'photos' in data:
            for photo in data['photos']:
                models.UserPhoto.objects.create(user=user, **photo)
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                slave_tells = []
                if 'slave_tells' in master_tell:
                    slave_tells = master_tell['slave_tells']
                    del master_tell['slave_tells']
                master_tell = models.MasterTell.objects.create(created_by=user, owned_by=user, **master_tell)
                for slave_tell in slave_tells:
                    models.SlaveTell.objects.create(
                        master_tell=master_tell, created_by=user, owned_by=user, **slave_tell
                    )
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                models.UserSocialProfile.objects.create(
                    user=user, netloc=social_profile['netloc'], url=social_profile['url'],
                )
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
                        pass
                    if response and 'id' in response:
                        UserSocialAuth.objects.create(
                            user=user, provider='facebook', uid=response['id'], extra_data=dumps(response),
                        )
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
                        pass
                    if response and 'id' in response:
                        UserSocialAuth.objects.create(
                            user=user, provider='linkedin-oauth2', uid=response['id'], extra_data=dumps(response),
                        )
        return user

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
                    pass
                uid = response['id'] if response and 'id' in response else ''
                if not uid:
                    return False
                if not UserSocialAuth.objects.filter(provider='facebook', uid=uid).count():
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
                    pass
                uid = response['id'] if response and 'id' in response else ''
                if not uid:
                    return False
                if not UserSocialAuth.objects.filter(provider='linkedin-oauth2', uid=uid).count():
                    return True
        return False


class RegisterResponseUserPhoto(UserPhoto):
    pass


class RegisterResponseUserSocialProfile(UserSocialProfile):
    pass


class RegisterResponseUserStatusAttachment(UserStatusAttachment):
    pass


class RegisterResponseUserStatus(UserStatus):

    attachments = RegisterResponseUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
    )

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


class RegisterResponseUserURL(UserURL):
    pass


class RegisterResponseSlaveTell(SlaveTell):
    pass


class RegisterResponseMasterTell(MasterTell):

    is_visible = BooleanField(required=False)
    slave_tells = RegisterResponseSlaveTell(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'is_visible',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
            'slave_tells',
        )
        model = models.MasterTell


class RegisterResponse(User):

    photos = RegisterResponseUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = RegisterResponseUserSocialProfile(
        help_text='List of User Social Profiles', many=True, required=False,
    )
    status = RegisterResponseUserStatus(help_text='User Status', required=False)
    urls = RegisterResponseUserURL(help_text='List of User URLs', many=True, required=False)
    master_tells = RegisterResponseMasterTell(help_text='List of Master Tells', many=True, required=False)

    token = SerializerMethodField()

    class Meta:

        fields = (
            'id',
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

    def get_token(self, instance):
        return instance.get_token()


class AuthenticateRequest(Serializer):

    access_token = CharField(help_text='OAuth 2 access token')


class AuthenticateResponse(User):

    token = SerializerMethodField()

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'token',
        )
        model = models.User

    def get_token(self, instance):
        return instance.get_token()


class UsersRequestUserPhoto(UserPhoto):
    pass


class UsersRequestUserSocialProfile(UserSocialProfile):
    pass


class UsersRequestUserStatusAttachment(UserStatusAttachment):
    pass


class UsersRequestUserStatus(UserStatus):

    attachments = UsersRequestUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
    )

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


class UsersRequestUserURL(UserURL):
    pass


class UsersRequestSettings(Serializer):

    show_last_name = BooleanField()
    show_profile_photo = BooleanField()
    show_email = BooleanField()
    show_phone_number = BooleanField()
    notifications_invitations = BooleanField()
    notifications_shared_profiles = BooleanField()
    notifications_messages = BooleanField()
    notifications_offers = BooleanField()
    notifications_saved_you = BooleanField()


class UsersRequest(User):

    settings = UsersRequestSettings(required=False)
    photos = RegisterResponseUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = RegisterResponseUserSocialProfile(
        help_text='List of User Social Profiles', many=True, required=False,
    )
    status = RegisterResponseUserStatus(help_text='User Status', required=False)
    urls = RegisterResponseUserURL(help_text='List of User URLs', many=True, required=False)

    class Meta:

        fields = (
            'id',
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
            'settings',
            'photos',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User

    def update(self, instance, data):
        if 'email' in data:
            instance.email = data['email']
        if 'email_status' in data:
            instance.email_status = data['email_status']
        if 'photo' in data:
            instance.photo = data['photo']
        if 'first_name' in data:
            instance.first_name = data['first_name']
        if 'last_name' in data:
            instance.last_name = data['last_name']
        if 'date_of_birth' in data:
            instance.date_of_birth = data['date_of_birth']
        if 'gender' in data:
            instance.gender = data['gender']
        if 'location' in data:
            instance.location = data['location']
        if 'description' in data:
            instance.description = data['description']
        if 'phone' in data:
            instance.phone = data['phone']
        if 'phone_status' in data:
            instance.phone_status = data['phone_status']
        if 'point' in data:
            instance.point = data['point']
        instance.save()
        self.update_settings(instance, data)
        self.update_photos(instance, data)
        self.update_social_profiles(instance, data)
        self.update_status(instance, data)
        self.update_status_attachments(instance, data)
        self.update_urls(instance, data)
        return instance

    def update_settings(self, instance, data):
        if 'settings' in data:
            for key, value in data['settings'].items():
                value = 'True' if value else 'False'
                user_setting = instance.settings.get_queryset().filter(key=key).first()
                if not user_setting:
                    user_setting = models.UserSetting.objects.create(user_id=instance.id, key=key)
                user_setting.value = value
                user_setting.save()
        return instance

    def update_photos(self, instance, data):
        ids = []
        if 'photos' in data:
            for photo in data['photos']:
                user_photo = instance.photos.get_queryset().filter(
                    Q(id=photo['id'] if 'id' in photo else 0) | Q(string=photo['string'] if 'string' in photo else ''),
                ).first()
                if not user_photo:
                    user_photo = models.UserPhoto.objects.create(
                        user_id=instance.id,
                        string=photo['string'] if 'string' in photo else '',
                        position=photo['position'] if 'position' in photo else 0,
                    )
                else:
                    user_photo.user_id = instance.id
                    if 'string' in photo:
                        user_photo.string = photo['string']
                    if 'position' in photo:
                        user_photo.position = photo['position']
                    user_photo.save()
                ids.append(user_photo.id)
        instance.photos.get_queryset().exclude(id__in=ids).delete()
        return instance

    def update_social_profiles(self, instance, data):
        ids = []
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                user_social_profile = instance.social_profiles.get_queryset().filter(
                    Q(id=social_profile['id'] if 'id' in social_profile else 0) |
                    Q(netloc=social_profile['netloc'] if 'netloc' in social_profile else ''),
                ).first()
                if not user_social_profile:
                    user_social_profile = models.UserSocialProfile.objects.create(
                        user_id=instance.id,
                        netloc=social_profile['netloc'] if 'netloc' in social_profile else '',
                        url=social_profile['url'] if 'url' in social_profile else '',
                    )
                else:
                    user_social_profile.user_id = instance.id
                    if 'netloc' in social_profile:
                        user_social_profile.netloc = social_profile['netloc']
                    if 'url' in social_profile:
                        user_social_profile.url = social_profile['url']
                    user_social_profile.save()
                ids.append(user_social_profile.id)
        instance.social_profiles.get_queryset().exclude(id__in=ids).delete()
        return instance

    def update_status(self, instance, data):
        ids = []
        if 'status' in data:
            user_status = models.UserStatus.objects.filter(user_id=instance.id).first()
            if not user_status:
                user_status = models.UserStatus.objects.create(
                    user_id=instance.id,
                    string=data['status']['string'] if 'string' in data['status'] else None,
                    title=data['status']['title'] if 'title' in data['status'] else None,
                    url=data['status']['url'] if 'url' in data['status'] else None,
                    notes=data['status']['notes'] if 'notes' in data['status'] else None,
                )
            else:
                user_status.user_id = instance.id
                if 'string' in data['status']:
                    user_status.string = data['status']['string']
                if 'title' in data['status']:
                    user_status.title = data['status']['title']
                if 'url' in data['status']:
                    user_status.url = data['status']['url']
                if 'notes' in data['status']:
                    user_status.notes = data['status']['notes']
                user_status.save()
            ids.append(user_status.id)
        models.UserStatus.objects.exclude(id__in=ids).delete()
        return instance

    def update_status_attachments(self, instance, data):
        ids = []
        if 'status' in data:
            user_status = models.UserStatus.objects.filter(user_id=instance.id).first()
            if 'attachments' in data['status']:
                for attachment in data['status']['attachments']:
                    user_status_attachment = models.UserStatusAttachment.objects.filter(
                        Q(id=attachment['id'] if 'id' in attachment else 0) |
                        Q(string=attachment['string'] if 'string' in attachment else ''),
                        user_status_id=user_status.id,
                    ).first()
                    if not user_status_attachment:
                        user_status_attachment = models.UserStatusAttachment.objects.create(
                            user_status_id=user_status.id,
                            string=attachment['string'] if 'string' in attachment else '',
                            position=attachment['position'] if 'position' in attachment else 0,
                        )
                    else:
                        user_status_attachment.user_status_id = user_status.id
                        if 'string' in attachment:
                            user_status_attachment.string = attachment['string']
                        if 'position' in attachment:
                            user_status_attachment.position = attachment['position']
                        user_status_attachment.save()
                    ids.append(user_status_attachment.id)
        models.UserStatusAttachment.objects.exclude(id__in=ids).delete()
        return instance

    def update_urls(self, instance, data):
        ids = []
        if 'urls' in data:
            for url in data['urls']:
                user_url = instance.urls.get_queryset().filter(
                    Q(id=url['id'] if 'id' in url else 0) |
                    Q(string=url['string'] if 'string' in url else ''),
                ).first()
                if not user_url:
                    user_url = models.UserURL.objects.create(
                        user_id=instance.id,
                        string=url['string'] if 'string' in url else '',
                        position=url['position'] if 'position' in url else 0,
                    )
                else:
                    user_url.user_id = instance.id
                    if 'string' in url:
                        user_url.string = url['string']
                    if 'position' in url:
                        user_url.position = url['position']
                    user_url.save()
                ids.append(user_url.id)
        instance.urls.get_queryset().exclude(id__in=ids).delete()
        return instance


class UsersResponseUserPhoto(UserPhoto):
    pass


class UsersResponseUserSocialProfile(UserSocialProfile):
    pass


class UsersResponseUserStatusAttachment(UserStatusAttachment):
    pass


class UsersResponseUserStatus(UserStatus):

    attachments = UsersResponseUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
    )

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


class UsersResponseUserURL(UserURL):
    pass


class UsersResponseSettings(Serializer):

    show_last_name = BooleanField()
    show_profile_photo = BooleanField()
    show_email = BooleanField()
    show_phone_number = BooleanField()
    notifications_invitations = BooleanField()
    notifications_shared_profiles = BooleanField()
    notifications_messages = BooleanField()
    notifications_offers = BooleanField()
    notifications_saved_you = BooleanField()

    def to_representation(self, instance):
        return self.parent.instance.get_settings()


class UsersResponse(User):

    settings = UsersResponseSettings(required=False)
    photos = UsersResponseUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = UsersResponseUserSocialProfile(
        help_text='List of User Social Profiles', many=True, required=False,
    )
    status = UsersResponseUserStatus(help_text='User Status', required=False)
    urls = UsersResponseUserURL(help_text='List of User URLs', many=True, required=False)
    is_tellcard = SerializerMethodField()

    class Meta:

        fields = (
            'id',
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
            'inserted_at',
            'updated_at',
            'settings',
            'photos',
            'social_profiles',
            'status',
            'urls',
            'is_tellcard',
        )
        model = models.User

    def get_is_tellcard(self, instance):
        return get_is_tellcard(self.context, instance)


class UsersProfile(RegisterResponse):

    master_tells = SerializerMethodField()
    messages = SerializerMethodField()
    is_tellcard = SerializerMethodField()

    class Meta:

        fields = (
            'id',
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

    def get_master_tells(self, instance):
        return [
            RegisterResponseMasterTell(master_tell).data
            for master_tell in instance.master_tells.filter(is_visible=True).order_by('position').all()
        ]

    def get_messages(self, instance):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        if models.Message.objects.filter(
            Q(user_source_id=user_id, user_destination_id=instance.id) |
            Q(user_source_id=instance.id, user_destination_id=user_id),
            type='Message',
        ).count():
            return 6
        message = models.Message.objects.filter(
            Q(user_source_id=user_id, user_destination_id=instance.id) |
            Q(user_source_id=instance.id, user_destination_id=user_id),
        ).order_by(
            '-inserted_at',
        ).first()
        if not message:
            return 0
        if message.type == 'Request':
            if message.user_source_id == user_id:
                return 1
            if message.user_source_id == instance.id:
                return 2
        if message.type == 'Response - Deferred':
            return 3
        if message.type == 'Response - Rejected':
            return 4
        if message.type == 'Response - Blocked':
            return 5
        if message.type == 'Response - Accepted':
            return 6
        if message.type == 'Message':
            return 6
        return 0

    def get_is_tellcard(self, instance):
        return get_is_tellcard(self.context, instance)


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
            'offers',
            'tellecasters',
            'connections',
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

    def create_or_update(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return {}
        user_tellzone = models.UserTellzone.objects.filter(
            user_id=user_id, tellzone_id=self.validated_data['tellzone_id'],
        ).first()
        if not user_tellzone:
            user_tellzone = models.UserTellzone.objects.create(
                user_id=user_id, tellzone_id=self.validated_data['tellzone_id'],
            )
        if self.validated_data['action'] == 'View':
            user_tellzone.viewed_at = datetime.now()
        if self.validated_data['action'] == 'Favorite':
            user_tellzone.favorited_at = datetime.now()
        user_tellzone.save()
        return user_tellzone

    def delete(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return {}
        user_tellzone = models.UserTellzone.objects.filter(
            user_id=user_id, tellzone_id=self.validated_data['tellzone_id'],
        ).first()
        if not user_tellzone:
            return {}
        if self.validated_data['action'] == 'View':
            user_tellzone.viewed_at = None
        if self.validated_data['action'] == 'Favorite':
            user_tellzone.favorited_at = None
        user_tellzone.save()
        return {}


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


class UsersOffersGetTellzone(Tellzone):

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


class UsersOffersGet(Offer):

    tellzone = UsersOffersGetTellzone()

    class Meta:

        fields = (
            'id',
            'name',
            'description',
            'photo',
            'code',
            'inserted_at',
            'updated_at',
            'expires_at',
            'is_saved',
            'is_redeemed',
            'tellzone',
        )
        model = models.Offer


class UsersOffersRequest(ModelSerializer):

    offer_id = IntegerField()
    action = ChoiceField(
        choices=(
            ('Save', 'Save',),
            ('Redeem', 'Redeem',),
        ),
    )

    class Meta:

        fields = (
            'offer_id',
            'action',
        )
        model = models.UserOffer

    def create_or_update(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return {}
        user_offer = models.UserOffer.objects.filter(user_id=user_id, offer_id=self.validated_data['offer_id']).first()
        if not user_offer:
            user_offer = models.UserOffer.objects.create(user_id=user_id, offer_id=self.validated_data['offer_id'])
        if self.validated_data['action'] == 'Save':
            user_offer.saved_at = datetime.now()
        if self.validated_data['action'] == 'Redeem':
            user_offer.redeemed_at = datetime.now()
        user_offer.save()
        return user_offer

    def delete(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return {}
        user_offer = models.UserOffer.objects.filter(user_id=user_id, offer_id=self.validated_data['offer_id']).first()
        if not user_offer:
            return {}
        if self.validated_data['action'] == 'Save':
            user_offer.saved_at = None
        if self.validated_data['action'] == 'Redeem':
            user_offer.redeemed_at = None
        user_offer.save()
        return {}


class UsersOffersResponse(ModelSerializer):

    user_id = IntegerField()
    offer_id = IntegerField()

    class Meta:

        fields = (
            'id',
            'user_id',
            'offer_id',
            'saved_at',
            'redeemed_at',
        )
        model = models.UserOffer


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


class HomeResponseViews(Serializer):

    total = IntegerField()
    today = IntegerField()
    days = DictField(child=IntegerField())
    weeks = DictField(child=IntegerField())
    months = DictField(child=IntegerField())


class HomeResponseSaves(Serializer):

    total = IntegerField()
    today = IntegerField()
    days = DictField(child=IntegerField())
    weeks = DictField(child=IntegerField())
    months = DictField(child=IntegerField())


class HomeResponseUsers(Serializer):

    near = IntegerField()
    area = IntegerField()


class HomeResponseTellzones(Tellzone):
    pass


class HomeResponseOffersTellzone(Tellzone):

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


class HomeResponseOffers(Offer):

    tellzone = HomeResponseOffersTellzone()

    class Meta:

        fields = (
            'id',
            'name',
            'description',
            'photo',
            'code',
            'inserted_at',
            'updated_at',
            'expires_at',
            'is_saved',
            'is_redeemed',
            'tellzone',
        )
        model = models.Offer


class HomeResponseConnectionsTellzone(Tellzone):

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


class HomeResponseConnectionsUserPhotos(UserPhoto):
    pass


class HomeResponseConnectionsUserStatusAttachment(UserStatusAttachment):
    pass


class HomeResponseConnectionsUserStatus(UserStatus):

    attachments = RegisterResponseUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
    )

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


class HomeResponseConnectionsUser(ModelSerializer):

    photos = HomeResponseConnectionsUserPhotos(help_text='List of User Photos', many=True, required=False)
    status = HomeResponseConnectionsUserStatus(help_text='User Status', required=False)
    master_tells = SerializerMethodField()
    is_tellcard = SerializerMethodField()

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

    def get_master_tells(self, instance):
        return [
            RegisterResponseMasterTell(master_tell).data
            for master_tell in instance.master_tells.filter(
                owned_by_id=instance.id, is_visible=True
            ).order_by('position').all()[0:5]
        ]

    def get_is_tellcard(self, instance):
        return get_is_tellcard(self.context, instance)


class HomeResponseConnections(Serializer):

    user = HomeResponseConnectionsUser()
    point = PointField()
    tellzone = HomeResponseConnectionsTellzone(required=False)
    timestamp = DateTimeField()

    class Meta:

        fields = (
            'user',
            'point',
            'tellzone',
            'timestamp',
        )
        model = models.UserLocation


class HomeResponse(Serializer):

    views = HomeResponseViews()
    saves = HomeResponseSaves()
    users = HomeResponseUsers()
    tellzones = HomeResponseTellzones(many=True)
    offers = HomeResponseOffers(many=True)
    connections = HomeResponseConnections(many=True)


class RadarGetRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    radius = FloatField()
    widths_radar = IntegerField()
    widths_group = IntegerField()


class RadarGetResponseUsersItemsPhotos(UserPhoto):
    pass


class RadarGetResponseUsersItemsStatusAttachment(UserStatusAttachment):
    pass


class RadarGetResponseUsersItemsStatus(UserStatus):

    attachments = RegisterResponseUserStatusAttachment(
        help_text='List of User Status Attachments', many=True, required=False,
    )

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


class RadarGetResponseUsersItems(ModelSerializer):

    photos = RadarGetResponseUsersItemsPhotos(help_text='List of User Photos', many=True, required=False)
    status = RadarGetResponseUsersItemsStatus(help_text='User Status', required=False)
    master_tells = SerializerMethodField()
    is_tellcard = SerializerMethodField()

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

    def get_master_tells(self, instance):
        return [
            RegisterResponseMasterTell(master_tell).data
            for master_tell in instance.master_tells.filter(
                owned_by_id=instance.id, is_visible=True
            ).order_by('position').all()[0:5]
        ]

    def get_is_tellcard(self, instance):
        return get_is_tellcard(self.context, instance)


class RadarGetResponseUsers(Serializer):

    degrees = FloatField()
    radius = FloatField()
    items = RadarGetResponseUsersItems(many=True, required=False)


class RadarGetResponseOffersItemsTellzone(Tellzone):

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
            'tellecasters',
            'connections',
            'views',
            'favorites',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone


class RadarGetResponseOffersItems(Offer):

    tellzone = RadarGetResponseOffersItemsTellzone()

    class Meta:

        fields = (
            'id',
            'name',
            'description',
            'photo',
            'code',
            'inserted_at',
            'updated_at',
            'expires_at',
            'is_saved',
            'is_redeemed',
            'tellzone',
        )
        model = models.Offer


class RadarGetResponseOffers(Serializer):

    degrees = FloatField()
    radius = FloatField()
    items = RadarGetResponseOffersItems(many=True, required=False)


class RadarGetResponse(Serializer):

    users = RadarGetResponseUsers(many=True, required=False)
    offers = RadarGetResponseOffers(many=True, required=False)


class RadarPostRequest(ModelSerializer):

    point = PointField()
    accuracies_horizontal = FloatField(required=False)
    accuracies_vertical = FloatField(required=False)
    tellzone_id = IntegerField(allow_null=True, required=False)
    bearing = IntegerField()
    is_casting = BooleanField(required=False)

    class Meta:

        fields = (
            'point',
            'accuracies_horizontal',
            'accuracies_vertical',
            'tellzone_id',
            'bearing',
            'is_casting',
        )
        model = models.UserLocation


class RadarPostResponse(Tellzone):

    class Meta:

        fields = (
            'id',
            'name',
        )
        model = models.Tellzone


class MessagesPostRequest(Serializer):

    user_source_is_hidden = BooleanField(default=False, required=False)
    user_destination_id = IntegerField()
    user_destination_is_hidden = BooleanField(default=False, required=False)
    user_status_id = IntegerField(required=False)
    master_tell_id = IntegerField(required=False)
    type = ChoiceField(
        choices=(
            ('Message', 'Message',),
            ('Request', 'Request',),
            ('Response - Accepted', 'Response - Accepted',),
            ('Response - Blocked', 'Response - Blocked',),
            ('Response - Deferred', 'Response - Deferred',),
            ('Response - Rejected', 'Response - Rejected',),
        ),
    )
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

    def create(self, data):
        message = models.Message.objects.create(
            user_source=data['user_source'],
            user_source_is_hidden=data['user_source_is_hidden'] if 'user_source_is_hidden' in data else None,
            user_destination_id=data['user_destination_id'],
            user_destination_is_hidden=data['user_destination_is_hidden']
            if 'user_destination_is_hidden' in data else None,
            user_status_id=data['user_status_id'] if 'user_status_id' in data else None,
            master_tell_id=data['master_tell_id'] if 'master_tell_id' in data else None,
            type=data['type'],
            contents=data['contents'],
            status=data['status'],
        )
        if 'attachments' in data:
            for attachment in data['attachments']:
                models.MessageAttachment.objects.create(
                    message=message,
                    string=attachment['string'],
                    position=attachment['position'] if 'position' in attachment else None,
                )
        return message

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

    def update(self, instance, data):
        if 'user_source_is_hidden' in data:
            instance.user_source_is_hidden = data['user_source_is_hidden']
        if 'user_destination_is_hidden' in data:
            instance.user_destination_is_hidden = data['user_destination_is_hidden']
        if 'status' in data:
            instance.status = data['status']
        instance.save()
        return instance


class MessagesPatchResponse(Message):
    pass


class MessagesBulkRequest(Serializer):

    user_id = IntegerField()


class MessagesBulkResponse(Message):
    pass


class SharesUsersGet(ModelSerializer):

    user = SerializerMethodField()
    object = UsersProfile()

    class Meta:

        fields = (
            'user',
            'object',
            'timestamp',
        )
        model = models.ShareUser

    def get_user(self, instance):
        request = self.context.get('request', None)
        if request:
            if 'type' in request.QUERY_PARAMS:
                if request.QUERY_PARAMS['type'] == 'Source':
                    if instance.user_destination:
                        return UsersProfile(instance.user_destination, context=self.context).data
                    return {}
                if request.QUERY_PARAMS['type'] == 'Destination':
                    return UsersProfile(instance.user_source, context=self.context).data
        return UsersProfile(instance.user_destination).data


class SharesUsersPostRequest(ModelSerializer):

    user_destination_id = IntegerField(default=None, required=False)
    object_id = IntegerField()

    class Meta:

        fields = (
            'user_destination_id',
            'object_id',
        )
        model = models.ShareUser

    def create(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        instance = models.ShareUser.objects.filter(
            user_source_id=user_id,
            user_destination_id=self.validated_data['user_destination_id'],
            object_id=self.validated_data['object_id'],
        ).first()
        if not instance:
            instance = models.ShareUser.objects.create(
                user_source_id=user_id,
                user_destination_id=self.validated_data['user_destination_id'],
                object_id=self.validated_data['object_id'],
            )
        return instance


class SharesUsersPostResponseEmail(Serializer):

    subject = CharField()
    body = CharField()


class SharesUsersPostResponse(Serializer):

    email = SharesUsersPostResponseEmail()
    sms = CharField()
    facebook_com = CharField()
    twitter_com = CharField()


class SharesOffersGetOfferTellzone(Tellzone):

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
            'tellecasters',
            'connections',
            'views',
            'favorites',
            'is_viewed',
            'is_favorited',
        )
        model = models.Tellzone


class SharesOffersGetOffer(Offer):

    tellzone = SharesOffersGetOfferTellzone()

    class Meta:

        fields = (
            'id',
            'name',
            'description',
            'photo',
            'code',
            'inserted_at',
            'updated_at',
            'expires_at',
            'is_saved',
            'is_redeemed',
            'tellzone',
        )
        model = models.Offer


class SharesOffersGet(ModelSerializer):

    user = SerializerMethodField()
    object = SharesOffersGetOffer()

    class Meta:

        fields = (
            'user',
            'object',
            'timestamp',
        )
        model = models.ShareOffer

    def get_user(self, instance):
        request = self.context.get('request', None)
        if request:
            if 'type' in request.QUERY_PARAMS:
                if request.QUERY_PARAMS['type'] == 'Source':
                    if instance.user_destination:
                        return UsersProfile(instance.user_destination, context=self.context).data
                    return {}
                if request.QUERY_PARAMS['type'] == 'Destination':
                    return UsersProfile(instance.user_source, context=self.context).data
        return UsersProfile(instance.user_destination).data


class SharesOffersPostRequest(ModelSerializer):

    user_destination_id = IntegerField(default=None, required=False)
    object_id = IntegerField()

    class Meta:

        fields = (
            'user_destination_id',
            'object_id',
        )
        model = models.ShareOffer

    def create(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        instance = models.ShareOffer.objects.filter(
            user_source_id=user_id,
            user_destination_id=self.validated_data['user_destination_id'],
            object_id=self.validated_data['object_id'],
        ).first()
        if not instance:
            instance = models.ShareOffer.objects.create(
                user_source_id=user_id,
                user_destination_id=self.validated_data['user_destination_id'],
                object_id=self.validated_data['object_id'],
            )
        return instance


class SharesOffersPostResponseEmail(Serializer):

    subject = CharField()
    body = CharField()


class SharesOffersPostResponse(Serializer):

    email = SharesOffersPostResponseEmail()
    sms = CharField()
    facebook_com = CharField()
    twitter_com = CharField()


class TellcardsRequest(ModelSerializer):

    user_destination_id = IntegerField()
    action = ChoiceField(
        choices=(
            ('View', 'View',),
            ('Save', 'Save',),
        ),
    )

    class Meta:

        fields = (
            'user_destination_id',
            'action',
        )
        model = models.Tellcard

    def create(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        instance = models.Tellcard.objects.filter(
            user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
        ).first()
        if not instance:
            instance = models.Tellcard.objects.create(
                user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
            )
        if self.validated_data['action'] == 'View':
            instance.viewed_at = datetime.now()
        if self.validated_data['action'] == 'Save':
            instance.saved_at = datetime.now()
        instance.save()
        return instance

    def delete(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return {}
        instance = models.Tellcard.objects.filter(
            user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
        ).first()
        if not instance:
            return {}
        if self.validated_data['action'] == 'View':
            instance.viewed_at = None
        if self.validated_data['action'] == 'Save':
            instance.saved_at = None
        instance.save()
        return {}


class TellcardsResponse(ModelSerializer):

    user = SerializerMethodField()

    class Meta:

        fields = (
            'id',
            'user',
            'viewed_at',
            'saved_at',
        )
        model = models.Tellcard

    def get_user(self, instance):
        request = self.context.get('request', None)
        if request:
            if 'type' in request.QUERY_PARAMS:
                if request.QUERY_PARAMS['type'] == 'Source':
                    return UsersProfile(instance.user_destination, context=self.context).data
                if request.QUERY_PARAMS['type'] == 'Destination':
                    return UsersProfile(instance.user_source, context=self.context).data
        return UsersProfile(instance.user_destination).data


class BlocksRequest(ModelSerializer):

    user_destination_id = IntegerField()
    report = BooleanField(default=False, required=False)

    class Meta:

        fields = (
            'user_destination_id',
            'report',
        )
        model = models.Block

    def create(self):
        user_id = get_user_id(self.context)
        if not user_id:
            return False
        instance = models.Block.objects.filter(
            user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
        ).first()
        if not instance:
            instance = models.Block.objects.create(
                user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
            )
        instance.timestamp = datetime.now()
        instance.save()
        if self.validated_data['report']:
            models.Report.objects.create(
                user_source_id=user_id, user_destination_id=self.validated_data['user_destination_id'],
            )
        return instance


class BlocksResponse(Block):
    pass


class TellzonesRequest(Serializer):

    latitude = FloatField()
    longitude = FloatField()
    radius = FloatField()


class TellzonesResponse(Tellzone):
    pass


def get_is_tellcard(context, instance):
    user_id = get_user_id(context)
    if not user_id:
        return False
    if not models.Tellcard.objects.filter(
        user_source_id=user_id, user_destination_id=instance.id, saved_at__isnull=False,
    ).count():
        return False
    return True


def get_user_id(context):
    request = context.get('request', None)
    if request is None:
        return 0
    if not request.user.is_authenticated():
        return 0
    return request.user.id
