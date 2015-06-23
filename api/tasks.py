# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy
from os import environ
from traceback import print_exc

from celery import Celery
from django.conf import settings
from rollbar import report_exc_info

environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from api import models  # noqa

celery = Celery('api.tasks')
celery.conf.update(
    BROKER_POOL_LIMIT=0,
    CELERY_ACCEPT_CONTENT=[
        'json',
    ],
    CELERY_ACKS_LATE=True,
    CELERY_IGNORE_RESULT=True,
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TASK_SERIALIZER='json',
    CELERYD_LOG_FORMAT='[%(asctime)s: %(levelname)s] %(message)s',
    CELERYD_POOL_RESTARTS=True,
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERYD_TASK_SOFT_TIME_LIMIT=3600,
    CELERYD_TASK_TIME_LIMIT=7200,
)
celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@celery.task
def push_notifications(user_id, json):
    for device in models.DeviceAPNS.objects.get_queryset().filter(user_id=user_id):
        try:
            device.send_message(deepcopy(json))
        except Exception:
            print_exc()
            report_exc_info()
    for device in models.DeviceGCM.objects.get_queryset().filter(user_id=user_id):
        try:
            device.send_message(deepcopy(json))
        except Exception:
            print_exc()
            report_exc_info()
