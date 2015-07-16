# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from celery import current_app
from django.conf import settings
from django.contrib.auth.models import update_last_login, User as Administrator
from django.contrib.auth.signals import user_logged_in
from django.contrib.gis.db.models import GeoManager, PointField
from django.contrib.gis.measure import D
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
    TextField,
)
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy
from django_extensions.db.fields import UUIDField
from itsdangerous import TimestampSigner
from jsonfield import JSONField
from push_notifications.apns import apns_send_message
from push_notifications.fields import HexIntegerField
from push_notifications.gcm import gcm_send_message
from social.apps.django_app.default.models import DjangoStorage, UserSocialAuth
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import dumps

user_logged_in.disconnect(update_last_login)


def __str__(self):
    return '{first_name} {last_name} ({email})'.format(
        email=self.email,
        first_name=self.first_name,
        last_name=self.last_name,
    )

Administrator.__str__ = __str__


def __unicode__(self):
    return u'{first_name} {last_name} ({email})'.format(
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
    return '{provider} - {uid}'.format(provider=self.provider, uid=self.uid)

UserSocialAuth.__str__ = __str__


def __unicode__(self):
    return u'{provider} - {uid}'.format(provider=self.provider, uid=self.uid)

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


class Tellzone(Model):

    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    photo = CharField(ugettext_lazy('Photo'), db_index=True, max_length=255)
    location = CharField(ugettext_lazy('Location'), db_index=True, max_length=255)
    phone = CharField(ugettext_lazy('Phone'), db_index=True, max_length=255)
    url = CharField(ugettext_lazy('URL'), db_index=True, max_length=255)
    hours = JSONField(ugettext_lazy('Hours'))
    point = PointField(ugettext_lazy('Point'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

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
    def views(self):
        return self.users.get_queryset().filter(viewed_at__isnull=False).count()

    @cached_property
    def tellecasters(self):
        return UserLocation.objects.get_queryset().filter(
            point__distance_lte=(self.point, D(ft=Tellzone.radius())),
            timestamp__gt=datetime.now() - timedelta(minutes=1),
            user__is_signed_in=True,
        ).distinct(
            'user_id',
        ).order_by(
            'user_id',
            '-id',
        ).count()

    @classmethod
    def radius(cls):
        return 300.00

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

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

    def is_viewed(self, user_id):
        return self.users.get_queryset().filter(user_id=user_id, viewed_at__isnull=False).count() > 0

    def is_favorited(self, user_id):
        return self.users.get_queryset().filter(user_id=user_id, favorited_at__isnull=False).count() > 0


class User(Model):

    email = EmailField(ugettext_lazy('Email'), db_index=True, max_length=255, unique=True)
    photo = CharField(ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255, null=True)
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
    is_signed_in = BooleanField(ugettext_lazy('Is Signed In?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    objects = GeoManager()

    class Meta:

        db_table = 'api_users'
        ordering = (
            '-id',
        )
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @cached_property
    def settings_(self):
        dictionary = UserSetting.dictionary
        for setting in self.settings.get_queryset():
            dictionary[setting.key] = True if setting.value == 'True' else False
        return dictionary

    @cached_property
    def token(self):
        return TimestampSigner(settings.SECRET_KEY).sign(str(self.id))

    @classmethod
    def insert(cls, data):
        user = User.objects.create(
            email=data['email'],
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
        if 'settings' in data:
            for key, value in data['settings'].items():
                user_setting = user.settings.get_queryset().filter(key=key).first()
                user_setting.value = 'True' if value else 'False'
                user_setting.save()
        if 'photos' in data:
            for photo in data['photos']:
                UserPhoto.insert(user.id, photo)
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                UserSocialProfile.insert(user.id, social_profile)
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
        if 'status' in data:
            UserStatus.insert(user.id, data['status'])
        if 'urls' in data:
            for url in data['urls']:
                UserURL.insert(user.id, url)
        if 'master_tells' in data:
            for master_tell in data['master_tells']:
                MasterTell.insert(user.id, master_tell)
        return user

    def __str__(self):
        return '{first_name} {last_name} ({email})'.format(
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
        )

    def __unicode__(self):
        return u'{first_name} {last_name} ({email})'.format(
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

    def update(self, data):
        if 'email' in data:
            self.email = data['email']
        self.photo = data['photo'] if 'photo' in data else None
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
                    Q(id=photo['id'] if 'id' in photo else 0) | Q(string=photo['string'] if 'string' in photo else ''),
                ).first()
                if user_photo:
                    if 'string' in photo:
                        user_photo.string = photo['string']
                    if 'position' in photo:
                        user_photo.position = photo['position']
                    user_photo.save()
                else:
                    user_photo = UserPhoto.objects.create(
                        user_id=self.id,
                        string=photo['string'] if 'string' in photo else '',
                        position=photo['position'] if 'position' in photo else 0,
                    )
                ids.append(user_photo.id)
        self.photos.get_queryset().exclude(id__in=ids).delete()
        return self

    def update_settings(self, data):
        if 'settings' in data:
            for key, value in data['settings'].items():
                user_setting = self.settings.get_queryset().filter(key=key).first()
                user_setting.value = 'True' if value else 'False'
                user_setting.save()
        return self

    def update_social_profiles(self, data):
        ids = []
        if 'social_profiles' in data:
            for social_profile in data['social_profiles']:
                if 'url' not in social_profile or not social_profile['url']:
                    continue
                user_social_profile = self.social_profiles.get_queryset().filter(
                    Q(id=social_profile['id'] if 'id' in social_profile else 0) |
                    Q(netloc=social_profile['netloc'] if 'netloc' in social_profile else ''),
                ).first()
                if user_social_profile:
                    if 'netloc' in social_profile:
                        user_social_profile.netloc = social_profile['netloc']
                    if 'url' in social_profile:
                        user_social_profile.url = social_profile['url']
                    user_social_profile.save()
                else:
                    user_social_profile = UserSocialProfile.objects.create(
                        user_id=self.id,
                        netloc=social_profile['netloc'] if 'netloc' in social_profile else '',
                        url=social_profile['url'] if 'url' in social_profile else '',
                    )
                ids.append(user_social_profile.id)
        self.social_profiles.get_queryset().exclude(id__in=ids).delete()
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
                        Q(string=attachment['string'] if 'string' in attachment else ''),
                        user_status_id=user_status.id,
                    ).first()
                    if user_status_attachment:
                        if 'string' in attachment:
                            user_status_attachment.string = attachment['string']
                        if 'position' in attachment:
                            user_status_attachment.position = attachment['position']
                        user_status_attachment.save()
                    else:
                        user_status_attachment = UserStatusAttachment.objects.create(
                            user_status_id=user_status.id,
                            string=attachment['string'] if 'string' in attachment else '',
                            position=attachment['position'] if 'position' in attachment else 0,
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
                    user_url.save()
                else:
                    user_url = UserURL.objects.create(
                        user_id=self.id,
                        string=url['string'] if 'string' in url else '',
                        position=url['position'] if 'position' in url else 0,
                    )
                ids.append(user_url.id)
        self.urls.get_queryset().exclude(id__in=ids).delete()
        return self

    def get_messages(self, id):
        if not id:
            return 0
        if Message.objects.get_queryset().filter(
            Q(user_source_id=id, user_destination_id=self.id) | Q(user_source_id=self.id, user_destination_id=id),
            type='Message',
        ).count():
            return 6
        message = Message.objects.get_queryset().filter(
            Q(user_source_id=id, user_destination_id=self.id) | Q(user_source_id=self.id, user_destination_id=id),
        ).order_by(
            '-inserted_at',
        ).first()
        if not message:
            return 0
        if message.type == 'Request':
            if message.user_source_id == id:
                return 1
            if message.user_source_id == self.id:
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

    def has_permission(self, instance=None):
        if isinstance(instance, User):
            return instance.id == self.id
        if isinstance(instance, UserLocation):
            return instance.user_id == self.id
        if isinstance(instance, UserPhoto):
            return instance.user_id == self.id
        if isinstance(instance, UserSetting):
            return instance.user_id == self.id
        if isinstance(instance, UserSocialProfile):
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
        if isinstance(instance, Message):
            return instance.user_source_id == self.id
        if isinstance(instance, MessageAttachment):
            return self.has_permission(self, instance=instance.message)
        if isinstance(instance, Notification):
            return instance.user_id == self.id
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
            return str(self.id) == TimestampSigner(settings.SECRET_KEY).unsign(token)
        except Exception:
            pass
        return False


class UserLocation(Model):

    user = ForeignKey(User, related_name='locations')
    tellzone = ForeignKey(Tellzone, blank=True, default=None, null=True, related_name='+')
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
            tellzone_id=data['tellzone_id'] if 'tellzone' in data else None,
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
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_photos'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: Photo'
        verbose_name_plural = 'Users :: Photos'

    @classmethod
    def insert(cls, user_id, data):
        return UserPhoto.objects.create(
            user_id=user_id,
            string=data['string'] if 'string' in data else None,
            position=data['position'] if 'position' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserSetting(Model):

    dictionary = {
        'notifications_invitations': True,
        'notifications_messages': True,
        'notifications_saved_you': True,
        'notifications_shared_profiles': True,
        'show_email': False,
        'show_last_name': False,
        'show_phone': False,
        'show_photo': True,
    }

    user = ForeignKey(User, related_name='settings')
    key = CharField(ugettext_lazy('Key'), db_index=True, max_length=255)
    value = CharField(ugettext_lazy('Value'), db_index=True, max_length=255)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:
        db_table = 'api_users_settings'
        ordering = (
            '-id',
        )
        unique_together = (
            'user',
            'key',
        )
        verbose_name = ugettext_lazy('Users :: Setting')
        verbose_name_plural = ugettext_lazy('Users :: Settings')

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserSocialProfile(Model):

    user = ForeignKey(User, related_name='social_profiles')
    netloc = CharField(
        ugettext_lazy('Network Location'),
        choices=(
            ('facebook.com', 'facebook.com',),
            ('google.com', 'google.com',),
            ('instagram.com', 'instagram.com',),
            ('linkedin.com', 'linkedin.com',),
            ('twitter.com', 'twitter.com',),
        ),
        db_index=True,
        max_length=255,
    )
    url = CharField(ugettext_lazy('URL'), db_index=True, max_length=255)

    class Meta:

        db_table = 'api_users_social_profiles'
        ordering = (
            '-id',
        )
        unique_together = (
            'user',
            'netloc',
        )
        verbose_name = 'Users :: Social Profile'
        verbose_name_plural = 'Users :: Social Profiles'

    @classmethod
    def insert(cls, user_id, data):
        if 'url' in data and data['url']:
            return UserSocialProfile.objects.create(user_id=user_id, netloc=data['netloc'], url=data['url'])

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
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_statuses_attachments'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: Statuses :: Attachment'
        verbose_name_plural = 'Users :: Statuses :: Attachments'

    @classmethod
    def insert(cls, user_status_id, data):
        return UserStatusAttachment.objects.create(
            user_status_id=user_status_id,
            string=data['string'] if 'string' in data else None,
            position=data['position'] if 'position' in data else None,
        )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


class UserTellzone(Model):

    user = ForeignKey(User, related_name='tellzones')
    tellzone = ForeignKey(Tellzone, related_name='users')
    viewed_at = DateTimeField(ugettext_lazy('Viewed At'), blank=True, db_index=True, null=True)
    favorited_at = DateTimeField(ugettext_lazy('Favorited At'), blank=True, db_index=True, null=True)

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
        if data['action'] == 'View':
            user_tellzone.viewed_at = now
        if data['action'] == 'Favorite':
            user_tellzone.favorited_at = now
        user_tellzone.save()
        return user_tellzone

    @classmethod
    def delete(cls, user_id, data):
        user_tellzone = UserTellzone.objects.get_queryset().filter(
            user_id=user_id,
            tellzone_id=data['tellzone_id'],
        ).first()
        if not user_tellzone:
            return {}
        if data['action'] == 'View':
            user_tellzone.viewed_at = None
        if data['action'] == 'Favorite':
            user_tellzone.favorited_at = None
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

    class Meta:

        db_table = 'api_users_urls'
        ordering = (
            '-id',
        )
        verbose_name = 'Users :: URL'
        verbose_name_plural = 'Users :: URLs'

    @classmethod
    def insert(cls, user_id, data):
        return UserURL.objects.create(
            user_id=user_id,
            string=data['string'] if 'string' in data else None,
            position=data['position'] if 'position' in data else None,
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
    def delete(cls, user_source_id, user_destination_id):
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
        return apns_send_message(self.registration_id, alert, badge=badge, extra=extra, sound='default')


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
        return gcm_send_message(self.registration_id, data)


class MasterTell(Model):

    created_by = ForeignKey(User, related_name='+')
    owned_by = ForeignKey(User, related_name='master_tells')
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    is_visible = BooleanField(ugettext_lazy('Is Visible?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:

        db_table = 'api_master_tells'
        ordering = (
            '-id',
        )
        verbose_name = 'Master Tell'
        verbose_name_plural = 'Master Tells'

    @classmethod
    def insert(cls, user_id, data):
        master_tell = MasterTell.objects.create(
            created_by_id=user_id,
            owned_by_id=user_id,
            contents=data['contents'] if 'contents' in data else None,
            position=data['position'] if 'position' in data else None,
            is_visible=data['is_visible'] if 'is_visible' in data else None,
        )
        if 'slave_tells' in data:
            for slave_tell in data['slave_tells']:
                slave_tell['master_tell_id'] = master_tell.id
                SlaveTell.insert(user_id, slave_tell)
        return master_tell

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)

    def update(self, data):
        if 'contents' in data:
            self.contents = data['contents']
        if 'position' in data:
            self.position = data['position']
        if 'is_visible' in data:
            self.is_visible = data['is_visible']
        self.save()
        return self


class Message(Model):

    user_source = ForeignKey(User, related_name='+')
    user_source_is_hidden = BooleanField(ugettext_lazy('Is Hidden?'), db_index=True, default=False)
    user_destination = ForeignKey(User, related_name='+')
    user_destination_is_hidden = BooleanField(ugettext_lazy('Is Hidden?'), db_index=True, default=False)
    user_status = ForeignKey(UserStatus, blank=True, null=True, related_name='+')
    master_tell = ForeignKey(MasterTell, blank=True, null=True, related_name='+')
    type = CharField(
        ugettext_lazy('Type'),
        choices=(
            ('Message', 'Message',),
            ('Request', 'Request',),
            ('Response - Accepted', 'Response - Accepted',),
            ('Response - Blocked', 'Response - Blocked',),
            ('Response - Deferred', 'Response - Deferred',),
            ('Response - Rejected', 'Response - Rejected',),
        ),
        db_index=True,
        max_length=255,
    )
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
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
        message = Message.objects.create(
            user_source_id=user_source_id,
            user_source_is_hidden=data['user_source_is_hidden'] if 'user_source_is_hidden' in data else None,
            user_destination_id=data['user_destination_id'],
            user_destination_is_hidden=data['user_destination_is_hidden']
            if 'user_destination_is_hidden' in data else None,
            user_status_id=data['user_status_id'] if 'user_status_id' in data else None,
            master_tell_id=data['master_tell_id'] if 'master_tell_id' in data else None,
            type=data['type'] if 'type' in data else None,
            contents=data['contents'] if 'contents' in data else None,
            status=data['status'] if 'status' in data else 'Unread',
        )
        if 'attachments' in data:
            for attachment in data['attachments']:
                MessageAttachment.insert(message.id, attachment)
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


class MessageAttachment(Model):

    message = ForeignKey(Message, related_name='attachments')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_messages_attachments'
        ordering = (
            '-id',
        )
        verbose_name = 'Messages :: Attachment'
        verbose_name_plural = 'Messages :: Attachments'

    @classmethod
    def insert(cls, message_id, data):
        return MessageAttachment.objects.create(
            message_id=message_id,
            string=data['string'] if 'string' in data else None,
            position=data['position'] if 'position' in data else None,
        )

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
    contents = JSONField(ugettext_lazy('Contents'))
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
                'subject': 'Tellecast - Shares/Users - {id}'.format(id=self.id),
                'body': 'Tellecast - Shares/Users - {id}'.format(id=self.id),
            },
            'sms': 'Tellecast - Shares/Users - {id}'.format(id=self.id),
            'facebook_com': 'tellecast://shares/users/{id}'.format(id=self.id),
            'twitter_com': 'tellecast://shares/users/{id}'.format(id=self.id),
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
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    is_editable = BooleanField(ugettext_lazy('Is Editable?'), db_index=True, default=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, db_index=True)

    class Meta:

        db_table = 'api_slave_tells'
        ordering = (
            '-id',
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
            contents=data['contents'] if 'contents' in data else None,
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
        if 'contents' in data:
            self.contents = data['contents']
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
            tellcard = Tellcard.objects.create(
                user_source_id=user_source_id,
                user_destination_id=data['user_destination_id'],
            )
        if 'tellzone_id' in data and data['tellzone_id']:
            tellcard.tellzone_id = data['tellzone_id']
            tellcard.location = None
            update_fields.append('tellzone_id')
            update_fields.append('location')
        else:
            if 'location' in data and data['location']:
                tellcard.tellzone_id = None
                tellcard.location = data['location']
                update_fields.append('tellzone_id')
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
    def delete(cls, user_source_id, data):
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


@receiver(post_save, sender=User)
def user_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        for key, value in UserSetting.dictionary.items():
            UserSetting.objects.create(user_id=instance.id, key=key, value=value)


@receiver(pre_save, sender=UserPhoto)
def user_photo_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserPhoto.objects.get_queryset().filter(
            user=instance.user,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserStatusAttachment)
def user_status_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserStatusAttachment.objects.get_queryset().filter(
            user_status=instance.user_status,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


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


@receiver(pre_save, sender=MasterTell)
def master_tell_pre_save(instance, **kwargs):
    if not instance.position:
        position = MasterTell.objects.get_queryset().filter(
            owned_by=instance.owned_by,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=Message)
def message_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        current_app.send_task(
            'api.tasks.push_notifications',
            (
                instance.user_destination_id,
                {
                    'aps': {
                        'alert': {
                            'body': instance.contents,
                            'title': 'New message from user',
                        },
                        'badge': Notification.objects.get_queryset().filter(
                            user_id=instance.user_destination_id,
                            status='Unread',
                        ).count(),
                    },
                    'type': 'message',
                },
            ),
            serializer='json',
        )


@receiver(pre_save, sender=MessageAttachment)
def message_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = MessageAttachment.objects.get_queryset().filter(
            message=instance.message,
        ).aggregate(
            Max('position'),
        )['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=ShareUser)
def share_user_post_save(instance, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        if instance.user_destination_id:
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
                        'photo': instance.user_source.photo if instance.user_source.settings_['show_photo'] else None,
                    },
                    'user_destination': {
                        'id': instance.object.id,
                        'first_name': instance.object.first_name,
                        'last_name': instance.object.last_name if instance.object.settings_[
                            'show_last_name'
                        ] else None,
                        'photo': instance.object.photo if instance.object.settings_['show_photo'] else None,
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


@receiver(post_save, sender=Tellcard)
def tellcard_post_save(instance, **kwargs):
    if instance.saved_at:
        if (
            ('created' in kwargs and kwargs['created']) or
            ('update_fields' in kwargs and kwargs['update_fields'] and 'saved_at' in kwargs['update_fields'])
        ):
            Notification.objects.create(
                user_id=instance.user_destination_id,
                type='A',
                contents={
                    'id': instance.user_source.id,
                    'first_name': instance.user_source.first_name,
                    'last_name': instance.user_source.last_name if instance.user_source.settings_[
                        'show_last_name'
                    ] else None,
                    'photo': instance.user_source.photo if instance.user_source.settings_['show_photo'] else None,
                },
            )
            string = u'{name} saved your tellcard'.format(
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
                            'badge': Notification.objects.get_queryset().filter(
                                user_id=instance.user_destination_id,
                                status='Unread',
                            ).count(),
                        },
                        'type': 'tellcard',
                    },
                ),
                serializer='json',
            )
