# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable,
)
from django.contrib.auth.models import update_last_login, UserManager
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.db import models
from django.db.models import Max
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy


class UserManager(UserManager):

    def _create_user(
        self,
        email,
        password,
        first_name,
        last_name,
        is_staff,
        is_superuser,
        **kwargs
    ):
        now = timezone.now()
        if not email:
            raise ValueError('Invalid Email')
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            inserted_at=now,
            updated_at=now,
            signed_in_at=now,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, password, first_name, last_name, **kwargs
    ):
        return self._create_user(
            email, password, first_name, last_name, True, True, **kwargs
        )

    def create_user(
        self, email, password, first_name, last_name, **kwargs
    ):
        return self._create_user(
            email, password, first_name, last_name, False, False, **kwargs
        )


class User(models.Model):
    email = models.EmailField(
        ugettext_lazy('Email'), db_index=True, max_length=255, unique=True,
    )
    password = models.CharField(
        ugettext_lazy('Password'), db_index=True, max_length=255,
    )
    photo = models.CharField(
        ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255,
    )
    first_name = models.CharField(
        ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255,
    )
    last_name = models.CharField(
        ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255,
    )
    location = models.CharField(
        ugettext_lazy('Location'), blank=True, db_index=True, max_length=255,
    )
    description = models.TextField(
        ugettext_lazy('Description'), blank=True, db_index=True,
    )
    phone = models.CharField(
        ugettext_lazy('Phone'), blank=True, db_index=True, max_length=255,
    )
    inserted_at = models.DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=timezone.now,
        db_index=True,
    )
    signed_in_at = models.DateTimeField(
        ugettext_lazy('Signed In At'), default=timezone.now, db_index=True,
    )
    is_staff = models.BooleanField(
        ugettext_lazy('Is Staff?'), default=False, db_index=True,
    )
    is_superuser = models.BooleanField(
        ugettext_lazy('Is Superuser?'), default=False, db_index=True,
    )
    is_active = models.BooleanField(
        ugettext_lazy('Is Active?'), default=True, db_index=True,
    )

    REQUIRED_FIELDS = [
        'password',
        'photo',
        'first_name',
        'last_name',
        'location',
        'description',
        'phone',
    ]
    USERNAME_FIELD = 'email'

    objects = UserManager()

    class Meta:
        db_table = 'api_users'
        ordering = ('-inserted_at', )
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.get_username()

    def check_password(self, raw_password):

        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=['password'])

        return check_password(raw_password, self.password, setter)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def natural_key(self):
        return (self.get_username(),)

    def get_full_name(self):
        return '%(first_name)s %(last_name)s' % {
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

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

    def has_module_perms(self, app_label):
        if self.is_active:
            return True

    def has_perm(self, perm, obj=None):
        if self.is_active:
            return True

    def has_perms(self, perm_list, obj=None):
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False

    def has_usable_password(self):
        return is_password_usable(self.password)

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


class UserPhoto(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='photos')
    string = models.CharField(
        ugettext_lazy('String'), db_index=True, max_length=255,
    )
    position = models.BigIntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_photos'
        ordering = ('position', )
        verbose_name = 'user photo'
        verbose_name_plural = 'user photos'


class UserSocialProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='social_profiles',
    )
    netloc = models.CharField(
        ugettext_lazy('Network Location'), db_index=True, max_length=255,
    )
    url = models.CharField(
        ugettext_lazy('URL'), db_index=True, max_length=255,
    )

    class Meta:
        db_table = 'api_users_social_profiles'
        get_latest_by = 'netloc'
        ordering = ('netloc', )
        verbose_name = 'user social profile'
        verbose_name_plural = 'user social profiles'


class UserStatus(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='status',
    )
    string = models.CharField(
        ugettext_lazy('String'), db_index=True, max_length=255,
    )
    title = models.CharField(
        ugettext_lazy('Title'), db_index=True, max_length=255,
    )
    url = models.CharField(
        ugettext_lazy('URL'), blank=True, db_index=True, max_length=255,
    )
    notes = models.TextField(ugettext_lazy('Notes'), blank=True, db_index=True)

    class Meta:
        db_table = 'api_users_statuses'
        get_latest_by = 'id'
        ordering = ('id', )
        verbose_name = 'user status'
        verbose_name_plural = 'user statuses'


class UserStatusAttachment(models.Model):
    status = models.ForeignKey(
        UserStatus, db_column='user_status_id', related_name='attachments',
    )
    string = models.CharField(
        ugettext_lazy('String'), db_index=True, max_length=255,
    )
    position = models.BigIntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_statuses_attachments'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'user status attachment'
        verbose_name_plural = 'user status attachments'


class UserUrl(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='urls')
    string = models.CharField(
        ugettext_lazy('String'), db_index=True, max_length=255,
    )
    position = models.BigIntegerField(ugettext_lazy('Position'), db_index=True)

    class Meta:
        db_table = 'api_users_urls'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'user url'
        verbose_name_plural = 'user urls'


class MasterTell(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='master_tells',
    )
    contents = models.TextField(ugettext_lazy('Contents'), db_index=True)
    position = models.BigIntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = models.DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        db_table = 'api_master_tells'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'master tell'
        verbose_name_plural = 'master tells'


class SlaveTell(models.Model):
    master_tell = models.ForeignKey(MasterTell, related_name='slave_tells')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='slave_tells',
    )
    photo = models.CharField(
        ugettext_lazy('Photo'), blank=True, db_index=True, max_length=255,
    )
    first_name = models.CharField(
        ugettext_lazy('First Name'), blank=True, db_index=True, max_length=255,
    )
    last_name = models.CharField(
        ugettext_lazy('Last Name'), blank=True, db_index=True, max_length=255,
    )
    type = models.CharField(
        ugettext_lazy('Type'), db_index=True, max_length=255,
    )
    contents = models.TextField(ugettext_lazy('Contents'), db_index=True)
    position = models.BigIntegerField(ugettext_lazy('Position'), db_index=True)
    inserted_at = models.DateTimeField(
        ugettext_lazy('Inserted At'),
        auto_now_add=True,
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        ugettext_lazy('Updated At'),
        auto_now=True,
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        db_table = 'api_slave_tells'
        get_latest_by = 'position'
        ordering = ('position', )
        verbose_name = 'slave tell'
        verbose_name_plural = 'slave tells'

user_logged_in.disconnect(update_last_login)


@receiver(user_logged_in, sender=User)
def update_signed_in_at(user, **kwargs):
    user.signed_in_at = timezone.now()
    user.save(update_fields=['signed_in_at'])


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


@receiver(pre_save, sender=UserUrl)
def pre_save_user_url(instance, **kwargs):
    if not instance.position:
        position = UserUrl.objects.filter(
            user=instance.user,
        ).aggregate(Max('position'))['position__max']
        instance.position = position + 1 if position else 1


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
