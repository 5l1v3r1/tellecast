# -*- coding: utf-8 -*-

from contextlib import closing
from datetime import date, datetime, timedelta
from math import atan2, cos, pi, sin, sqrt
from random import randint, uniform

from arrow import get
from celery import current_app
from django.conf import settings
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy
from geopy.distance import vincenty
from numpy import mean
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN,
)
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from social.apps.django_app.default.models import DjangoStorage
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import loads

from api import models, serializers
from api.algorithms.clusters import get_clusters


class Blocks(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Blocks

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.BlocksResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.BlocksResponse(
                models.Block.objects.get_queryset().filter(user_source_id=self.request.user.id),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Blocks

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: mandatory

        + report
            - Type: boolean (default = False)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.BlocksRequest
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.BlocksRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.insert_or_update()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def delete(self, request):
        '''
        DELETE Blocks

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.BlocksRequest
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.BlocksRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)


class DevicesAPNS(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Devices :: APNS

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.DevicesAPNSResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.DevicesAPNSResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT/UPDATE Devices :: APNS

        <pre>
        Input
        =====

        + name
            - Type: string
            - Status: mandatory

        + device_id
            - Type: UUID
            - Status: mandatory

        + registration_id
            - Type: string
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.DevicesAPNSRequest
        response_serializer: api.serializers.DevicesAPNSResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.DevicesAPNSRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.DevicesAPNSResponse(
                serializer.insert_or_update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def delete(self, request, id):
        '''
        DELETE Devices :: APNS

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        devices_apns = self.get_queryset().filter(id=id).first()
        if not devices_apns:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        devices_apns.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_queryset(self):
        return models.DeviceAPNS.objects.get_queryset().filter(user_id=self.request.user.id)


class DevicesGCM(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Devices :: GCM

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.DevicesGCMResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.DevicesGCMResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT/UPDATE Devices :: GCM

        <pre>
        Input
        =====

        + name
            - Type: string
            - Status: mandatory

        + device_id
            - Type: UUID
            - Status: mandatory

        + registration_id
            - Type: string
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.DevicesGCMRequest
        response_serializer: api.serializers.DevicesGCMResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.DevicesGCMRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.DevicesGCMResponse(
                serializer.insert_or_update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def delete(self, request, id):
        '''
        DELETE Devices :: GCM

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        devices_gcm = self.get_queryset().filter(id=id).first()
        if not devices_gcm:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        devices_gcm.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_queryset(self):
        return models.DeviceGCM.objects.get_queryset().filter(user_id=self.request.user.id)


class MasterTells(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Master Tells

        <pre>
        Input
        =====

        + inserted_at
            - Type: datetime
            - Status: optional

        + updated_at
            - Type: datetime
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: inserted_at
              paramType: query
              type: datetime
            - name: updated_at
              paramType: query
              type: datetime
        response_serializer: api.serializers.MasterTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.MasterTellsResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Master Tells

        <pre>
        Input
        =====

        + contents
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTellsRequest
        response_serializer: api.serializers.MasterTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.MasterTellsRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.MasterTellsResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def put(self, request, id):
        '''
        UPDATE Master Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + contents
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTellsRequest
        response_serializer: api.serializers.MasterTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.MasterTellsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.MasterTellsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def patch(self, request, id):
        '''
        UPDATE Master Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + contents
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTellsRequest
        response_serializer: api.serializers.MasterTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.MasterTellsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.MasterTellsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Master Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_instance(self, id):
        return self.get_queryset().filter(id=id).first()

    def get_queryset(self):
        queryset = models.MasterTell.objects.get_queryset().filter(owned_by_id=self.request.user.id)
        inserted_at = self.request.QUERY_PARAMS.get('inserted_at', None)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
        updated_at = self.request.QUERY_PARAMS.get('updated_at', None)
        if updated_at:
            queryset = queryset.filter(updated_at__gte=updated_at)
        return queryset


class Messages(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Messages

        <pre>
        Input
        =====

        + recent
            Type: boolean (default = True)
            Status: optional
            Choices:
                - True
                - False
            Notes:
                - Python evaluates `'False'` (string) to `True` (boolean).
                - In order to pass `recent=False`, please use `recent=` (empty value).
            Examples:
                - `recent=True` is evaluated as `recent=True`
                - `recent=true` is evaluated as `recent=True`
                - `recent=t` is evaluated as `recent=True`
                - `recent=False` is evaluated as `recent=True`
                - `recent=false` is evaluated as `recent=True`
                - `recent=f` is evaluated as `recent=True`
                - `recent=` is evaluated as `recent=False`
                - `` is evaluated as `recent=False`

        + user_id
            Description: If supplied, all messages will pertain to this `user_id`. Only applicable if
            `recent` = False.
            Type: integer
            Status: optional

        + user_status_id
            Description: If supplied, all messages will pertain to this `user_status_id`. Only applicable if
            `recent` = False.
            Type: integer
            Status: optional

        + master_tell_id
            Description: If supplied, all messages will pertain to this `master_tell_id`. Only applicable if
            `recent` = False.
            Type: integer
            Status: optional

        + since_id
            Description: (similar to how it works in all major APIs; Example: twitter.com) Only applicable if
            `recent` = False.
            Type: integer
            Status: optional

        + max_id
            Description: (similar to how it works in all major APIs; Example: twitter.com) Only applicable if
            `recent` = False.
            Type: integer
            Status: optional

        + limit
            Description: Only applicable if `recent` = False.
            Type: integer (default = 100)
            Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: recent
              paramType: query
              type: string
            - name: user_id
              paramType: query
              type: integer
            - name: user_status_id
              paramType: query
              type: integer
            - name: master_tell_id
              paramType: query
              type: integer
            - name: since_id
              paramType: query
              type: integer
            - name: max_id
              paramType: query
              type: integer
            - name: limit
              paramType: query
              type: integer
        response_serializer: api.serializers.MessagesGetResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        messages = []
        if request.query_params.get('recent', True):
            for user in models.User.objects.get_queryset().exclude(id=request.user.id):
                message = models.Message.objects.get_queryset().filter(
                    Q(user_source_id=request.user.id, user_destination_id=user.id) |
                    Q(user_source_id=user.id, user_destination_id=request.user.id),
                ).order_by(
                    '-inserted_at',
                ).first()
                if message:
                    messages.append(message)
            messages = sorted(messages, key=lambda message: message.inserted_at, reverse=True)
        else:
            query = models.Message.objects.get_queryset().filter(
                Q(user_source_id=request.user.id) | Q(user_destination_id=request.user.id),
            )
            user_id = request.query_params.get('user_id', None)
            if user_id:
                query = query.filter(Q(user_source_id=user_id) | Q(user_destination_id=user_id))
            user_status_id = request.query_params.get('user_status_id', None)
            if user_status_id:
                query = query.filter(user_status_id=user_status_id)
            master_tell_id = request.query_params.get('master_tell_id', None)
            if master_tell_id:
                query = query.filter(master_tell_id=master_tell_id)
            since_id = 0
            try:
                since_id = int(request.query_params.get('since_id', '0'))
            except Exception:
                pass
            if since_id:
                query = query.filter(id__gt=since_id)
            max_id = 0
            try:
                max_id = int(request.query_params.get('max_id', '0'))
            except Exception:
                pass
            if max_id:
                query = query.filter(id__lt=max_id)
            limit = 100
            try:
                limit = int(request.query_params.get('limit', '100'))
            except Exception:
                pass
            for message in query.order_by('-inserted_at')[:limit]:
                messages.append(message)
        return Response(
            data=serializers.MessagesGetResponse(
                messages,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Messages

        <pre>
        Input
        =====

        + user_source_is_hidden
            - Type: boolean (default = False)
            - Status: optional

        + user_destination_id
            - Type: integer
            - Status: mandatory

        + user_destination_is_hidden
            - Type: boolean (default = False)
            - Status: optional

        + user_status_id
            - Type: integer
            - Status: optional

        + master_tell_id
            - Type: integer
            - Status: optional

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - Message
                - Request
                - Response - Accepted
                - Response - Blocked
                - Response - Deferred
                - Response - Rejected

        + contents
            - Type: string
            - Status: mandatory

        + status
            - Type: string
            - Status: mandatory
            - Choices:
                - Read
                - Unread

        + attachments
            - Type: list
            - Status: optional

            Example:

            [
                {
                    "string": "...",
                    "position": 1,
                },
                ...,
                {
                    "string": "...",
                    "position": n,
                },
            ]

        Output
        ======

        (see below; "Response Class" -> "Model Schema")

        Push Notification
        =================

        {
            'alert': {
                'body': '{{ body }}',
                'title': 'New message from user',
            },
            'badge': {{ total_number_of_unread_notifications }},
            'type': 'message',
        }
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MessagesPostRequest
        response_serializer: api.serializers.MessagesPostResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.MessagesPostRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        if is_blocked(request.user.id, serializer.validated_data['user_destination_id']):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if request.user.id == serializer.validated_data['user_destination_id']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if not models.Message.objects.get_queryset().filter(
            Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_destination_id']) |
            Q(user_source_id=serializer.validated_data['user_destination_id'], user_destination_id=request.user.id),
            type__in=[
                'Response - Accepted',
                'Response - Deferred',
                'Response - Rejected',
                'Message',
            ],
        ).count():
            message = models.Message.objects.get_queryset().filter(
                Q(
                    user_source_id=request.user.id,
                    user_destination_id=serializer.validated_data['user_destination_id'],
                ) |
                Q(
                    user_source_id=serializer.validated_data['user_destination_id'],
                    user_destination_id=request.user.id,
                ),
            ).order_by(
                '-inserted_at',
            ).first()
            if message:
                if message.user_source_id == request.user.id:
                    if message.type == 'Request' and serializer.validated_data['type'] == 'Message':
                        return Response(status=HTTP_403_FORBIDDEN)
                    if message.type == 'Response - Blocked':
                        return Response(status=HTTP_403_FORBIDDEN)
                if message.user_destination_id == request.user.id:
                    if message.type == 'Request' and serializer.validated_data['type'] == 'Message':
                        return Response(status=HTTP_403_FORBIDDEN)
                    if message.type == 'Response - Blocked':
                        return Response(status=HTTP_403_FORBIDDEN)
            else:
                if not serializer.validated_data['type'] == 'Request':
                    return Response(status=HTTP_403_FORBIDDEN)
        return Response(
            data=serializers.MessagesPostResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def patch(self, request, id):
        '''
        UPDATE Messages

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + user_source_is_hidden
            - Type: boolean (default = False)
            - Status: optional

        + user_destination_is_hidden
            - Type: boolean (default = False)
            - Status: optional

        + status
            - Type: string
            - Status: optional
            - Choices:
                - Read
                - Unread

        Output
        ======

        (see below; "Response Class" -> "Model Schema")

        Push Notification
        =================

        {
            'type': 'updateMessage',
        }
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MessagesPatchRequest
        response_serializer: api.serializers.MessagesPatchResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.MessagesPatchRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        if 'user_source_is_hidden' in request.data or 'user_destination_is_hidden' in request.data:
            current_app.send_task(
                'api.tasks.push_notifications',
                (
                    request.user.id,
                    {
                        'aps': {},
                        'type': 'updateMessage',
                    },
                ),
                serializer='json',
            )
        return Response(
            data=serializers.MessagesPatchResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Messages

        <pre>
        Input
        =====

        + id
            - Status: mandatory
            - Type: integer

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_instance(self, id):
        return models.Message.objects.get_queryset().filter(
            Q(user_source_id=self.request.user.id) | Q(user_destination_id=self.request.user.id),
            id=id,
        ).first()


class Notifications(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        '''
        SELECT Notifications

        <pre>
        Input
        =====

        + since_id
            Description: (similar to how it works in all major APIs; Example: twitter.com)
            Type: integer
            Status: optional

        + max_id
            Description: (similar to how it works in all major APIs; Example: twitter.com)
            Type: integer
            Status: optional

        + limit
            Type: integer (default = 50)
            Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")

        The contents column will contain a serialized dictionary based on the value of the type column.

        type = A

            + contents
                + user <- This user saved your Tellcard
                    - id
                    - first_name
                    - last_name
                    - photo

        type = B

            + contents
                + user_source <- This user shared a profile with you.
                    - id
                    - first_name
                    - last_name
                    - photo
                + user_destination <- This user's profile was shared.
                    - id
                    - first_name
                    - last_name
                    - photo

        type = G

            + contents
                + user <- This user sent an invitation to you.
                    - id
                    - first_name
                    - last_name
                    - photo
                + message
                    - id
                    - user_source_is_hidden
                    - user_destination_is_hidden
                    - user_status
                    - master_tell
                    - type
                    - contents
                    - status
                    - inserted_at
                    - updated_at
                    - attachments

        type = H

            + contents
                + user <- This user replied to your invitation.
                    - id
                    - first_name
                    - last_name
                    - photo
                + message
                    - id
                    - user_source_is_hidden
                    - user_destination_is_hidden
                    - user_status
                    - master_tell
                    - type
                    - contents
                    - status
                    - inserted_at
                    - updated_at
                    - attachments
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: since_id
              paramType: query
              type: integer
            - name: max_id
              paramType: query
              type: integer
            - name: limit
              paramType: query
              type: integer
        response_serializer: api.serializers.Notifications
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        query = models.Notification.objects.get_queryset().filter(user_id=request.user.id)
        since_id = 0
        try:
            since_id = int(request.query_params.get('since_id', '0'))
        except Exception:
            pass
        if since_id:
            query = query.filter(id__gt=since_id)
        max_id = 0
        try:
            max_id = int(request.query_params.get('max_id', '0'))
        except Exception:
            pass
        if max_id:
            query = query.filter(id__lt=max_id)
        limit = 50
        try:
            limit = int(request.query_params.get('limit', '100'))
        except Exception:
            pass
        return Response(
            data=serializers.Notifications(
                query.order_by('-timestamp')[:limit],
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        Update (status) Notifications

        <pre>
        Input
        =====

        [
            {
                "id": 1,
                "status": 'Read',
            },
            ...,
            ...,
            ...,
            {
                "id": n,
                "status": 'Read',
            }
        ]

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Notifications
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        notifications = []
        for item in request.DATA:
            notification = models.Notification.objects.get_queryset().filter(
                id=item['id'], user_id=request.user.id,
            ).first()
            if not notification:
                continue
            notification.status = item['status']
            notification.save()
            notifications.append(notification)
        return Response(
            data=serializers.Notifications(
                notifications,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )


class Radar(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        GET Radar

        <pre>
        Input
        =====

        + latitude
            - Type: float
            - Status: mandatory

        + longitude
            - Type: float
            - Status: mandatory

        + radius
            - Unit: foot
            - Type: float
            - Status: mandatory

        + widths_radar
            - Description: Width of the screen
            - Unit: `dip` (density-independent pixel) for Android; `point` for iOS
            - Type: integer
            - Status: mandatory

        + widths_group
            - Description: Width of the group (or the profile image)
            - Unit: `dip` (density-independent pixel) for Android; `point` for iOS
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: latitude
              paramType: query
              required: true
              type: number
            - name: longitude
              paramType: query
              required: true
              type: number
            - name: radius
              paramType: query
              required: true
              type: number
            - name: widths_radar
              paramType: query
              required: true
              type: number
            - name: widths_group
              paramType: query
              required: true
              type: number
        response_serializer: api.serializers.RadarGetResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.RadarGetRequest(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(raise_exception=True)
        point = get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
        users = {}
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    api_users_locations.user_id,
                    ST_AsGeoJSON(api_users_locations.point),
                    ST_Distance(
                        ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                        ST_Transform(api_users_locations.point, 2163)
                    ) * 3.28084
                FROM api_users_locations
                INNER JOIN api_users ON api_users.id = api_users_locations.user_id
                LEFT OUTER JOIN api_blocks ON
                    (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_users_locations.user_id)
                    OR
                    (api_blocks.user_source_id = api_users_locations.user_id AND api_blocks.user_destination_id = %s)
                WHERE
                    api_users_locations.user_id != %s
                    AND
                    ST_DWithin(
                        ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                        ST_Transform(api_users_locations.point, 2163),
                        %s
                    )
                    AND
                    api_users_locations.is_casting IS TRUE
                    AND
                    api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
                    AND
                    api_users.is_signed_in IS TRUE
                    AND
                    api_blocks.id IS NULL
                ORDER BY api_users_locations.timestamp DESC
                ''',
                (
                    'POINT({x} {y})'.format(x=point.x, y=point.y),
                    request.user.id,
                    request.user.id,
                    request.user.id,
                    'POINT({x} {y})'.format(x=point.x, y=point.y),
                    serializer.validated_data['radius'] * 0.3048,
                )
            )
            for record in cursor.fetchall():
                if record[0] not in users:
                    p = loads(record[1])
                    p = get_point(p['coordinates'][1], p['coordinates'][0])
                    users[record[0]] = (
                        models.User.objects.get_queryset().filter(id=record[0]).first(),
                        p,
                        self.get_degrees(point, p),
                        record[2],
                    )
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT api_users.id
                FROM api_users
                LEFT OUTER JOIN api_blocks ON
                    (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_users.id)
                    OR
                    (api_blocks.user_source_id = api_users.id AND api_blocks.user_destination_id = %s)
                WHERE
                    api_users.email = ANY('{
                        bradotts@gmail.com,
                        callmejerms@aol.com,
                        fl@fernandoleal.me,
                        kevin@tellecast.com,
                        mbatchelder13@yahoo.com
                    }'::text[])
                    AND
                    api_blocks.id IS NULL
                ORDER BY api_users.id ASC
                ''',
                (request.user.id, request.user.id,)
            )
            for record in cursor.fetchall():
                w = ((serializer.validated_data['radius'] * 0.3048) / 111300) * sqrt(uniform(0.0, 1.0))
                t = 2 * pi * uniform(0.0, 1.0)
                x = w * cos(t)
                y = w * sin(t)
                p = get_point(point.y + y, point.x + x)
                if record[0] not in users:
                    users[record[0]] = (
                        models.User.objects.get_queryset().filter(id=record[0]).first(),
                        p,
                        self.get_degrees(point, p),
                        vincenty((point.x, point.y), (p.x, p.y)).ft,
                    )
        return Response(
            data=serializers.RadarGetResponse(
                {
                    'users': self.get_containers(
                        get_clusters(
                            users.values(),
                            (
                                (serializer.validated_data['widths_group'] * serializer.validated_data['radius']) /
                                serializer.validated_data['widths_radar']
                            )
                        )
                    ),
                },
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        POST Radar

        <pre>
        Input
        =====

        + point
            - Type: dictionary (of floats)
            - Status: mandatory

            Example:

            {
                'latitude': 0.0000000000,
                'longitude': 0.0000000000,
            }

        + accuracies_horizontal
            - Type: float
            - Status: optional

        + accuracies_vertical
            - Type: float
            - Status: optional

        + tellzone_id
            - Type: integer
            - Status: optional

        + bearing
            - Type: integer
            - Status: mandatory

        + is_casting
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.RadarPostRequest
        response_serializer: api.serializers.RadarPostResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.RadarPostRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        user_location = serializer.insert()
        return Response(
            data=serializers.RadarPostResponse(
                models.Tellzone.objects.get_queryset().filter(
                    point__distance_lte=(user_location.point, D(ft=models.Tellzone.radius())),
                ).distance(
                    user_location.point,
                ),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def get_containers(self, groups):
        containers = []
        for group in groups:
            containers.append({
                'degrees': mean([item[2] for item in group]),
                'radius': mean([item[3] for item in group]),
                'items': [item[0] for item in group],
            })
        return containers

    def get_degrees(self, point_1, point_2):
        return (360 - (((atan2((point_1.y - point_2.y), (point_1.x - point_2.x)) * (180 / pi)) + 360) % 360))


class SharesUsers(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        '''
        SELECT Shares :: Users

        <pre>
        Input
        =====

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - Source (shared by me; default)
                - Destination (shared by others)

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.SharesUsersGet
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        type = request.QUERY_PARAMS['type'] if 'type' in request.QUERY_PARAMS else ''
        if not type or type not in ['Source', 'Destination']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `type`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=serializers.SharesUsersGet(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        INSERT Shares :: Users

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: optional

        + object_id
            - Description: ID of the user whose profile is being shared
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SharesUsersPostRequest
        response_serializer: api.serializers.SharesUsersPostResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.SharesUsersPostRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.SharesUsersPostResponse(
                serializer.insert().get_dictionary(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def get_queryset(self):
        if 'type' in self.request.QUERY_PARAMS:
            if self.request.QUERY_PARAMS['type'] == 'Source':
                return models.ShareUser.objects.get_queryset().filter(
                    user_source_id=self.request.user.id,
                )
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.ShareUser.objects.get_queryset().filter(
                    user_destination_id=self.request.user.id,
                )
        return models.ShareUser.objects.get_queryset().filter(user_source_id=self.request.user.id)


class SlaveTells(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Slave Tells

        <pre>
        Input
        =====

        + inserted_at
            - Type: datetime
            - Status: optional

        + updated_at
            - Type: datetime
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: inserted_at
              paramType: query
              type: datetime
            - name: updated_at
              paramType: query
              type: datetime
        response_serializer: api.serializers.SlaveTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.SlaveTellsResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Slave Tells

        <pre>
        Input
        =====

        + master_tell_id
            - Type: integer
            - Status: mandatory

        + photo
            - Type: string
            - Status: optional

        + first_name
            - Type: string
            - Status: optional

        + last_name
            - Type: string
            - Status: optional

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - application/pdf
                - audio/*
                - audio/aac
                - audio/mp4
                - audio/mpeg
                - audio/mpeg3
                - audio/x-mpeg3
                - image/*
                - image/bmp
                - image/gif
                - image/jpeg
                - image/png
                - text/plain
                - video/*
                - video/3gpp
                - video/mp4
                - video/mpeg
                - video/x-mpeg

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_editable
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTellsRequest
        response_serializer: api.serializers.SlaveTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.SlaveTellsRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.SlaveTellsResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def put(self, request, id):
        '''
        UPDATE Slave Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + master_tell_id
            - Type: integer
            - Status: mandatory

        + photo
            - Type: string
            - Status: optional

        + first_name
            - Type: string
            - Status: optional

        + last_name
            - Type: string
            - Status: optional

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - application/pdf
                - audio/*
                - audio/aac
                - audio/mp4
                - audio/mpeg
                - audio/mpeg3
                - audio/x-mpeg3
                - image/*
                - image/bmp
                - image/gif
                - image/jpeg
                - image/png
                - text/plain
                - video/*
                - video/3gpp
                - video/mp4
                - video/mpeg
                - video/x-mpeg

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_editable
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTellsRequest
        response_serializer: api.serializers.SlaveTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.SlaveTellsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.SlaveTellsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def patch(self, request, id):
        '''
        UPDATE Slave Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + master_tell_id
            - Type: integer
            - Status: mandatory

        + photo
            - Type: string
            - Status: optional

        + first_name
            - Type: string
            - Status: optional

        + last_name
            - Type: string
            - Status: optional

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - application/pdf
                - audio/*
                - audio/aac
                - audio/mp4
                - audio/mpeg
                - audio/mpeg3
                - audio/x-mpeg3
                - image/*
                - image/bmp
                - image/gif
                - image/jpeg
                - image/png
                - text/plain
                - video/*
                - video/3gpp
                - video/mp4
                - video/mpeg
                - video/x-mpeg

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_editable
            - Type: boolean (default = True)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTellsRequest
        response_serializer: api.serializers.SlaveTellsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.SlaveTellsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.SlaveTellsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Slave Tells

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''

        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_instance(self, id):
        return self.get_queryset().filter(id=id).first()

    def get_queryset(self):
        queryset = models.SlaveTell.objects.get_queryset().filter(owned_by_id=self.request.user.id)
        inserted_at = self.request.QUERY_PARAMS.get('inserted_at', None)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
        updated_at = self.request.QUERY_PARAMS.get('updated_at', None)
        if updated_at:
            queryset = queryset.filter(updated_at__gte=updated_at)
        return queryset


class Tellcards(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        '''
        SELECT Tellcards

        <pre>
        Input
        =====

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - Source (saved by me; default)
                - Destination (saved by others)

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: type
              paramType: query
              required: true
              type: string
        response_serializer: api.serializers.TellcardsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        type = request.QUERY_PARAMS['type'] if 'type' in request.QUERY_PARAMS else ''
        if not type or type not in ['Source', 'Destination']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `type`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=serializers.TellcardsResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Tellcards

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - View
                - Save

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.TellcardsRequest
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.TellcardsRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        if is_blocked(request.user.id, serializer.validated_data['user_destination_id']):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer.insert_or_update()
        return Response(data=serializers.Null().data, status=HTTP_201_CREATED)

    def delete(self, request):
        '''
        DELETE Tellcards

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - View
                - Save

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.TellcardsRequest
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.TellcardsRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_queryset(self):
        if 'type' in self.request.QUERY_PARAMS:
            if self.request.QUERY_PARAMS['type'] == 'Source':
                return models.Tellcard.objects.get_queryset().filter(
                    user_source_id=self.request.user.id,
                    saved_at__isnull=False,
                )
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.Tellcard.objects.get_queryset().filter(
                    user_destination_id=self.request.user.id,
                    saved_at__isnull=False,
                )
        return models.Tellcard.objects.get_queryset().filter(
            user_source_id=self.request.user.id,
            saved_at__isnull=False,
        )


class Users(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        '''
        SELECT Users

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.UsersResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=serializers.UsersResponse(
                instance,
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def put(self, request, id):
        '''
        UPDATE Users

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + email
            - Type: string
            - Status: mandatory

        + photo
            - Type: string
            - Status: optional

        + first_name
            - Type: string
            - Status: optional

        + last_name
            - Type: string
            - Status: optional

        + date_of_birth
            - Type: date
            - Status: optional

        + gender
            - Type: string
            - Status: optional
            - Choices:
                - Female
                - Male

        + location
            - Type: string
            - Status: optional

        + description
            - Type: string
            - Status: optional

        + phone
            - Type: string
            - Status: optional

        + point
            - Type: dictionary (of floats)
            - Status: optional

            Example:

            {
                'latitude': 0.0000000000,
                'longitude': 0.0000000000,
            }

        + settings
            - Type: dictionary
            - Status: optional

            Example:

            {
                'notifications_invitations': true,
                'notifications_messages': true,
                'notifications_saved_you': true,
                'notifications_shared_profiles': true,
                'show_email': false,
                'show_last_name': true,
                'show_phone': false,
                'show_photo': true,
            }

        + photos
            - Type: list (a list of Photo objects; see below)
            - Status: optional

        + social_profiles
            - Type: list (a list of Social Profile objects; see below)
            - Status: optional

        + status
            - Type: dictionary (one Status object; see below)
            - Status: optional

        + urls
            - Type: list (a list of URL objects; see below)
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")

        Photo
        =====

        + id
            - Type: integer
            - Status: optional

        + user_id
            - Type: integer
            - Status: optional

        + string
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        Social Profile
        ==============

        + id
            - Type: integer
            - Status: optional

        + user_id
            - Type: integer
            - Status: optional

        + netloc
            - Type: string
            - Status: mandatory
            - Choices:
                - facebook.com
                - google.com
                - instagram.com
                - linkedin.com
                - twitter.com

        + url
            - Type: string
            - Status: mandatory

        Status
        ======

        + id
            - Type: integer
            - Status: optional

        + user_id
            - Type: integer
            - Status: optional

        + string
            - Type: string
            - Status: mandatory

        + title
            - Type: string
            - Status: mandatory

        + url
            - Type: string
            - Status: optional

        + notes
            - Type: string
            - Status: optional

        + attachments
            - Type: list (a list of Attachment objects; see below)
            - Status: optional

        Attachment
        ==========

        + id
            - Type: integer
            - Status: optional

        + user_status_id
            - Type: integer
            - Status: mandatory

        + string
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        URL
        ===

        + id
            - Type: integer
            - Status: optional

        + user_id
            - Type: integer
            - Status: optional

        + string
            - Type: string
            - Status: mandatory

        + position
            - Type: integer
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UsersRequest
        response_serializer: api.serializers.UsersResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        serializer = serializers.UsersRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.UsersResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Users

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_instance(id)
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)

    def get_instance(self, id):
        return models.User.objects.get_queryset().exclude(~Q(id__in=[id])).filter(id=self.request.user.id).first()


class UsersTellzones(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        '''
        SELECT Users :: Tellzones

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.UsersTellzonesGet
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.UsersTellzonesGet(
                [
                    user_tellzone.tellzone
                    for user_tellzone in models.UserTellzone.objects.get_queryset().filter(
                        user_id=request.user.id,
                        favorited_at__isnull=False,
                    )
                ],
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, id):
        '''
        INSERT/UPDATE (View, Favorite) Users :: Tellzones

        <pre>
        Input
        =====

        + tellzone_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - View
                - Favorite

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UsersTellzonesRequest
        response_serializer: api.serializers.UsersTellzonesResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.UsersTellzonesRequest(
            context={
                'request': request,
            },
            data=request.DATA,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.UsersTellzonesResponse(
                serializer.insert_or_update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def delete(self, request, id):
        '''
        DELETE (View, Favorite) Users :: Tellzones

        <pre>
        Input
        =====

        + tellzone_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - View
                - Favorite

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UsersTellzonesRequest
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.UsersTellzonesRequest(
            context={
                'request': request,
            },
            data=request.DATA,
        )
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(data=serializers.Null().data, status=HTTP_200_OK)


@api_view(('GET',))
@permission_classes(())
def ads(request):
    '''
    SELECT Ads

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.Ads
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    return Response(
        data=serializers.Ads(
            models.Ad.objects.get_queryset(),
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes(())
def authenticate(request, backend):
    '''
    Authenticate Users

    <pre>
    Input
    =====

    + backend
        - Type: string
        - Status: mandatory
        - Choices:
            - facebook
            - linkedin-oauth2

    + access_token
        - Type: string
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - description: >
              A valid Python Social Auth supported backend. As of now, only
              "facebook" and "linkedin-oauth2" are supported. Reference:
              http://psa.matiasaguirre.net/docs/backends/index.html
          name: backend
          paramType: path
          required: true
          type: string
        - name: body
          paramType: body
          pytype: api.serializers.AuthenticateRequest
    response_serializer: api.serializers.AuthenticateResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    if backend not in ['facebook', 'linkedin-oauth2']:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `backend`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    backend = get_backend(settings.AUTHENTICATION_BACKENDS, backend)(strategy=DjangoStrategy(storage=DjangoStorage()))
    if not backend or backend.name not in ['facebook', 'linkedin-oauth2']:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `backend`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if 'access_token' not in request.DATA or not request.DATA['access_token']:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `access_token`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    user = None
    try:
        user = backend.do_auth(request.DATA['access_token'], request=request)
    except Exception:
        pass
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `user`'),
            },
            status=HTTP_401_UNAUTHORIZED,
        )
    request.user = user
    request.user.sign_in()
    return Response(
        data=serializers.AuthenticateResponse(
            user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes(())
def deauthenticate(request):
    '''
    Deauthenticate Users

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.Null
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    request.user.sign_out()
    return Response(data=serializers.Null().data, status=HTTP_200_OK)


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home_connections(request):
    '''
    SELECT Home/Connections

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + dummy
        - Type: string
        - Status: optional
        - Choices:
            - Yes
            - No

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: latitude
          paramType: query
          required: true
          type: number
        - name: longitude
          paramType: query
          required: true
          type: number
        - name: dummy
          paramType: query
          required: false
          type: string
    response_serializer: api.serializers.HomeConnectionsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.HomeConnectionsRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data['dummy'] == 'Yes':
        connections = [
            {
                'user': user,
                'tellzone': models.Tellzone.objects.get_queryset().order_by('?').first(),
                'point': user.point,
                'timestamp': datetime.now() - timedelta(days=randint(1, 31)),
            }
            for user in models.User.objects.get_queryset().exclude(id=request.user.id).order_by('?')[0:5]
        ]
    else:
        connections = {}
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    api_users_locations_2.user_id,
                    api_users_locations_2.tellzone_id,
                    api_users_locations_2.point,
                    api_users_locations_2.timestamp
                FROM api_users_locations api_users_locations_1
                INNER JOIN api_users_locations api_users_locations_2 ON
                    api_users_locations_1.user_id != api_users_locations_2.user_id
                    AND
                    ST_DWithin(
                        ST_Transform(api_users_locations_1.point, 2163),
                        ST_Transform(api_users_locations_2.point, 2163),
                        91.44
                    )
                    AND
                    api_users_locations_1.timestamp BETWEEN
                        api_users_locations_2.timestamp - INTERVAL '1 minute'
                        AND
                        api_users_locations_2.timestamp + INTERVAL '1 minute'
                LEFT OUTER JOIN api_tellcards ON
                    api_tellcards.user_source_id = api_users_locations_1.user_id
                    AND
                    api_tellcards.user_destination_id = api_users_locations_2.user_id
                LEFT OUTER JOIN api_messages ON
                    api_messages.user_source_id = api_users_locations_1.user_id
                    AND
                    api_messages.user_destination_id = api_users_locations_2.user_id
                WHERE
                    api_users_locations_1.user_id = 1
                    AND
                    api_users_locations_1.timestamp > NOW() - INTERVAL '1 day'
                    AND
                    api_tellcards.id IS NULL
                    AND
                    api_messages.id IS NULL
                GROUP BY api_users_locations_2.id
                ''',
                (request.user.id,)
            )
            for record in cursor.fetchall():
                if record[0] not in connections:
                    connections[record[0]] = {
                        'user': models.User.objects.get_queryset().filter(id=record[0]).first(),
                        'tellzone': models.Tellzone.objects.get_queryset().filter(id=record[1]).first(),
                        'point': record[2],
                        'timestamp': record[3],
                    }
        connections = connections.values()
    return Response(
        data=serializers.HomeConnectionsResponse(
            connections,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home_statistics_frequent(request):
    '''
    SELECT Home/Statistics/Frequent

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + dummy
        - Type: string
        - Status: optional
        - Choices:
            - Yes
            - No

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: latitude
          paramType: query
          required: true
          type: number
        - name: longitude
          paramType: query
          required: true
          type: number
        - name: dummy
          paramType: query
          required: false
          type: string
    response_serializer: api.serializers.HomeStatisticsFrequentResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.HomeStatisticsFrequentRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    point = get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
    today = date.today()
    if serializer.validated_data['dummy'] == 'Yes':
        views_today = randint(1, 150)
        views_total = randint(1, 1500)
        saves_today = randint(1, 50)
        saves_total = randint(1, 50)
        users_near = randint(1, 50)
        users_area = randint(1, 500)
    else:
        views_total = models.Tellcard.objects.get_queryset().filter(
            user_destination_id=request.user.id,
            viewed_at__isnull=False,
        ).count()
        views_today = models.Tellcard.objects.get_queryset().filter(
            user_destination_id=request.user.id,
            viewed_at__startswith=today,
        ).count()
        saves_total = models.Tellcard.objects.get_queryset().filter(
            user_destination_id=request.user.id,
            saved_at__isnull=False,
        ).count()
        saves_today = models.Tellcard.objects.get_queryset().filter(
            user_destination_id=request.user.id,
            saved_at__startswith=today,
        ).count()
        users_near = models.UserLocation.objects.filter(
            ~Q(user_id=request.user.id),
            point__distance_lte=(point, D(ft=300)),
            is_casting=True,
            timestamp__gt=datetime.now() - timedelta(minutes=1),
            user__is_signed_in=True,
        ).distinct(
            'user_id',
        ).order_by(
            'user_id',
        ).count()
        users_area = models.UserLocation.objects.filter(
            ~Q(user_id=request.user.id),
            point__distance_lte=(point, D(mi=10)),
            is_casting=True,
            timestamp__gt=datetime.now() - timedelta(minutes=1),
            user__is_signed_in=True,
        ).distinct(
            'user_id',
        ).order_by(
            'user_id',
        ).count()
    return Response(
        data=serializers.HomeStatisticsFrequentResponse(
            {
                'views': {
                    'total': views_total,
                    'today': views_today,
                },
                'saves': {
                    'total': saves_total,
                    'today': saves_today,
                },
                'users': {
                    'near': users_near,
                    'area': users_area,
                },
            },
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home_statistics_infrequent(request):
    '''
    SELECT Home/Statistics/Infrequent

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + dummy
        - Type: string
        - Status: optional
        - Choices:
            - Yes
            - No

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: latitude
          paramType: query
          required: true
          type: number
        - name: longitude
          paramType: query
          required: true
          type: number
        - name: dummy
          paramType: query
          required: false
          type: string
    response_serializer: api.serializers.HomeStatisticsInfrequentResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.HomeStatisticsInfrequentRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    today = date.today()
    days = get_days(today)
    weeks = get_weeks(today)
    months = get_months(today)
    if serializer.validated_data['dummy'] == 'Yes':
        views_days = {}
        for day in days:
            views_days[day] = randint(1, 150)
        views_weeks = {}
        for week in weeks[0]:
            views_weeks[week] = randint(1, 150)
        views_months = {}
        for month in months[0]:
            views_months[month] = randint(1, 150)
        saves_days = {}
        for day in days:
            saves_days[day] = randint(1, 50)
        saves_weeks = {}
        for week in weeks[0]:
            saves_weeks[week] = randint(1, 50)
        saves_months = {}
        for month in months[0]:
            saves_months[month] = randint(1, 50)
    else:
        views_days = {}
        for day in days:
            views_days[day] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT viewed_at::DATE AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND viewed_at::DATE BETWEEN %s AND %s
                GROUP BY viewed_at::DATE
                ORDER BY viewed_at::DATE DESC
                ''',
                (request.user.id, days[6], days[0],)
            )
            for item in cursor.fetchall():
                views_days[item[0]] = item[1]
        views_weeks = {}
        for week in weeks[0]:
            views_weeks[week] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT DATE_TRUNC('WEEK', viewed_at) AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND viewed_at::DATE BETWEEN %s AND %s
                GROUP BY DATE_TRUNC('WEEK', viewed_at)
                ORDER BY DATE_TRUNC('WEEK', viewed_at) DESC
                ''',
                (request.user.id, weeks[2], weeks[1],)
            )
            for item in cursor.fetchall():
                views_weeks[item[0]] = item[1]
        views_months = {}
        for month in months[0]:
            views_months[month] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT DATE_TRUNC('MONTH', viewed_at) AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND viewed_at::DATE BETWEEN %s AND %s
                GROUP BY DATE_TRUNC('MONTH', viewed_at)
                ORDER BY DATE_TRUNC('MONTH', viewed_at) DESC
                ''',
                (request.user.id, months[2], months[1],)
            )
            for item in cursor.fetchall():
                views_months[item[0]] = item[1]
        saves_days = {}
        for day in days:
            saves_days[day] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT saved_at::DATE AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND saved_at::DATE BETWEEN %s AND %s
                GROUP BY saved_at::DATE
                ORDER BY saved_at::DATE DESC
                ''',
                (request.user.id, days[6], days[0],)
            )
            for item in cursor.fetchall():
                saves_days[item[0]] = item[1]
        saves_weeks = {}
        for week in weeks[0]:
            saves_weeks[week] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT DATE_TRUNC('WEEK', saved_at) AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND saved_at::DATE BETWEEN %s AND %s
                GROUP BY DATE_TRUNC('WEEK', saved_at)
                ORDER BY DATE_TRUNC('WEEK', saved_at) DESC
                ''',
                (request.user.id, weeks[2], weeks[1],)
            )
            for item in cursor.fetchall():
                saves_weeks[item[0]] = item[1]
        saves_months = {}
        for month in months[0]:
            saves_months[month] = 0
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT DATE_TRUNC('MONTH', saved_at) AS key, COUNT(id) AS value
                FROM api_tellcards
                WHERE user_destination_id = %s AND saved_at::DATE BETWEEN %s AND %s
                GROUP BY DATE_TRUNC('MONTH', saved_at)
                ORDER BY DATE_TRUNC('MONTH', saved_at) DESC
                ''',
                (request.user.id, months[2], months[1],)
            )
            for item in cursor.fetchall():
                saves_months[item[0]] = item[1]
    return Response(
        data=serializers.HomeStatisticsInfrequentResponse(
            {
                'views': {
                    'days': views_days,
                    'weeks': views_weeks,
                    'months': views_months,
                },
                'saves': {
                    'days': saves_days,
                    'weeks': saves_weeks,
                    'months': saves_months,
                },
            },
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home_tellzones(request):
    '''
    SELECT Home/Tellzones

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + dummy
        - Type: string
        - Status: optional
        - Choices:
            - Yes
            - No

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: latitude
          paramType: query
          required: true
          type: number
        - name: longitude
          paramType: query
          required: true
          type: number
        - name: dummy
          paramType: query
          required: false
          type: string
    response_serializer: api.serializers.HomeTellzonesResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.HomeTellzonesRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    point = get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
    if serializer.validated_data['dummy'] == 'Yes':
        tellzones = models.Tellzone.objects.get_queryset().distance(point).order_by('?')[0:5]
    else:
        tellzones = models.Tellzone.objects.get_queryset().filter(
            point__distance_lte=(point, D(mi=10)),
        ).distance(
            point,
        ).order_by(
            'distance',
        )
    return Response(
        data=serializers.HomeTellzonesResponse(
            tellzones,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def master_tells_ids(request):
    '''
    SELECT (id) Master Tells

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    [
        1,
        ...,
        ...,
        ...,
        n,
    ]
    </pre>
    ---
    '''
    return Response(
        data=[
            master_tell.id
            for master_tell in models.MasterTell.objects.get_queryset().filter(owned_by_id=request.user.id)
        ],
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def master_tells_positions(request):
    '''
    UPDATE (position) Master Tells

    <pre>
    Input
    =====

    [
        {
            "id": 1,
            "position": 1,
        },
        ...,
        ...,
        ...,
        {
            "id": n,
            "position": n,
        }
    ]

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
    response_serializer: api.serializers.MasterTellsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    master_tells = []
    for item in request.DATA:
        master_tell = models.MasterTell.objects.get_queryset().filter(
            id=item['id'], owned_by_id=request.user.id,
        ).first()
        if not master_tell:
            continue
        master_tell.position = item['position']
        master_tell.save()
        master_tells.append(master_tell)
    return Response(
        data=serializers.MasterTellsResponse(
            master_tells,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def messages_bulk_is_hidden(request):
    '''
    UPDATE (user_source_is_hidden, user_destination_is_hidden) Messages

    <pre>
    Input
    =====

    + user_id
        - Type: integer
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")

    Push Notification
    =================

    {
        'type': 'updateThread',
    }
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
          pytype: api.serializers.MessagesBulkRequest
    response_serializer: api.serializers.MessagesBulkResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.MessagesBulkRequest(
        context={
            'request': request,
        },
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)
    messages = []
    for message in models.Message.objects.get_queryset().filter(
        Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_id']) |
        Q(user_source_id=serializer.validated_data['user_id'], user_destination_id=request.user.id),
    ):
        if message.user_source_id == request.user.id:
            message.user_source_is_hidden = True
        if message.user_destination_id == request.user.id:
            message.user_destination_is_hidden = True
        message.save()
        messages.append(message)
    current_app.send_task(
        'api.tasks.push_notifications',
        (
            request.user.id,
            {
                'aps': {},
                'type': 'updateThread',
            },
        ),
        serializer='json',
    )
    return Response(
        data=serializers.MessagesBulkResponse(
            messages,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def messages_bulk_status(request):
    '''
    UPDATE (status) Messages

    <pre>
    Input
    =====

    + user_id
        - Type: integer
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
          pytype: api.serializers.MessagesBulkRequest
    response_serializer: api.serializers.MessagesBulkResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.MessagesBulkRequest(
        context={
            'request': request,
        },
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)
    messages = []
    for message in models.Message.objects.get_queryset().filter(
        Q(user_source_id=serializer.validated_data['user_id'], user_destination_id=request.user.id),
    ):
        message.status = 'Read'
        message.save()
        messages.append(message)
    current_app.send_task(
        'api.tasks.push_notifications',
        (
            request.user.id,
            {
                'aps': {},
                'type': 'updateThread',
            },
        ),
        serializer='json',
    )
    return Response(
        data=serializers.MessagesBulkResponse(
            messages,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes(())
def register(request):
    '''
    Register Users

    <pre>
    Input
    =====

    + email
        - Type: string
        - Status: mandatory

    + photo
        - Type: string
        - Status: optional

    + first_name
        - Type: string
        - Status: optional

    + last_name
        - Type: string
        - Status: optional

    + date_of_birth
        - Type: date
        - Status: optional

    + gender
        - Type: string
        - Status: optional
        - Choices:
            - Female
            - Male

    + location
        - Type: string
        - Status: optional

    + description
        - Type: string
        - Status: optional

    + phone
        - Type: string
        - Status: optional

    + point
        - Type: dictionary (of floats)
        - Status: optional

        Example:

        {
            'latitude': 0.0000000000,
            'longitude': 0.0000000000,
        }

    + photos (see /api/users/ for more details)
        - Type: list (a list of Photo objects)
        - Status: optional

    + social_profiles (see /api/users/ for more details)
        - Type: list (a list of Social Profile objects)
        - Status: mandatory (either "facebook.com" or "linkedin.com" is mandatory)

    + status (see /api/users/ for more details)
        - Type: dictionary (one Status object)
        - Status: optional

    + urls (see /api/users/ for more details)
        - Type: list (a list of URL objects)
        - Status: optional

    + master tells (see /api/users/master-tells/ for more details)
        - Type: list (a list of Master Tell objects; with a list of Slave Tell objects under "slave_tells")
        - Status: optional

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
          pytype: api.serializers.RegisterRequest
    response_serializer: api.serializers.RegisterResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.RegisterRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    if not serializer.is_valid_(request.DATA):
        return Response(
            data={
                'error': ugettext_lazy('Invalid `access_token` - #2'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    return Response(
        data=serializers.RegisterResponse(
            serializer.insert(),
            context={
                'request': request,
            },
        ).data,
        status=HTTP_201_CREATED,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def slave_tells_ids(request):
    '''
    SELECT (id) Slave Tells

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    [
        1,
        ...,
        ...,
        ...,
        n,
    ]
    </pre>
    ---
    '''
    return Response(
        data=[
            slave_tell.id
            for slave_tell in models.SlaveTell.objects.get_queryset().filter(owned_by_id=request.user.id)
        ],
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def slave_tells_positions(request):
    '''
    UPDATE (position) Slave Tells

    <pre>
    Input
    =====

    [
        {
            "id": 1,
            "position": 1,
        },
        ...,
        ...,
        ...,
        {
            "id": n,
            "position": n,
        }
    ]

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
    response_serializer: api.serializers.SlaveTellsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    slave_tells = []
    for item in request.DATA:
        slave_tell = models.SlaveTell.objects.get_queryset().filter(id=item['id'], owned_by_id=request.user.id).first()
        if not slave_tell:
            continue
        slave_tell.position = item['position']
        slave_tell.save()
        slave_tells.append(slave_tell)
    return Response(
        data=serializers.SlaveTellsResponse(
            slave_tells,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def tellzones(request):
    '''
    SELECT Tellzones

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + radius
        - Unit: foot
        - Type: float
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: latitude
          paramType: query
          required: true
          type: number
        - name: longitude
          paramType: query
          required: true
          type: number
        - name: radius
          paramType: query
          required: true
          type: number
    response_serializer: api.serializers.TellzonesResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.TellzonesRequest(
        context={
            'request': request,
        },
        data=request.QUERY_PARAMS,
    )
    serializer.is_valid(raise_exception=True)
    point = get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
    return Response(
        data=serializers.TellzonesResponse(
            [
                tellzone
                for tellzone in models.Tellzone.objects.get_queryset().filter(
                    point__distance_lte=(point, D(ft=serializer.validated_data['radius'])),
                ).distance(
                    point,
                )
            ],
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def tellzones_master_tells(request, id):
    '''
    SELECT (Master Tells) Tellzones

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.TellzonesMasterTells
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    tellzone = models.Tellzone.objects.get_queryset().filter(id=id).first()
    if not tellzone:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    master_tells = []
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            '''
            SELECT
                api_master_tells.id,
                api_master_tells.created_by_id,
                api_master_tells.owned_by_id,
                api_master_tells.contents,
                api_master_tells.position,
                api_master_tells.is_visible,
                api_master_tells.inserted_at,
                api_master_tells.updated_at
            FROM api_users_locations
            INNER JOIN api_users ON api_users.id = api_users_locations.user_id
            INNER JOIN api_master_tells ON api_master_tells.owned_by_id = api_users_locations.user_id
            LEFT OUTER JOIN api_blocks ON
                (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_users_locations.user_id)
                OR
                (api_blocks.user_source_id = api_users_locations.user_id AND api_blocks.user_destination_id = %s)
            WHERE
                api_users_locations.user_id != %s
                AND
                ST_DWithin(
                    ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                    ST_Transform(api_users_locations.point, 2163),
                    %s
                )
                AND
                api_users_locations.is_casting IS TRUE
                AND
                api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
                AND
                api_users.is_signed_in IS TRUE
                AND
                api_blocks.id IS NULL
            ORDER BY api_users_locations.timestamp DESC
            ''',
            (
                request.user.id,
                request.user.id,
                request.user.id,
                'POINT({x} {y})'.format(x=tellzone.point.x, y=tellzone.point.y),
                models.Tellzone.radius() * 0.3048,
            )
        )
        for record in cursor.fetchall():
            master_tells.append({
                'id': record[0],
                'created_by_id': record[1],
                'owned_by_id': record[2],
                'contents': record[3],
                'position': record[4],
                'is_visible': record[5],
                'inserted_at': record[6],
                'updated_at': record[7],
            })
    return Response(
        data=serializers.TellzonesMasterTells(
            master_tells,
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes(())
def users_profile(request, id):
    '''
    SELECT (Profile) Users

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.UsersProfile
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    if request.user.is_authenticated():
        if is_blocked(request.user.id, id):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
    user = models.User.objects.get_queryset().filter(id=id).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    return Response(
        data=serializers.UsersProfile(
            user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


def handler400(request):
    return JsonResponse(
        data={
            'error': '400 Bad Request',
        },
        status=400,
    )


def handler403(request):
    return JsonResponse(
        data={
            'error': '403 Forbidden',
        },
        status=403,
    )


def handler404(request):
    return JsonResponse(
        data={
            'error': '404 Not Found',
        },
        status=404,
    )


def handler500(request):
    return JsonResponse(
        data={
            'error': '500 Internal Server Error',
        },
        status=500,
    )


def get_days(today):
    return [(today - timedelta(days=index + 1)).isoformat() for index in range(0, 7)]


def get_weeks(today):
    dates = [
        get(today - timedelta(days=today.weekday())).replace(weeks=-1 - index).date()
        for index in range(0, 8)
    ]
    return [
        [d.isoformat() for d in dates],
        dates[-1].isoformat(),
        get(dates[0]).replace(days=-1, weeks=1).date().isoformat(),
    ]


def get_months(today):
    dates = [get(today).replace(day=1, months=-1 - index).date() for index in range(0, 12)]
    return [
        [d.isoformat() for d in dates],
        dates[-1].isoformat(),
        get(dates[0]).replace(days=-1, months=1).date().isoformat(),
    ]


def get_point(latitude, longitude):
    return fromstr('POINT({longitude} {latitude})'.format(latitude=latitude, longitude=longitude))


def is_blocked(one, two):
    if models.Block.objects.get_queryset().filter(
        Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
    ).count():
        return True
    return False
