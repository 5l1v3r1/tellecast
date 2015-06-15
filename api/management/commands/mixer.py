# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from api import middleware, models


class Command(BaseCommand):

    help = 'Mixer'

    def handle(self, *args, **kwargs):
        models.Ad.objects.get_queryset().delete()

        middleware.mixer.cycle(100).blend('api.Ad')
