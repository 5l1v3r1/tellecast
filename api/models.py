# -*- coding: utf-8 -*-

from base64 import urlsafe_b64encode
from contextlib import closing
from datetime import datetime, timedelta

from bcrypt import gensalt, hashpw
from celery import current_app
from django.conf import settings
from django.contrib.auth.models import update_last_login, User as Administrator
from django.contrib.auth.signals import user_logged_in
from django.contrib.gis.db.models import GeoManager, PointField
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.db import connection, IntegrityError
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FloatField,
    ForeignKey,
    IntegerField,
    Max,
    Model,
    OneToOneField,
    Q,
    SET_NULL,
    TextField,
)
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy
from django_extensions.db.fields import UUIDField
from geopy.distance import vincenty
from jsonfield import JSONField
from numpy import array_split
from push_notifications.apns import apns_send_message
from push_notifications.fields import HexIntegerField
from push_notifications.gcm import _gcm_send_json
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps, loads


def __init__(
    self,
    verbose_name=None,
    name=None,
    auto=False,
    version=4,
    node=None,
    clock_seq=None,
    namespace=None,
    uuid_name=None,
    *args,
    **kwargs
):
    kwargs.setdefault('max_length', self.DEFAULT_MAX_LENGTH)
    if auto:
        self.empty_strings_allowed = False
        kwargs['blank'] = True
        kwargs.setdefault('editable', False)
    self.auto = auto
    self.version = version
    self.node = node
    self.clock_seq = clock_seq
    self.namespace = namespace
    self.uuid_name = uuid_name or name
    super(UUIDField, self).__init__(verbose_name=verbose_name, *args, **kwargs)

UUIDField.__init__ = __init__

user_logged_in.disconnect(update_last_login)


def __str__(self):
    return '{first_name:s} {last_name:s} ({email:s})'.format(
        email=self.email,
        first_name=self.first_name,
        last_name=self.last_name,
    )

Administrator.__str__ = __str__


def __unicode__(self):
    return u'{first_name:s} {last_name:s} ({email:s})'.format(
        email=self.email,
        first_name=self.first_name,
        last_name=self.last_name,
    )

Administrator.__unicode__ = __unicode__

Administrator._meta.get_field('is_active').verbose_name = ugettext_lazy('Active?')
Administrator._meta.get_field('is_staff').verbose_name = ugettext_lazy('Staff?')
Administrator._meta.get_field('is_superuser').verbose_name = ugettext_lazy('Superuser?')
Administrator._meta.get_field('last_login').verbose_name = ugettext_lazy('Last Signed In At')
Administrator._meta.ordering = (
    '-id',
)
Administrator._meta.verbose_name = ugettext_lazy('administrator')
Administrator._meta.verbose_name_plural = ugettext_lazy('administrators')


def __str__(self):
    return '{provider:s} - {uid:s}'.format(provider=self.provider, uid=self.uid)

UserSocialAuth.__str__ = __str__


def __unicode__(self):
    return u'{provider:s} - {uid:s}'.format(provider=self.provider, uid=self.uid)

UserSocialAuth.__unicode__ = __unicode__

UserSocialAuth._meta.get_field('extra_data').verbose_name = ugettext_lazy('Extra Data')
UserSocialAuth._meta.get_field('uid').verbose_name = ugettext_lazy('UID')
UserSocialAuth._meta.ordering = (
    '-id',
)
UserSocialAuth._meta.verbose_name = ugettext_lazy('user')
UserSocialAuth._meta.verbose_name_plural = ugettext_lazy('users')


def create_user(self, *args, **kwargs):
    return self.get_queryset().filter(email=kwargs['email']).first()

GeoManager.create_user = create_user


