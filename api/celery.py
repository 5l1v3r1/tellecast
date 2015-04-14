# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import environ

from celery import Celery
from django.conf import settings
from ujson import dumps

environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

tasks = Celery('api')
tasks.config_from_object('django.conf:settings')
tasks.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@tasks.task
def push_notifications(id):
    from api import models, serializers
    message = models.Message.objects.filter(id=id).first()
    if not message:
        return
    for device in models.DeviceAPNS.objects.filter(user_id=message.user_destination_id).order_by('id').all():
        try:
            device.send_message(dumps(serializers.Message(message).data))
        except Exception:
            from traceback import print_exc
            print_exc()
    for device in models.DeviceGCM.objects.filter(user_id=message.user_destination_id).order_by('id').all():
        try:
            device.send_message(serializers.Message(message).data)
        except Exception:
            from traceback import print_exc
            print_exc()
