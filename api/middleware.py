# -*- coding: utf-8 -*-

from traceback import print_exc

from django.http import JsonResponse
from rollbar import report_exc_info


class Exception(object):

    def process_exception(self, request, exception):
        print_exc()
        report_exc_info()
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
