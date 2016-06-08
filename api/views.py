# -*- coding: utf-8 -*-

from base64 import urlsafe_b64decode
from contextlib import closing
from datetime import date, datetime, timedelta
from random import randint

from arrow import get
from bcrypt import hashpw
from celery import current_app
from django.conf import settings
from django.contrib import messages
from django.contrib.gis.measure import D
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy
from faker import Faker
from geopy.distance import vincenty
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_409_CONFLICT,
)
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from social.apps.django_app.default.models import DjangoStorage
from social.backends.linkedin import LinkedinOAuth2
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import loads

from api import middleware, models, serializers


def do_auth(self, access_token, *args, **kwargs):
    data = self.user_data(access_token, *args, **kwargs)
    data['access_token'] = access_token
    response = kwargs.get('response') or {}
    response.update(data or {})
    kwargs.update({
        'backend': self,
        'response': response,
    })
    return self.strategy.authenticate(*args, **kwargs)

LinkedinOAuth2.do_auth = do_auth


class IsAuthenticatedNetwork(IsAuthenticated):

    def has_permission(self, request, view):
        if super(IsAuthenticatedNetwork, self).has_permission(request, view):
            if request.user.type in ['Root', 'Network']:
                return True
        return False


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

    def get_1(self, request):
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
              required: false
              type: datetime
            - name: updated_at
              paramType: query
              required: false
              type: datetime
        response_serializer: api.serializers.MasterTellsGet1Response
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.MasterTellsGet1Request(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(request.query_params)
        return Response(
            data=serializers.MasterTellsGet1Response(
                self.get_queryset(
                    inserted_at=serializer.validated_data[
                        'inserted_at'
                    ] if 'inserted_at' in serializer.validated_data else None,
                    updated_at=serializer.validated_data[
                        'updated_at'
                    ] if 'updated_at' in serializer.validated_data else None,
                ),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def get_2(self, request, id):
        '''
        SELECT Master Tell

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
        response_serializer: api.serializers.MasterTellsGet2Response
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = models.MasterTell.objects.get_queryset().filter(id=id).first()
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=serializers.MasterTellsGet2Response(
                instance,
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Master Tells

        <pre>
        Input
        =====

        + category_id
            - Type: integer
            - Status: mandatory

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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

        + category_id
            - Type: integer
            - Status: mandatory

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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

        + category_id
            - Type: integer
            - Status: mandatory

        + contents
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + position
            - Type: integer
            - Status: optional

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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

    def get_queryset(self, inserted_at=None, updated_at=None):
        queryset = models.MasterTell.objects.get_queryset().filter(owned_by_id=self.request.user.id)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
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
                - True ('t', 'T', 'true', 'True', 'TRUE', '1', 1, True)
                - False ('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False, '')

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

        + post_id
            Description: If supplied, all messages will pertain to this `post_id`. Only applicable if
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
              required: False
              type: string
            - name: user_id
              paramType: query
              required: False
              type: integer
            - name: user_status_id
              paramType: query
              required: False
              type: integer
            - name: master_tell_id
              paramType: query
              required: False
              type: integer
            - name: post_id
              paramType: query
              required: False
              type: integer
            - name: since_id
              paramType: query
              required: False
              type: integer
            - name: max_id
              paramType: query
              required: False
              type: integer
            - name: limit
              paramType: query
              required: False
              type: integer
        response_serializer: api.serializers.MessagesGetResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.MessagesGetRequest(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(request.query_params)
        messages = []
        blocks = []
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT user_source_id, user_destination_id
                FROM api_blocks
                WHERE user_source_id = %s OR user_destination_id = %s
                ''',
                (request.user.id, request.user.id,)
            )
            for record in cursor.fetchall():
                if record[0] != request.user.id:
                    blocks.append(record[0])
                if record[1] != request.user.id:
                    blocks.append(record[1])
        if serializer.validated_data.get('recent', True):
            for user in models.User.objects.get_queryset().exclude(id__in=[request.user.id] + blocks):
                message = models.Message.objects.get_queryset().filter(
                    Q(user_source_id=request.user.id, user_destination_id=user.id) |
                    Q(user_source_id=user.id, user_destination_id=request.user.id),
                    is_suppressed=False,
                ).order_by(
                    '-id',
                ).first()
                if message:
                    messages.append(message)
            messages = sorted(messages, key=lambda message: message.inserted_at, reverse=True)
        else:
            query = models.Message.objects.get_queryset().filter(
                Q(user_source_id=request.user.id) | Q(user_destination_id=request.user.id),
                ~Q(user_source_id__in=blocks) & ~Q(user_destination_id__in=blocks),
                is_suppressed=False,
            )
            user_id = serializer.validated_data.get('user_id', None)
            if user_id:
                query = query.filter(Q(user_source_id=user_id) | Q(user_destination_id=user_id))
            user_status_id = serializer.validated_data.get('user_status_id', None)
            if user_status_id:
                query = query.filter(user_status_id=user_status_id)
            master_tell_id = serializer.validated_data.get('master_tell_id', None)
            if master_tell_id:
                query = query.filter(master_tell_id=master_tell_id)
            post_id = serializer.validated_data.get('post_id', None)
            if post_id:
                query = query.filter(post_id=post_id)
            since_id = 0
            try:
                since_id = serializer.validated_data.get('since_id', 0)
            except Exception:
                pass
            if since_id:
                query = query.filter(id__gt=since_id)
            max_id = 0
            try:
                max_id = serializer.validated_data.get('max_id', 0)
            except Exception:
                pass
            if max_id:
                query = query.filter(id__lt=max_id)
            limit = 100
            try:
                limit = serializer.validated_data.get('limit', 100)
            except Exception:
                pass
            for message in query.order_by('-id')[:limit]:
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

        + post_id
            - Type: integer
            - Status: optional

        + type
            - Type: string
            - Status: mandatory
            - Choices:
                - Ask
                - Message
                - Request
                - Response - Accepted
                - Response - Blocked
                - Response - Rejected

        + contents
            - Type: string
            - Status: mandatory (optional when type = 'Response - Blocked' or type = 'Response - Rejected')

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
            'aps': {
                'alert': {
                    'body': '{{ body }}',
                    'title': 'New message from user',
                },
                'badge': {{ total_number_of_unread_messages + total_number_of_unread_notifications }},
            },
            'type': 'message',
            'user_source_id': {{ user_source_id }},
            'master_tell_id': '{{ master_tell_id }}',
            'post_id': {{ post_id }},
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
            - code: 403
              message: Invalid Input
            - code: 409
              message: Invalid Input
        '''
        serializer = serializers.MessagesPostRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        if request.user.id == serializer.validated_data['user_destination_id']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if models.is_blocked(request.user.id, serializer.validated_data['user_destination_id']):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if 'post_id' not in serializer.validated_data or not serializer.validated_data['post_id']:
            if not models.Message.objects.get_queryset().filter(
                Q(
                    user_source_id=request.user.id,
                    user_destination_id=serializer.validated_data['user_destination_id'],
                ) | Q(
                    user_source_id=serializer.validated_data['user_destination_id'],
                    user_destination_id=request.user.id,
                ),
                post_id__isnull=True,
                type__in=[
                    'Response - Accepted',
                    'Response - Rejected',
                    'Message',
                    'Ask',
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
                    post_id__isnull=True,
                ).order_by(
                    '-id',
                ).first()
                if message:
                    if message.user_source_id == request.user.id:
                        if message.type == 'Request':
                            return Response(status=HTTP_409_CONFLICT)
                        if message.type == 'Response - Blocked':
                            return Response(status=HTTP_403_FORBIDDEN)
                    if message.user_destination_id == request.user.id:
                        if message.type == 'Request' and serializer.validated_data['type'] in ['Message', 'Ask']:
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
            'action': 'updateMessage',
            'type': 'message',
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
                        'action': 'updateMessage',
                        'aps': {},
                        'type': 'message',
                    },
                ),
                queue='api.tasks.push_notifications',
                routing_key='api.tasks.push_notifications',
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


class Networks(ViewSet):

    permission_classes = (IsAuthenticatedNetwork,)

    def get_1(self, request):
        '''
        SELECT Networks

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.NetworksResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.NetworksRequest(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(request.query_params)
        return Response(
            data=serializers.NetworksResponse(
                self.get_queryset(),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def get_2(self, request, id):
        '''
        SELECT Network

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
        response_serializer: api.serializers.NetworksResponse
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
            data=serializers.NetworksResponse(
                instance,
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Networks

        <pre>
        Input
        =====

        + name
            - Type: string
            - Status: mandatory

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.NetworksRequest
        response_serializer: api.serializers.NetworksResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.NetworksRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.NetworksResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def put(self, request, id):
        '''
        UPDATE Networks

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + name
            - Type: string
            - Status: mandatory

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.NetworksRequest
        response_serializer: api.serializers.NetworksResponse
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
        serializer = serializers.NetworksRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.NetworksResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def patch(self, request, id):
        '''
        UPDATE Networks

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + name
            - Type: string
            - Status: mandatory

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.NetworksRequest
        response_serializer: api.serializers.NetworksResponse
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
        serializer = serializers.NetworksRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.NetworksResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Networks

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
        return models.Network.objects.get_queryset().filter(user_id=self.request.user.id)


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
              required: False
              type: integer
            - name: max_id
              paramType: query
              required: False
              type: integer
            - name: limit
              paramType: query
              required: False
              type: integer
        response_serializer: api.serializers.NotificationsGetResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.NotificationsGetRequest(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(request.query_params)
        query = models.Notification.objects.get_queryset().filter(user_id=request.user.id)
        since_id = 0
        try:
            since_id = serializer.validated_data.get('since_id', 0)
        except Exception:
            pass
        if since_id:
            query = query.filter(id__gt=since_id)
        max_id = 0
        try:
            max_id = serializer.validated_data.get('max_id', 0)
        except Exception:
            pass
        if max_id:
            query = query.filter(id__lt=max_id)
        limit = 50
        try:
            limit = serializer.validated_data.get('limit', 100)
        except Exception:
            pass
        return Response(
            data=serializers.NotificationsGetResponse(
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


class Posts(ViewSet):

    permission_classes = (IsAuthenticated,)

    def search(self, request):
        '''
        SEARCH Posts

        <pre>
        Input
        =====

        + user_ids
            - Type: a comma-separated list of User IDs
            - Status: optional

        + category_ids
            - Type: a comma-separated list of Category IDs
            - Status: optional

        + network_ids
            - Type: a comma-separated list of Network IDs
            - Status: optional

        + tellzone_ids
            - Type: a comma-separated list of Tellzone IDs
            - Status: optional

        + keywords
            - Type: string
            - Status: optional

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        omit_parameters:
            - form
        parameters:
            - name: user_ids
              paramType: query
              required: false
              type: string
            - name: category_ids
              paramType: query
              required: false
              type: string
            - name: network_ids
              paramType: query
              required: false
              type: string
            - name: tellzone_ids
              paramType: query
              required: false
              type: string
            - name: keywords
              paramType: query
              required: false
              type: string
        response_serializer: api.serializers.PostsSearch
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.PostsResponse(
                self.get_queryset(
                    user_ids=request.query_params.get('user_ids', None),
                    category_ids=request.query_params.get('category_ids', None),
                    network_ids=request.query_params.get('network_ids', None),
                    tellzone_ids=request.query_params.get('tellzone_ids', None),
                    keywords=request.query_params.get('keywords', None),
                ),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def get_1(self, request):
        '''
        SELECT Posts

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        response_serializer: api.serializers.PostsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return Response(
            data=serializers.PostsResponse(
                self.get_queryset(user_id=request.user.id),
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def get_2(self, request, id):
        '''
        SELECT Post

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
        response_serializer: api.serializers.PostsResponse
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
            data=serializers.PostsResponse(
                instance,
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Posts

        <pre>
        Input
        =====

        + category_id
            - Type: integer
            - Status: mandatory

        + title
            - Type: string
            - Status: optional

        + contents
            - Type: string
            - Status: mandatory

        + attachments
            - Type: list (a list of Attachment objects; see below)
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

                + string_original
                    - Type: string
                    - Status: mandatory

                + string_preview
                    - Type: string
                    - Status: optional

                + position
                    - Type: integer
                    - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.PostsRequest
        response_serializer: api.serializers.PostsResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.PostsRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.PostsResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def put(self, request, id):
        '''
        UPDATE Posts

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + category_id
            - Type: integer
            - Status: mandatory

        + title
            - Type: string
            - Status: optional

        + contents
            - Type: string
            - Status: mandatory

        + attachments
            - Type: list (a list of Attachment objects; see below)
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

                + string_original
                    - Type: string
                    - Status: mandatory

                + string_preview
                    - Type: string
                    - Status: optional

                + position
                    - Type: integer
                    - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.PostsRequest
        response_serializer: api.serializers.PostsResponse
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
        serializer = serializers.PostsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.PostsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def patch(self, request, id):
        '''
        UPDATE Posts

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + category_id
            - Type: integer
            - Status: mandatory

        + title
            - Type: string
            - Status: optional

        + contents
            - Type: string
            - Status: mandatory

        + attachments
            - Type: list (a list of Attachment objects; see below)
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

                + string_original
                    - Type: string
                    - Status: mandatory

                + string_preview
                    - Type: string
                    - Status: optional

                + position
                    - Type: integer
                    - Status: optional

        + tellzones
            - Type: list (a list of Tellzone IDs)
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
              pytype: api.serializers.PostsRequest
        response_serializer: api.serializers.PostsResponse
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
        serializer = serializers.PostsRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.PostsResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Posts

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

    def get_queryset(
        self, user_id=None, user_ids=None, category_ids=None, network_ids=None, tellzone_ids=None, keywords=None,
    ):
        queryset = models.Post.objects.get_queryset().select_related(
            'user',
            'category',
        ).prefetch_related(
            'posts_tellzones',
            'attachments',
            'user__settings',
        )
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if user_ids:
            queryset = queryset.filter(user_id__in=map(int, user_ids.split(',')))
        if category_ids:
            queryset = queryset.filter(category_id__in=map(int, category_ids.split(',')))
        if network_ids:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT post_id
                    FROM api_posts_tellzones
                    WHERE tellzone_id IN (
                        SELECT tellzone_id
                        FROM api_networks_tellzones
                        WHERE network_id IN %s
                    )
                    ''',
                    (tuple(map(int, network_ids.split(','))),),
                )
                queryset = queryset.filter(id__in=[record[0] for record in cursor.fetchall()])
        if tellzone_ids:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    '''
                    SELECT post_id
                    FROM api_posts_tellzones
                    WHERE tellzone_id IN %s
                    ''',
                    (tuple(map(int, tellzone_ids.split(','))),),
                )
                queryset = queryset.filter(id__in=[record[0] for record in cursor.fetchall()])
        if keywords:
            queryset = queryset.filter(Q(title__icontains=keywords) | Q(contents__icontains=keywords))
        return queryset


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
        point = models.get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
        users = models.get_users(
            request.user.id,
            None,
            None,
            point,
            serializer.validated_data['radius'] * 0.3048,
            True,
        )
        users = {key: value for key, value in users.items() if not models.is_blocked(request.user.id, key)}
        return Response(
            data=serializers.RadarGetResponse(
                [
                    {
                        'hash': models.get_hash(items),
                        'items': items,
                        'position': position + 1,
                    }
                    for position, items in enumerate(
                        models.get_items(
                            [user[0] for user in sorted(users.values(), key=lambda user: (user[2], user[0].id,))],
                            len(users.values()) or 1
                        )
                    )
                ],
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        POST Radar

        <pre>
        Input
        =====

        + network_id
            - Type: integer
            - Status: optional

        + tellzone_id
            - Type: integer
            - Status: optional

        + location
            - Type: string
            - Status: optional

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

        + bearing
            - Type: integer
            - Status: optional

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
        if 'point' in serializer.validated_data and serializer.validated_data['point']:
            if not request.user.tellzone:
                user_location = serializer.insert()
            tellzones = sorted(
                models.Tellzone.objects.get_queryset().filter(
                    point__distance_lte=(user_location.point, D(ft=models.Tellzone.radius())),
                ).prefetch_related(
                    'social_profiles',
                    'networks_tellzones',
                    'networks_tellzones__network',
                ).distance(
                    user_location.point,
                ),
                key=lambda tellzone: (tellzone.distance.ft, -tellzone.id),
            )
            if not tellzones:
                network_ids = []
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        '''
                        SELECT DISTINCT api_networks.id
                        FROM api_tellzones
                        INNER JOIN api_networks_tellzones ON api_networks_tellzones.tellzone_id = api_tellzones.id
                        INNER JOIN api_networks ON api_networks.id = api_networks_tellzones.network_id
                        WHERE ST_DWithin(
                            ST_Transform(api_tellzones.point, 2163),
                            ST_Transform(ST_GeomFromText(%s, 4326), 2163),
                            8046.72
                        )
                        ORDER BY api_networks.id ASC
                        ''',
                        (
                            'POINT({longitude:.14f} {latitude:.14f})'.format(
                                longitude=user_location.point.x, latitude=user_location.point.y,
                            ),
                        ),
                    )
                    network_ids = list(sorted(set([record[0] for record in cursor.fetchall()])))
                tellzones = sorted(
                    models.Tellzone.objects.get_queryset().filter(
                        status='Public',
                        networks_tellzones__network_id__in=network_ids,
                    ).prefetch_related(
                        'social_profiles',
                        'networks_tellzones',
                        'networks_tellzones__network',
                    ).distance(
                        user_location.point,
                    ).distinct(),
                    key=lambda tellzone: (tellzone.distance.ft, -tellzone.id),
                )
        else:
            tellzones = []
        return Response(
            data=serializers.RadarPostResponse(
                tellzones,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )


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
                ).select_related(
                    'user_source',
                    'user_destination',
                    'object',
                )
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.ShareUser.objects.get_queryset().filter(
                    user_destination_id=self.request.user.id,
                ).select_related(
                    'user_source',
                    'user_destination',
                    'object',
                )
        return models.ShareUser.objects.get_queryset().filter(
            user_source_id=self.request.user.id,
        ).select_related(
            'user_source',
            'user_destination',
            'object',
        )


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
              required: false
              type: datetime
            - name: updated_at
              paramType: query
              required: false
              type: datetime
        response_serializer: api.serializers.SlaveTellsGetResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.SlaveTellsGetRequest(
            context={
                'request': request,
            },
            data=request.query_params,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.SlaveTellsResponse(
                self.get_queryset(
                    inserted_at=serializer.validated_data[
                        'inserted_at'
                    ] if 'inserted_at' in serializer.validated_data else None,
                    updated_at=serializer.validated_data[
                        'updated_at'
                    ] if 'updated_at' in serializer.validated_data else None,
                ),
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

        + contents_original
            - Type: string
            - Status: mandatory

        + contents_preview
            - Type: string
            - Status: optional

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

        + contents_original
            - Type: string
            - Status: mandatory

        + contents_preview
            - Type: string
            - Status: optional

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

        + contents_original
            - Type: string
            - Status: mandatory

        + contents_preview
            - Type: string
            - Status: optional

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

    def get_queryset(self, inserted_at=None, updated_at=None):
        queryset = models.SlaveTell.objects.get_queryset().filter(owned_by_id=self.request.user.id)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
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

        + network_id
            - Type: integer
            - Status: optional

        + tellzone_id
            - Type: integer
            - Status: optional

        + location
            - Type: string
            - Status: optional

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
        if models.is_blocked(request.user.id, serializer.validated_data['user_destination_id']):
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


class Tellzones(ViewSet):

    permission_classes = (IsAuthenticated,)

    def get_1(self, request):
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

        + network_ids
            - Type: a comma-separated list of Network IDs
            - Status: optional

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
            - name: network_ids
              paramType: query
              required: false
              type: string
        response_serializer: api.serializers.TellzonesResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.TellzonesSearch(
            context={
                'request': request,
            },
            data=request.QUERY_PARAMS,
        )
        serializer.is_valid(raise_exception=True)
        records = {}
        network_ids = request.query_params.get('network_ids', None)
        point = 'POINT({longitude} {latitude})'.format(
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
        )
        query = '''
        SELECT
            api_tellzones.id AS id,
            api_tellzones.description AS description,
            ST_Distance(
                ST_Transform(api_tellzones.point, 2163),
                ST_Transform(ST_GeomFromText(%s, 4326), 2163)
            ) * 3.28084 AS distance,
            api_tellzones.hours AS hours,
            api_tellzones.location AS location,
            api_tellzones.name AS name,
            api_tellzones.phone AS phone,
            api_tellzones.photo AS photo,
            ST_AsGeoJSON(api_tellzones.point) AS point,
            api_tellzones.url AS url,
            api_tellzones.ended_at AS ended_at,
            api_tellzones.inserted_at AS inserted_at,
            api_tellzones.started_at AS started_at,
            api_tellzones.updated_at AS updated_at,
            api_users.id AS users_id,
            api_users.first_name AS users_first_name,
            api_users.last_name AS users_last_name,
            api_users.location AS users_location,
            api_users.photo_original AS users_photo_original,
            api_users.photo_preview AS users_photo_preview,
            api_users_settings.key AS users_settings_key,
            api_users_settings.value AS users_settings_value,
            api_tellzones_types.id AS tellzones_types_id,
            api_tellzones_types.name AS tellzones_types_name,
            api_tellzones_types.title AS tellzones_types_title,
            api_tellzones_types.icon AS tellzones_types_icon,
            api_tellzones_types.description AS tellzones_types_description,
            api_tellzones_types.position AS tellzones_types_position,
            api_tellzones_statuses.id AS tellzones_statuses_id,
            api_tellzones_statuses.name AS tellzones_statuses_name,
            api_tellzones_statuses.title AS tellzones_statuses_title,
            api_tellzones_statuses.icon AS tellzones_statuses_icon,
            api_tellzones_statuses.description AS tellzones_statuses_description,
            api_tellzones_statuses.position AS tellzones_statuses_position,
            api_tellzones_social_profiles.id AS tellzones_social_profiles_id,
            api_tellzones_social_profiles.netloc AS tellzones_social_profiles_netloc,
            api_tellzones_social_profiles.url AS tellzones_social_profiles_url,
            api_master_tells.id AS master_tells_id,
            api_master_tells.contents AS master_tells_contents,
            api_master_tells.description AS master_tells_description,
            api_master_tells.position AS master_tells_position,
            api_master_tells.is_visible AS master_tells_is_visible,
            api_master_tells.inserted_at AS master_tells_inserted_at,
            api_master_tells.updated_at AS master_tells_updated_at,
            api_categories.id AS master_tells_category_id,
            api_categories.name AS master_tells_category_name,
            api_categories.photo AS master_tells_category_photo,
            api_categories.display_type AS master_tells_category_display_type,
            api_categories.description AS master_tells_category_description,
            api_categories.position AS master_tells_category_position,
            api_users_created_by.id AS master_tells_created_by_id,
            api_users_created_by.photo_original AS master_tells_created_by_photo_original,
            api_users_created_by.photo_preview AS master_tells_created_by_photo_preview,
            api_users_created_by.first_name AS master_tells_created_by_first_name,
            api_users_created_by.last_name AS master_tells_created_by_last_name,
            api_users_created_by.description AS master_tells_created_by_description,
            api_users_created_by.location AS master_tells_created_by_location,
            api_users_settings_created_by.key AS master_tells_created_by_settings_key,
            api_users_settings_created_by.value AS master_tells_created_by_settings_value,
            api_slave_tells.id AS slave_tells_id,
            api_slave_tells.created_by_id AS slave_tells_created_by_id,
            api_slave_tells.owned_by_id AS slave_tells_owned_by_id,
            api_slave_tells.photo AS slave_tells_photo,
            api_slave_tells.first_name AS slave_tells_first_name,
            api_slave_tells.last_name AS slave_tells_last_name,
            api_slave_tells.type AS slave_tells_type,
            api_slave_tells.contents_original AS slave_tells_contents_original,
            api_slave_tells.contents_preview AS slave_tells_contents_preview,
            api_slave_tells.description AS slave_tells_description,
            api_slave_tells.position AS slave_tells_position,
            api_slave_tells.is_editable AS slave_tells_is_editable,
            api_slave_tells.inserted_at AS slave_tells_inserted_at,
            api_slave_tells.updated_at AS slave_tells_updated_at
        FROM api_tellzones
        LEFT JOIN api_users ON api_tellzones.user_id = api_users.id
        LEFT JOIN api_tellzones_types ON api_tellzones.type_id = api_tellzones_types.id
        LEFT JOIN api_tellzones_statuses ON api_tellzones.status_id = api_tellzones_statuses.id
        LEFT OUTER JOIN api_users_settings AS api_users_settings ON api_users_settings.user_id = api_users.id
        LEFT OUTER JOIN api_tellzones_social_profiles ON api_tellzones_social_profiles.tellzone_id = api_tellzones.id
        LEFT OUTER JOIN api_networks_tellzones ON api_networks_tellzones.tellzone_id = api_tellzones.id
        LEFT OUTER JOIN api_master_tells_tellzones ON api_master_tells_tellzones.tellzone_id = api_tellzones.id
        LEFT JOIN api_master_tells ON api_master_tells.id = api_master_tells_tellzones.master_tell_id
        LEFT JOIN api_users AS api_users_created_by ON api_users_created_by.id = api_master_tells.created_by_id
        LEFT OUTER JOIN api_users_settings AS api_users_settings_created_by
            ON api_users_settings_created_by.user_id = api_master_tells.created_by_id
        LEFT JOIN api_categories ON api_categories.id = api_master_tells.category_id
        LEFT OUTER JOIN api_slave_tells ON api_slave_tells.master_tell_id = api_master_tells.id
        WHERE
            ST_Distance_Sphere(api_tellzones.point, ST_GeomFromText(%s)) <= %s
            AND
            api_tellzones_statuses.name = %s
        '''
        parameters = [point, point, serializer.validated_data['radius'] * 0.3048, 'open']
        network_ids = tuple(filter(None, map(int, network_ids.split(',') if network_ids else '')))
        if network_ids:
            query = '{query:s} AND api_networks_tellzones.network_id IN %s'.format(query=query)
            parameters.append(network_ids)
        with closing(connection.cursor()) as cursor:
            cursor.execute(query, parameters)
            columns = [column.name for column in cursor.description]
            for record in cursor.fetchall():
                record = dict(zip(columns, record))
                if record['id'] not in records:
                    records[record['id']] = {
                        'type': {},
                        'status': {},
                        'social_profiles': {},
                        'master_tells': {},
                        'is_favorited': False,
                        'is_pinned': False,
                        'is_viewed': False,
                    }
                records[record['id']]['id'] = record['id']
                records[record['id']]['description'] = record['description']
                records[record['id']]['distance'] = record['distance']
                records[record['id']]['hours'] = loads(record['hours']) if record['hours'] else {}
                records[record['id']]['location'] = record['location']
                records[record['id']]['name'] = record['name']
                records[record['id']]['phone'] = record['phone']
                records[record['id']]['photo'] = record['photo']
                point = loads(record['point'])
                records[record['id']]['point'] = {
                    'latitude': str(point['coordinates'][1]),
                    'longitude': str(point['coordinates'][0]),
                }
                records[record['id']]['url'] = record['url']
                records[record['id']]['ended_at'] = record['ended_at']
                records[record['id']]['inserted_at'] = record['inserted_at']
                records[record['id']]['started_at'] = record['started_at']
                records[record['id']]['updated_at'] = record['updated_at']
                if record['users_id']:
                    if 'user' not in records[record['id']]:
                        records[record['id']]['user'] = {
                            'id': record['users_id'],
                            'first_name': record['users_first_name'],
                            'last_name': record['users_last_name'],
                            'location': record['users_location'],
                            'photo_original': record['users_photo_original'],
                            'photo_preview': record['users_photo_preview'],
                        }
                    if record['users_settings_key']:
                        if 'settings' not in records[record['id']]['user']:
                            records[record['id']]['user']['settings'] = {}
                        if record['users_settings_key'] not in records[record['id']]['user']['settings']:
                            records[record['id']]['user']['settings'][
                                record['users_settings_key']
                            ] = record['users_settings_value']
                if record['tellzones_types_id']:
                    records[record['id']]['type'] = {
                        'id': record['tellzones_types_id'],
                        'name': record['tellzones_types_name'],
                        'title': record['tellzones_types_title'],
                        'icon': record['tellzones_types_icon'],
                        'description': record['tellzones_types_description'],
                        'position': record['tellzones_types_position'],
                    }
                if record['tellzones_statuses_id']:
                    records[record['id']]['status'] = {
                        'id': record['tellzones_statuses_id'],
                        'name': record['tellzones_statuses_name'],
                        'title': record['tellzones_statuses_title'],
                        'icon': record['tellzones_statuses_icon'],
                        'description': record['tellzones_statuses_description'],
                        'position': record['tellzones_statuses_position'],
                    }
                if record['tellzones_social_profiles_id']:
                    if record['tellzones_social_profiles_id'] not in records[record['id']]['social_profiles']:
                        records[record['id']]['social_profiles'][record['tellzones_social_profiles_id']] = {
                            'id': record['tellzones_social_profiles_id'],
                            'netloc': record['tellzones_social_profiles_netloc'],
                            'url': record['tellzones_social_profiles_url'],
                        }
                if record['master_tells_id']:
                    if record['master_tells_id'] not in records[record['id']]['master_tells']:
                        records[record['id']]['master_tells'][record['master_tells_id']] = {
                            'id': record['master_tells_id'],
                            'contents': record['master_tells_contents'],
                            'description': record['master_tells_description'],
                            'position': record['master_tells_position'],
                            'is_visible': record['master_tells_is_visible'],
                            'inserted_at': record['master_tells_inserted_at'],
                            'updated_at': record['master_tells_updated_at'],
                            'slave_tells': {},
                        }
                    if record['master_tells_category_id']:
                        records[record['id']]['master_tells'][record['master_tells_id']]['category'] = {
                            'id': record['master_tells_category_id'],
                            'name': record['master_tells_category_name'],
                            'photo': record['master_tells_category_photo'],
                            'display_type': record['master_tells_category_display_type'],
                            'description': record['master_tells_category_description'],
                            'position': record['master_tells_category_position'],
                        }
                    if record['master_tells_created_by_id']:
                        if 'created_by' not in records[record['id']]['master_tells'][record['master_tells_id']]:
                            records[record['id']]['master_tells'][record['master_tells_id']]['created_by'] = {
                                'id': record['master_tells_created_by_id'],
                                'first_name': record['master_tells_created_by_first_name'],
                                'last_name': record['master_tells_created_by_last_name'],
                                'location': record['master_tells_created_by_location'],
                                'photo_original': record['master_tells_created_by_photo_original'],
                                'photo_preview': record['master_tells_created_by_photo_preview'],
                            }
                    if record['master_tells_created_by_settings_key']:
                        if (
                            'settings' not in
                            records[record['id']]['master_tells'][record['master_tells_id']]['created_by']
                        ):
                            records[
                                record['id']
                            ]['master_tells'][record['master_tells_id']]['created_by']['settings'] = {}
                        records[record['id']]['master_tells'][record['master_tells_id']]['created_by']['settings'][
                            record['master_tells_created_by_settings_key']
                        ] = record['master_tells_created_by_settings_value']
                    if record['slave_tells_id']:
                        if (
                            record['slave_tells_id'] not in
                            records[record['id']]['master_tells'][record['master_tells_id']]['slave_tells']
                        ):
                            records[
                                record['id']
                            ]['master_tells'][record['master_tells_id']]['slave_tells'][record['slave_tells_id']] = {
                                'id': record['slave_tells_id'],
                                'created_by_id': record['slave_tells_created_by_id'],
                                'owned_by_id': record['slave_tells_owned_by_id'],
                                'photo': record['slave_tells_photo'],
                                'first_name': record['slave_tells_first_name'],
                                'last_name': record['slave_tells_last_name'],
                                'type': record['slave_tells_type'],
                                'contents_original': record['slave_tells_contents_original'],
                                'contents_preview': record['slave_tells_contents_preview'],
                                'description': record['slave_tells_description'],
                                'position': record['slave_tells_position'],
                                'is_editable': record['slave_tells_is_editable'],
                                'inserted_at': record['slave_tells_inserted_at'],
                                'updated_at': record['slave_tells_updated_at'],
                            }
        for key, value in records.items():
            if 'user' not in records[key]:
                records[key]['user'] = {}
            if records[key]['user']:
                records[key]['user']['photo_original'] = (
                    records[key]['user']['photo_original']
                    if records[key]['user']['settings']['show_photo'] == 'True' else None
                )
                records[key]['user']['photo_preview'] = (
                    records[key]['user']['photo_preview']
                    if records[key]['user']['settings']['show_photo'] == 'True' else None
                )
                records[key]['user']['last_name'] = (
                    records[key]['user']['last_name']
                    if records[key]['user']['settings']['show_last_name'] == 'True' else None
                )
                del records[key]['user']['settings']
            records[key]['social_profiles'] = value['social_profiles'].values()
            for k, v in records[key]['master_tells'].items():
                records[key]['master_tells'][k]['created_by']['photo_original'] = (
                    records[key]['master_tells'][k]['created_by']['photo_original']
                    if records[key]['master_tells'][k]['created_by']['settings']['show_photo'] == 'True' else None
                )
                records[key]['master_tells'][k]['created_by']['photo_preview'] = (
                    records[key]['master_tells'][k]['created_by']['photo_preview']
                    if records[key]['master_tells'][k]['created_by']['settings']['show_photo'] == 'True' else None
                )
                records[key]['master_tells'][k]['created_by']['last_name'] = (
                    records[key]['master_tells'][k]['created_by']['last_name']
                    if records[key]['master_tells'][k]['created_by']['settings']['show_last_name'] == 'True' else None
                )
                del records[key]['master_tells'][k]['created_by']['settings']
                records[key]['master_tells'][k]['slave_tells'] = v['slave_tells'].values()
            records[key]['master_tells'] = records[key]['master_tells'].values()
        return Response(data=records.values(), status=HTTP_200_OK)

    def get_2(self, request, id):
        '''
        SELECT Tellzone

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
        response_serializer: api.serializers.TellzonesResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = models.Tellzone.objects.get_queryset().prefetch_related('social_profiles').filter(id=id).first()
        if not instance:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        return Response(
            data=serializers.TellzonesResponse(
                instance,
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request):
        '''
        INSERT Tellzones

        <pre>
        Input
        =====

        + type_id
            - Type: integer
            - Status: mandatory

        + status_id
            - Type: integer
            - Status: mandatory

        + name
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + photo
            - Type: string
            - Status: optional

        + location
            - Type: string
            - Status: optional

        + phone
            - Type: string
            - Status: optional

        + url
            - Type: string
            - Status: optional

        + hours
            - Type: string
            - Status: optional

            Example:

            {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            }

        + point
            - Type: dictionary (of floats)
            - Status: mandatory

            Example:

            {
                'latitude': 0.0000000000,
                'longitude': 0.0000000000,
            }

        + started_at
            - Type: datetime
            - Status: optional

        + ended_at
            - Type: datetime
            - Status: optional

        + social_profiles
            - Type: list (a list of Social Profile objects; see below)
            - Status: optional

        + master_tells
            - Type: list (a list of Master Tell IDs)
            - Status: optional

        + networks
            - Type: list (a list of Tellzone IDs)
            - Status: optional

        + posts
            - Type: list (a list of Post IDs)
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
              pytype: api.serializers.TellzonesRequest
        response_serializer: api.serializers.TellzonesResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.TellzonesRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.TellzonesResponse(
                serializer.insert(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_201_CREATED,
        )

    def put(self, request, id):
        '''
        UPDATE Tellzones

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + type_id
            - Type: integer
            - Status: mandatory

        + status_id
            - Type: integer
            - Status: mandatory

        + name
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + photo
            - Type: string
            - Status: optional

        + location
            - Type: string
            - Status: optional

        + phone
            - Type: string
            - Status: optional

        + url
            - Type: string
            - Status: optional

        + hours
            - Type: string
            - Status: optional

            Example:

            {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            }

        + point
            - Type: dictionary (of floats)
            - Status: mandatory

            Example:

            {
                'latitude': 0.0000000000,
                'longitude': 0.0000000000,
            }

        + started_at
            - Type: datetime
            - Status: optional

        + ended_at
            - Type: datetime
            - Status: optional

        + social_profiles
            - Type: list (a list of Social Profile objects; see below)
            - Status: optional

        + master_tells
            - Type: list (a list of Master Tell IDs)
            - Status: optional

        + networks
            - Type: list (a list of Tellzone IDs)
            - Status: optional

        + posts
            - Type: list (a list of Post IDs)
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
              pytype: api.serializers.TellzonesRequest
        response_serializer: api.serializers.TellzonesResponse
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
        serializer = serializers.TellzonesRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.TellzonesResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def patch(self, request, id):
        '''
        UPDATE Tellzones

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + type_id
            - Type: integer
            - Status: mandatory

        + status_id
            - Type: integer
            - Status: mandatory

        + name
            - Type: string
            - Status: mandatory

        + description
            - Type: string
            - Status: optional

        + photo
            - Type: string
            - Status: optional

        + location
            - Type: string
            - Status: optional

        + phone
            - Type: string
            - Status: optional

        + url
            - Type: string
            - Status: optional

        + hours
            - Type: string
            - Status: optional

            Example:

            {
                'Mon': '09:00 am - 05:00 pm',
                'Tue': '09:00 am - 05:00 pm',
                'Wed': '09:00 am - 05:00 pm',
                'Thu': '09:00 am - 05:00 pm',
                'Fri': '09:00 am - 05:00 pm',
                'Sat': '09:00 am - 05:00 pm',
                'Sun': '09:00 pm - 05:00 pm',
            }

        + point
            - Type: dictionary (of floats)
            - Status: mandatory

            Example:

            {
                'latitude': 0.0000000000,
                'longitude': 0.0000000000,
            }

        + started_at
            - Type: datetime
            - Status: optional

        + ended_at
            - Type: datetime
            - Status: optional

        + social_profiles
            - Type: list (a list of Social Profile objects; see below)
            - Status: optional

        + master_tells
            - Type: list (a list of Master Tell IDs)
            - Status: optional

        + networks
            - Type: list (a list of Tellzone IDs)
            - Status: optional

        + posts
            - Type: list (a list of Post IDs)
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
              pytype: api.serializers.TellzonesRequest
        response_serializer: api.serializers.TellzonesResponse
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
        serializer = serializers.TellzonesRequest(
            instance,
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.TellzonesResponse(
                serializer.update(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def delete(self, request, id):
        '''
        DELETE Tellzones

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
        return models.Tellzone.objects.get_queryset().filter(id=id).first()


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

        + password
            - Type: string
            - Status: optional

        + photo_original
            - Type: string
            - Status: optional

        + photo_preview
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
                'show_last_name': false,
                'show_phone': false,
                'show_photo': true,
                'show_photos': true,
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

        + string_original
            - Type: string
            - Status: mandatory

        + string_preview
            - Type: string
            - Status: optional

        + description
            - Type: string
            - Status: optional

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

        + string_original
            - Type: string
            - Status: mandatory

        + string_preview
            - Type: string
            - Status: optional

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

        + is_visible
            - Type: boolean (default = True)
            - Status: optional

        Note: If you want to unset/remove a value, skip the corresponding key.

            Example 1:

            {
                ...,
                ...,
                ...,
                'phone': '1234567890',
                ...,
                ...,
                ...,
            }

            This will set the `phone` to '1234567890'.

            {
                ...,
                ...,
                ...,
                ...,
                ...,
                ...,
            }

            This will unset/remove the `phone`.

            Example 2:

            {
                ...,
                ...,
                ...,
                'status': {
                    ...,
                    ...,
                    ...,
                },
                ...,
                ...,
                ...,
            }

            This will set the `status` (DELETE old record and INSERT new record).

            {
                ...,
                ...,
                ...,
                ...,
                ...,
                ...,
            }

            This will unset/remove the `status`.

            Example 3:

            {
                ...,
                ...,
                ...,
                'photos': [
                    ...,
                    ...,
                    ...,
                ],
                ...,
                ...,
                ...,
            }

            This will set the `photos` (INSERT/UPDATE new records and DELETE old/unused/unreferenced records).

            {
                ...,
                ...,
                ...,
                ...,
                ...,
                ...,
            }

            This will unset/remove all the `photos`.

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

        + id
            - Type: integer
            - Status: mandatory

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
        point = None
        user_location = models.UserLocation.objects.get_queryset().filter(user_id=request.user.id).first()
        if user_location:
            point = user_location.point
        return Response(
            data=serializers.UsersTellzonesGet(
                sorted(
                    [
                        user_tellzone.tellzone
                        for user_tellzone in models.UserTellzone.objects.get_queryset().prefetch_related(
                            'tellzone__social_profiles',
                        ).filter(
                            user_id=request.user.id,
                            favorited_at__isnull=False,
                        )
                    ],
                    key=lambda tellzone: (
                        -tellzone.tellecasters, self.get_distance(tellzone.point, point), -tellzone.id
                    ),
                ),
                context={
                    'point': point,
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, id):
        '''
        INSERT/UPDATE (Favorite, Pin, View) Users :: Tellzones

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + tellzone_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - Favorite
                - Pin
                - View

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
        DELETE (Favorite, Pin, View) Users :: Tellzones

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        + tellzone_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - Favorite
                - Pin
                - View

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

    def get_distance(self, point_1, point_2):
        if not point_1 or not point_2:
            return 0.00
        return vincenty((point_1.x, point_1.y), (point_2.x, point_2.y)).ft


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def versions(request):
    '''
    SELECT Versions

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.Versions
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    return Response(
        data=serializers.Versions(
            models.Version.objects.get_queryset(),
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
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
def authenticate_1(request):
    '''
    Authenticate Users

    <pre>
    Input
    =====

    + email
        - Type: string
        - Status: mandatory

    + password
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
          pytype: api.serializers.Authenticate1Request
    response_serializer: api.serializers.Authenticate1Response
    responseMessages:
        - code: 400
          message: Invalid Input
        - code: 401
          message: Invalid Input
    '''
    serializer = serializers.Authenticate1Request(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    user = models.User.objects.get_queryset().filter(email=serializer.validated_data['email']).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if not user.is_verified:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if not user.password:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `password`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if hashpw(serializer.validated_data['password'].encode('utf-8'), user.password.encode('utf-8')) != user.password:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `password`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    request.user = user
    request.user.sign_in()
    return Response(
        data=serializers.Authenticate1Response(
            user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes(())
def authenticate_2(request, backend):
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
            - google-oauth2
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
              "facebook", "google-oauth2" and "linkedin-oauth2" are supported. Reference:
              http://psa.matiasaguirre.net/docs/backends/index.html
          name: backend
          paramType: path
          required: true
          type: string
        - name: body
          paramType: body
          pytype: api.serializers.Authenticate2Request
    response_serializer: api.serializers.Authenticate2Response
    responseMessages:
        - code: 400
          message: Invalid Input
        - code: 401
          message: Invalid Input
    '''
    if backend not in ['facebook', 'google-oauth2', 'linkedin-oauth2']:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `backend`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    backend = get_backend(settings.AUTHENTICATION_BACKENDS, backend)(strategy=DjangoStrategy(storage=DjangoStorage()))
    if not backend or backend.name not in ['facebook', 'google-oauth2', 'linkedin-oauth2']:
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
    if not user.is_verified:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `user`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    request.user = user
    request.user.sign_in()
    return Response(
        data=serializers.Authenticate2Response(
            user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def categories(request):
    '''
    SELECT Categries

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.Categories
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    return Response(
        data=serializers.Categories(
            models.Category.objects.get_queryset(),
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def deauthenticate(request):
    '''
    Deauthenticate Users

    <pre>
    Input
    =====

    + type
        - Type: string
        - Status: optional
        - Choices:
            - APNS
            - GCM

    + device_id
        - Description: Only applicable if `type` = 'GCM'.
        - Type: UUID
        - Status: optional

    + registration_id
        - Description: Only applicable if `type` = 'APNS'.
        - Type: string
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
          pytype: api.serializers.DeauthenticateRequest
    response_serializer: api.serializers.DeauthenticateResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.DeauthenticateRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    serializer.process()
    request.user.sign_out()
    return Response(data=serializers.DeauthenticateResponse().data, status=HTTP_200_OK)


@api_view(('POST',))
@permission_classes(())
def forgot_password(request):
    '''
    Forgot Password

    <pre>
    Input
    =====

    + email
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
          pytype: api.serializers.ForgotPassword
    response_serializer: api.serializers.Null
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.ForgotPassword(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    user = models.User.objects.get_queryset().filter(email=serializer.validated_data['email']).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if not user.is_verified:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    current_app.send_task(
        'api.tasks.email_notifications',
        (user.id, 'reset_password',),
        queue='api.tasks.email_notifications',
        routing_key='api.tasks.email_notifications',
        serializer='json',
    )
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
    data = {
        'days': {},
        'trailing_24_hours': 0,
        'users': [],
    }
    now = datetime.now()
    today = date.today()
    days = get_days(today)
    for day in days:
        data['days'][day] = 0
    if serializer.validated_data['dummy'] == 'Yes':
        for day in days:
            data['days'][day] = randint(1, 150)
        data['trailing_24_hours'] = randint(1, 150)
        data['users'] = [
            {
                'user': user,
                'tellzone': models.Tellzone.objects.get_queryset().prefetch_related(
                    'social_profiles',
                ).order_by('?').first(),
                'location': None,
                'point': user.point,
                'timestamp': datetime.now() - timedelta(days=randint(1, 7)),
            }
            for user in models.User.objects.get_queryset().exclude(id=request.user.id).order_by('?')[0:5]
        ]
    else:
        data['users'] = {}
        records = []
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    DISTINCT ON (api_users_locations_2.user_id)
                    api_users_locations_2.user_id,
                    api_users_locations_2.tellzone_id,
                    api_users_locations_2.location,
                    ST_AsGeoJSON(api_users_locations_2.point),
                    api_users_locations_2.timestamp
                FROM api_users_locations api_users_locations_1
                INNER JOIN api_users_locations api_users_locations_2 ON
                    api_users_locations_1.user_id = %s
                    AND
                    api_users_locations_2.user_id != %s
                    AND
                    api_users_locations_1.timestamp BETWEEN
                        NOW() - INTERVAL '25 hour'
                        AND
                        NOW() - INTERVAL '1 hour'
                    AND
                    api_users_locations_2.timestamp BETWEEN
                        NOW() - INTERVAL '25 hour'
                        AND
                        NOW() - INTERVAL '1 hour'
                    AND
                    api_users_locations_1.timestamp BETWEEN
                        api_users_locations_2.timestamp - INTERVAL '1 minute'
                        AND
                        api_users_locations_2.timestamp + INTERVAL '1 minute'
                    AND
                    ST_DWithin(
                        ST_Transform(api_users_locations_1.point, 2163),
                        ST_Transform(api_users_locations_2.point, 2163),
                        91.44
                    )
                LEFT OUTER JOIN api_tellcards ON
                    api_tellcards.user_source_id = api_users_locations_1.user_id
                    AND
                    api_tellcards.user_destination_id = api_users_locations_2.user_id
                LEFT OUTER JOIN api_messages ON
                    api_messages.user_source_id = api_users_locations_1.user_id
                    AND
                    api_messages.user_destination_id = api_users_locations_2.user_id
                WHERE
                    api_tellcards.id IS NULL
                    AND
                    api_messages.id IS NULL
                GROUP BY api_users_locations_2.id
                ORDER BY api_users_locations_2.user_id ASC , api_users_locations_2.timestamp DESC
                ''',
                (request.user.id, request.user.id,)
            )
            records = cursor.fetchall()
        for record in records:
            if record[4] > now - timedelta(hours=24):
                data['trailing_24_hours'] += 1
            d = record[4].date().isoformat()
            if d in data['days']:
                data['days'][d] += 1
            if record[0] not in data['users']:
                p = loads(record[3])
                data['users'][record[0]] = {
                    'user': models.User.objects.get_queryset().filter(id=record[0]).first(),
                    'tellzone': models.Tellzone.objects.get_queryset().prefetch_related(
                        'social_profiles',
                    ).filter(
                        id=record[1],
                    ).first(),
                    'location': record[2],
                    'point': {
                        'latitude': p['coordinates'][1],
                        'longitude': p['coordinates'][0],
                    },
                    'timestamp': record[4],
                }
        data['users'] = data['users'].values()
    return Response(
        data=serializers.HomeConnectionsResponse(
            data,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home_master_tells(request):
    '''
    SELECT (Master Tells) Home

    <pre>
    Input
    =====

    + latitude
        - Type: float
        - Status: mandatory

    + longitude
        - Type: float
        - Status: mandatory

    + tellzone_id
        - Type: integer
        - Status: optional

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
        - name: tellzone_id
          paramType: query
          required: false
          type: integer
        - name: dummy
          paramType: query
          required: false
          type: string
    response_serializer: api.serializers.HomeMasterTellsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.HomeMasterTellsRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    return Response(
        data=models.get_master_tells(
            request.user.id,
            serializer.validated_data['tellzone_id'],
            [(0, serializer.validated_data['longitude'], serializer.validated_data['latitude'],)],
            (models.Tellzone.radius() * 0.3048) if not serializer.validated_data['dummy'] == 'Yes' else 999999999,
        ),
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
    point = models.get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
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
            '-id',
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
            '-id',
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
    point = models.get_point(serializer.validated_data['latitude'], serializer.validated_data['longitude'])
    if serializer.validated_data['dummy'] == 'Yes':
        tellzones = models.Tellzone.objects.get_queryset().prefetch_related(
            'social_profiles',
        ).distance(point).order_by('?')[0:5]
    else:
        tellzones = models.Tellzone.objects.get_queryset().prefetch_related(
            'social_profiles',
        ).filter(
            point__distance_lte=(point, D(mi=10)),
        ).distance(
            point,
        ).order_by(
            'distance',
            '-id',
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
def master_tells_all(request, *args, **kwargs):
    '''
    SELECT Master Tells :: All
    <br>
    <br>
    This endpoint will return a list of all master tells pinned in all tellzones:
    <br>1. Where given user ({user_id}) has pinned atleast one master tell.
    <br>2. Which the given user ({user_id}) has pinned.
    <br>3. Which the given user ({user_id}) has favorited.
    <br>
    <br>Notes:
    <br>1. Master Tells owned by the given user ({user_id}) will be excluded.
    <br>2. {tellzone_id}, if specified, will be excluded.

    <pre>
    Input
    =====

    + user_id
        - Type: integer
        - Status: mandatory

    + tellzone_id
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
        - name: user_id
          paramType: query
          required: true
          type: integer
        - name: tellzone_id
          paramType: query
          type: integer
    response_serializer: api.serializers.MasterTellsAllResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.MasterTellsAllRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    master_tells = {}
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            '''
            SELECT
                api_master_tells.id AS id,
                api_master_tells.contents AS contents,
                api_master_tells.description AS description,
                api_master_tells.position AS position,
                api_master_tells.is_visible AS is_visible,
                api_master_tells.inserted_at AS inserted_at,
                api_master_tells.updated_at AS updated_at,
                true AS is_pinned,
                api_slave_tells.id AS slave_tell_id,
                api_slave_tells.created_by_id AS slave_tell_created_by_id,
                api_slave_tells.owned_by_id AS slave_tell_owned_by_id,
                api_slave_tells.photo AS slave_tell_photo,
                api_slave_tells.first_name AS slave_tell_first_name,
                api_slave_tells.last_name AS slave_tell_last_name,
                api_slave_tells.type AS slave_tell_type,
                api_slave_tells.contents_original AS slave_tell_contents_original,
                api_slave_tells.contents_preview AS slave_tell_contents_preview,
                api_slave_tells.description AS slave_tell_description,
                api_slave_tells.position AS slave_tell_position,
                api_slave_tells.is_editable AS slave_tell_is_editable,
                api_slave_tells.inserted_at AS slave_tell_inserted_at,
                api_slave_tells.updated_at AS slave_tell_updated_at,
                api_users_created_by.id AS created_by_id,
                api_users_created_by.photo_original AS created_by_photo_original,
                api_users_created_by.photo_preview AS created_by_photo_preview,
                api_users_created_by.first_name AS created_by_first_name,
                api_users_created_by.last_name AS created_by_last_name,
                api_users_created_by.description AS created_by_description,
                api_users_settings_created_by.key AS created_by_setting_key,
                api_users_settings_created_by.value AS created_by_setting_value,
                api_users_owned_by.id AS owned_by_id,
                api_users_owned_by.photo_original AS owned_by_photo_original,
                api_users_owned_by.photo_preview AS owned_by_photo_preview,
                api_users_owned_by.first_name AS owned_by_first_name,
                api_users_owned_by.last_name AS owned_by_last_name,
                api_users_owned_by.description AS owned_by_description,
                api_users_settings_owned_by.key AS owned_by_setting_key,
                api_users_settings_owned_by.value AS owned_by_setting_value,
                api_categories.id AS category_id,
                api_categories.name AS category_name,
                api_categories.photo AS category_photo,
                api_categories.display_type AS category_display_type,
                api_categories.description AS category_description,
                api_categories.position AS category_position,
                api_tellzones.id AS tellzone_id,
                api_tellzones.name AS tellzone_name
            FROM api_master_tells_tellzones
            INNER JOIN api_master_tells ON api_master_tells.id = api_master_tells_tellzones.master_tell_id
            INNER JOIN api_tellzones ON api_tellzones.id = api_master_tells_tellzones.tellzone_id
            LEFT OUTER JOIN api_slave_tells ON api_slave_tells.master_tell_id = api_master_tells.id
            INNER JOIN api_users AS api_users_created_by
                ON api_users_created_by.id = api_master_tells.created_by_id
            LEFT OUTER JOIN api_users_settings AS api_users_settings_created_by
                ON api_users_settings_created_by.user_id = api_master_tells.created_by_id
            INNER JOIN api_users AS api_users_owned_by
                ON api_users_owned_by.id = api_master_tells.owned_by_id
            LEFT OUTER JOIN api_users_settings AS api_users_settings_owned_by
                ON api_users_settings_owned_by.user_id = api_master_tells.owned_by_id
            INNER JOIN api_categories ON api_categories.id = api_master_tells.category_id
            LEFT OUTER JOIN api_blocks ON
                (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_master_tells.owned_by_id)
                OR
                (api_blocks.user_source_id = api_master_tells.owned_by_id AND api_blocks.user_destination_id = %s)
            WHERE
                api_master_tells.owned_by_id != %s
                AND
                api_master_tells_tellzones.tellzone_id IN (
                    SELECT tellzone_id
                    FROM api_users_tellzones
                    WHERE
                        user_id = %s
                        AND
                        tellzone_id != %s
                        AND
                        (pinned_at IS NOT NULL OR favorited_at IS NOT NULL)
                    UNION
                    SELECT tellzone_id
                    FROM api_master_tells_tellzones
                    INNER JOIN api_master_tells ON api_master_tells.id = api_master_tells_tellzones.master_tell_id
                    WHERE
                        api_master_tells_tellzones.tellzone_id != %s
                        AND
                        api_master_tells.owned_by_id = %s
                )
                AND
                api_blocks.id IS NULL
            ORDER BY api_master_tells.id ASC, api_slave_tells.position ASC
            ''',
            (
                serializer.validated_data['user_id'],
                serializer.validated_data['user_id'],
                serializer.validated_data['user_id'],
                serializer.validated_data['user_id'],
                serializer.validated_data['tellzone_id'],
                serializer.validated_data['tellzone_id'],
                serializer.validated_data['user_id'],
            )
        )
        columns = [column.name for column in cursor.description]
        for record in cursor.fetchall():
            record = dict(zip(columns, record))
            if record['id'] not in master_tells:
                master_tells[record['id']] = {}
            if 'id' not in master_tells[record['id']]:
                master_tells[record['id']]['id'] = record['id']
            if 'contents' not in master_tells[record['id']]:
                master_tells[record['id']]['contents'] = record['contents']
            if 'description' not in master_tells[record['id']]:
                master_tells[record['id']]['description'] = record['description']
            if 'position' not in master_tells[record['id']]:
                master_tells[record['id']]['position'] = record['position']
            if 'is_visible' not in master_tells[record['id']]:
                master_tells[record['id']]['is_visible'] = record['is_visible']
            if 'inserted_at' not in master_tells[record['id']]:
                master_tells[record['id']]['inserted_at'] = record['inserted_at']
            if 'updated_at' not in master_tells[record['id']]:
                master_tells[record['id']]['updated_at'] = record['updated_at']
            if 'is_pinned' not in master_tells[record['id']]:
                master_tells[record['id']]['is_pinned'] = record['is_pinned']
            if 'slave_tells' not in master_tells[record['id']]:
                master_tells[record['id']]['slave_tells'] = {}
            if record['slave_tell_id']:
                if record['slave_tell_id'] not in master_tells[record['id']]['slave_tells']:
                    master_tells[record['id']]['slave_tells'][record['slave_tell_id']] = {
                        'id': record['slave_tell_id'],
                        'created_by_id': record['slave_tell_created_by_id'],
                        'owned_by_id': record['slave_tell_owned_by_id'],
                        'photo': record['slave_tell_photo'],
                        'first_name': record['slave_tell_first_name'],
                        'last_name': record['slave_tell_last_name'],
                        'type': record['slave_tell_type'],
                        'contents_original': record['slave_tell_contents_original'],
                        'contents_preview': record['slave_tell_contents_preview'],
                        'description': record['slave_tell_description'],
                        'position': record['slave_tell_position'],
                        'is_editable': record['slave_tell_is_editable'],
                        'inserted_at': record['slave_tell_inserted_at'],
                        'updated_at': record['slave_tell_updated_at'],
                    }
            if 'created_by' not in master_tells[record['id']]:
                master_tells[record['id']]['created_by'] = {
                    'id': record['created_by_id'],
                    'photo_original': record['created_by_photo_original'],
                    'photo_preview': record['created_by_photo_preview'],
                    'first_name': record['created_by_first_name'],
                    'last_name': record['created_by_last_name'],
                    'description': record['created_by_description'],
                }
            if 'settings' not in master_tells[record['id']]['created_by']:
                master_tells[record['id']]['created_by']['settings'] = {}
            if record['created_by_setting_key']:
                if record['created_by_setting_key'] not in master_tells[record['id']]['created_by']['settings']:
                    master_tells[record['id']]['created_by']['settings'][
                        record['created_by_setting_key']
                    ] = record['created_by_setting_value']
            if 'owned_by' not in master_tells[record['id']]:
                master_tells[record['id']]['owned_by'] = {
                    'id': record['owned_by_id'],
                    'photo_original': record['owned_by_photo_original'],
                    'photo_preview': record['owned_by_photo_preview'],
                    'first_name': record['owned_by_first_name'],
                    'last_name': record['owned_by_last_name'],
                    'description': record['owned_by_description'],
                }
            if 'settings' not in master_tells[record['id']]['owned_by']:
                master_tells[record['id']]['owned_by']['settings'] = {}
            if record['owned_by_setting_key']:
                if record['owned_by_setting_key'] not in master_tells[record['id']]['owned_by']['settings']:
                    master_tells[record['id']]['owned_by']['settings'][
                        record['owned_by_setting_key']
                    ] = record['owned_by_setting_value']
            if 'category' not in master_tells[record['id']]:
                master_tells[record['id']]['category'] = {
                    'id': record['category_id'],
                    'name': record['category_name'],
                    'photo': record['category_photo'],
                    'display_type': record['category_display_type'],
                    'description': record['category_description'],
                    'position': record['category_position'],
                }
            if 'tellzones' not in master_tells[record['id']]:
                master_tells[record['id']]['tellzones'] = {}
            if (
                'tellzone_id' in record and record['tellzone_id'] and
                'tellzone_name' in record and record['tellzone_name']
            ):
                master_tells[record['id']]['tellzones'][record['tellzone_id']] = {
                    'id': record['tellzone_id'],
                    'name': record['tellzone_name'],
                }
    master_tells = sorted(master_tells.values(), key=lambda item: item['id'])
    for key, value in enumerate(master_tells):
        master_tells[key]['created_by']['photo_original'] = (
            master_tells[key]['created_by']['photo_original']
            if master_tells[key]['created_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['created_by']['photo_preview'] = (
            master_tells[key]['created_by']['photo_preview']
            if master_tells[key]['created_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['created_by']['last_name'] = (
            master_tells[key]['created_by']['last_name']
            if master_tells[key]['created_by']['settings']['show_last_name'] == 'True' else None
        )
        master_tells[key]['owned_by']['photo_original'] = (
            master_tells[key]['owned_by']['photo_original']
            if master_tells[key]['owned_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['owned_by']['photo_preview'] = (
            master_tells[key]['owned_by']['photo_preview']
            if master_tells[key]['owned_by']['settings']['show_photo'] == 'True' else None
        )
        master_tells[key]['owned_by']['last_name'] = (
            master_tells[key]['owned_by']['last_name']
            if master_tells[key]['owned_by']['settings']['show_last_name'] == 'True' else None
        )
        del master_tells[key]['created_by']['settings']
        del master_tells[key]['owned_by']['settings']
        master_tells[key]['slave_tells'] = sorted(
            master_tells[key]['slave_tells'].values(), key=lambda item: item['position'],
        )
        master_tells[key]['tellzones'] = sorted(master_tells[key]['tellzones'].values(), key=lambda item: item['id'])
    return Response(data=master_tells, status=HTTP_200_OK)


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def master_tells_ids(request, *args, **kwargs):
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
def master_tells_positions(request, *args, **kwargs):
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

    + user_status_id
        - Type: integer
        - Status: optional

    + master_tell_id
        - Type: integer
        - Status: optional

    + post_id
        - Type: integer
        - Status: optional

    Output
    ======

    (see below; "Response Class" -> "Model Schema")

    Push Notification
    =================

    {
        'action': 'updateThread',
        'type': 'message',
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
    queryset = models.Message.objects.get_queryset().filter(
        Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_id']) |
        Q(user_source_id=serializer.validated_data['user_id'], user_destination_id=request.user.id)
    )
    if serializer.validated_data['user_status_id']:
        queryset = queryset.filter(user_status_id=serializer.validated_data['user_status_id'])
    else:
        queryset = queryset.filter(user_status_id__isnull=True)
    if serializer.validated_data['master_tell_id']:
        queryset = queryset.filter(master_tell_id=serializer.validated_data['master_tell_id'])
    else:
        queryset = queryset.filter(master_tell_id__isnull=True)
    if serializer.validated_data['post_id']:
        queryset = queryset.filter(post_id=serializer.validated_data['post_id'])
    else:
        queryset = queryset.filter(post_id__isnull=True)
    for message in queryset.select_related(
        'user_source',
        'user_destination',
        'user_status',
        'master_tell',
        'post',
    ).order_by('id'):
        if message.user_source_id == request.user.id:
            message.user_source_is_hidden = True
        if message.user_destination_id == request.user.id:
            message.user_destination_is_hidden = True
        message.save()
        if not message.is_suppressed:
            messages.append(message)
    current_app.send_task(
        'api.tasks.push_notifications',
        (
            request.user.id,
            {
                'action': 'updateThread',
                'aps': {},
                'type': 'message',
            },
        ),
        queue='api.tasks.push_notifications',
        routing_key='api.tasks.push_notifications',
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

    + user_status_id
        - Type: integer
        - Status: optional

    + master_tell_id
        - Type: integer
        - Status: optional

    + post_id
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
    queryset = models.Message.objects.get_queryset().filter(
        user_source_id=serializer.validated_data['user_id'],
        user_destination_id=request.user.id,
    )
    if serializer.validated_data['user_status_id']:
        queryset = queryset.filter(user_status_id=serializer.validated_data['user_status_id'])
    else:
        queryset = queryset.filter(user_status_id__isnull=True)
    if serializer.validated_data['master_tell_id']:
        queryset = queryset.filter(master_tell_id=serializer.validated_data['master_tell_id'])
    else:
        queryset = queryset.filter(master_tell_id__isnull=True)
    if serializer.validated_data['post_id']:
        queryset = queryset.filter(post_id=serializer.validated_data['post_id'])
    else:
        queryset = queryset.filter(post_id__isnull=True)
    for message in queryset.select_related(
        'user_source',
        'user_destination',
        'user_status',
        'master_tell',
        'post',
    ).order_by('id'):
        message.status = 'Read'
        message.save()
        if not message.is_suppressed:
            messages.append(message)
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


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def networks_master_tells(request, id):
    '''
    SELECT (Master Tells) Networks

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
    omit_parameters:
        - form
    parameters:
        - name: tellzone_id
          paramType: query
          required: false
          type: integer
    response_serializer: api.serializers.NetworksMasterTellsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    network = models.Network.objects.get_queryset().filter(id=id).first()
    if not network:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    serializer = serializers.NetworksMasterTellsRequest(
        context={
            'request': request,
        },
        data=request.query_params,
    )
    serializer.is_valid(raise_exception=True)
    return Response(
        data=models.get_master_tells(
            request.user.id,
            serializer.validated_data['tellzone_id'],
            [
                (network_tellzone.tellzone.id, network_tellzone.tellzone.point.x, network_tellzone.tellzone.point.y,)
                for network_tellzone in network.networks_tellzones.get_queryset()
            ],
            models.Tellzone.radius() * 0.3048,
        ),
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def networks_tellzones(request, id):
    '''
    SELECT (Tellzones) Networks

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
    response_serializer: api.serializers.TellzonesResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    network = models.Network.objects.get_queryset().filter(id=id).first()
    if not network:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    return Response(
        data=serializers.TellzonesResponse(
            [network_tellzone.tellzone for network_tellzone in network.networks_tellzones.get_queryset()], many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def profiles(request):
    '''
    SELECT (Profiles) Users

    <pre>
    Input
    =====

    + ids
        - Type: a list of User IDs
        - Status: mandatory

        Example:

        {
            "ids": [...]
        }

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
          pytype: api.serializers.ProfilesRequest
    response_serializer: api.serializers.ProfilesResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.ProfilesRequest(
        context={
            'request': request,
        },
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)
    return Response(
        data=serializers.ProfilesResponse(
            [
                user
                for user in models.User.objects.get_queryset().filter(
                    id__in=serializer.validated_data['ids'],
                ).order_by(
                    'id',
                )
                if not models.is_blocked(request.user.id, user.id)
            ],
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes(())
def recommended_tells(request, type):
    '''
    SELECT Recommended Tells

    <pre>
    Input
    =====

    + type
        - Type: string
        - Status: mandatory
        - Choices:
            - Hobby
            - Mind
            - Passion

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: type
          paramType: path
          required: true
          type: string
    response_serializer: api.serializers.RecommendedTellsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.RecommendedTellsRequest(
        context={
            'request': request,
        },
        data={
            'type': type,
        },
    )
    serializer.is_valid(raise_exception=True)
    return Response(
        data=serializers.RecommendedTellsResponse(
            models.RecommendedTell.objects.get_queryset().filter(type=serializer.validated_data['type']),
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

    + password
        - Type: string
        - Status: mandatory (optional, if social_profiles is provided)

    + photo_original
        - Type: string
        - Status: optional

    + photo_preview
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

    + access_code
        - Type: string
        - Status: optional

    + settings
        - Type: dictionary
        - Status: mandatory

        Example:

        {
            'notifications_invitations': true,
            'notifications_messages': true,
            'notifications_saved_you': true,
            'notifications_shared_profiles': true,
            'show_email': false,
            'show_last_name': false,
            'show_phone': false,
            'show_photo': true,
            'show_photos': true,
        }

    + photos (see /api/users/ for more details)
        - Type: list (a list of Photo objects)
        - Status: optional

    + social_profiles (see /api/users/ for more details)
        - Type: list (a list of Social Profile objects)
        - Status: mandatory (either "facebook.com" or "google.com" or "linkedin.com" is mandatory)
                            (optional, if password is provided)

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
        - code: 401
          message: Invalid Input
        - code: 403
          message: Invalid Input
    '''
    serializer = serializers.RegisterRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    user = models.User.objects.get_queryset().filter(email=serializer.validated_data['email']).first()
    if user:
        if user.is_verified:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `email`'),
                },
                status=HTTP_403_FORBIDDEN,
            )
        else:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `email`'),
                },
                status=HTTP_401_UNAUTHORIZED,
            )
    if not serializer.is_valid_(request.DATA):
        return Response(
            data={
                'error': ugettext_lazy('Invalid `password`/`access_token`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    request.user = serializer.insert()
    return Response(
        data=serializers.RegisterResponse(
            request.user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_201_CREATED,
    )


@api_view(('POST',))
@permission_classes(())
def reset_password(request):
    '''
    Reset Password

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: mandatory

    + hash
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
          pytype: api.serializers.ResetPasswordRequest
    response_serializer: api.serializers.ResetPasswordResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.ResetPasswordRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    user = models.User.objects.get_queryset().filter(id=serializer.validated_data['id']).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    if not user.is_verified:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    token = ''
    try:
        token = urlsafe_b64decode(serializer.validated_data['hash'].encode('utf-8'))
    except Exception:
        pass
    if not user.is_valid(token):
        return Response(
            data={
                'error': ugettext_lazy('Invalid `hash`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    return Response(
        data=serializers.ResetPasswordResponse(
            user,
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
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


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def tellzones_ids(request):
    '''
    SELECT Tellzones

    <pre>
    Input
    =====

    + ids
        - Type: a list of Tellzone IDs
        - Status: mandatory

        Example:

        {
            "ids": [...]
        }

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
          pytype: api.serializers.TellzonesIDsRequest
    response_serializer: api.serializers.TellzonesIDsResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.TellzonesIDsRequest(
        context={
            'request': request,
        },
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)
    return Response(
        data=serializers.TellzonesIDsResponse(
            sorted(
                [
                    tellzone
                    for tellzone in models.Tellzone.objects.get_queryset().prefetch_related(
                        'social_profiles',
                    ).filter(
                        id__in=serializer.validated_data['ids'],
                    )
                ],
                key=lambda tellzone: (-tellzone.tellecasters, -tellzone.id),
            ),
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
    return Response(
        data=models.get_master_tells(
            request.user.id,
            0,
            [(tellzone.id, tellzone.point.x, tellzone.point.y,)],
            models.Tellzone.radius() * 0.3048,
        ),
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def tellzones_types(request):
    '''
    SELECT Tellzones :: Types

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.TellzoneType
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    return Response(
        data=serializers.TellzoneType(
            models.TellzoneType.objects.get_queryset(),
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def tellzones_statuses(request):
    '''
    SELECT Tellzones :: Statuses

    <pre>
    Input
    =====

    + N/A

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    response_serializer: api.serializers.TellzoneStatus
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    return Response(
        data=serializers.TellzoneStatus(
            models.TellzoneStatus.objects.get_queryset(),
            context={
                'request': request,
            },
            many=True,
        ).data,
        status=HTTP_200_OK,
    )


def users(request, platform):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('admin:api_user_changelist'))
    if not platform in ['Android', 'iOS']:
        return HttpResponseRedirect(reverse('admin:api_user_changelist'))
    for user in models.User.objects.all():
        if user.last_name == platform:
            user.delete()
    fake = Faker()
    with middleware.mixer.ctx(commit=False):
        for user in middleware.mixer.cycle(10).blend('api.User'):
            tellzone = models.Tellzone.objects.get_queryset().order_by('?').first()
            user.photo_original = fake.image_url()
            user.photo_preview = fake.image_url()
            user.first_name = fake.first_name_male()
            user.last_name = platform
            user.date_of_birth = fake.date(pattern='%Y-%m-%d')
            user.gender = 'Male'
            user.location = fake.street_name()
            user.description = fake.text(max_nb_chars=200)
            user.phone = fake.phone_number()
            user.point = tellzone.point
            user.is_verified = True
            user.is_signed_in = True
            user.tellzone = tellzone
            user.save()
            for tellzone in models.Tellzone.objects.get_queryset().exclude(id=user.tellzone.id).order_by('?')[0:3]:
                models.UserTellzone.objects.create(
                    user=user,
                    tellzone=tellzone,
                    favorited_at=datetime.now(),
                    pinned_at=None,
                    viewed_at=None,
                )
    messages.success(request, '10 {platform:s} Users were added successfully.'.format(platform=platform))
    return HttpResponseRedirect(reverse('admin:api_user_changelist'))


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def users_messages(request, id):
    '''
    SELECT (Messages) Users

    <pre>
    Input
    =====

    [
        1,
        2,
        3,
        4,
        5
    ]

    Output
    ======

    [
        {
            "id": "1":
            "messages": 0
        },
        {
            "id": "2",
            "messages": 0
        },
        {
            "id": "3",
            "messages": 0
        },
        {
            "id": "4",
            "messages": 0
        },
        {
            "id": "5",
            "messages": 0
        }
    ]

    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
    response_serializer: api.serializers.Null
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    items = []
    user_ids = []
    try:
        user_ids = sorted(set(request.DATA))
    except Exception:
        pass
    for user_id in user_ids:
        if not models.is_blocked(request.user.id, user_id):
            items.append({
                'id': user_id,
                'messages': request.user.get_messages(user_id),
            })
    return Response(data=items, status=HTTP_200_OK)


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
        - code: 403
          message: Invalid Input
    '''
    if request.user.is_authenticated():
        if models.is_blocked(request.user.id, id):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_403_FORBIDDEN,
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


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def users_tellzones_all(request, id):
    '''
    SELECT Users :: Tellzones
    <br>
    <br>
    This endpoint will return a list of all tellzones:
    <br>
    1. Where the given user ({id}) is currently in.
    <br>
    2. Where the given user ({id}) has pinned a master tell.
    <br>
    3. Which the given user ({id}) has favorited.
    <br>
    4. Which the given user ({id}) has pinned.
    <br>
    5. Which the given user ({id}) owns.

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")

    + source
        - Type: integer
        - Status: mandatory
        - Choices:
            1 = Where the given user ({id}) is currently in.
            2 = Where the given user ({id}) has pinned a master tell.
            3 = Which the given user ({id}) has favorited.
            4 = Which the given user ({id}) has pinned.
            5 = Which the given user ({id}) owns.
    </pre>
    ---
    response_serializer: api.serializers.UsersTellzonesAll
    responseMessages:
        - code: 400
          message: Invalid Input
        - code: 403
          message: Invalid Input
    '''
    if int(id) != request.user.id:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_403_FORBIDDEN,
        )
    tellzones = {}
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            '''
            SELECT api_tellzones_1.id AS id, api_tellzones_1.name AS name, api_tellzones_2.source AS source
            FROM api_tellzones api_tellzones_1
            INNER JOIN (
                SELECT tellzone_id, 1 As source
                FROM api_users_locations
                WHERE user_id = %s AND timestamp > NOW() - INTERVAL '1 minute'
                UNION
                SELECT tellzone_id, 2 As source
                FROM api_master_tells_tellzones
                INNER JOIN api_master_tells ON api_master_tells.id = api_master_tells_tellzones.master_tell_id
                WHERE api_master_tells.owned_by_id = %s
                UNION
                SELECT tellzone_id, 3 As source
                FROM api_users_tellzones
                WHERE user_id = %s AND favorited_at IS NOT NULL
                UNION
                SELECT tellzone_id, 4 As source
                FROM api_users_tellzones
                WHERE user_id = %s AND pinned_at IS NOT NULL
                UNION
                SELECT id, 5 As source
                FROM api_tellzones
                WHERE user_id = %s
            ) api_tellzones_2 ON api_tellzones_2.tellzone_id = api_tellzones_1.id
            ORDER BY api_tellzones_2.source ASC, api_tellzones_1.id ASC
            ''',
            (request.user.id, request.user.id, request.user.id, request.user.id, request.user.id,),
        )
        columns = [column.name for column in cursor.description]
        for record in cursor.fetchall():
            record = dict(zip(columns, record))
            if record['id'] not in tellzones:
                tellzones[record['id']] = {}
            if 'id' not in tellzones[record['id']]:
                tellzones[record['id']]['id'] = record['id']
            if 'name' not in tellzones[record['id']]:
                tellzones[record['id']]['name'] = record['name']
            if 'source' not in tellzones[record['id']]:
                tellzones[record['id']]['source'] = record['source']
    return Response(
        data=serializers.UsersTellzonesAll(sorted(tellzones.values(), key=lambda item: item['id']), many=True).data,
        status=HTTP_200_OK,
    )


@api_view(('GET',))
@permission_classes(())
def verify_1(request, email):
    '''
    Resend verification email

    <pre>
    Input
    =====

    + email
        - Type: string
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
    user = models.User.objects.get_queryset().filter(email=email).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `email`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    current_app.send_task(
        'api.tasks.email_notifications',
        (user.id, 'verify',),
        queue='api.tasks.email_notifications',
        routing_key='api.tasks.email_notifications',
        serializer='json',
    )
    return Response(data=serializers.Null().data, status=HTTP_200_OK)


@api_view(('POST',))
@permission_classes(())
def verify_2(request):
    '''
    Verify Users

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: mandatory

    + hash
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
          pytype: api.serializers.VerifyRequest
    response_serializer: api.serializers.VerifyResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.VerifyRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    serializer.is_valid(raise_exception=True)
    user = models.User.objects.get_queryset().filter(id=serializer.validated_data['id']).first()
    if not user:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `id`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    token = ''
    try:
        token = urlsafe_b64decode(serializer.validated_data['hash'].encode('utf-8'))
    except Exception:
        pass
    if not user.is_valid(token):
        return Response(
            data={
                'error': ugettext_lazy('Invalid `hash`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    user.is_verified = True
    user.save()
    request.user = user
    return Response(
        data=serializers.VerifyResponse(
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
