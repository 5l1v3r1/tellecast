# -*- coding: utf-8 -*-

from re import sub

from django.utils.translation import ugettext_lazy
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api import models


class Authentication(BaseAuthentication):

    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return
        if not token.startswith('Token'):
            return
        token = sub(r'^Token ', '', token)
        user = None
        try:
            user = models.User.objects.get(id=token.split('.')[0])
        except Exception:
            raise AuthenticationFailed(ugettext_lazy('Invalid Token'))
        if not user:
            raise AuthenticationFailed(ugettext_lazy('Invalid Token'))
        if not user.is_valid(token):
            raise AuthenticationFailed(ugettext_lazy('Invalid Token'))
        return (user, None)
