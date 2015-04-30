# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    ForeignKey,
    IntegerField,
    Max,
    Model,
    OneToOneField,
    TextField,
)
from django.contrib.auth.models import update_last_login, User as Administrator
from django.contrib.auth.signals import user_logged_in
from django.contrib.gis.db.models import GeoManager, PointField
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy
from itsdangerous import TimestampSigner
from push_notifications.apns import apns_send_message
from push_notifications.fields import HexIntegerField
from push_notifications.gcm import gcm_send_message
from social.apps.django_app.default.models import UserSocialAuth
from django_extensions.db.fields import UUIDField


class Tellzone(Model):

    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    photo = CharField(ugettext_lazy('Photo'), db_index=True, max_length=255)
    location = CharField(ugettext_lazy('Location'), db_index=True, max_length=255)
    phone = CharField(ugettext_lazy('Phone'), db_index=True, max_length=255)
    url = CharField(ugettext_lazy('URL'), db_index=True, max_length=255)
    hours = TextField(ugettext_lazy('Hours'))
    point = PointField(ugettext_lazy('Point'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

    objects = GeoManager()

    class Meta:

        db_table = 'api_tellzones'
        ordering = (
            '-inserted_at',
        )
        verbose_name = 'Tellzone'
        verbose_name_plural = 'Tellzones'

    @classmethod
    def radius(cls):
        return 30.00

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)


class Offer(Model):

    tellzone = ForeignKey(Tellzone, related_name='offers')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    description = TextField(ugettext_lazy('Description'), db_index=True)
    photo = CharField(ugettext_lazy('Photo'), db_index=True, max_length=255)
    code = CharField(ugettext_lazy('Code'), db_index=True, max_length=255)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)
    expires_at = DateTimeField(ugettext_lazy('Expires At'), blank=True, db_index=True, null=True)

    class Meta:

        db_table = 'api_offers'
        ordering = (
            '-inserted_at',
        )
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)


class User(Model):

    email = EmailField(ugettext_lazy('Email'), db_index=True, max_length=255, unique=True)
    email_status = CharField(
        ugettext_lazy('Email Status'),
        choices=(
            ('Private', 'Private',),
            ('Public', 'Public',),
        ),
        db_index=True,
        default='Private',
        max_length=255,
    )
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
    phone_status = CharField(
        ugettext_lazy('Phone Status'),
        choices=(
            ('Private', 'Private',),
            ('Public', 'Public',),
        ),
        db_index=True,
        default='Private',
        max_length=255,
    )
    point = PointField(ugettext_lazy('Point'), blank=True, db_index=True, null=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

    objects = GeoManager()

    class Meta:

        db_table = 'api_users'
        ordering = (
            '-inserted_at',
        )
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return '%(first_name)s %(last_name)s (%(email)s)' % {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def __unicode__(self):
        return u'%(first_name)s %(last_name)s (%(email)s)' % {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def get_token(self):
        return TimestampSigner(settings.SECRET_KEY).sign(str(self.id))

    def has_permission(self, object=None):
        if isinstance(object, User):
            return object.id == self.id
        if isinstance(object, UserStatus):
            return object.user.id == self.id
        if isinstance(object, UserStatusAttachment):
            return object.user_status.user.id == self.id
        if isinstance(object, UserURL):
            return object.user.id == self.id
        if isinstance(object, UserPhoto):
            return object.user.id == self.id
        if isinstance(object, UserSocialProfile):
            return object.user.id == self.id
        if isinstance(object, UserLocation):
            return object.user.id == self.id
        if isinstance(object, UserTellzone):
            return object.user.id == self.id
        if isinstance(object, UserOffer):
            return object.user.id == self.id
        if isinstance(object, DeviceAPNS):
            return object.user.id == self.id
        if isinstance(object, DeviceGCM):
            return object.user.id == self.id
        if isinstance(object, MasterTell):
            return object.owned_by.id == self.id
        if isinstance(object, SlaveTell):
            return object.owned_by.id == self.id
        if isinstance(object, Message):
            return object.user_source.id == self.id
        if isinstance(object, MessageAttachment):
            return object.message.user_source.id == self.id
        if isinstance(object, Tellcard):
            return object.user_source.id == self.id
        if isinstance(object, Block):
            return object.user_source.id == self.id

    def is_authenticated(self):
        return True

    def is_valid(self, token):
        try:
            return str(self.id) == TimestampSigner(settings.SECRET_KEY).unsign(token)
        except Exception:
            pass
        return False


class UserPhoto(Model):

    user = ForeignKey(User, related_name='photos')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_photos'
        ordering = (
            'user',
            'position',
        )
        verbose_name = 'User Photo'
        verbose_name_plural = 'User Photos'


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
            'user',
            'netloc',
        )
        unique_together = (
            'user',
            'netloc',
        )
        verbose_name = 'User Social Profile'
        verbose_name_plural = 'User Social Profiles'


class UserStatus(Model):

    user = OneToOneField(User, related_name='status')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255)
    url = CharField(ugettext_lazy('URL'), blank=True, db_index=True, max_length=255, null=True)
    notes = TextField(ugettext_lazy('Notes'), blank=True, db_index=True, null=True)

    class Meta:

        db_table = 'api_users_statuses'
        ordering = (
            'user',
            'string',
        )
        verbose_name = 'User Status'
        verbose_name_plural = 'User Statuses'

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
            'user_status',
            'position',
        )
        verbose_name = 'User Status Attachment'
        verbose_name_plural = 'User Status Attachments'


