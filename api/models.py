# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable,
)
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    ForeignKey,
    IntegerField,
    Max,
    Model,
    OneToOneField,
    TextField,
)
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy
from rest_framework.authtoken.models import Token

from api import managers


class MasterTell(Model):
    created_by = ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    owned_by = ForeignKey(
        settings.AUTH_USER_MODEL, related_name='master_tells',
    )
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=now,
        db_index=True,
    )
    updated_at = DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=now,
        db_index=True,
    )

    class Meta:
        db_table = 'api_master_tells'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'master tell'
        verbose_name_plural = 'master tells'


class SlaveTell(Model):
    master_tell = ForeignKey(MasterTell, related_name='slave_tells')
    created_by = ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    owned_by = ForeignKey(settings.AUTH_USER_MODEL, related_name='slave_tells')
    photo = CharField(
        ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255,
    )
    first_name = CharField(
        ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255,
    )
    last_name = CharField(
        ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255,
    )
    type = CharField(ugettext_lazy('Type'), db_index=True, max_length=255)
    contents = TextField(ugettext_lazy('Contents'), db_index=True)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=now,
        db_index=True,
    )
    updated_at = DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=now,
        db_index=True,
    )

    class Meta:
        db_table = 'api_slave_tells'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'slave tell'
        verbose_name_plural = 'slave tells'


class User(Model):
    email = EmailField(
        ugettext_lazy('Email'), db_index=True, max_length=255, unique=True,
    )
    password = CharField(
        ugettext_lazy('Password'), db_index=True, max_length=255,
    )
    photo = CharField(
        ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255,
    )
    first_name = CharField(
        ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255,
    )
    last_name = CharField(
        ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255,
    )
    location = CharField(
        ugettext_lazy('Location'), blank=True, db_index=True, max_length=255,
    )
    description = TextField(
        ugettext_lazy('Description'), blank=True, db_index=True,
    )
    phone = CharField(
        ugettext_lazy('Phone'), blank=True, db_index=True, max_length=255,
    )
    inserted_at = DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=now,
        db_index=True,
    )
    updated_at = DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=now,
        db_index=True,
    )
    signed_in_at = DateTimeField(
        ugettext_lazy('Signed In At'), default=now, db_index=True,
    )
    is_staff = BooleanField(
        ugettext_lazy('Is Staff?'), default=False, db_index=True,
    )
    is_superuser = BooleanField(
        ugettext_lazy('Is Superuser?'), default=False, db_index=True,
    )
    is_active = BooleanField(
        ugettext_lazy('Is Active?'), default=True, db_index=True,
    )

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = managers.User()

    class Meta:
        db_table = 'api_users'
        ordering = ('-inserted_at', )
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.get_username()

    def check_password(self, password):

        def setter(password):
            self.set_password(password)
            self.save(update_fields=['password'])

        return check_password(password, self.password, setter)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def natural_key(self):
        return (self.get_username(), )

    def get_full_name(self):
        return '%(first_name)s %(last_name)s' % {
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def get_token(self):
        try:
            return self.auth_token
        except ObjectDoesNotExist:
            pass
        return Token.objects.create(user=self)

    def set_password(self, password):
        self.password = make_password(password)

    def get_session_auth_hash(self):
        return salted_hmac(
            'django.contrib.auth.models.AbstractBaseUser.'
            'get_session_auth_hash',
            self.password
        ).hexdigest()

    def get_short_name(self):
        return self.first_name

    def get_username(self):
        return getattr(self, self.USERNAME_FIELD)

    def set_unusable_password(self):
        self.password = make_password(None)

    def has_module_perms(self, *args, **kwargs):
        if self.is_active:
            return True

    def has_perm(self, permission, object=None):
        if self.is_staff:
            return True
        if self.is_superuser:
            return True
        if not self.is_active:
            if isinstance(object, User):
                return object.id == self.id
            if isinstance(object, UserStatus):
                return object.user_id == self.id
            if isinstance(object, UserStatusAttachment):
                return object.user_status.user_id == self.id
            if isinstance(object, UserURL):
                return object.user_id == self.id
            if isinstance(object, UserPhoto):
                return object.user_id == self.id
            if isinstance(object, UserSocialProfile):
                return object.user_id == self.id
            if isinstance(object, MasterTell):
                return object.owned_by == self.id
            if isinstance(object, SlaveTell):
                return object.owned_by == self.id

    def has_perms(self, permissions, object=None):
        for permission in permissions:
            if not self.has_perm(permission, object):
                return False

    def has_usable_password(self):
        return is_password_usable(self.password)

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


class UserPhoto(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL, related_name='photos')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_photos'
        ordering = ('position', )
        verbose_name = 'user photo'
        verbose_name_plural = 'user photos'


class UserSocialProfile(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL, related_name='social_profiles')
    netloc = CharField(
        ugettext_lazy('Network Location'), db_index=True, max_length=255,
    )
    url = CharField(ugettext_lazy('URL'), db_index=True, max_length=255)

    class Meta:
        db_table = 'api_users_social_profiles'
        get_latest_by = 'netloc'
        ordering = ('netloc', )
        verbose_name = 'user social profile'
        verbose_name_plural = 'user social profiles'


class UserStatus(Model):
    user = OneToOneField(settings.AUTH_USER_MODEL, related_name='status')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    title = CharField(ugettext_lazy('Title'), db_index=True, max_length=255)
    url = CharField(
        ugettext_lazy('URL'), blank=True, db_index=True, max_length=255,
    )
    notes = TextField(ugettext_lazy('Notes'), blank=True, db_index=True)

    class Meta:
        db_table = 'api_users_statuses'
        get_latest_by = 'id'
        ordering = ('id', )
        verbose_name = 'user status'
        verbose_name_plural = 'user statuses'


class UserStatusAttachment(Model):
    user_status = ForeignKey(
        UserStatus, db_column='user_status_id', related_name='attachments',
    )
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_statuses_attachments'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'user status attachment'
        verbose_name_plural = 'user status attachments'


class UserURL(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL, related_name='urls')
    string = CharField(ugettext_lazy('String'), db_index=True, max_length=255)
    position = IntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_urls'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'user url'
        verbose_name_plural = 'user urls'

user_logged_in.disconnect(update_last_login)


@receiver(pre_save, sender=MasterTell)
def pre_save_master_tell(instance, **kwargs):
    if not instance.position:
        position = MasterTell.objects.filter(
            owned_by=instance.owned_by,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=SlaveTell)
def pre_save_slave_tell(instance, **kwargs):
    if not instance.position:
        position = SlaveTell.objects.filter(
            owned_by=instance.owned_by,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserPhoto)
def pre_save_user_photo(instance, **kwargs):
    if not instance.position:
        position = UserPhoto.objects.filter(
            user=instance.user,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserStatusAttachment)
def pre_save_user_status_attachment(instance, **kwargs):
    if not instance.position:
        position = UserStatusAttachment.objects.filter(
            status=instance.status,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(pre_save, sender=UserURL)
def pre_save_user_url(instance, **kwargs):
    if not instance.position:
        position = UserURL.objects.filter(
            user=instance.user,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


@receiver(user_logged_in, sender=User)
def update_signed_in_at(user, **kwargs):
    user.signed_in_at = now()
    user.save(update_fields=['signed_in_at'])
