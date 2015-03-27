# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.serializers import (
    CharField, ChoiceField, DateField, EmailField, IntegerField, ModelSerializer, Serializer, SerializerMethodField,
)
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps

from api import models


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


class MasterTell(ModelSerializer):

    id = IntegerField(required=False)
    created_by_id = IntegerField(required=False)
    owned_by_id = IntegerField(required=False)
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

    id = IntegerField(required=False)
    master_tell_id = IntegerField(required=False)
    created_by_id = IntegerField(required=False)
    owned_by_id = IntegerField(required=False)
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


class RegisterRequestUserPhoto(ModelSerializer):

    position = IntegerField(required=False)

    class Meta:

        fields = (
            'string',
            'position',
        )
        model = models.UserPhoto


class RegisterRequestUserSocialProfile(Serializer):

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
        )
        model = models.SlaveTell


class RegisterRequestMasterTell(ModelSerializer):

    position = IntegerField(required=False)
    slave_tells = RegisterRequestSlaveTell(help_text='List of Slave Tells', many=True)

    class Meta:

        fields = (
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
    )
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

    slave_tells = RegisterResponseSlaveTell(help_text='List of Slave Tells', many=True, required=False)

    class Meta:

        fields = (
            'id',
            'created_by_id',
            'owned_by_id',
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


class UsersRequest(User):

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
            'photos',
            'social_profiles',
            'status',
            'urls',
        )
        model = models.User

    def update(self, instance, data):
        instance.email = data['email']
        instance.email_status = data['email_status']
        instance.photo = data['photo']
        instance.first_name = data['first_name']
        instance.last_name = data['last_name']
        instance.date_of_birth = data['date_of_birth']
        instance.gender = data['gender']
        instance.location = data['location']
        instance.description = data['description']
        instance.phone = data['phone']
        instance.phone_status = data['phone_status']
        instance.save()
        ids = []
        if 'photos' in data:
            for photo in data['photos']:
                i = instance.photos.get_queryset().filter(
                    Q(id=photo['id'] if 'id' in photo else 0) | Q(string=photo['string']),
                ).first()
                if i:
                    i.user_id = instance.id
                    i.string = photo['string']
                    if 'position' in photo and photo['position']:
                        i.position = photo['position']
                    i.save()
                else:
                    i = models.UserPhoto.objects.create(
                        user_id=instance.id,
                        string=photo['string'],
                        position=photo['position'] if 'position' in photo else 0,
                    )
                ids.append(i.id)
        instance.photos.get_queryset().exclude(id__in=ids).delete()
        ids = []
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                i = instance.social_profiles.get_queryset().filter(
                    Q(id=social_profile['id'] if 'id' in social_profile else 0) | Q(netloc=social_profile['netloc']),
                ).first()
                if i:
                    i.user_id = instance.id
                    i.netloc = social_profile['netloc']
                    i.url = social_profile['url']
                    i.save()
                else:
                    i = models.UserSocialProfile.objects.create(
                        user_id=instance.id, netloc=social_profile['netloc'], url=social_profile['url'],
                    )
                ids.append(i.id)
        instance.social_profiles.get_queryset().exclude(id__in=ids).delete()
        try:
            if instance.status:
                i = instance.status
                i.user_id = instance.id
                i.string = data['status']['string']
                i.title = data['status']['title']
                i.url = data['status']['url']
                i.notes = data['status']['notes']
                i.save()
        except ObjectDoesNotExist:
            i = models.UserStatus.objects.create(
                user_id=instance.id,
                string=data['status']['string'],
                title=data['status']['title'],
                url=data['status']['url'],
                notes=data['status']['string'],
            )
        ids = []
        if 'attachments' in data['status']:
            for attachment in data['status']['attachments']:
                i = instance.status.attachments.get_queryset().filter(
                    Q(id=attachment['id'] if 'id' in attachment else 0) | Q(string=attachment['string']),
                ).first()
                if i:
                    i.user_status_id = instance.status.id
                    i.string = attachment['string']
                    if 'position' in attachment and attachment['position']:
                        i.position = attachment['position']
                    i.save()
                else:
                    i = models.UserStatusAttachment.objects.create(
                        user_status_id=instance.status.id,
                        string=attachment['string'],
                        position=attachment['position'] if 'position' in attachment else 0,
                    )
                ids.append(i.id)
        instance.status.attachments.get_queryset().exclude(id__in=ids).delete()
        if 'urls' in data:
            for url in data['urls']:
                i = instance.urls.get_queryset().filter(
                    Q(id=url['id'] if 'id' in url else 0) | Q(string=url['string']),
                ).first()
                if i:
                    i.user_id = instance.id
                    i.string = url['string']
                    if 'position' in url and url['position']:
                        i.position = url['position']
                    i.save()
                else:
                    i = models.UserURL.objects.create(
                        user_id=instance.id,
                        string=url['string'],
                        position=url['position'] if 'position' in url else 0,
                    )
                ids.append(i.id)
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


class UsersResponse(User):

    photos = UsersResponseUserPhoto(help_text='List of User Photos', many=True, required=False)
    social_profiles = UsersResponseUserSocialProfile(
        help_text='List of User Social Profiles', many=True, required=False,
    )
    status = UsersResponseUserStatus(help_text='User Status', required=False)
    urls = UsersResponseUserURL(help_text='List of User URLs', many=True, required=False)

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
        )
        model = models.User

    def get_token(self, instance):
        return instance.get_token()


class UsersProfile(RegisterResponse):

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
        )
        model = models.User


class MessagesAttachment(ModelSerializer):

    id = IntegerField(required=False)
    position = IntegerField(required=False)

    class Meta:

        fields = (
            'id',
            'string',
            'position',
        )
        model = models.MessageAttachment


class Messages(ModelSerializer):

    id = IntegerField(required=False)
    user_source = User()
    user_destination = User()
    user_status = UserStatus(required=False)
    master_tell = MasterTell(required=False)
    type = CharField()
    contents = CharField()
    status = CharField()
    attachments = MessagesAttachment(help_text='List of Message Attachments', many=True, required=False)

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


class MessagesPostRequest(Serializer):

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
    attachments = MessagesAttachment(help_text='List of Message Attachments', many=True, required=False)

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


class MessagesPostResponse(Messages):
    pass


class MessagesPatchRequest(Serializer):

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


class MessagesPatchResponse(Messages):
    pass
