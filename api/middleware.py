# -*- coding: utf-8 -*-

from django.http import JsonResponse


class ExceptionMiddleware(object):

    def process_exception(self, request, exception):
        from traceback import print_exc
        print_exc()
        return JsonResponse(
            data={
                'error': unicode(exception),
            },
            status=500,
        )