class UserURL(Model):

    user = ForeignKey(User, related_name='urls')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_users_urls'
        ordering = (
            'user',
            'position',
        )
        verbose_name = 'User URL'
        verbose_name_plural = 'User URLs'


class UserLocation(Model):

    user = ForeignKey(User, related_name='locations')
    point = PointField(ugettext_lazy('Point'), db_index=True)
    tellzone = ForeignKey(Tellzone, blank=True, default=None, null=True, related_name='+')
    bearing = IntegerField(ugettext_lazy('Bearing'), db_index=True)
    is_casting = BooleanField(ugettext_lazy('Is Casting?'), db_index=True, default=True)
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, default=now, db_index=True)

    objects = GeoManager()

    class Meta:

        db_table = 'api_locations'
        ordering = (
            'user',
            '-timestamp',
        )
        verbose_name = 'User Location'
        verbose_name_plural = 'User Locations'


class UserTellzone(Model):

    user = ForeignKey(User, related_name='tellzones')
    tellzone = ForeignKey(Tellzone, related_name='users')
    viewed_at = DateTimeField(ugettext_lazy('Viewed At'), blank=True, db_index=True, null=True)
    favorited_at = DateTimeField(ugettext_lazy('Favorited At'), blank=True, db_index=True, null=True)

    class Meta:

        db_table = 'api_users_tellzones'
        ordering = (
            'user',
            'tellzone',
            '-viewed_at',
            '-favorited_at',
        )
        verbose_name = 'User Tellzone'
        verbose_name_plural = 'User Tellzones'


class UserOffer(Model):

    user = ForeignKey(User, related_name='offers')
    offer = ForeignKey(Offer, related_name='users')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, default=now, db_index=True)

    class Meta:

        db_table = 'api_users_offers'
        ordering = (
            'user',
            'offer',
            '-timestamp',
        )
        verbose_name = 'User Offer'
        verbose_name_plural = 'User Offers'


class DeviceAPNS(Model):

    user = ForeignKey(User, related_name='+')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    device_id = UUIDField(db_index=True, max_length=255, name=ugettext_lazy('Device ID'))
    registration_id = CharField(ugettext_lazy('Registration ID'), db_index=True, max_length=255)

    class Meta:
        db_table = 'api_devices_apns'
        ordering = (
            'id',
        )
        verbose_name = 'APNS Device'
        verbose_name_plural = 'APNS Devices'

    def send_message(self, extra):
        return apns_send_message(self.registration_id, extra)


class DeviceGCM(Model):

    user = ForeignKey(User, related_name='+')
    name = CharField(ugettext_lazy('Name'), db_index=True, max_length=255)
    device_id = HexIntegerField(ugettext_lazy('Device ID'), db_index=True, max_length=255)
    registration_id = TextField(ugettext_lazy('Registration ID'), db_index=True, max_length=255)

    class Meta:
        db_table = 'api_devices_gcm'
        ordering = (
            'id',
        )
        verbose_name = 'GCM Device'
        verbose_name_plural = 'GCM Devices'

    def send_message(self, data):
        return gcm_send_message(self.registration_id, data)


class MasterTell(Model):

    created_by = ForeignKey(User, related_name='+')
    owned_by = ForeignKey(User, related_name='master_tells')
    is_visible = BooleanField(ugettext_lazy('Is Visible?'), db_index=True, default=True)
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

    class Meta:

        db_table = 'api_master_tells'
        ordering = (
            'owned_by',
            'position',
        )
        verbose_name = 'Master Tell'
        verbose_name_plural = 'Master Tells'

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return unicode(self.id)


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
    is_editable = BooleanField(ugettext_lazy('Is Editable?'), db_index=True, default=True)
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    description = TextField(ugettext_lazy('Description'), blank=True, db_index=True, null=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

    class Meta:

        db_table = 'api_slave_tells'
        ordering = (
            'owned_by',
            'master_tell',
            'position',
        )
        verbose_name = 'Slave Tell'
        verbose_name_plural = 'Slave Tells'


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
        max_length=255,
    )
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

    class Meta:

        db_table = 'api_messages'
        ordering = (
            '-inserted_at',
        )
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return str(self.type)

    def __unicode__(self):
        return unicode(self.type)


