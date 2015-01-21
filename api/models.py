# -*- coding: utf-8 -*-

from django.contrib.auth.hashers import (
    check_password, make_password, is_password_usable,
)
from django.contrib.auth.models import update_last_login, UserManager
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.db import models
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


class Backend(object):

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass


class User(models.Model):
    email = models.EmailField(
        ugettext_lazy('Email'), db_index=True, max_length=255, unique=True
    )
    password = models.CharField(
        ugettext_lazy('Password'), db_index=True, max_length=255
    )
    first_name = models.CharField(
        ugettext_lazy('First Name'), db_index=True, max_length=255
    )
    last_name = models.CharField(
        ugettext_lazy('Last Name'), db_index=True, max_length=255
    )
    inserted_at = models.DateTimeField(
        ugettext_lazy('Inserted At'), default=timezone.now, db_index=True
    )
    updated_at = models.DateTimeField(
        ugettext_lazy('Updated At'), default=timezone.now, db_index=True
    )
    signed_in_at = models.DateTimeField(
        ugettext_lazy('Signed In At'), default=timezone.now, db_index=True
    )
    is_staff = models.BooleanField(
        ugettext_lazy('Is Staff?'), default=False, db_index=True
    )
    is_superuser = models.BooleanField(
        ugettext_lazy('Is Superuser?'), default=False, db_index=True
    )
    is_active = models.BooleanField(
        ugettext_lazy('Is Active?'), default=True, db_index=True
    )

    objects = UserManager()

    REQUIRED_FIELDS = ['password', 'first_name', 'last_name', ]
    USERNAME_FIELD = 'email'

    class Meta:
        abstract = False
        verbose_name = ugettext_lazy('user')
        verbose_name_plural = ugettext_lazy('users')

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


def update_signed_in_at(sender, user, **kwargs):
    user.signed_in_at = timezone.now()
    user.save(update_fields=['signed_in_at'])

user_logged_in.connect(update_signed_in_at)

user_logged_in.disconnect(update_last_login)
