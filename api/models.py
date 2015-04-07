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
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy
from itsdangerous import TimestampSigner
from social.apps.django_app.default.models import UserSocialAuth


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
    inserted_at = DateTimeField(ugettext_lazy('Inserted At'), auto_now_add=True, default=now, db_index=True)
    updated_at = DateTimeField(ugettext_lazy('Updated At'), auto_now=True, default=now, db_index=True)

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
        if isinstance(object, MasterTell):
            return object.owned_by.id == self.id
        if isinstance(object, SlaveTell):
            return object.owned_by.id == self.id

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
        return self.string


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


class MasterTell(Model):

    created_by = ForeignKey(User, related_name='+')
    owned_by = ForeignKey(User, related_name='master_tells')
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
    user_destination = ForeignKey(User, related_name='+')
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
