# -*- coding: utf-8 -*-

from django.contrib.auth.models import UserManager
from django.utils.timezone import now


class User(UserManager):

    def _create_user(
        self,
        email,
        password,
        is_staff,
        is_superuser,
        **kwargs
    ):
        now_ = now()
        if not email:
            raise ValueError('Invalid Email')
        user = self.model(
            email=email,
            inserted_at=now_,
            updated_at=now_,
            signed_in_at=now_,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        return self._create_user(email, password, True, True, **kwargs)

    def create_user(self, email, password, **kwargs):
        return self._create_user(email, password, False, False, **kwargs)
