# -*- coding: utf-8 -*-

from rest_framework import viewsets

from models import User
from serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        is_active=True, is_staff=False, is_superuser=False,
    ).all()
    serializer_class = UserSerializer
