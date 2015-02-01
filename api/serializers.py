# -*- coding: utf-8 -*-

from django.conf import settings
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateField,
    EmailField,
    IntegerField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    URLField,
)
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps

from api import models


class UserStatusAttachment(ModelSerializer):
    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatus(ModelSerializer):
    id = IntegerField(read_only=True)
    url = URLField(required=False)
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


class User(ModelSerializer):
    id = IntegerField(read_only=True)
    photo = URLField(required=False)
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
            'inserted_at',
            'updated_at',
        )
        model = models.User


class SlaveTell(ModelSerializer):
    id = IntegerField(read_only=True)
    photo = URLField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'id',
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class MasterTell(ModelSerializer):
    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class TCardStatusAttachment(UserStatusAttachment):
    pass


class TCardStatus(UserStatus):
    id = IntegerField(read_only=True)
    url = URLField(required=False)
    notes = CharField(required=False)
    attachments = UserStatusAttachment(many=True, required=False)

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


class TCardURL(UserURL):
    pass


class TCardPhoto(UserPhoto):
    pass


class TCardMasterTell(MasterTell):
    id = IntegerField(read_only=True)
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class TCardSocialProfile(UserSocialProfile):
    pass


class TCard(User):
    status = TCardStatus(required=False)
    urls = TCardURL(many=True, required=False)
    photos = TCardPhoto(many=True, required=False)
    master_tells = TCardMasterTell(many=True, required=False)
    social_profiles = TCardSocialProfile(many=True, required=False)

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
            'inserted_at',
            'updated_at',
            'status',
            'urls',
            'photos',
            'master_tells',
            'social_profiles',
        )
        model = models.User


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
            'inserted_at',
            'updated_at',
            'token',
        )
        model = models.User

    def get_token(self, instance):
        return instance.get_token().key


class RegisterStatusAttachment(ModelSerializer):
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterStatus(ModelSerializer):
    url = URLField(required=False)
    notes = CharField(required=False)
    attachments = RegisterStatusAttachment(many=True, required=False)

    class Meta:
        fields = (
            'string',
            'title',
            'url',
            'notes',
            'attachments',
        )
        model = models.UserStatus


class RegisterURL(ModelSerializer):
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserURL


class RegisterPhoto(ModelSerializer):
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserPhoto


class RegisterSlaveTell(ModelSerializer):
    photo = URLField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    position = IntegerField(required=False)

    class Meta:
        fields = (
            'photo',
            'first_name',
            'last_name',
            'type',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.SlaveTell


class RegisterMasterTell(ModelSerializer):
    position = IntegerField(required=False)
    slave_tells = RegisterSlaveTell(many=True)

    class Meta:
        fields = (
            'contents',
            'position',
            'inserted_at',
            'updated_at',
            'slave_tells',
        )
        model = models.MasterTell


class RegisterSocialProfile(Serializer):
    access_token = CharField()
    netloc = ChoiceField(
        choices=(
            ('facebook.com', 'facebook.com', ),
            ('google.com', 'google.com', ),
            ('instagram.com', 'instagram.com', ),
            ('linkedin.com', 'linkedin.com', ),
            ('twitter.com', 'twitter.com', ),
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


class Register(Serializer):
    email = EmailField()
    email_status = ChoiceField(
        choices=(
            ('Private', 'Private', ),
            ('Public', 'Public', ),
        ),
    )
    photo = URLField(required=False)
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    date_of_birth = DateField(required=False)
    gender = ChoiceField(
        allow_null=True,
        choices=(
            ('Female', 'Female', ),
            ('Male', 'Male', ),
        ),
        required=False,
    )
    location = CharField(required=False)
    description = CharField(required=False)
    phone = CharField(required=False)
    status = RegisterStatus(help_text='Status instance', required=False)
    urls = RegisterURL(
        help_text='List of URL instances', many=True, required=False,
    )
    photos = RegisterPhoto(
        help_text='List of Photo instances', many=True, required=False,
    )
    master_tells = RegisterMasterTell(
        help_text='List of Master Tell instances', many=True, required=False,
    )
    social_profiles = RegisterSocialProfile(
        help_text='List of Social Profile instances',
        many=True,
        required=False,
    )

    def create(self, data):
        user = models.User.objects.create(
            email=data['email'],
            email_status=data['email_status'],
            photo=data['photo'] if 'photo' in data else None,
            first_name=data['first_name'] if 'first_name' in data else None,
            last_name=data['last_name'] if 'last_name' in data else None,
            date_of_birth=(
                data['date_of_birth'] if 'date_of_birth' in data else None
            ),
            gender=data['gender'] if 'gender' in data else None,
            location=data['location'] if 'location' in data else None,
            description=data['description'] if 'description' in data else None,
            phone=data['phone'] if 'phone' in data else None,
        )
        user.save()
        if 'status' in data:
            attachments = []
            if 'attachments' in data['status']:
                attachments = data['status']['attachments']
                del data['status']['attachments']
            user_status = models.UserStatus.objects.create(
                user=user, **data['status']
            )
            user_status.save()
            for attachment in attachments:
                models.UserStatusAttachment.objects.create(
                    user_status=user_status, **attachment
                ).save()
        if 'urls' in data:
            for url in data['urls']:
                models.UserURL.objects.create(user=user, **url).save()
        if 'photos' in data:
            for photo in data['photos']:
                models.UserPhoto.objects.create(user=user, **photo).save()
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                slave_tells = []
                if 'slave_tells' in master_tell:
                    slave_tells = master_tell['slave_tells']
                    del master_tell['slave_tells']
                master_tell = models.MasterTell.objects.create(
                    created_by=user, owned_by=user, **master_tell
                )
                master_tell.save()
                for slave_tell in slave_tells:
                    models.SlaveTell.objects.create(
                        master_tell=master_tell,
                        created_by=user,
                        owned_by=user,
                        **slave_tell
                    ).save()
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                models.UserSocialProfile.objects.create(
                    user=user,
                    netloc=social_profile['netloc'],
                    url=social_profile['url'],
                ).save()
                if social_profile['netloc'] == 'linkedin.com':
                    response = get_backend(
                        settings.AUTHENTICATION_BACKENDS, 'linkedin-oauth2',
                    )(
                        strategy=DjangoStrategy(storage=DjangoStorage())
                    ).user_data(
                        social_profile['access_token']
                    )
                    UserSocialAuth.objects.create(
                        user=user,
                        provider='linkedin-oauth2',
                        uid=response['id'],
                        extra_data=dumps(response),
                    ).save()
        return user
