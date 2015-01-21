# -*- coding: utf-8 -*-

from rest_framework import serializers

from models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        fields = (
            'id',
            'email',
            'photo',
            'first_name',
            'last_name',
            'location',
            'description',
            'phone',
            'inserted_at',
            'updated_at',
            'signed_in_at',
        )
        model = User
