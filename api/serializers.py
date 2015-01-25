# -*- coding: utf-8 -*-

from django.conf import settings
from rest_framework.serializers import (
    CharField, EmailField, ModelSerializer, Serializer, SerializerMethodField,
)
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps

from api import models


class UserStatusAttachment(ModelSerializer):

    class Meta:
        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class UserStatus(ModelSerializer):

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

    class Meta:
        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserURL


class UserPhoto(ModelSerializer):

    class Meta:
        fields = (
            'id',
            'string',
            'position',
        )
        model = models.UserPhoto


class UserSocialProfile(ModelSerializer):

    class Meta:
        fields = (
            'id',
            'netloc',
            'url',
        )
        model = models.UserSocialProfile


class User(ModelSerializer):

    class Meta:
        fields = (
            'id',
            'email',
            'photo',
            'first_name',
            'last_name',
            'location',
            'description',
            'phone',
            'inserted_at',
            'updated_at',
        )
        model = models.User


class SlaveTell(ModelSerializer):

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
        read_only_fields = ('created_by', )


class MasterTell(ModelSerializer):

    class Meta:
        fields = (
            'id',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell
        read_only_fields = ('created_by', )


class TCardStatusAttachment(UserStatusAttachment):
    pass


class TCardStatus(UserStatus):
    attachments = UserStatusAttachment(many=True)

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
    created_by = User()
    owned_by = User()

    class Meta:
        fields = (
            'id',
            'created_by',
            'owned_by',
            'contents',
            'position',
            'inserted_at',
            'updated_at',
        )
        model = models.MasterTell


class TCardSocialProfile(UserSocialProfile):
    pass


class TCard(User):
    status = TCardStatus()
    urls = TCardURL(many=True)
    photos = TCardPhoto(many=True)
    master_tells = TCardMasterTell(many=True)
    social_profiles = TCardSocialProfile(many=True)

    class Meta:
        fields = (
            'id',
            'email',
            'photo',
            'first_name',
            'last_name',
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


class AuthenticateResponse(TCard):
    token = SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'email',
            'photo',
            'first_name',
            'last_name',
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
            'token',
        )
        model = models.User

    def get_token(self, instance):
        return instance.get_token().key


class RegisterStatusAttachment(ModelSerializer):

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserStatusAttachment


class RegisterStatus(ModelSerializer):
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

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserURL


class RegisterPhoto(ModelSerializer):

    class Meta:
        fields = (
            'string',
            'position',
        )
        model = models.UserPhoto


class RegisterSlaveTell(ModelSerializer):

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


class RegisterSocialProfileFacebook(Serializer):
    url = CharField()


class RegisterSocialProfileGoogle(Serializer):
    url = CharField()


class RegisterSocialProfileInstagram(Serializer):
    url = CharField()


class RegisterSocialProfileLinkedIn(Serializer):
    access_token = CharField(help_text='OAuth 2 access token')
    url = CharField()


class RegisterSocialProfileTwitter(Serializer):
    url = CharField()


class RegisterSocialProfile(Serializer):
    facebook = RegisterSocialProfileFacebook(required=False)
    google = RegisterSocialProfileGoogle(required=False)
    instagram = RegisterSocialProfileInstagram(required=False)
    linkedin = RegisterSocialProfileLinkedIn()
    twitter = RegisterSocialProfileTwitter(required=False)


class Register(Serializer):
    email = EmailField()
    photo = CharField()
    first_name = CharField()
    last_name = CharField()
    location = CharField()
    description = CharField()
    phone = CharField()
    status = RegisterStatus(help_text='Status instance')
    urls = RegisterURL(help_text='List of URL instances', many=True)
    photos = RegisterPhoto(help_text='List of Photo instances', many=True)
    master_tells = RegisterMasterTell(
        help_text='List of Master Tell instances', many=True,
    )
    social_profiles = RegisterSocialProfile(
        help_text='List of Social Profile instances',
    )

    def create(self, data):
        user = models.User.objects.create(
            email=data['email'],
            photo=data['photo'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            location=data['location'],
            description=data['description'],
            phone=data['phone'],
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
            for netloc in data['social_profiles']:
                models.UserSocialProfile.objects.create(
                    user=user,
                    netloc=netloc,
                    url=data['social_profiles'][netloc]['url'],
                ).save()
                if netloc == 'linkedin':
                    response = get_backend(
                        settings.AUTHENTICATION_BACKENDS, 'linkedin-oauth2',
                    )(
                        strategy=DjangoStrategy(storage=DjangoStorage())
                    ).user_data(
                        data['social_profiles'][netloc]['access_token']
                    )
                    UserSocialAuth.objects.create(
                        user=user,
                        provider='linkedin-oauth2',
                        uid=response['id'],
                        extra_data=dumps(response),
                    ).save()
        return user