class Version(Model):

    platform = CharField(
        ugettext_lazy('Slot'),
        choices=(
            ('Android', 'Android',),
            ('iOS', 'iOS',),
        ),
        db_index=True,
        default='Android',
        max_length=255,
    )
    number = CharField(ugettext_lazy('Number'), db_index=True, max_length=255)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:
        db_table = 'api_versions'
        ordering = (
            '-id',
        )
        verbose_name = 'Version'
        verbose_name_plural = 'Version'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Ad(Model):

    slot = CharField(
        ugettext_lazy('Slot'),
        choices=(
            ('Example #1', 'Example #1',),
            ('Example #2', 'Example #2',),
            ('Example #3', 'Example #3',),
        ),
        db_index=True,
        default='Example #1',
        help_text=ugettext_lazy('(...to be finalized...)'),
        max_length=255,
    )
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('Photo', 'Photo',),
            ('Video', 'Video',),
        ),
        db_index=True,
        default='Photo',
        max_length=255,
    )
    source = CharField(
        ugettext_lazy('Source'),
        db_index=True,
        help_text=ugettext_lazy('...URL of the Photo/Video'),
        max_length=255,
    )
    target = CharField(
        ugettext_lazy('Target'),
        db_index=True,
        help_text=ugettext_lazy(
            '...only applicable if Type is Photo. Examples: http://..., https://..., tellecast://...',
        ),
        max_length=255,
    )
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:
        db_table = 'api_ads'
        ordering = (
            '-id',
        )
        verbose_name = 'Ad'
        verbose_name_plural = 'Ads'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Category(Model):

    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255, unique=True)
    photo = CharField(ugettext_lazy('Photo'), db_index=True, max_length=255)
    display_type = CharField(ugettext_lazy('Display Type'), blank=True, db_index=True, max_length=255, null=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_categories'
        ordering = (
            'position',
        )
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return str(self.name)

    def __unicode__(self):
        return unicode(self.name)


class RecommendedTell(Model):

    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('Hobby', 'Hobby',),
            ('Mind', 'Mind',),
            ('Passion', 'Passion',),
        ),
        db_index=True,
        default='Hobby',
        max_length=255,
    )
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    photo = CharField(ugettext_lazy('Photo'), db_index=True, max_length=255)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:
        db_table = 'api_recommended_tells'
        ordering = (
            '-id',
        )
        verbose_name = 'Recommended Tell'
        verbose_name_plural = 'Recommended Tells'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class User(Model):

    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('Root', 'Root',),
            ('Network', 'Network',),
            ('Regular', 'Regular',),
        ),
        default='Regular',
        db_index=True,
        max_length=255,
    )
    email = EmailField(ugettext_lazy('Email'), db_index=True, max_length=255, unique=True)
    password = CharField(ugettext_lazy('Password'), blank=True, db_index=True, max_length=255, null=True)
    photo_original = CharField(
        ugettext_lazy('Photo :: Original'),
        blank=True,
        db_index=True,
        max_length=255,
        null=True,
    )
    photo_preview = CharField(ugettext_lazy('Photo :: Preview'), blank=True, db_index=True, max_length=255, null=True)
    first_name = CharField(ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255, null=True)
    last_name = CharField(ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255, null=True)
    date_of_birth = DateField(ugettext_lazy('Date of Birth'), blank=True, db_index=True, null=True)
    gender = CharField(
        ugettext_lazy('Gender'),
        blank=True,
        choices=(
            ('Female', 'Female',),
            ('Male', 'Male',),
        ),
        db_index=True,
        max_length=255,
        null=True,
    )
    location = CharField(ugettext_lazy('Location'), blank=True, db_index=True, max_length=255, null=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    phone = CharField(ugettext_lazy('Phone'), blank=True, db_index=True, max_length=255, null=True)
    point = PointField(ugettext_lazy('Point'), blank=True, db_index=True, null=True)
    settings = JSONField(ugettext_lazy('Settings'), blank=True, null=True)
    social_profiles = JSONField(ugettext_lazy('Social Profiles'), blank=True, null=True)
    is_verified = BooleanField(ugettext_lazy('Is Verified?'), db_index=True, default=True)
    is_signed_in = BooleanField(ugettext_lazy('Is Signed In?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)
    access_code = CharField(ugettext_lazy('Access Code'), blank=True, db_index=True, max_length=255, null=True)
    source = CharField(ugettext_lazy('Source'), blank=True, db_index=True, max_length=255, null=True)

    tellzone = ForeignKey('Tellzone', blank=True, default=None, null=True, related_name='+')

    objects = GeoManager()

    class Meta:

        db_table = 'api_users'
        ordering = (
            '-id',
        )
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @cached_property
    def hash(self):
        return urlsafe_b64encode(
            str(self.id) +
            settings.SEPARATOR +
            hashpw((str(self.id) + settings.SECRET_KEY).encode('utf-8'), gensalt(10))
        )

    @cached_property
    def token(self):
        if not self.is_verified:
            return None
        return (
            str(self.id) +
            settings.SEPARATOR +
            hashpw((str(self.id) + settings.SECRET_KEY).encode('utf-8'), gensalt(10))
        )

    @classmethod
    def insert(cls, data):
        settings_ = {}
        if 'settings' in data:
            for key, value in data['settings'].items():
                settings_[key] = 'True' if value else 'False'
        social_profiles = []
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                if (
                    'netloc' in social_profile and
                    social_profile['netloc'] and
                    'url' in social_profile and
                    social_profile['url']
                ):
                    social_profiles.append({
                        'netloc': social_profile['netloc'],
                        'url': social_profile['url'] if 'url' in social_profile else '',
                    })
        user = User.objects.create(
            email=data['email'],
            photo_original=data['photo_original'] if 'photo_original' in data else None,
            photo_preview=data['photo_preview'] if 'photo_preview' in data else None,
            first_name=data['first_name'] if 'first_name' in data else None,
            last_name=data['last_name'] if 'last_name' in data else None,
            date_of_birth=data['date_of_birth'] if 'date_of_birth' in data else None,
            gender=data['gender'] if 'gender' in data else None,
            location=data['location'] if 'location' in data else None,
            description=data['description'] if 'description' in data else None,
            phone=data['phone'] if 'phone' in data else None,
            point=data['point'] if 'point' in data else None,
            is_verified=False,
            access_code=data['access_code'] if 'access_code' in data else None,
            source=data['source'] if 'source' in data else None,
            settings=settings_,
            social_profiles=social_profiles,
        )
        if 'password' in data:
            user.password = hashpw(data['password'].encode('utf-8'), gensalt(10))
            user.save()
        if 'photos' in data:
            for photo in data['photos']:
                UserPhoto.insert(user.id, photo)
            user.save()
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                if 'access_token' in social_profile:
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
                            response['access_token'] = social_profile['access_token']
                            UserSocialAuth.objects.create(
                                user_id=user.id,
                                provider='facebook',
                                uid=response['id'],
                                extra_data=dumps(response),
                            )
                            user.is_verified = True
                            user.save()
                    if social_profile['netloc'] == 'google.com':
                        response = None
                        try:
                            response = get_backend(
                                settings.AUTHENTICATION_BACKENDS, 'google-oauth2',
                            )(
                                strategy=DjangoStrategy(storage=DjangoStorage())
                            ).user_data(
                                social_profile['access_token']
                            )
                        except Exception:
                            pass
                        if response and 'id' in response:
                            response['access_token'] = social_profile['access_token']
                            UserSocialAuth.objects.create(
                                user_id=user.id,
                                provider='google-oauth2',
                                uid=response['id'],
                                extra_data=dumps(response),
                            )
                            user.is_verified = True
                            user.save()
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
                            response['access_token'] = social_profile['access_token']
                            UserSocialAuth.objects.create(
                                user_id=user.id,
                                provider='linkedin-oauth2',
                                uid=response['id'],
                                extra_data=dumps(response),
                            )
                            user.is_verified = True
                            user.save()
        if 'status' in data:
            UserStatus.insert(user.id, data['status'])
        if 'urls' in data:
            for url in data['urls']:
                UserURL.insert(user.id, url)
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                MasterTell.insert(user.id, master_tell)
        if not user.is_verified:
            current_app.send_task(
                'api.tasks.email_notifications',
                (user.id, 'verify',),
                queue='api.tasks.email_notifications',
                routing_key='api.tasks.email_notifications',
                serializer='json',
            )
        return user

    @property
    def settings_(self):
        dictionary = {}
        for key, value in self.settings.items():
            dictionary[key] = True if value == 'True' else False
        return dictionary

    def __str__(self):
        return '{first_name:s} {last_name:s} ({email:s})'.format(
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
        )

    def __unicode__(self):
        return u'{first_name:s} {last_name:s} ({email:s})'.format(
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
        )

    def sign_in(self):
        self.is_signed_in = True
        self.save()

    def sign_out(self):
        self.is_signed_in = False
        self.save()
        user_location_1 = UserLocation.objects.get_queryset().filter(
            user_id=self.id,
            is_casting=True,
            timestamp__gt=datetime.now() - timedelta(minutes=1),
        ).first()
        if not user_location_1:
            return
        user_ids = {
            'home': [],
            'networks': [],
            'tellzones': [],
        }
        for user_location_2 in UserLocation.objects.get_queryset().filter(
            ~Q(user_id=user_location_1.user_id), is_casting=True, timestamp__gt=datetime.now() - timedelta(minutes=1),
        ):
            if not is_blocked(user_location_1.user_id, user_location_2.user_id):
                if vincenty(
                    (user_location_1.point.x, user_location_1.point.y),
                    (user_location_2.point.x, user_location_2.point.y)
                ).ft <= 300.00:
                    user_ids['home'].append(user_location_2.user_id)
                if user_location_1.network_id and user_location_1.network_id == user_location_2.network_id:
                    user_ids['networks'].append(user_location_2.user_id)
                if user_location_1.tellzone_id and user_location_1.tellzone_id == user_location_2.tellzone_id:
                    user_ids['tellzones'].append(user_location_2.user_id)
        if user_ids['home']:
            current_app.send_task(
                'api.management.commands.websockets',
                (
                    {
                        'user_ids': user_ids['home'],
                        'subject': 'master_tells',
                        'body': {
                            'type': 'home',
                        },
                    },
                ),
                queue='api.management.commands.websockets',
                routing_key='api.management.commands.websockets',
                serializer='json',
            )
        if user_ids['networks']:
            current_app.send_task(
                'api.management.commands.websockets',
                (
                    {
                        'user_ids': user_ids['networks'],
                        'subject': 'master_tells',
                        'body': {
                            'type': 'networks',
                            'id': user_location_1.network_id,
                        },
                    },
                ),
                queue='api.management.commands.websockets',
                routing_key='api.management.commands.websockets',
                serializer='json',
            )
        if user_ids['tellzones']:
            current_app.send_task(
                'api.management.commands.websockets',
                (
                    {
                        'user_ids': user_ids['tellzones'],
                        'subject': 'master_tells',
                        'body': {
                            'type': 'tellzones',
                            'id': user_location_1.tellzone_id,
                        },
                    },
                ),
                queue='api.management.commands.websockets',
                routing_key='api.management.commands.websockets',
                serializer='json',
            )

    def update(self, data):
        if 'email' in data:
            self.email = data['email']
        if 'password' in data:
            self.password = hashpw(data['password'].encode('utf-8'), gensalt(10))
        self.photo_original = data['photo_original'] if 'photo_original' in data else None
        self.photo_preview = data['photo_preview'] if 'photo_preview' in data else None
        self.first_name = data['first_name'] if 'first_name' in data else None
        self.last_name = data['last_name'] if 'last_name' in data else None
        self.date_of_birth = data['date_of_birth'] if 'date_of_birth' in data else None
        self.gender = data['gender'] if 'gender' in data else None
        self.location = data['location'] if 'location' in data else None
        self.description = data['description'] if 'description' in data else None
        self.phone = data['phone'] if 'phone' in data else None
        self.point = data['point'] if 'point' in data else None
        self.save()
        self.update_photos(data)
        self.update_settings(data)
        self.update_social_profiles(data)
        self.update_status(data)
        self.update_status_attachments(data)
        self.update_urls(data)
        return self

    def update_photos(self, data):
        ids = []
        if 'photos' in data:
            for photo in data['photos']:
                user_photo = self.photos.get_queryset().filter(
                    Q(id=photo['id'] if 'id' in photo else 0) |
                    Q(string_original=photo['string_original'] if 'string_original' in photo else ''),
                ).first()
                if user_photo:
                    if 'string_original' in photo:
                        user_photo.string_original = photo['string_original']
                    if 'string_preview' in photo:
                        user_photo.string_preview = photo['string_preview']
                    if 'description' in photo:
                        user_photo.description = photo['description']
                    if 'position' in photo:
                        user_photo.position = photo['position']
                    user_photo.save()
                else:
                    user_photo = UserPhoto.insert(self.id, photo)
                ids.append(user_photo.id)
        self.photos.get_queryset().exclude(id__in=ids).delete()
        return self

    def update_settings(self, data):
        if 'settings' in data:
            for key, value in data['settings'].items():
                data['settings'][key] = 'True' if value else 'False'
            self.settings = data['settings']
            self.save()
        return self

    def update_social_profiles(self, data):
        if 'social_profiles' in data:
            social_profiles = []
            for social_profile in data['social_profiles']:
                if (
                    'netloc' in social_profile and
                    social_profile['netloc'] and
                    'url' in social_profile and
                    social_profile['url']
                ):
                    social_profiles.append({
                        'netloc': social_profile['netloc'],
                        'url': social_profile['url'] if 'url' in social_profile else '',
                    })
            self.social_profiles = social_profiles
            self.save()
        return self

    def update_status(self, data):
        ids = []
        if 'status' in data:
            user_status = UserStatus.objects.get_queryset().filter(user_id=self.id).first()
            if user_status:
                if 'string' in data['status']:
                    user_status.string = data['status']['string']
                if 'title' in data['status']:
                    user_status.title = data['status']['title']
                if 'url' in data['status']:
                    user_status.url = data['status']['url']
                if 'notes' in data['status']:
                    user_status.notes = data['status']['notes']
                user_status.save()
            else:
                user_status = UserStatus.objects.create(
                    user_id=self.id,
                    string=data['status']['string'] if 'string' in data['status'] else None,
                    title=data['status']['title'] if 'title' in data['status'] else None,
                    url=data['status']['url'] if 'url' in data['status'] else None,
                    notes=data['status']['notes'] if 'notes' in data['status'] else None,
                )
            ids.append(user_status.id)
        UserStatus.objects.get_queryset().filter(user_id=self.id).exclude(id__in=ids).delete()
        return self

    def update_status_attachments(self, data):
        ids = []
        if 'status' in data:
            user_status = UserStatus.objects.get_queryset().filter(user_id=self.id).first()
            if 'attachments' in data['status']:
                for attachment in data['status']['attachments']:
                    user_status_attachment = UserStatusAttachment.objects.get_queryset().filter(
                        Q(id=attachment['id'] if 'id' in attachment else 0) |
                        Q(string_original=attachment['string_original'] if 'string_original' in attachment else ''),
                        user_status_id=user_status.id,
                    ).first()
                    if user_status_attachment:
                        if 'string_original' in attachment:
                            user_status_attachment.string_original = attachment['string_original']
                        if 'string_preview' in attachment:
                            user_status_attachment.string_preview = attachment['string_preview']
                        if 'position' in attachment:
                            user_status_attachment.position = attachment['position']
                        user_status_attachment.save()
                    else:
                        user_status_attachment = UserStatusAttachment.objects.create(
                            user_status_id=user_status.id,
                            string_original=attachment['string_original'] if 'string_original' in attachment else None,
                            string_preview=attachment['string_preview'] if 'string_preview' in attachment else None,
                            position=attachment['position'] if 'position' in attachment else None,
                        )
                    ids.append(user_status_attachment.id)
        UserStatusAttachment.objects.get_queryset().filter(user_status__user_id=self.id).exclude(id__in=ids).delete()
        return self

    def update_urls(self, data):
        ids = []
        if 'urls' in data:
            for url in data['urls']:
                user_url = self.urls.get_queryset().filter(
                    Q(id=url['id'] if 'id' in url else 0) | Q(string=url['string'] if 'string' in url else ''),
                ).first()
                if user_url:
                    if 'string' in url:
                        user_url.string = url['string']
                    if 'position' in url:
                        user_url.position = url['position']
                    if 'is_visible' in url:
                        user_url.is_visible = url['is_visible']
                    user_url.save()
                else:
                    user_url = UserURL.insert(self.id, url)
                ids.append(user_url.id)
        self.urls.get_queryset().exclude(id__in=ids).delete()
        return self

    def get_messages(self, id):
        if not id:
            return 0
        if Message.objects.get_queryset().filter(
            Q(user_source_id=id, user_destination_id=self.id) | Q(user_source_id=self.id, user_destination_id=id),
            post_id__isnull=True,
            type__in=['Message', 'Ask'],
        ).count():
            return 2
        message = Message.objects.get_queryset().filter(
            Q(user_source_id=id, user_destination_id=self.id) | Q(user_source_id=self.id, user_destination_id=id),
            post_id__isnull=True,
        ).order_by(
            '-id',
        ).first()
        if not message:
            return 0
        if message.type == 'Request':
            if message.user_source_id == id:
                return 1
            if message.user_source_id == self.id:
                return 1
        if message.type == 'Response - Rejected':
            return 0
        if message.type == 'Response - Blocked':
            return 3
        if message.type == 'Response - Accepted':
            return 2
        if message.type == 'Message':
            return 2
        if message.type == 'Ask':
            return 2
        return 0

    def get_posts(self):
        return self.posts.get_queryset().count()

    def has_permission(self, instance=None):
        if isinstance(instance, User):
            return instance.id == self.id
        if isinstance(instance, UserLocation):
            return instance.user_id == self.id
        if isinstance(instance, UserPhoto):
            return instance.user_id == self.id
        if isinstance(instance, UserStatus):
            return instance.user_id == self.id
        if isinstance(instance, UserStatusAttachment):
            return self.has_permission(self, instance=instance.user_status)
        if isinstance(instance, UserTellzone):
            return instance.user_id == self.id
        if isinstance(instance, UserURL):
            return instance.user_id == self.id
        if isinstance(instance, Block):
            return instance.user_source_id == self.id
        if isinstance(instance, DeviceAPNS):
            return instance.user_id == self.id
        if isinstance(instance, DeviceGCM):
            return instance.user_id == self.id
        if isinstance(instance, MasterTell):
            return instance.owned_by_id == self.id
        if isinstance(instance, MasterTellTellzone):
            return self.has_permission(self, instance=instance.master_tell)
        if isinstance(instance, Message):
            return instance.user_source_id == self.id
        if isinstance(instance, Notification):
            return instance.user_id == self.id
        if isinstance(instance, Post):
            return instance.user_id == self.id
        if isinstance(instance, PostAttachment):
            return self.has_permission(self, instance=instance.post)
        if isinstance(instance, PostTellzone):
            return self.has_permission(self, instance=instance.post)
        if isinstance(instance, Report):
            return instance.user_source_id == self.id
        if isinstance(instance, ShareUser):
            return instance.user_source_id == self.id
        if isinstance(instance, SlaveTell):
            return instance.owned_by_id == self.id
        if isinstance(instance, Tellcard):
            return instance.user_source_id == self.id

    def is_authenticated(self):
        return True

    def is_tellcard(self, id):
        return Tellcard.objects.get_queryset().filter(
            user_source_id=id,
            user_destination_id=self.id,
            saved_at__isnull=False,
        ).count() > 0

    def is_valid(self, token):
        try:
            id, hash = token.split(settings.SEPARATOR, 1)
            return hashpw((id + settings.SECRET_KEY).encode('utf-8'), hash.encode('utf-8')) == hash
        except Exception:
            pass
        return False


class TellzoneType(Model):

    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255, unique=True)
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255, unique=True)
    icon = CharField(ugettext_lazy('Icon'), blank=True, db_index=True, max_length=255, null=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_tellzones_types'
        ordering = (
            'position',
        )
        verbose_name = 'Tellzone :: Type'
        verbose_name_plural = 'Tellzones :: Types'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)


class TellzoneStatus(Model):

    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255, unique=True)
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255, unique=True)
    icon = CharField(ugettext_lazy('Icon'), blank=True, db_index=True, max_length=255, null=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_tellzones_statuses'
        ordering = (
            'position',
        )
        verbose_name = 'Tellzone :: Status'
        verbose_name_plural = 'Tellzones :: Statuses'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)


