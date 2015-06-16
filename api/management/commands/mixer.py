# -*- coding: utf-8 -*-

from django.contrib.gis.geos import fromstr
from django.core.management.base import BaseCommand
from django.utils.functional import cached_property

from api import middleware, models


class Command(BaseCommand):

    help = 'Mixer'

    @cached_property
    def point(self):
        return fromstr('POINT(1.00 1.00)')

    def handle(self, *args, **kwargs):
        models.Ad.objects.get_queryset().delete()
        models.Tellzone.objects.get_queryset().delete()
        models.User.objects.get_queryset().delete()

        middleware.mixer.cycle(10).blend('api.Ad')

        for tellzone in middleware.mixer.cycle(10).blend('api.Tellzone'):
            tellzone.point = self.point
            tellzone.save()

        for user in middleware.mixer.cycle(10).blend('api.User'):
            user.point = self.point
            user.is_signed_in = True
            user.save()
            self.user_location(user)

        for email in [
            'bradotts@gmail.com',
            'callmejerms@aol.com',
            'fl@fernandoleal.me',
            'kevin@tellecast.com',
            'mbatchelder13@yahoo.com',
        ]:
            user = middleware.mixer.blend('api.User', email=email)
            user.point = self.point
            user.is_signed_in = True
            user.save()
            self.user_location(user)

    def user_location(self, user):
        models.UserLocation.objects.create(
            user_id=user.id,
            tellzone_id=models.Tellzone.objects.get_queryset().order_by('?').first().id,
            point=self.point,
            accuracies_horizontal=0.00,
            accuracies_vertical=0.00,
            bearing=0,
            is_casting=True,
        )
