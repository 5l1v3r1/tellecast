# -*- coding: utf-8 -*-

from api import models


class Backend(object):

    def authenticate(self, username=None, password=None):
        try:
            user = models.User.objects.get(email=username)
            if user.check_password(password):
                return user
        except models.User.DoesNotExist:
            pass

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            pass
