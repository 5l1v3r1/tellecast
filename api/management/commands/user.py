# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from api import models


class Command(BaseCommand):

    help = 'User'

    def add_arguments(self, parser):
        parser.add_argument('token', default='', nargs='?', type=str)

    def handle(self, *args, **kwargs):
        user = models.User.objects.get_queryset().filter(id=kwargs['token'].split('.')[0]).first()
        if not user:
            self.stdout.write('False', ending='')
            return
        if not user.is_valid(kwargs['token']):
            self.stdout.write('False', ending='')
            return
        self.stdout.write('True', ending='')
        return