class MessageAttachment(Model):

    message = ForeignKey(Message, related_name='attachments')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:

        db_table = 'api_messages_attachments'
        ordering = (
            'message',
            'position',
        )
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'


class Tellcard(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, default=now, db_index=True)

    class Meta:
        db_table = 'api_tellcards'
        ordering = (
            'user_source',
            '-timestamp',
        )
        verbose_name = 'Tellcard'
        verbose_name_plural = 'Tellcards'


class Block(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, default=now, db_index=True)

    class Meta:
        db_table = 'api_blocks'
        ordering = (
            'user_source',
            '-timestamp',
        )
        verbose_name = 'Block'
        verbose_name_plural = 'Blocks'


class Report(Model):

    user_source = ForeignKey(User, related_name='+')
    user_destination = ForeignKey(User, related_name='+')
    timestamp = DateTimeField(ugettext_lazy('Timestamp'), auto_now_add=True, default=now, db_index=True)

    class Meta:
        db_table = 'api_reports'
        ordering = (
            'user_source',
            '-timestamp',
        )
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'


@receiver(pre_save, sender=UserPhoto)
def user_photo_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserPhoto.objects.filter(user=instance.user).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserStatusAttachment)
def user_status_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserStatusAttachment.objects.filter(
            user_status=instance.user_status,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserURL)
def user_url_pre_save(instance, **kwargs):
    if not instance.position:
        position = UserURL.objects.filter(user=instance.user).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=MasterTell)
def master_tell_pre_save(instance, **kwargs):
    if not instance.position:
        position = MasterTell.objects.filter(owned_by=instance.owned_by).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=SlaveTell)
def slave_tell_pre_save(instance, **kwargs):
    if not instance.position:
        position = SlaveTell.objects.filter(owned_by=instance.owned_by).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=MessageAttachment)
def message_attachment_pre_save(instance, **kwargs):
    if not instance.position:
        position = MessageAttachment.objects.filter(
            message=instance.message,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(post_save, sender=Block)
def block_post_save(instance, **kwargs):
    Tellcard.objects.filter(
        Q(user_source_id=instance.user_source.id, user_destination_id=instance.user_destination.id) |
        Q(user_source_id=instance.user_destination.id, user_destination_id=instance.user_source.id),
    ).delete()

user_logged_in.disconnect(update_last_login)


def __str__(self):
    return '%(first_name)s %(last_name)s (%(email)s)' % {
        'email': self.email,
        'first_name': self.first_name,
        'last_name': self.last_name,
    }

Administrator.__str__ = __str__


def __unicode__(self):
    return u'%(first_name)s %(last_name)s (%(email)s)' % {
        'email': self.email,
        'first_name': self.first_name,
        'last_name': self.last_name,
    }

Administrator.__unicode__ = __unicode__

Administrator._meta.get_field('is_active').verbose_name = ugettext_lazy('Active?')
Administrator._meta.get_field('is_staff').verbose_name = ugettext_lazy('Staff?')
Administrator._meta.get_field('is_superuser').verbose_name = ugettext_lazy('Superuser?')
Administrator._meta.get_field('last_login').verbose_name = ugettext_lazy('Last Signed In At')
Administrator._meta.verbose_name = ugettext_lazy('administrator')
Administrator._meta.verbose_name_plural = ugettext_lazy('administrators')


def __str__(self):
    return '%(provider)s - %(uid)s' % {
        'provider': self.provider,
        'uid': self.uid,
    }

UserSocialAuth.__str__ = __str__


def __unicode__(self):
    return u'%(provider)s - %(uid)s' % {
        'provider': self.provider,
        'uid': self.uid,
    }

UserSocialAuth.__unicode__ = __unicode__

UserSocialAuth._meta.get_field('extra_data').verbose_name = ugettext_lazy('Extra Data')
UserSocialAuth._meta.get_field('uid').verbose_name = ugettext_lazy('UID')
UserSocialAuth._meta.verbose_name = ugettext_lazy('user')
UserSocialAuth._meta.verbose_name_plural = ugettext_lazy('users')
