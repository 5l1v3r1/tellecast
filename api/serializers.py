# -*- coding: utf-8 -*-

from django.conf import settings
from rest_framework.serializers import (
    CharField, ChoiceField, DateField, EmailField, IntegerField, ModelSerializer, Serializer, SerializerMethodField,
)
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps

from api import models


class User(ModelSerializer):

    id = IntegerField(read_only=True)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(required=False)
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)

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
        )
        model = models.User


class UserPhoto(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSocialProfile(ModelSerializer):

    id = IntegerField(read_only=True)

    class Meta:

        fields = (
            'id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatusAttachment(ModelSerializer):

    id = IntegerField(read_only=True)
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

    id = IntegerField(read_only=True)
    url = CharField(required=False)
    notes = CharField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'title',
            'url',
            'notes',
        )
        model = models.UserStatus


class UserURL(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserURL


class MasterTell(ModelSerializer):

    id = IntegerField(read_only=True)
    created_by_id = IntegerField()
    owned_by_id = IntegerField()
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class SlaveTell(ModelSerializer):

    id = IntegerField(read_only=True)
    master_tell_id = IntegerField()
    created_by_id = IntegerField()
    owned_by_id = IntegerField()
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
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
            'contents',
            'description',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class MessageAttachment(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.MessageAttachment


class Message(ModelSerializer):

    id = IntegerField(read_only=True)
    user_source = User()
    user_destination = User()
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
            'user_destination',
            'user_status',
            'master_tell',
            'type',
            'contents',
            'status',
            'attachments',
        )
        model = models.Message


class SlaveTellFull(ModelSerializer):

    id = IntegerField(read_only=True)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    description = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
            'description',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class MasterTellFull(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)
    slave_tells = SlaveTellFull(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
            'slave_tells',
        )
        model = models.MasterTell


class UserPhotoFull(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSocialProfileFull(ModelSerializer):

    id = IntegerField(read_only=True)

    class Meta:

        fields = (
            'id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatusAttachmentFull(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatusFull(ModelSerializer):

    id = IntegerField(read_only=True)
    url = CharField(required=False)
    notes = CharField(required=False)
    attachments = UserStatusAttachmentFull(help_text='List of User Status Attachments', many=True, required=False)

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


class UserURLFull(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserURL


class UserFull(ModelSerializer):

    id = IntegerField(read_only=True)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(required=False)
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    master_tells = MasterTellFull(help_text='List of Master Tells', many=True, required=False)
    photos = UserPhotoFull(help_text='List of User Photos', many=True, required=False)
    social_profiles = UserSocialProfileFull(help_text='List of User Social Profiles', many=True, required=False)
    status = UserStatusFull(help_text='User Status', required=False)
    urls = UserURLFull(help_text='List of User URLs', many=True, required=False)

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
            'master_tells',
            'photos',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User


class SlaveTellSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    description = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
            'description',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class MasterTellSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)
    slave_tells = SlaveTellSimple(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
            'slave_tells',
        )
        model = models.MasterTell


class UserPhotoSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSocialProfileSimple(ModelSerializer):

    id = IntegerField(read_only=True)

    class Meta:

        fields = (
            'id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class UserStatusAttachmentSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatusSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    url = CharField(required=False)
    notes = CharField(required=False)
    attachments = UserStatusAttachmentSimple(help_text='List of User Status Attachments', many=True, required=False)

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


class UserURLSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserURL


class UserSimple(ModelSerializer):

    id = IntegerField(read_only=True)
    photo = CharField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = CharField(required=False)
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    master_tells = MasterTellSimple(help_text='List of Master Tells', many=True, required=False)
    photos = UserPhotoSimple(help_text='List of User Photos', many=True, required=False)
    social_profiles = UserSocialProfileSimple(help_text='List of User Social Profiles', many=True, required=False)
    status = UserStatusSimple(help_text='User Status', required=False)
    urls = UserURLSimple(help_text='List of User URLs', many=True, required=False)

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
            'master_tells',
            'photos',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User


class RegisterRequestPhoto(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserPhoto


class RegisterRequestSocialProfile(Serializer):

    access_token = CharField()
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

    class Meta:

        fields = (
            'access_token',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class RegisterRequestStatusAttachment(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterRequestStatus(ModelSerializer):

    url = CharField(required=False)
    notes = CharField(required=False)
    attachments = RegisterRequestStatusAttachment(
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


class RegisterRequestURL(ModelSerializer):

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
    description = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
            'description',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class RegisterRequestMasterTell(ModelSerializer):

    position = IntegerField(required=False)
    slave_tells = RegisterRequestSlaveTell(help_text='List of Slave Tells', many=True)

    class Meta:

        fields = (
            'contents',
            'position',
            'inserted_at',
            'updated_at',
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
    )
    photos = RegisterRequestPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = RegisterRequestSocialProfile(help_text='List of User Social Profiles', many=True, required=False)
    status = RegisterRequestStatus(help_text='User Status', required=False)
    urls = RegisterRequestURL(help_text='List of User URLs', many=True, required=False)
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
            phone_status=data['phone_status'],
        )
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


class RegisterResponse(UserFull):

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
            'inserted_at',
            'updated_at',
            'master_tells',
            'photos',
            'social_profiles',
            'status',
            'urls',
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
            'inserted_at',
            'updated_at',
            'token',
        )
        model = models.User

    def get_token(self, instance):
        return instance.get_token()


class MessagePostRequest(Serializer):

    user_destination_id = IntegerField()
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

    class Meta:

        fields = (
            'user_destination_id',
            'user_status_id',
            'master_tell_id',
            'type',
            'contents',
            'status',
            'inserted_at',
            'updated_at',
            'attachments',
        )

    def create(self, data):
        message = models.Message.objects.create(
            user_source=data['user_source'],
            user_destination_id=data['user_destination_id'],
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


class MessagePostResponse(Message):
    pass


class MessagePatchRequest(Serializer):

    status = ChoiceField(
        choices=(
            ('Read', 'Read',),
            ('Unread', 'Unread',),
        ),
    )

    class Meta:

        fields = (
            'status',
        )

    def update(self, instance, data):
        instance.status = data['status']
        instance.save()
        return instance


class MessagePatchResponse(Message):
    pass
