# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from api import models


class Command(BaseCommand):

    help = 'Users'

    def handle(self, *args, **kwargs):
        for user in models.User.objects.get_queryset().filter(tellzone_id__isnull=False).order_by('id').all():
            if not user.is_signed_in:
                user.is_signed_in = True
                user.save()
            network = user.tellzone.networks_tellzones.get_queryset().order_by('network_id').first()
            models.UserLocation.objects.create(
                user_id=user.id,
                network_id=network.id if network else None,
                tellzone_id=user.tellzone.id,
                location=None,
                point=user.tellzone.point,
                accuracies_horizontal=0.0,
                accuracies_vertical=0.0,
                bearing=0,
                is_casting=True,
            )