class Tellzone(Model):

    user = ForeignKey(User, blank=True, on_delete=SET_NULL, null=True, related_name='+')
    type = ForeignKey(TellzoneType, null=True, related_name='tellzones')
    status = ForeignKey(TellzoneStatus, null=True, related_name='tellzones')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    photo = CharField(ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255, null=True)
    location = CharField(ugettext_lazy('Location'), blank=True, db_index=True, max_length=255, null=True)
    phone = CharField(ugettext_lazy('Phone'), blank=True, db_index=True, max_length=255, null=True)
    url = CharField(ugettext_lazy('URL'), blank=True, db_index=True, max_length=255, null=True)
    hours = JSONField(ugettext_lazy('Hours'), blank=True, null=True)
    point = PointField(ugettext_lazy('Point'), db_index=True)
    social_profiles = JSONField(ugettext_lazy('Social Profiles'), blank=True, null=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)
    started_at = DateTimeField(ugettext_lazy('Started At'), db_index=True, null=True)
    ended_at = DateTimeField(ugettext_lazy('Ended At'), db_index=True, null=True)
    are_pinned_tells_queued = BooleanField(ugettext_lazy('Queue Pinned Tells?'), db_index=True, default=False)

    objects = GeoManager()

    class Meta:

        db_table = 'api_tellzones'
        ordering = (
            '-id',
        )
        verbose_name = 'Tellzone'
        verbose_name_plural = 'Tellzones'

    @cached_property
    def favorites(self):
        return self.users.get_queryset().filter(favorited_at__isnull=False).count()

    @cached_property
    def pins(self):
        return self.users.get_queryset().filter(pinned_at__isnull=False).count()

    @cached_property
    def views(self):
        return self.users.get_queryset().filter(viewed_at__isnull=False).count()

    @cached_property
    def networks(self):
        return sorted(
            [network_tellzone.network for network_tellzone in self.networks_tellzones.get_queryset()],
            key=lambda network: (network.name, -network.id,),
        )

    @cached_property
    def tellecasters(self):
        count = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT COUNT(DISTINCT(user_id)) AS count
                FROM api_users_locations
                WHERE
                    ST_DWithin(ST_Transform(ST_GeomFromText(%s, 4326), 2163), ST_Transform(point, 2163), %s)
                    AND
                    timestamp > NOW() - INTERVAL '1 minute'
                ''',
                (
                    'POINT({longitude:.14f} {latitude:.14f})'.format(longitude=self.point.x, latitude=self.point.y),
                    Tellzone.radius() * 0.3048,
                )
            )
            count = cursor.fetchone()[0]
        return count

    @classmethod
    def insert(cls, user_id, data):
        social_profiles = []
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                if (
                    'netloc' in social_profile and
                    social_profile['netloc'] and
                    'url' in social_profile and
                    social_profile['url']
                ):
                    social_profiles.append({
                        'netloc': social_profile['netloc'],
                        'url': social_profile['url'] if 'url' in social_profile else '',
                    })
        tellzone = Tellzone.objects.create(
            user_id=user_id,
            type_id=data['type_id'] if 'type_id' in data else None,
            status_id=data['status_id'] if 'status_id' in data else None,
            name=data['name'] if 'name' in data else None,
            description=data['description'] if 'description' in data else None,
            photo=data['photo'] if 'photo' in data else None,
            location=data['location'] if 'location' in data else None,
            phone=data['phone'] if 'phone' in data else None,
            url=data['url'] if 'url' in data else None,
            hours=data['hours'] if 'hours' in data else None,
            point=data['point'] if 'point' in data else None,
            social_profiles=social_profiles,
            started_at=data['started_at'] if 'started_at' in data else None,
            ended_at=data['ended_at'] if 'ended_at' in data else None,
        )
        if 'networks' in data:
            for network in data['networks']:
                network = Network.objects.get_queryset().filter(id=network).first()
                if not network:
                    continue
                if not network.user:
                    continue
                if not network.user.id == tellzone.user_id:
                    continue
                NetworkTellzone.objects.create(network_id=network.id, tellzone_id=tellzone.id)
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                master_tell = MasterTell.objects.get_queryset().filter(id=master_tell).first()
                if not master_tell:
                    continue
                MasterTellTellzone.objects.create(master_tell_id=master_tell.id, tellzone_id=tellzone.id)
        if 'posts' in data:
            for post in data['posts']:
                post = Post.objects.get_queryset().filter(id=post).first()
                if not post:
                    continue
                PostTellzone.objects.create(post_id=post.id, tellzone_id=tellzone.id)
        return tellzone

    @classmethod
    def radius(cls):
        return 300.00

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    def update(self, data):
        if 'type_id' in data:
            self.type_id = data['type_id']
        if 'status_id' in data:
            self.status_id = data['status_id']
        if 'name' in data:
            self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        if 'photo' in data:
            self.photo = data['photo']
        if 'location' in data:
            self.location = data['location']
        if 'phone' in data:
            self.phone = data['phone']
        if 'url' in data:
            self.url = data['url']
        if 'hours' in data:
            self.hours = data['hours']
        if 'point' in data:
            self.point = data['point']
        if 'started_at' in data:
            self.started_at = data['started_at']
        if 'ended_at' in data:
            self.ended_at = data['ended_at']
        self.save()
        if 'social_profiles' in data:
            social_profiles = []
            for social_profile in data['social_profiles']:
                if (
                    'netloc' in social_profile and
                    social_profile['netloc'] and
                    'url' in social_profile and
                    social_profile['url']
                ):
                    social_profiles.append({
                        'netloc': social_profile['netloc'],
                        'url': social_profile['url'] if 'url' in social_profile else '',
                    })
            self.social_profiles = social_profiles
            self.save()
        if 'networks' in data:
            for network in data['networks']:
                network = Network.objects.get_queryset().filter(id=network).first()
                if not network:
                    continue
                if not network.user:
                    continue
                if not network.user.id == self.user_id:
                    continue
                if NetworkTellzone.objects.get_queryset().filter(network_id=network.id, tellzone_id=self.id).count():
                    continue
                NetworkTellzone.objects.create(network_id=network.id, tellzone_id=self.id)
            NetworkTellzone.objects.get_queryset().filter(
                ~Q(network_id__in=data['networks']), tellzone_id=self.id,
            ).delete()
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                master_tell = MasterTell.objects.get_queryset().filter(id=master_tell).first()
                if not master_tell:
                    continue
                if MasterTellTellzone.objects.get_queryset().filter(
                    master_tell_id=master_tell.id, tellzone_id=self.id,
                ).count():
                    continue
                MasterTellTellzone.objects.create(master_tell_id=master_tell.id, tellzone_id=self.id)
            MasterTellTellzone.objects.get_queryset().filter(
                ~Q(master_tell_id__in=data['master_tells']), tellzone_id=self.id,
            ).delete()
        if 'posts' in data:
            for post in data['posts']:
                post = Post.objects.get_queryset().filter(id=post).first()
                if not post:
                    continue
                if PostTellzone.objects.get_queryset().filter(post_id=post.id, tellzone_id=self.id).count():
                    continue
                PostTellzone.objects.create(post_id=post.id, tellzone_id=self.id)
            PostTellzone.objects.get_queryset().filter(~Q(post_id__in=data['posts']), tellzone_id=self.id).delete()
        return self

    def get_connections(self, user_id):
        connections = []
        user_ids = [
            user_location.user_id
            for user_location in UserLocation.objects.get_queryset().filter(
                ~Q(user_id=user_id),
                point__distance_lte=(self.point, D(ft=Tellzone.radius())),
                is_casting=True,
                timestamp__gt=datetime.now() - timedelta(minutes=1),
                user__is_signed_in=True,
            )
        ]
        for tellcard in Tellcard.objects.get_queryset().filter(
            Q(user_source_id=user_id, user_destination_id__in=user_ids) |
            Q(user_source_id__in=user_ids, user_destination_id=user_id),
            saved_at__isnull=False,
        ).select_related(
            'user_source',
            'user_destination',
        ):
            if tellcard.user_source_id == user_id:
                connections.append(tellcard.user_destination)
            if tellcard.user_destination_id == user_id:
                connections.append(tellcard.user_source)
        return connections

    def get_master_tells(self, user_id):
        ids = []
        for block in Block.objects.filter(
            Q(user_source_id=user_id) | Q(user_destination_id=user_id),
        ).order_by(
            '-timestamp',
        ).all():
            if block.user_source.id == user_id:
                if block.user_destination.id not in ids:
                    ids.append(block.user_destination.id)
            if block.user_destination.id == user_id:
                if block.user_source.id not in ids:
                    ids.append(block.user_source.id)
        return [
            master_tell_tellzone.master_tell
            for master_tell_tellzone in MasterTellTellzone.objects.get_queryset().filter(tellzone_id=self.id)
            if master_tell_tellzone.master_tell.owned_by_id not in ids
        ]

    def get_posts(self, user_id):
        return [
            post_tellzone.post
            for post_tellzone in PostTellzone.objects.get_queryset().filter(tellzone_id=self.id)
        ]

    def is_favorited(self, user_id):
        return self.users.get_queryset().filter(user_id=user_id, favorited_at__isnull=False).count() > 0

    def is_pinned(self, user_id):
        return self.users.get_queryset().filter(user_id=user_id, pinned_at__isnull=False).count() > 0

    def is_viewed(self, user_id):
        return self.users.get_queryset().filter(user_id=user_id, viewed_at__isnull=False).count() > 0


class Campaign(Model):

    tellzone = ForeignKey(Tellzone, related_name='campaigns')
    access_code = CharField(ugettext_lazy('Access Code'), db_index=True, max_length=255, unique=True)

    class Meta:
        db_table = 'api_campaigns'
        ordering = (
            'access_code',
        )
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'

    def __str__(self):
        return str(self.access_code)

    def __unicode__(self):
        return unicode(self.access_code)


class Network(Model):

    user = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='+')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)

    class Meta:

        db_table = 'api_networks'
        ordering = (
            '-id',
        )
        verbose_name = 'Network'
        verbose_name_plural = 'Networks'

    @classmethod
    def insert(cls, user_id, data):
        network = Network.objects.create(
            user_id=user_id,
            name=data['name'] if 'name' in data else None,
        )
        if 'tellzones' in data:
            for tellzone in data['tellzones']:
                tellzone = Tellzone.objects.get_queryset().filter(id=tellzone).first()
                if not tellzone:
                    continue
                if not tellzone.user:
                    continue
                if not tellzone.user.id == user_id:
                    continue
                if NetworkTellzone.objects.get_queryset().filter(
                    network_id=network.id, tellzone_id=tellzone.id,
                ).count():
                    continue
                NetworkTellzone.objects.create(network_id=network.id, tellzone_id=tellzone.id)
        return network

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    def update(self, data):
        if 'name' in data:
            self.name = data['name']
        self.save()
        if 'tellzones' in data:
            for tellzone in data['tellzones']:
                tellzone = Tellzone.objects.get_queryset().filter(id=tellzone).first()
                if not tellzone:
                    continue
                if not tellzone.user:
                    continue
                if not tellzone.user.id == self.user_id:
                    continue
                if NetworkTellzone.objects.get_queryset().filter(
                    network_id=self.id, tellzone_id=tellzone.id,
                ).count():
                    continue
                NetworkTellzone.objects.create(network_id=self.id, tellzone_id=tellzone.id)
            NetworkTellzone.objects.get_queryset().filter(
                ~Q(tellzone_id__in=data['tellzones']), network_id=self.id,
            ).delete()
        return self


class NetworkTellzone(Model):

    network = ForeignKey(Network, related_name='networks_tellzones')
    tellzone = ForeignKey(Tellzone, related_name='networks_tellzones')

    class Meta:

        db_table = 'api_networks_tellzones'
        ordering = (
            '-id',
        )
        verbose_name = 'Networks :: Tellzone'
        verbose_name_plural = 'Networks :: Tellzones'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserLocation(Model):

    user = ForeignKey(User, related_name='locations')
    network = ForeignKey(Network, blank=True, default=None, null=True, related_name='+')
    tellzone = ForeignKey(Tellzone, blank=True, default=None, null=True, related_name='+')
    location = CharField(ugettext_lazy('Location'), blank=True, default=None, db_index=True, max_length=255, null=True)
    point = PointField(ugettext_lazy('Point'), db_index=True)
    accuracies_horizontal = FloatField(ugettext_lazy('Accuracies :: Horizontal'), blank=True, db_index=True, null=True)
    accuracies_vertical = FloatField(ugettext_lazy('Accuracies :: Vertical'), blank=True, db_index=True, null=True)
    bearing = IntegerField(ugettext_lazy('Bearing'), db_index=True)
    is_casting = BooleanField(ugettext_lazy('Is Casting?'), db_index=True, default=True)
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, db_index=True)

    objects = GeoManager()

    class Meta:

        db_table = 'api_users_locations'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: Location'
        verbose_name_plural = 'Users :: Locations'

    @classmethod
    def insert(cls, user_id, data):
        return UserLocation.objects.create(
            user_id=user_id,
            network_id=data['network_id'] if 'network_id' in data else None,
            tellzone_id=data['tellzone_id'] if 'tellzone_id' in data else None,
            location=data['location'] if 'location' in data else None,
            point=data['point'] if 'point' in data else None,
            accuracies_horizontal=data['accuracies_horizontal'] if 'accuracies_horizontal' in data else None,
            accuracies_vertical=data['accuracies_vertical'] if 'accuracies_vertical' in data else None,
            bearing=data['bearing'] if 'bearing' in data else None,
            is_casting=data['is_casting'] if 'is_casting' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserPhoto(Model):

    user = ForeignKey(User, related_name='photos')
    string_original = CharField(
        ugettext_lazy('String :: Original'),
        blank=True,
        db_index=True,
        max_length=255,
        null=True,
    )
    string_preview = CharField(
        ugettext_lazy('String :: Preview'),
        blank=True,
        db_index=True,
        max_length=255,
        null=True,
    )
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_photos'
        ordering = (
            '-user_id',
            'position',
        )
        verbose_name = 'Users :: Photo'
        verbose_name_plural = 'Users :: Photos'

    @classmethod
    def insert(cls, user_id, data):
        return UserPhoto.objects.create(
            user_id=user_id,
            string_original=data['string_original'] if 'string_original' in data else None,
            string_preview=data['string_preview'] if 'string_preview' in data else None,
            description=data['description'] if 'description' in data else None,
            position=data['position'] if 'position' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserStatus(Model):

    user = OneToOneField(User, related_name='status')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255)
    url = CharField(ugettext_lazy('URL'), blank=True, db_index=True, max_length=255, null=True)
    notes = TextField(ugettext_lazy('Notes'), blank=True, db_index=True, null=True)

    class Meta:

        db_table = 'api_users_statuses'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: Status'
        verbose_name_plural = 'Users :: Statuses'

    @classmethod
    def insert(cls, user_id, data):
        user_status = UserStatus.objects.create(
            user_id=user_id,
            string=data['string'] if 'string' in data else None,
            title=data['title'] if 'title' in data else None,
            url=data['url'] if 'url' in data else None,
            notes=data['notes'] if 'notes' in data else None,
        )
        if 'attachments' in data:
            for attachment in data['attachments']:
                UserStatusAttachment.insert(user_status.id, attachment)
        return user_status

    def __str__(self):
        return self.string

    def __unicode__(self):
        return unicode(self.string)


class UserStatusAttachment(Model):

    user_status = ForeignKey(UserStatus, related_name='attachments')
    string_original = CharField(
        ugettext_lazy('String :: Original'),
        blank=True,
        db_index=True,
        max_length=255,
        null=True,
    )
    string_preview = CharField(
        ugettext_lazy('String :: Preview'),
        blank=True,
        db_index=True,
        max_length=255,
        null=True,
    )
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_statuses_attachments'
        ordering = (
            '-user_status_id',
            'position',
        )
        verbose_name = 'Users :: Statuses :: Attachment'
        verbose_name_plural = 'Users :: Statuses :: Attachments'

    @classmethod
    def insert(cls, user_status_id, data):
        return UserStatusAttachment.objects.create(
            user_status_id=user_status_id,
            string_original=data['string_original'] if 'string_original' in data else None,
            string_preview=data['string_preview'] if 'string_preview' in data else None,
            position=data['position'] if 'position' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserTellzone(Model):

    user = ForeignKey(User, related_name='tellzones')
    tellzone = ForeignKey(Tellzone, related_name='users')
    favorited_at = DateTimeField(ugettext_lazy('Favorited At'), blank=True, db_index=True, null=True)
    pinned_at = DateTimeField(ugettext_lazy('Pinned At'), blank=True, db_index=True, null=True)
    viewed_at = DateTimeField(ugettext_lazy('Viewed At'), blank=True, db_index=True, null=True)

    class Meta:

        db_table = 'api_users_tellzones'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: Tellzone'
        verbose_name_plural = 'Users :: Tellzones'

    @classmethod
    def insert_or_update(cls, user_id, data):
        user_tellzone = UserTellzone.objects.get_queryset().filter(
            user_id=user_id,
            tellzone_id=data['tellzone_id'],
        ).first()
        if not user_tellzone:
            user_tellzone = UserTellzone.objects.create(user_id=user_id, tellzone_id=data['tellzone_id'])
        now = datetime.now()
        if data['action'] == 'Favorite':
            user_tellzone.favorited_at = now
        if data['action'] == 'Pin':
            user_tellzone.pinned_at = now
        if data['action'] == 'View':
            user_tellzone.viewed_at = now
        user_tellzone.save()
        return user_tellzone

    @classmethod
    def remove(cls, user_id, data):
        user_tellzone = UserTellzone.objects.get_queryset().filter(
            user_id=user_id,
            tellzone_id=data['tellzone_id'],
        ).first()
        if not user_tellzone:
            return {}
        if data['action'] == 'Favorite':
            user_tellzone.favorited_at = None
        if data['action'] == 'Pin':
            user_tellzone.pinned_at = None
        if data['action'] == 'View':
            user_tellzone.viewed_at = None
        user_tellzone.save()
        return user_tellzone

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserURL(Model):

    user = ForeignKey(User, related_name='urls')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    is_visible = BooleanField(ugettext_lazy('Is Visible?'), db_index=True, default=True)

    class Meta:

        db_table = 'api_users_urls'
        ordering = (
            '-user_id',
            'position',
        )
        verbose_name = 'Users :: URL'
        verbose_name_plural = 'Users :: URLs'

    @classmethod
    def insert(cls, user_id, data):
        return UserURL.objects.create(
            user_id=user_id,
            string=data['string'] if 'string' in data else None,
            position=data['position'] if 'position' in data else None,
            is_visible=data['is_visible'] if 'is_visible' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Block(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'api_blocks'
        ordering = (
            '-id',
        )
        verbose_name = 'Block'
        verbose_name_plural = 'Blocks'

    @classmethod
    def insert_or_update(cls, user_source_id, user_destination_id, report):
        block = Block.objects.get_queryset().filter(
            user_source_id=user_source_id,
            user_destination_id=user_destination_id,
        ).first()
        if not block:
            block = Block.objects.create(user_source_id=user_source_id, user_destination_id=user_destination_id)
        if report:
            report = Report.objects.get_queryset().filter(
                user_source_id=user_source_id,
                user_destination_id=user_destination_id,
            ).first()
            if not report:
                report = Report.objects.create(user_source_id=user_source_id, user_destination_id=user_destination_id)
        return block

    @classmethod
    def remove(cls, user_source_id, user_destination_id):
        return Block.objects.get_queryset().filter(
            user_source_id=user_source_id,
            user_destination_id=user_destination_id,
        ).delete()

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class DeviceAPNS(Model):

    user = ForeignKey(User, related_name='+')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    device_id = UUIDField(ugettext_lazy('Device ID'), db_index=True, max_length=255, name=ugettext_lazy('Device ID'))
    registration_id = CharField(ugettext_lazy('Registration ID'), db_index=True, max_length=255)

    class Meta:
        db_table = 'api_devices_apns'
        ordering = (
            '-id',
        )
        verbose_name = 'Devices :: APNS'
        verbose_name_plural = 'Devices :: APNS'

    @classmethod
    def insert_or_update(cls, user_id, data):
        DeviceAPNS.objects.get_queryset().filter(~Q(user_id=user_id), registration_id=data['registration_id']).delete()
        device = DeviceAPNS.objects.get_queryset().filter(
            user_id=user_id, registration_id=data['registration_id'],
        ).first()
        if device:
            device.name = data['name']
            device.device_id = data['device_id']
            device.registration_id = data['registration_id']
            device.save()
        else:
            device = DeviceAPNS.objects.create(
                user_id=user_id,
                name=data['name'],
                device_id=data['device_id'],
                registration_id=data['registration_id'],
            )
        return device

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def send_message(self, extra):
        alert = None
        badge = None
        if 'aps' in extra:
            if 'alert' in extra['aps']:
                alert = extra['aps']['alert']
                del extra['aps']['alert']
            if 'badge' in extra['aps']:
                badge = extra['aps']['badge']
                del extra['aps']['badge']
            del extra['aps']
        try:
            apns_send_message(self.registration_id, alert, badge=badge, extra=extra, sound='default')
        except Exception:
            pass


class DeviceGCM(Model):

    user = ForeignKey(User, related_name='+')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    device_id = HexIntegerField(ugettext_lazy('Device ID'), db_index=True)
    registration_id = TextField(ugettext_lazy('Registration ID'), db_index=True, max_length=255)

    class Meta:
        db_table = 'api_devices_gcm'
        ordering = (
            '-id',
        )
        verbose_name = 'Devices :: GCM'
        verbose_name_plural = 'Devices :: GCM'

    @classmethod
    def insert_or_update(cls, user_id, data):
        DeviceGCM.objects.get_queryset().filter(~Q(user_id=user_id), device_id=data['device_id']).delete()
        device = DeviceGCM.objects.get_queryset().filter(user_id=user_id, device_id=data['device_id']).first()
        if device:
            device.name = data['name']
            device.device_id = data['device_id']
            device.registration_id = data['registration_id']
            device.save()
        else:
            device = DeviceGCM.objects.create(
                user_id=user_id,
                name=data['name'],
                device_id=data['device_id'],
                registration_id=data['registration_id'],
            )
        return device

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def send_message(self, data):
        try:
            _gcm_send_json([self.registration_id], data)
        except Exception:
            pass


class MasterTell(Model):

    created_by = ForeignKey(User, related_name='+')
    owned_by = ForeignKey(User, related_name='master_tells')
    category = ForeignKey(Category, null=True, related_name='master_tells')
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    is_visible = BooleanField(ugettext_lazy('Is Visible?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:

        db_table = 'api_master_tells'
        ordering = (
            '-owned_by_id',
            'position',
        )
        verbose_name = 'Master Tell'
        verbose_name_plural = 'Master Tells'

    @classmethod
    def insert(cls, user_id, data):
        master_tell = MasterTell.objects.create(
            created_by_id=user_id,
            owned_by_id=user_id,
            category_id=data['category_id'] if 'category_id' in data else None,
            contents=data['contents'] if 'contents' in data else None,
            description=data['description'] if 'description' in data else None,
            position=data['position'] if 'position' in data else None,
            is_visible=data['is_visible'] if 'is_visible' in data else None,
        )
        if 'slave_tells' in data:
            for slave_tell in data['slave_tells']:
                slave_tell['master_tell_id'] = master_tell.id
                SlaveTell.insert(user_id, slave_tell)
        if 'tellzones' in data:
            for tellzone in data['tellzones']:
                MasterTellTellzone.insert_or_update(master_tell.id, tellzone)
        return master_tell

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def update(self, data):
        if 'category_id' in data:
            self.category_id = data['category_id']
        if 'contents' in data:
            self.contents = data['contents']
        if 'description' in data:
            self.description = data['description']
        if 'position' in data:
            self.position = data['position']
        if 'is_visible' in data:
            self.is_visible = data['is_visible']
        self.save()
        if 'tellzones' in data:
            MasterTellTellzone.objects.get_queryset().filter(
                master_tell_id=self.id,
            ).exclude(
                tellzone_id__in=data['tellzones'],
            ).delete()
            for tellzone in data['tellzones']:
                MasterTellTellzone.insert_or_update(self.id, tellzone)
        return self


class MasterTellTellzone(Model):

    master_tell = ForeignKey(MasterTell, related_name='master_tells_tellzones')
    tellzone = ForeignKey(Tellzone, related_name='master_tells_tellzones')
    status = CharField(
        ugettext_lazy('Status'),
        choices=(
            ('Published', 'Published',),
            ('In Review', 'In Review',),
        ),
        default='Published',
        db_index=True,
        max_length=255,
    )

    class Meta:

        db_table = 'api_master_tells_tellzones'
        ordering = (
            '-id',
        )
        verbose_name = 'Master Tells :: Tellzone'
        verbose_name_plural = 'Master Tells :: Tellzones'

    @classmethod
    def insert_or_update(cls, master_tell_id, tellzone_id):
        master_tell_tellzone = MasterTellTellzone.objects.get_queryset().filter(
            master_tell_id=master_tell_id, tellzone_id=tellzone_id,
        ).first()
        if not master_tell_tellzone:
            master_tell_tellzone = MasterTellTellzone.objects.create(
                master_tell_id=master_tell_id, tellzone_id=tellzone_id,
            )
        return master_tell_tellzone

    @classmethod
    def remove(cls, master_tell_id, tellzone_id):
        return MasterTellTellzone.objects.get_queryset().filter(
            master_tell_id=master_tell_id, tellzone_id=tellzone_id,
        ).delete()

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Notification(Model):

    user = ForeignKey(User, related_name='notifications')
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('A', 'A',),
            ('B', 'B',),
            ('C', 'C',),
            ('D', 'D',),
            ('E', 'E',),
            ('F', 'F',),
            ('G', 'G',),
            ('H', 'H',),
        ),
        db_index=True,
        max_length=255,
    )
    contents = JSONField(ugettext_lazy('Contents'), blank=True, null=True)
    status = CharField(
        ugettext_lazy('Status'),
        choices=(
            ('Read', 'Read',),
            ('Unread', 'Unread',),
        ),
        db_index=True,
        default='Unread',
        max_length=255,
    )
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'api_notifications'
        ordering = (
            '-id',
        )
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Report(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'api_reports'
        ordering = (
            '-id',
        )
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class ShareUser(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, blank=True, related_name='+', null=True)
    object = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, db_index=True)

    class Meta:

        db_table = 'api_shares_users'
        ordering = (
            '-id',
        )
        verbose_name = 'Shares :: User'
        verbose_name_plural = 'Shares :: Users'

    @classmethod
    def insert(cls, user_source_id, user_destination_id, object_id):
        share_user = ShareUser.objects.get_queryset().filter(
            user_source_id=user_source_id,
            user_destination_id=user_destination_id,
            object_id=object_id,
        ).first()
        if not share_user:
            share_user = ShareUser.objects.create(
                user_source_id=user_source_id,
                user_destination_id=user_destination_id,
                object_id=object_id,
            )
        return share_user

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def get_dictionary(self):
        return {
            'email': {
                'subject': 'Tellecast - Shares/Users - {id:d}'.format(id=self.id),
                'body': 'Tellecast - Shares/Users - {id:d}'.format(id=self.id),
            },
            'sms': 'Tellecast - Shares/Users - {id:d}'.format(id=self.id),
            'facebook_com': 'tellecast://shares/users/{id:d}'.format(id=self.id),
            'twitter_com': 'tellecast://shares/users/{id:d}'.format(id=self.id),
        }


class SlaveTell(Model):

    master_tell = ForeignKey(MasterTell, related_name='slave_tells')
    created_by = ForeignKey(User, related_name='+')
    owned_by = ForeignKey(User, related_name='slave_tells')
    photo = CharField(ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255, null=True)
    first_name = CharField(ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255, null=True)
    last_name = CharField(ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255, null=True)
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('application/pdf', 'application/pdf',),
            ('audio/*', 'audio/*',),
            ('audio/aac', 'audio/aac',),
            ('audio/mp4', 'audio/mp4',),
            ('audio/mpeg', 'audio/mpeg',),
            ('audio/mpeg3', 'audio/mpeg3',),
            ('audio/x-mpeg3', 'audio/x-mpeg3',),
            ('image/*', 'image/*',),
            ('image/bmp', 'image/bmp',),
            ('image/gif', 'image/gif',),
            ('image/jpeg', 'image/jpeg',),
            ('image/png', 'image/png',),
            ('text/plain', 'text/plain',),
            ('video/*', 'video/*',),
            ('video/3gpp', 'video/3gpp',),
            ('video/mp4', 'video/mp4',),
            ('video/mpeg', 'video/mpeg',),
            ('video/x-mpeg', 'video/x-mpeg',),
        ),
        db_index=True,
        max_length=255,
    )
    contents_original = TextField(ugettext_lazy('Contents :: Original'), blank=True, db_index=True, null=True)
    contents_preview = TextField(ugettext_lazy('Contents :: Preview'), blank=True, db_index=True, null=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    is_editable = BooleanField(ugettext_lazy('Is Editable?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:

        db_table = 'api_slave_tells'
        ordering = (
            '-master_tell_id',
            'position',
        )
        verbose_name = 'Slave Tell'
        verbose_name_plural = 'Slave Tells'

    @classmethod
    def insert(cls, user_id, data):
        return SlaveTell.objects.create(
            master_tell_id=data['master_tell_id'] if 'master_tell_id' in data else None,
            created_by_id=user_id,
            owned_by_id=user_id,
            photo=data['photo'] if 'photo' in data else None,
            first_name=data['first_name'] if 'first_name' in data else None,
            last_name=data['last_name'] if 'last_name' in data else None,
            type=data['type'] if 'type' in data else None,
            contents_original=data['contents_original'] if 'contents_original' in data else None,
            contents_preview=data['contents_preview'] if 'contents_preview' in data else None,
            description=data['description'] if 'description' in data else None,
            position=data['position'] if 'position' in data else None,
            is_editable=data['is_editable'] if 'is_editable' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def update(self, data):
        if 'master_tell_id' in data:
            self.master_tell_id = data['master_tell_id']
        if 'photo' in data:
            self.photo = data['photo']
        if 'first_name' in data:
            self.first_name = data['first_name']
        if 'last_name' in data:
            self.last_name = data['last_name']
        if 'type' in data:
            self.type = data['type']
        if 'contents_original' in data:
            self.contents_original = data['contents_original']
        if 'contents_preview' in data:
            self.contents_preview = data['contents_preview']
        if 'description' in data:
            self.description = data['description']
        if 'position' in data:
            self.position = data['position']
        if 'is_editable' in data:
            self.is_editable = data['is_editable']
        self.save()
        return self


class Tellcard(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    network = ForeignKey(Network, blank=True, default=None, null=True, related_name='+')
    tellzone = ForeignKey(Tellzone, blank=True, default=None, null=True, related_name='+')
    location = CharField(ugettext_lazy('Location'), blank=True, default=None, db_index=True, max_length=255, null=True)
    viewed_at = DateTimeField(ugettext_lazy('Viewed At'), blank=True, db_index=True, null=True)
    saved_at = DateTimeField(ugettext_lazy('Saved At'), blank=True, db_index=True, null=True)

    class Meta:
        db_table = 'api_tellcards'
        ordering = (
            '-id',
        )
        verbose_name = 'Tellcard'
        verbose_name_plural = 'Tellcards'

    @classmethod
    def insert_or_update(cls, user_source_id, data):
        update_fields = []
        tellcard = Tellcard.objects.get_queryset().filter(
            user_source_id=user_source_id,
            user_destination_id=data['user_destination_id'],
        ).first()
        if not tellcard:
            try:
                tellcard = Tellcard.objects.create(
                    user_source_id=user_source_id,
                    user_destination_id=data['user_destination_id'],
                )
            except IntegrityError:
                return
        tellcard.tellzone_id = None
        tellcard.location = None
        if 'network_id' in data and data['network_id']:
            tellcard.network_id = data['network_id']
            update_fields.append('network_id')
        if 'tellzone_id' in data and data['tellzone_id']:
            tellcard.tellzone_id = data['tellzone_id']
            update_fields.append('tellzone_id')
        if 'location' in data and data['location']:
            tellcard.location = data['location']
            update_fields.append('location')
        now = datetime.now()
        if data['action'] == 'View':
            update_fields.append('viewed_at')
            tellcard.viewed_at = now
        if data['action'] == 'Save':
            update_fields.append('saved_at')
            tellcard.saved_at = now
        tellcard.save(update_fields=update_fields)
        return tellcard

    @classmethod
    def remove(cls, user_source_id, data):
        tellcard = Tellcard.objects.get_queryset().filter(
            user_source_id=user_source_id,
            user_destination_id=data['user_destination_id'],
        ).first()
        if not tellcard:
            return {}
        if data['action'] == 'View':
            tellcard.viewed_at = None
        if data['action'] == 'Save':
            tellcard.saved_at = None
        tellcard.save()
        return tellcard

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Post(Model):

    user = ForeignKey(User, related_name='posts')
    category = ForeignKey(Category, null=True, related_name='posts')
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255, null=True)
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)
    expired_at = DateTimeField(ugettext_lazy('Expired At'), db_index=True)

    class Meta:
        db_table = 'api_posts'
        ordering = (
            '-id',
        )
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    @cached_property
    def tellzones(self):
        return [
            post_tellzone.tellzone
            for post_tellzone in self.posts_tellzones.get_queryset().prefetch_related('tellzone__social_profiles')
        ]

    @classmethod
    def insert(cls, user_id, data):
        post = Post.objects.create(
            user_id=user_id,
            category_id=data['category_id'] if 'category_id' in data else None,
            title=data['title'] if 'title' in data else None,
            contents=data['contents'] if 'contents' in data else None,
        )
        if 'attachments' in data:
            for attachment in data['attachments']:
                PostAttachment.objects.create(
                    post_id=post.id,
                    type=attachment['type'] if 'type' in attachment else None,
                    string_original=attachment['string_original'] if 'string_original' in attachment else None,
                    string_preview=attachment['string_preview'] if 'string_preview' in attachment else None,
                    position=attachment['position'] if 'position' in attachment else None,
                )
        if 'tellzones' in data:
            for tellzone in data['tellzones']:
                PostTellzone.insert_or_update(post.id, tellzone)
        return post

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def update(self, data):
        if 'category_id' in data:
            self.category_id = data['category_id']
        if 'title' in data:
            self.title = data['title']
        if 'contents' in data:
            self.contents = data['contents']
        self.save()
        if 'attachments' in data:
            ids = []
            for attachment in data['attachments']:
                instance = self.attachments.get_queryset().filter(
                    Q(id=attachment['id'] if 'id' in attachment else 0),
                ).first()
                if instance:
                    if 'type' in attachment:
                        instance.type = attachment['type']
                    if 'string_original' in attachment:
                        instance.string_original = attachment['string_original']
                    if 'string_preview' in attachment:
                        instance.string_preview = attachment['string_preview']
                    if 'position' in attachment:
                        instance.position = attachment['position']
                    instance.save()
                else:
                    instance = PostAttachment.objects.create(
                        post_id=self.id,
                        type=attachment['type'] if 'type' in attachment else None,
                        string_original=attachment['string_original'] if 'string_original' in attachment else None,
                        string_preview=attachment['string_preview'] if 'string_preview' in attachment else None,
                        position=attachment['position'] if 'position' in attachment else None,
                    )
                ids.append(instance.id)
            self.attachments.get_queryset().exclude(id__in=ids).delete()
        if 'tellzones' in data:
            PostTellzone.objects.get_queryset().filter(
                post_id=self.id,
            ).exclude(
                tellzone_id__in=data['tellzones'],
            ).delete()
            for tellzone in data['tellzones']:
                PostTellzone.insert_or_update(self.id, tellzone)
        return self


class PostAttachment(Model):

    post = ForeignKey(Post, related_name='attachments')
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('application/pdf', 'application/pdf',),
            ('audio/*', 'audio/*',),
            ('audio/aac', 'audio/aac',),
            ('audio/mp4', 'audio/mp4',),
            ('audio/mpeg', 'audio/mpeg',),
            ('audio/mpeg3', 'audio/mpeg3',),
            ('audio/x-mpeg3', 'audio/x-mpeg3',),
            ('image/*', 'image/*',),
            ('image/bmp', 'image/bmp',),
            ('image/gif', 'image/gif',),
            ('image/jpeg', 'image/jpeg',),
            ('image/png', 'image/png',),
            ('text/plain', 'text/plain',),
            ('video/*', 'video/*',),
            ('video/3gpp', 'video/3gpp',),
            ('video/mp4', 'video/mp4',),
            ('video/mpeg', 'video/mpeg',),
            ('video/x-mpeg', 'video/x-mpeg',),
        ),
        db_index=True,
        max_length=255,
    )
    string_original = TextField(ugettext_lazy('String :: Original'), db_index=True)
    string_preview = TextField(ugettext_lazy('String :: Preview'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:
        db_table = 'api_posts_attachments'
        ordering = (
            '-post_id',
            'position',
        )
        verbose_name = 'Posts :: Attachment'
        verbose_name_plural = 'Posts :: Attachments'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class PostTellzone(Model):

    post = ForeignKey(Post, related_name='posts_tellzones')
    tellzone = ForeignKey(Tellzone, related_name='posts_tellzones')

    class Meta:

        db_table = 'api_posts_tellzones'
        ordering = (
            '-id',
        )
        verbose_name = 'Posts :: Tellzone'
        verbose_name_plural = 'Posts :: Tellzones'

    @classmethod
    def insert_or_update(cls, post_id, tellzone_id):
        post_tellzone = PostTellzone.objects.get_queryset().filter(post_id=post_id, tellzone_id=tellzone_id).first()
        if not post_tellzone:
            post_tellzone = PostTellzone.objects.create(post_id=post_id, tellzone_id=tellzone_id)
        return post_tellzone

    @classmethod
    def remove(cls, post_id, tellzone_id):
        return PostTellzone.objects.get_queryset().filter(post_id=post_id, tellzone_id=tellzone_id).delete()

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class Message(Model):

    user_source = ForeignKey(User, related_name='+')
    user_source_is_hidden = BooleanField(ugettext_lazy('Is Hidden?'), db_index=True, default=False)
    user_destination = ForeignKey(User, related_name='+')
    user_destination_is_hidden = BooleanField(ugettext_lazy('Is Hidden?'), db_index=True, default=False)
    user_status = ForeignKey(UserStatus, blank=True, null=True, related_name='+')
    master_tell = ForeignKey(MasterTell, blank=True, null=True, related_name='+')
    post = ForeignKey(Post, blank=True, null=True, related_name='+')
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('Ask', 'Ask',),
            ('Message', 'Message',),
            ('Request', 'Request',),
            ('Response - Accepted', 'Response - Accepted',),
            ('Response - Blocked', 'Response - Blocked',),
            ('Response - Rejected', 'Response - Rejected',),
        ),
        db_index=True,
        max_length=255,
    )
    contents = TextField(ugettext_lazy('Contents'), blank=True, db_index=True)
    attachments = JSONField(ugettext_lazy('Attachments'), blank=True, null=True)
    status = CharField(
        ugettext_lazy('Status'),
        choices=(
            ('Read', 'Read',),
            ('Unread', 'Unread',),
        ),
        db_index=True,
        default='Unread',
        max_length=255,
    )
    is_suppressed = BooleanField(ugettext_lazy('Is Suppressed?'), db_index=True, default=False)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:

        db_table = 'api_messages'
        ordering = (
            '-id',
        )
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    @classmethod
    def insert(cls, user_source_id, data):
        attachments = []
        if 'attachments' in data:
            for attachment in data['attachments']:
                attachments.append({
                    'position': attachment['position'] if 'position' in attachment else '',
                    'string': attachment['string'] if 'string' in attachment else '',
                })
        message = Message.objects.create(
            user_source_id=user_source_id,
            user_source_is_hidden=data['user_source_is_hidden'] if 'user_source_is_hidden' in data else None,
            user_destination_id=data['user_destination_id'],
            user_destination_is_hidden=data['user_destination_is_hidden']
            if 'user_destination_is_hidden' in data else None,
            user_status_id=data['user_status_id'] if 'user_status_id' in data else None,
            master_tell_id=data['master_tell_id'] if 'master_tell_id' in data else None,
            post_id=data['post_id'] if 'post_id' in data else None,
            type=data['type'] if 'type' in data else None,
            contents=data['contents'] if 'contents' in data else None,
            status=data['status'] if 'status' in data else 'Unread',
            attachments=attachments,
        )
        if message.type in ['Request']:
            Message.objects.create(
                user_source_id=message.user_destination_id,
                user_source_is_hidden=False,
                user_destination_id=message.user_source_id,
                user_destination_is_hidden=False,
                user_status_id=message.user_status_id,
                master_tell_id=message.master_tell_id,
                post_id=message.post_id,
                type='Response - Accepted',
                contents='',
                status='Unread',
            )
        return message

    def __str__(self):
        return str(self.type)

    def __unicode__(self):
        return unicode(self.type)

    def update(self, data):
        if 'user_source_is_hidden' in data:
            self.user_source_is_hidden = data['user_source_is_hidden']
        if 'user_destination_is_hidden' in data:
            self.user_destination_is_hidden = data['user_destination_is_hidden']
        if 'status' in data:
            self.status = data['status']
        self.save()
        return self


@receiver(pre_save, sender=Category)
def category_pre_save(instance, **kwargs):
    if not instance.position:
        position = Category.objects.get_queryset().aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=TellzoneType)
def tellzone_type_pre_save(instance, **kwargs):
    if not instance.position:
        position = TellzoneType.objects.get_queryset().aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=TellzoneStatus)
def tellzone_status_pre_save(instance, **kwargs):
    if not instance.position:
        position = TellzoneStatus.objects.get_queryset().aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_delete, sender=Tellzone)
def tellzone_post_delete(instance, **kwargs):
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'tellzones',
                'body': instance.id,
                'action': 'deleted',
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )


@receiver(pre_save, sender=User)
def user_pre_save(instance, **kwargs):
    if instance.tellzone:
        return
    if not instance.access_code:
        return
    campaign = Campaign.objects.get_queryset().filter(access_code=instance.access_code).first()
    if not campaign:
        return
    instance.tellzone = campaign.tellzone


@receiver(post_save, sender=User)
def user_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        settings = {}
        for key, value in {
            'notifications_invitations': True,
            'notifications_messages': True,
            'notifications_saved_you': True,
            'notifications_shared_profiles': True,
            'show_email': False,
            'show_last_name': False,
            'show_phone': True,
            'show_photo': False
        }.items():
            settings[key] = 'True' if value else 'False'
        instance.settings = settings
        instance.save()
    current_app.send_task(
        'api.tasks.thumbnails_1',
        ('User', instance.id,),
        queue='api.tasks.thumbnails',
        routing_key='api.tasks.thumbnails',
        serializer='json',
    )
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'profile',
                'body': instance.id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )


@receiver(post_save, sender=UserLocation)
def user_location_post_save(instance, **kwargs):
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'users_locations',
                'body': instance.id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )
    user_location_1 = instance
    user_location_2 = UserLocation.objects.get_queryset().filter(
        id__lt=user_location_1.id,
        user_id=user_location_1.user_id,
        timestamp__gt=user_location_1.timestamp - timedelta(minutes=1),
    ).first()
    user_ids = {
        'home': [],
        'networks': {},
        'tellzones': {},
    }
    for user_location in UserLocation.objects.get_queryset().filter(
        ~Q(user_id=user_location_1.user_id),
        is_casting=True,
        timestamp__gt=user_location_1.timestamp - timedelta(minutes=1),
    ):
        if is_blocked(user_location_1.user_id, user_location.user_id):
            continue
        if user_location_2:
            is_casting = (
                user_location_1.is_casting and not user_location_2.is_casting
            ) or (
                not user_location_1.is_casting and user_location_2.is_casting
            )
            if is_casting or (
                vincenty(
                    (user_location_1.point.x, user_location_1.point.y),
                    (user_location_2.point.x, user_location_2.point.y)
                ).ft > 300.00
            ):
                if vincenty(
                    (user_location.point.x, user_location.point.y),
                    (user_location_1.point.x, user_location_1.point.y)
                ).ft <= 300.00:
                    user_ids['home'].append(user_location.user_id)
            if is_casting or (user_location_1.network_id != user_location_2.network_id):
                if user_location.network_id and user_location.network_id == user_location_2.network_id:
                    if user_location.network_id not in user_ids['networks']:
                        user_ids['networks'][user_location.network_id] = []
                    user_ids['networks'][user_location.network_id].append(user_location.user_id)
            if is_casting or (user_location_1.tellzone_id != user_location_2.tellzone_id):
                if user_location.tellzone_id and user_location.tellzone_id == user_location_1.tellzone_id:
                    if user_location.tellzone_id not in user_ids['tellzones']:
                        user_ids['tellzones'][user_location.tellzone_id] = []
                    user_ids['tellzones'][user_location.tellzone_id].append(user_location.user_id)
        else:
            if not user_location_1.is_casting:
                continue
            if vincenty(
                (user_location.point.x, user_location.point.y), (user_location_1.point.x, user_location_1.point.y)
            ).ft <= 300.00:
                user_ids['home'].append(user_location.user_id)
            if user_location.network_id and user_location.network_id == user_location_1.network_id:
                if user_location.network_id not in user_ids['networks']:
                    user_ids['networks'][user_location.network_id] = []
                user_ids['networks'][user_location.network_id].append(user_location.user_id)
            if user_location.tellzone_id and user_location.tellzone_id == user_location_1.tellzone_id:
                if user_location.tellzone_id not in user_ids['tellzones']:
                    user_ids['tellzones'][user_location.tellzone_id] = []
                user_ids['tellzones'][user_location.tellzone_id].append(user_location.user_id)
    if user_ids['home']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['home'],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'home',
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )
    for network_id in user_ids['networks']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['networks'][network_id],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'networks',
                        'id': network_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )
    for tellzone_id in user_ids['tellzones']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['tellzones'][tellzone_id],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'tellzones',
                        'id': tellzone_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )


@receiver(pre_save, sender=UserPhoto)
def user_photo_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserPhoto.objects.get_queryset().filter(
            user=instance.user,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=UserPhoto)
def user_photo_post_save(instance, **kwargs):
    current_app.send_task(
        'api.tasks.thumbnails_1',
        ('UserPhoto', instance.id,),
        queue='api.tasks.thumbnails',
        routing_key='api.tasks.thumbnails',
        serializer='json',
    )


@receiver(pre_save, sender=UserStatusAttachment)
def user_status_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserStatusAttachment.objects.get_queryset().filter(
            user_status=instance.user_status,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=UserStatusAttachment)
def user_status_attachment_post_save(instance, **kwargs):
    current_app.send_task(
        'api.tasks.thumbnails_1',
        ('UserStatusAttachment', instance.id,),
        queue='api.tasks.thumbnails',
        routing_key='api.tasks.thumbnails',
        serializer='json',
    )


@receiver(post_save, sender=UserTellzone)
def user_tellzone_post_save(instance, **kwargs):
    if not instance.favorited_at:
        return
    user_ids = []
    user_ids.append(instance.user_id)
    for user_location in UserLocation.objects.get_queryset().filter(
        ~Q(user_id=instance.user_id),
        tellzone_id=instance.tellzone_id,
        is_casting=True,
        timestamp__gt=datetime.now() - timedelta(minutes=1),
    ):
        if not is_blocked(instance.user_id, user_location.user_id):
            user_ids.append(user_location.user_id)
    if user_ids:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids,
                    'subject': 'master_tells',
                    'body': {
                        'type': 'tellzones',
                        'id': instance.tellzone_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )


@receiver(pre_save, sender=UserURL)
def user_url_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserURL.objects.get_queryset().filter(
            user=instance.user,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=Block)
def block_post_save(instance, **kwargs):
    Tellcard.objects.get_queryset().filter(
        Q(user_source_id=instance.user_source_id, user_destination_id=instance.user_destination_id) |
        Q(user_source_id=instance.user_destination_id, user_destination_id=instance.user_source_id),
    ).delete()
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'blocks',
                'body': instance.id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )
    current_app.send_task(
        'api.tasks.reports',
        (instance.id,),
        queue='api.tasks.reports',
        routing_key='api.tasks.reports',
        serializer='json',
    )


@receiver(pre_save, sender=MasterTell)
def master_tell_pre_save(instance, **kwargs):
    if not instance.position:
        position = MasterTell.objects.get_queryset().filter(
            owned_by=instance.owned_by,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_delete, sender=MasterTell)
def master_tell_post_delete(instance, **kwargs):
    master_tells_websockets_1(instance)


@receiver(post_save, sender=MasterTell)
def master_tell_post_save(instance, **kwargs):
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'profile',
                'body': instance.owned_by_id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )
    master_tells_websockets_1(instance)


def master_tells_websockets_1(instance):
    user_location = UserLocation.objects.get_queryset().filter(
        user_id=instance.owned_by_id,
        is_casting=True,
        timestamp__gt=datetime.now() - timedelta(minutes=1),
    ).first()
    if not user_location:
        return
    user_ids = {
        'home': [],
        'networks': [],
        'tellzones': [],
    }
    for ul in UserLocation.objects.get_queryset().filter(
        ~Q(user_id=user_location.user_id), is_casting=True, timestamp__gt=datetime.now() - timedelta(minutes=1),
    ):
        if not is_blocked(user_location.user_id, ul.user_id):
            if vincenty((user_location.point.x, user_location.point.y), (ul.point.x, ul.point.y)).ft <= 300.00:
                user_ids['home'].append(ul.user_id)
            if user_location.network_id and user_location.network_id == ul.network_id:
                user_ids['networks'].append(ul.user_id)
            if user_location.tellzone_id and user_location.tellzone_id == ul.tellzone_id:
                    user_ids['tellzones'].append(ul.user_id)
    if user_ids['home']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['home'],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'home',
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )
    if user_ids['networks']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['networks'],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'networks',
                        'id': user_location.network_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )
    if user_ids['tellzones']:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': user_ids['tellzones'],
                    'subject': 'master_tells',
                    'body': {
                        'type': 'tellzones',
                        'id': user_location.tellzone_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )


@receiver(pre_save, sender=MasterTellTellzone)
def master_tell_tellzone_pre_save(instance, **kwargs):
    if instance.tellzone.are_pinned_tells_queued:
        instance.status = 'In Review'


@receiver(post_save, sender=MasterTellTellzone)
def master_tell_tellzone_post_save(instance, **kwargs):
    master_tells_websockets_2(instance)


@receiver(post_delete, sender=MasterTellTellzone)
def master_tell_tellzone_post_delete(instance, **kwargs):
    master_tells_websockets_2(instance)


def master_tells_websockets_2(instance):
    user_ids = set()
    for master_tell_tellzone in MasterTellTellzone.objects.get_queryset().filter(
        ~Q(master_tell__owned_by_id=instance.master_tell.owned_by_id),
        tellzone_id=instance.tellzone_id,
    ):
        if not is_blocked(instance.master_tell.owned_by_id, master_tell_tellzone.master_tell.owned_by_id):
            if instance.tellzone_id and instance.tellzone_id == master_tell_tellzone.tellzone_id:
                user_ids.add(master_tell_tellzone.master_tell.owned_by_id)
    for ul in UserLocation.objects.get_queryset().filter(
        ~Q(user_id=instance.master_tell.owned_by_id),
        tellzone_id=instance.tellzone_id,
        is_casting=True,
        timestamp__gt=datetime.now() - timedelta(minutes=1),
    ):
        if not is_blocked(instance.master_tell.owned_by_id, ul.user_id):
            if instance.tellzone_id and instance.tellzone_id == ul.tellzone_id:
                user_ids.add(ul.user_id)
    if user_ids:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'user_ids': list(user_ids),
                    'subject': 'master_tells',
                    'body': {
                        'type': 'tellzones',
                        'id': instance.tellzone_id,
                    },
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )


@receiver(pre_save, sender=Message)
def message_pre_save(instance, **kwargs):
    if not instance.contents:
        instance.contents = ''


@receiver(post_save, sender=Message)
def message_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        if instance.type == 'Response - Blocked':
            Block.insert_or_update(instance.user_source.id, instance.user_destination_id, False)
        if instance.type in ['Response - Rejected', 'Response - Blocked']:
            instance.is_suppressed = True
            instance.save()
            for message in Message.objects.get_queryset().filter(
                Q(user_source_id=instance.user_source_id, user_destination_id=instance.user_destination_id) |
                Q(user_source_id=instance.user_destination_id, user_destination_id=instance.user_source_id),
                id__lt=instance.id,
                master_tell_id=instance.master_tell_id,
                user_status_id=instance.user_status_id,
                post_id=instance.post_id,
            ).order_by('-id'):
                if message.type == 'Request':
                    message.is_suppressed = True
                    message.save()
                    break
        status = False
        if instance.type in ['Request', 'Response - Accepted']:
            if instance.user_destination.settings_['notifications_invitations']:
                status = True
        if instance.type in ['Ask', 'Message']:
            if instance.user_destination.settings_['notifications_messages']:
                status = True
        if status:
            if instance.type in ['Ask', 'Message']:
                body = u'{first_name:s} {last_name:s}: {contents:s}'.format(
                    first_name=instance.user_source.first_name,
                    last_name=instance.user_source.last_name,
                    contents=instance.contents,
                )
            else:
                body = instance.contents
            current_app.send_task(
                'api.tasks.push_notifications',
                (
                    instance.user_destination_id,
                    {
                        'aps': {
                            'alert': {
                                'body': body,
                                'title': 'New message from user',
                            },
                            'badge': get_badge(instance.user_destination_id),
                        },
                        'type': 'message',
                        'user_source_id': instance.user_source_id,
                        'master_tell_id': instance.master_tell_id,
                        'post_id': instance.post_id,
                    },
                ),
                queue='api.tasks.push_notifications',
                routing_key='api.tasks.push_notifications',
                serializer='json',
            )
    if ('created' in kwargs and kwargs['created']) or not instance.is_suppressed:
        current_app.send_task(
            'api.management.commands.websockets',
            (
                {
                    'subject': 'messages',
                    'body': instance.id,
                },
            ),
            queue='api.management.commands.websockets',
            routing_key='api.management.commands.websockets',
            serializer='json',
        )


@receiver(post_delete, sender=Message)
def message_post_delete(instance, **kwargs):
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'messages',
                'body': instance.id,
                'action': 'deleted',
                'users': [instance.user_source_id, instance.user_destination_id],
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )


@receiver(post_save, sender=Notification)
def notification_post_save(instance, **kwargs):
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'notifications',
                'body': instance.id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )


@receiver(post_save, sender=ShareUser)
def share_user_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        if instance.user_destination_id:
            if instance.user_destination.settings_['notifications_shared_profiles']:
                Notification.objects.create(
                    user_id=instance.user_destination_id,
                    type='B',
                    contents={
                        'user_source': {
                            'id': instance.user_source.id,
                            'first_name': instance.user_source.first_name,
                            'last_name': instance.user_source.last_name if instance.user_source.settings_[
                                'show_last_name'
                            ] else None,
                            'photo_original': instance.user_source.photo_original if instance.user_source.settings_[
                                'show_photo'
                            ] else None,
                            'photo_preview': instance.user_source.photo_preview if instance.user_source.settings_[
                                'show_photo'
                            ] else None,
                        },
                        'user_destination': {
                            'id': instance.object.id,
                            'first_name': instance.object.first_name,
                            'last_name': instance.object.last_name if instance.object.settings_[
                                'show_last_name'
                            ] else None,
                            'photo_original': instance.object.photo_original if instance.object.settings_[
                                'show_photo'
                            ] else None,
                            'photo_preview': instance.object.photo_preview if instance.object.settings_[
                                'show_photo'
                            ] else None,
                        },
                    },
                )


@receiver(pre_save, sender=SlaveTell)
def slave_tell_pre_save(instance, **kwargs):
    if not instance.position:
        position = SlaveTell.objects.get_queryset().filter(
            owned_by=instance.owned_by,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=SlaveTell)
def slave_tell_post_save(instance, **kwargs):
    current_app.send_task(
        'api.tasks.thumbnails_1',
        ('SlaveTell', instance.id,),
        queue='api.tasks.thumbnails',
        routing_key='api.tasks.thumbnails',
        serializer='json',
    )
    current_app.send_task(
        'api.management.commands.websockets',
        (
            {
                'subject': 'profile',
                'body': instance.owned_by_id,
            },
        ),
        queue='api.management.commands.websockets',
        routing_key='api.management.commands.websockets',
        serializer='json',
    )


@receiver(post_save, sender=Tellcard)
def tellcard_post_save(instance, **kwargs):
    if instance.saved_at:
        if (
            ('created' in kwargs and kwargs['created']) or
            ('update_fields' in kwargs and kwargs['update_fields'] and 'saved_at' in kwargs['update_fields'])
        ):
            if instance.user_destination.settings_['notifications_saved_you']:
                Notification.objects.create(
                    user_id=instance.user_destination_id,
                    type='A',
                    contents={
                        'id': instance.user_source.id,
                        'first_name': instance.user_source.first_name,
                        'last_name': instance.user_source.last_name if instance.user_source.settings_[
                            'show_last_name'
                        ] else None,
                        'photo_original': instance.user_source.photo_original if instance.user_source.settings_[
                            'show_photo'
                        ] else None,
                        'photo_preview': instance.user_source.photo_preview if instance.user_source.settings_[
                            'show_photo'
                        ] else None,
                    },
                )
                string = u'{name:s} saved your profile'.format(
                    name=' '.join(
                        filter(
                            None,
                            [
                                instance.user_source.first_name,
                                instance.user_source.last_name if instance.user_source.settings_[
                                    'show_last_name'
                                ] else None,
                            ]
                        )
                    ),
                )
                current_app.send_task(
                    'api.tasks.push_notifications',
                    (
                        instance.user_destination_id,
                        {
                            'aps': {
                                'alert': {
                                    'body': string,
                                    'title': string,
                                },
                                'badge': get_badge(instance.user_destination_id),
                            },
                            'type': 'tellcard',
                        },
                    ),
                    queue='api.tasks.push_notifications',
                    routing_key='api.tasks.push_notifications',
                    serializer='json',
                )


@receiver(pre_save, sender=Post)
def post_pre_save(instance, **kwargs):
    instance.expired_at = datetime.now() + timedelta(days=365)


@receiver(pre_save, sender=PostAttachment)
def post_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = PostAttachment.objects.get_queryset().filter(
            post=instance.post,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=PostAttachment)
def post_attachment_post_save(instance, **kwargs):
    current_app.send_task(
        'api.tasks.thumbnails_1',
        ('PostAttachment', instance.id,),
        queue='api.tasks.thumbnails',
        routing_key='api.tasks.thumbnails',
        serializer='json',
    )


def get_badge(user_id):
    return (
        Message.objects.get_queryset().filter(user_destination_id=user_id, status='Unread').count() +
        Notification.objects.get_queryset().filter(user_id=user_id, status='Unread').count()
    )


def get_hash(items):
    return '-'.join(map(str, [item.id for item in items]))


def get_items(items, count):
    return [item.tolist() for item in array_split(items, count)]


def get_master_tells(user_id, tellzone_id, tellzones, radius):
    master_tells = {}
    records = []
    for tellzone in tellzones:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    api_master_tells.id AS id,
                    api_master_tells.contents AS contents,
                    api_master_tells.description AS description,
                    api_master_tells.position AS position,
                    api_master_tells.is_visible AS is_visible,
                    api_master_tells.inserted_at AS inserted_at,
                    api_master_tells.updated_at AS updated_at,
                    true AS is_pinned,
                    api_slave_tells.id AS slave_tell_id,
                    api_slave_tells.created_by_id AS slave_tell_created_by_id,
                    api_slave_tells.owned_by_id AS slave_tell_owned_by_id,
                    api_slave_tells.photo AS slave_tell_photo,
                    api_slave_tells.first_name AS slave_tell_first_name,
                    api_slave_tells.last_name AS slave_tell_last_name,
                    api_slave_tells.type AS slave_tell_type,
                    api_slave_tells.contents_original AS slave_tell_contents_original,
                    api_slave_tells.contents_preview AS slave_tell_contents_preview,
                    api_slave_tells.description AS slave_tell_description,
                    api_slave_tells.position AS slave_tell_position,
                    api_slave_tells.is_editable AS slave_tell_is_editable,
                    api_slave_tells.inserted_at AS slave_tell_inserted_at,
                    api_slave_tells.updated_at AS slave_tell_updated_at,
                    api_users_created_by.id AS created_by_id,
                    api_users_created_by.photo_original AS created_by_photo_original,
                    api_users_created_by.photo_preview AS created_by_photo_preview,
                    api_users_created_by.first_name AS created_by_first_name,
                    api_users_created_by.last_name AS created_by_last_name,
                    api_users_created_by.description AS created_by_description,
                    api_users_created_by.settings AS created_by_settings,
                    api_users_owned_by.id AS owned_by_id,
                    api_users_owned_by.photo_original AS owned_by_photo_original,
                    api_users_owned_by.photo_preview AS owned_by_photo_preview,
                    api_users_owned_by.first_name AS owned_by_first_name,
                    api_users_owned_by.last_name AS owned_by_last_name,
                    api_users_owned_by.description AS owned_by_description,
                    api_users_owned_by.settings AS owned_by_settings,
                    api_categories.id AS category_id,
                    api_categories.name AS category_name,
                    api_categories.photo AS category_photo,
                    api_categories.display_type AS category_display_type,
                    api_categories.description AS category_description,
                    api_categories.position AS category_position,
                    api_tellzones.id AS tellzone_id,
                    api_tellzones.name AS tellzone_name
                FROM api_master_tells_tellzones
                INNER JOIN api_master_tells ON api_master_tells.id = api_master_tells_tellzones.master_tell_id
                INNER JOIN api_tellzones ON api_tellzones.id = api_master_tells_tellzones.tellzone_id
                LEFT OUTER JOIN api_slave_tells ON api_slave_tells.master_tell_id = api_master_tells.id
                INNER JOIN api_users AS api_users_created_by
                    ON api_users_created_by.id = api_master_tells.created_by_id
                INNER JOIN api_users AS api_users_owned_by
                    ON api_users_owned_by.id = api_master_tells.owned_by_id
                INNER JOIN api_categories ON api_categories.id = api_master_tells.category_id
                LEFT OUTER JOIN api_blocks ON
                    (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_master_tells.owned_by_id)
                    OR
                    (api_blocks.user_source_id = api_master_tells.owned_by_id AND api_blocks.user_destination_id = %s)
                WHERE
                    api_master_tells.owned_by_id != %s
                    AND
                    (
                        api_master_tells_tellzones.tellzone_id IS NULL
                        OR
                        api_master_tells_tellzones.tellzone_id != %s
                    )
                    AND
                    api_master_tells_tellzones.tellzone_id = %s
                    AND
                    api_master_tells_tellzones.status = %s
                    AND
                    api_blocks.id IS NULL
                ORDER BY api_master_tells.id ASC, api_slave_tells.position ASC
                ''',
                (
                    user_id, user_id, user_id, tellzone_id, tellzone[0], 'Published',
                ),
            )
            columns = [column.name for column in cursor.description]
            for record in cursor.fetchall():
                records.append(dict(zip(columns, record)))
    for record in records:
        if record['id'] not in master_tells:
            master_tells[record['id']] = {}
        if 'id' not in master_tells[record['id']]:
            master_tells[record['id']]['id'] = record['id']
        if 'contents' not in master_tells[record['id']]:
            master_tells[record['id']]['contents'] = record['contents']
        if 'description' not in master_tells[record['id']]:
            master_tells[record['id']]['description'] = record['description']
        if 'position' not in master_tells[record['id']]:
            master_tells[record['id']]['position'] = record['position']
        if 'is_visible' not in master_tells[record['id']]:
            master_tells[record['id']]['is_visible'] = record['is_visible']
        if 'inserted_at' not in master_tells[record['id']]:
            master_tells[record['id']]['inserted_at'] = record['inserted_at']
        if 'updated_at' not in master_tells[record['id']]:
            master_tells[record['id']]['updated_at'] = record['updated_at']
        if 'is_pinned' not in master_tells[record['id']]:
            master_tells[record['id']]['is_pinned'] = record['is_pinned']
        if 'slave_tells' not in master_tells[record['id']]:
            master_tells[record['id']]['slave_tells'] = {}
        if record['slave_tell_id']:
            if record['slave_tell_id'] not in master_tells[record['id']]['slave_tells']:
                master_tells[record['id']]['slave_tells'][record['slave_tell_id']] = {
                    'id': record['slave_tell_id'],
                    'created_by_id': record['slave_tell_created_by_id'],
                    'owned_by_id': record['slave_tell_owned_by_id'],
                    'photo': record['slave_tell_photo'],
                    'first_name': record['slave_tell_first_name'],
                    'last_name': record['slave_tell_last_name'],
                    'type': record['slave_tell_type'],
                    'contents_original': record['slave_tell_contents_original'],
                    'contents_preview': record['slave_tell_contents_preview'],
                    'description': record['slave_tell_description'],
                    'position': record['slave_tell_position'],
                    'is_editable': record['slave_tell_is_editable'],
                    'inserted_at': record['slave_tell_inserted_at'],
                    'updated_at': record['slave_tell_updated_at'],
                }
        if 'created_by' not in master_tells[record['id']]:
            master_tells[record['id']]['created_by'] = {
                'id': record['created_by_id'],
                'photo_original': record['created_by_photo_original'],
                'photo_preview': record['created_by_photo_preview'],
                'first_name': record['created_by_first_name'],
                'last_name': record['created_by_last_name'],
                'description': record['created_by_description'],
                'settings': loads(record['created_by_settings']),
            }
        if 'owned_by' not in master_tells[record['id']]:
            master_tells[record['id']]['owned_by'] = {
                'id': record['owned_by_id'],
                'photo_original': record['owned_by_photo_original'],
                'photo_preview': record['owned_by_photo_preview'],
                'first_name': record['owned_by_first_name'],
                'last_name': record['owned_by_last_name'],
                'description': record['owned_by_description'],
                'settings': loads(record['owned_by_settings']),
            }
        if 'category' not in master_tells[record['id']]:
            master_tells[record['id']]['category'] = {
                'id': record['category_id'],
                'name': record['category_name'],
                'photo': record['category_photo'],
                'display_type': record['category_display_type'],
                'description': record['category_description'],
                'position': record['category_position'],
            }
        if 'tellzones' not in master_tells[record['id']]:
            master_tells[record['id']]['tellzones'] = {}
        if 'tellzone_id' in record and record['tellzone_id'] and 'tellzone_name' in record and record['tellzone_name']:
            master_tells[record['id']]['tellzones'][record['tellzone_id']] = {
                'id': record['tellzone_id'],
                'name': record['tellzone_name'],
            }
    master_tells = sorted(master_tells.values(), key=lambda item: item['id'])
    for key, value in enumerate(master_tells):
        master_tells[key]['created_by']['photo_original'] = (
            master_tells[key]['created_by']['photo_original']
            if master_tells[key]['created_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['created_by']['photo_preview'] = (
            master_tells[key]['created_by']['photo_preview']
            if master_tells[key]['created_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['created_by']['last_name'] = (
            master_tells[key]['created_by']['last_name']
            if master_tells[key]['created_by']['settings']['show_last_name'] == 'True' else None
        )
        master_tells[key]['owned_by']['photo_original'] = (
            master_tells[key]['owned_by']['photo_original']
            if master_tells[key]['owned_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['owned_by']['photo_preview'] = (
            master_tells[key]['owned_by']['photo_preview']
            if master_tells[key]['owned_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['owned_by']['last_name'] = (
            master_tells[key]['owned_by']['last_name']
            if master_tells[key]['owned_by']['settings']['show_last_name'] == 'True' else None
        )
        del master_tells[key]['created_by']['settings']
        del master_tells[key]['owned_by']['settings']
        master_tells[key]['slave_tells'] = sorted(
            master_tells[key]['slave_tells'].values(), key=lambda item: item['position'],
        )
        master_tells[key]['tellzones'] = sorted(master_tells[key]['tellzones'].values(), key=lambda item: item['id'])
    return master_tells


def get_point(latitude, longitude):
    return fromstr('POINT({longitude:.14f} {latitude:.14f})'.format(latitude=latitude, longitude=longitude))


def get_users(user_id, network_id, tellzone_id, point, radius, include_user_id):
    point = 'POINT({longitude:.14f} {latitude:.14f})'.format(longitude=point.x, latitude=point.y)
    users = {}
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            '''
            SELECT
                api_users_locations.user_id,
                api_users_locations.network_id,
                api_users_locations.tellzone_id,
                ST_AsGeoJSON(api_users_locations.point),
                ST_Distance(
                    ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                    ST_Transform(api_users_locations.point, 2163)
                ) * 3.28084 AS distance
            FROM api_users_locations
            INNER JOIN api_users ON api_users.id = api_users_locations.user_id
            INNER JOIN (
                SELECT MAX(api_users_locations.id) AS id
                FROM api_users_locations
                GROUP BY api_users_locations.user_id
            ) api_users_locations_ ON api_users_locations.id = api_users_locations_.id
            WHERE
                (api_users_locations.user_id != %s OR %s = true)
                AND
                ST_DWithin(
                    ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                    ST_Transform(api_users_locations.point, 2163),
                    %s
                )
                AND
                api_users_locations.is_casting = TRUE
                AND
                api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
                AND
                api_users.is_signed_in = TRUE
            ORDER BY distance ASC, api_users_locations.user_id ASC
            ''',
            (point, user_id, include_user_id, point, radius,),
        )
        for record in cursor.fetchall():
            if record[0] not in users:
                p = loads(record[3])
                p = get_point(p['coordinates'][1], p['coordinates'][0])
                users[record[0]] = (User.objects.get_queryset().filter(id=record[0]).first(), p, record[4],)
                users[record[0]][0].group = 1
                if tellzone_id:
                    if record[2]:
                        if tellzone_id == record[2]:
                            users[record[0]][0].group = 1
                        else:
                            users[record[0]][0].group = 2
                    else:
                        if record[4] <= 300.0:
                            users[record[0]][0].group = 1
                        else:
                            users[record[0]][0].group = 2
                else:
                    if record[4] <= 300.0:
                        users[record[0]][0].group = 1
                    else:
                        users[record[0]][0].group = 2
    return users


def is_blocked(one, two):
    if Block.objects.get_queryset().filter(
        Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
    ).count():
        return True
    return False
