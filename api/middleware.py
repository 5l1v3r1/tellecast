# -*- coding: utf-8 -*-

from django.contrib.gis.geos import fromstr
from django.http import JsonResponse
from mixer.backend.django import mixer
from raven.contrib.django.raven_compat.models import client

mixer.register(
    'api.Tellzone',
    hours={
        'Mon': '09:00 AM to 05:00 PM',
        'Tue': '09:00 AM to 05:00 PM',
        'Wed': '09:00 AM to 05:00 PM',
        'Thu': '09:00 AM to 05:00 PM',
        'Fri': '09:00 AM to 05:00 PM',
        'Sat': '09:00 AM to 05:00 PM',
        'Sun': '09:00 AM to 05:00 PM',
    },
    point=fromstr('POINT(1.00 1.00)'),
)


class Exception(object):

    def process_exception(self, request, exception):
        client.captureException()
        return JsonResponse(
            data={
                'error': unicode(exception),
            },
            status=500,
        )


class Session(object):

    def process_request(self, request):
        if '/api/' in request.path and '/admin/' not in request.path:
            del request.session
