# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import environ

from celery import Celery
from django.conf import settings
from ujson import dumps

environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from api import models  # noqa

tasks = Celery('api')
tasks.config_from_object('django.conf:settings')
tasks.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@tasks.task
def push_notifications(user_id, json):
    for device in models.DeviceAPNS.objects.filter(user_id=user_id).order_by('id').all():
        try:
            device.send_message(dumps(json))
        except Exception:
            from traceback import print_exc
            print_exc()
    for device in models.DeviceGCM.objects.filter(user_id=user_id).order_by('id').all():
        try:
            device.send_message(json)
        except Exception:
            from traceback import print_exc
            print_exc()
