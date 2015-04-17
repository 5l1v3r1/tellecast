# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import login
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import (
    CreateModelMixin, DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from social.apps.django_app.default.models import DjangoStorage
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy

from api import models, serializers


@api_view(('POST',))
@permission_classes(())
def register(request):
    '''
    Register a User

    <pre>
    Input
    =====

    + email
        - Type: string
        - Status: mandatory

    + email_status
        - Type: string
        - Status: mandatory
        - Choices:
            - Private
            - Public

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

    + phone_status
        - Type: string
        - Status: optional
        - Choices:
            - Private
            - Public

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
        - Status: mandatory ("linkedin.com" is mandatory)

    + status (see /api/users/ for more details)
        - Type: dictionary (one Status object)
        - Status: optional

    + urls (see /api/users/ for more details)
        - Type: list (a list of URL objects)
        - Status: optional

    + master tells (see /api/users/master-tells/ for more details)
        - Type: list (a list of Master Tell objects; with a list of Slave Tell objects under "slave_tells")
        - Status: optional

    + slave tells (see /api/users/slave-tells/ for more details)
        - Type: list (a list of Slave Tell objects; see above)
        - Status: optional

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    parameters:
        - name: body
          pytype: api.serializers.RegisterRequest
          paramType: body
    response_serializer: api.serializers.RegisterResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.RegisterRequest(data=request.DATA)
    if not serializer.is_valid():
        return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
    if not serializer.is_valid_(serializer.data):
        return Response(
            data={
                'error': ugettext_lazy('Invalid `access_token`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    user = serializer.save(force_insert=True, user=request.user)
    return Response(data=serializers.RegisterResponse(user).data, status=HTTP_201_CREATED)


@api_view(('POST',))
@permission_classes(())
def authenticate(request, backend):
    '''
    Authenticate an existing User using an OAuth 1/OAuth 2 `access_token`

    <pre>
    Input
    =====

    + backend
        - Type: string
        - Status: mandatory
        - Choices:
            - linkedin-oauth2

    + access_token
        - Type: string
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    parameters:
        - description: >
              A valid Python Social Auth supported backend. As of now, only
              "linkedin-oauth2" is supported. Reference:
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
    if not backend == 'linkedin-oauth2':
        return Response(
            data={
                'error': ugettext_lazy('Invalid `backend`'),
            },
            status=HTTP_400_BAD_REQUEST,
        )
    backend = get_backend(settings.AUTHENTICATION_BACKENDS, backend)(strategy=DjangoStrategy(storage=DjangoStorage()))
    if not backend or backend.name != 'linkedin-oauth2':
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
    login(request, user)
    return Response(data=serializers.AuthenticateResponse(user).data, status=HTTP_200_OK)


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
        - Unit: meter (m)
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
    serializer = serializers.TellzonesRequest(data=request.QUERY_PARAMS)
    if not serializer.is_valid():
        return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
    point = fromstr(
        'POINT(%(longitude)s %(latitude)s)' % {
            'latitude': serializer.data['latitude'],
            'longitude': serializer.data['longitude'],
        }
    )
    data = []
    for tellzone in models.Tellzone.objects.filter(
        point__distance_lte=(point, D(m=float(serializer.data['radius']))),
    ).distance(
        point,
    ).all():
        data.append(serializers.TellzonesResponse(
            tellzone,
            context={
                'request': request,
            },
        ).data)
    return Response(data=data, status=HTTP_200_OK)


class Users(DestroyModelMixin, GenericViewSet, ListModelMixin, RetrieveModelMixin, UpdateModelMixin):

    '''
    Users

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: optional

    + email
        - Type: string
        - Status: mandatory

    + email_status
        - Type: string
        - Status: mandatory
        - Choices:
            - Private
            - Public

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

    + phone_status
        - Type: string
        - Status: optional
        - Choices:
            - Private
            - Public

    + point
        - Type: dictionary (of floats)
        - Status: optional

        Example:

        {
            'latitude': 0.0000000000,
            'longitude': 0.0000000000,
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
    </pre>
    ---
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UsersResponse
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UsersResponse
    update:
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
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    queryset = models.User.objects.all()
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UsersResponse

    def list(self, request, *args, **kwargs):
        '''
        SELECT Users
        ---
        '''
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        '''
        SELECT User
        ---
        '''
        return Response(data=self.get_serializer(self.get_object()).data, status=HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        '''
        UPDATE a User
        ---
        '''
        serializer = serializers.UsersRequest(self.get_object(), data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        return Response(data=serializers.UsersResponse(serializer.save()).data, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a User
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_204_NO_CONTENT)


@api_view(('POST', 'DELETE',))
@permission_classes((IsAuthenticated,))
def users_tellzones(request, id):
    '''
    View/Favorite/Unview/Unfavorite a Tellzone

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

    + POST: (see below; "Response Class" -> "Model Schema")

    + DELETE: N/A
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
    if not serializer.is_valid():
        return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
    if request.method == 'POST':
        return Response(
            data=serializers.UsersTellzonesResponse(serializer.create_or_update()).data,
            status=HTTP_201_CREATED,
        )
    if request.method == 'DELETE':
        serializer.delete()
        return Response(data={}, status=HTTP_204_NO_CONTENT)


@api_view(('POST', 'DELETE',))
@permission_classes((IsAuthenticated,))
def users_offers(request, id):
    '''
    Save/Unsave an Offer

    <pre>
    Input
    =====

    + offer_id
        - Type: integer
        - Status: mandatory

    Output
    ======

    + POST: (see below; "Response Class" -> "Model Schema")

    + DELETE: N/A
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
          pytype: api.serializers.UsersOffersRequest
    response_serializer: api.serializers.UsersOffersResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.UsersOffersRequest(
        context={
            'request': request,
        },
        data=request.DATA,
    )
    if not serializer.is_valid():
        return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
    if request.method == 'POST':
        return Response(
            data=serializers.UsersOffersResponse(serializer.create_or_update()).data,
            status=HTTP_201_CREATED,
        )
    if request.method == 'DELETE':
        serializer.delete()
        return Response(data={}, status=HTTP_204_NO_CONTENT)


@api_view(('GET',))
@permission_classes(())
def users_profile(request, id):
    '''
    Retrieve the profile of a User
    ---
    responseMessages:
        - code: 400
          message: Invalid Input
    serializer: api.serializers.UsersProfile
    '''
    return Response(
        data=serializers.UsersProfile(
            get_object_or_404(models.User, id=id),
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


class MasterTells(ModelViewSet):

    '''
    Master Tells

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: optional

    + created_by_id
        - Type: integer
        - Status: optional

    + owned_by_id
        - Type: integer
        - Status: optional

    + contents
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
    list:
        parameters:
            - name: inserted_at
              paramType: query
              type: datetime
            - name: updated_at
              paramType: query
              type: datetime
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        response_serializer: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        response_serializer: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        response_serializer: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.MasterTell

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, owned_by=self.request.user)

    def get_queryset(self):
        queryset = models.MasterTell.objects.filter(owned_by_id=self.request.user.id)
        inserted_at = self.request.QUERY_PARAMS.get('inserted_at', None)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
        updated_at = self.request.QUERY_PARAMS.get('updated_at', None)
        if updated_at:
            queryset = queryset.filter(updated_at__gte=updated_at)
        return queryset.order_by('position').all()


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def master_tells_ids(request):
    '''
    Retrieve the IDs of Master Tells

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
            for master_tell in models.MasterTell.objects.filter(owned_by_id=request.user.id).order_by('position').all()
        ],
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def master_tells_positions(request):
    '''
    Bulk update positions of Master Tells

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
    response_serializer: api.serializers.MasterTell
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    data = []
    for item in request.DATA:
        try:
            master_tell = models.MasterTell.objects.get(id=item['id'])
            master_tell.position = item['position']
            master_tell.save()
            data.append(serializers.MasterTell(master_tell).data)
        except models.MasterTell.DoesNotExist:
            pass
    return Response(data=data, status=HTTP_200_OK)


class SlaveTells(ModelViewSet):

    '''
    Slave Tells

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: optional

    + master_tell_id
        - Type: integer
        - Status: mandatory

    + created_by_id
        - Type: integer
        - Status: optional

    + owned_by_id
        - Type: integer
        - Status: optional

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

    + is_editable
        - Type: boolean
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

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    list:
        parameters:
            - name: inserted_at
              paramType: query
              type: datetime
            - name: updated_at
              paramType: query
              type: datetime
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        response_serializer: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        response_serializer: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        response_serializer: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.SlaveTell

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, owned_by=self.request.user)

    def get_queryset(self):
        queryset = models.SlaveTell.objects.filter(owned_by_id=self.request.user.id)
        inserted_at = self.request.QUERY_PARAMS.get('inserted_at', None)
        if inserted_at:
            queryset = queryset.filter(inserted_at__gte=inserted_at)
        updated_at = self.request.QUERY_PARAMS.get('updated_at', None)
        if updated_at:
            queryset = queryset.filter(updated_at__gte=updated_at)
        return queryset.order_by('position').all()


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def slave_tells_ids(request):
    '''
    Retrieve the IDs of Slave Tells

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
            for slave_tell in models.SlaveTell.objects.filter(owned_by_id=request.user.id).order_by('position').all()
        ],
        status=HTTP_200_OK,
    )


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def slave_tells_positions(request):
    '''
    Bulk update positions of Slave Tells

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
    response_serializer: api.serializers.SlaveTell
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    data = []
    for item in request.DATA:
        try:
            slave_tell = models.SlaveTell.objects.get(id=item['id'])
            slave_tell.position = item['position']
            slave_tell.save()
            data.append(serializers.SlaveTell(slave_tell).data)
        except models.SlaveTell.DoesNotExist:
            pass
    return Response(data=data, status=HTTP_200_OK)


class Messages(CreateModelMixin, DestroyModelMixin, GenericViewSet, ListModelMixin):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.Message

    def get_queryset(self):
        return models.Message.objects.order_by('-inserted_at').all()

    def list(self, request, *args, **kwargs):
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
        parameters:
            - name: recent
              paramType: query
              required: true
              type: boolean
            - name: user_status_id
              paramType: query
              type: integer
            - name: master_tell_id
              paramType: query
              type: integer
            - name: max_id
              paramType: query
              type: integer
            - name: limit
              paramType: query
              type: integer
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.Message
        '''
        messages = []
        if request.query_params.get('recent', True):
            for user in models.User.objects.exclude(id=request.user.id).order_by('id').all():
                message = models.Message.objects.filter(
                    Q(user_source_id=request.user.id, user_destination_id=user.id)
                    |
                    Q(user_source_id=user.id, user_destination_id=request.user.id),
                    user_status_id__isnull=True,
                    master_tell_id__isnull=True,
                ).order_by('-inserted_at').first()
                if message:
                    messages.append(message)
            messages = sorted(messages, key=lambda message: message.inserted_at, reverse=True)
        else:
            query = models.Message.objects.filter(
                Q(user_source_id=request.user.id) | Q(user_destination_id=request.user.id),
            )
            user_id = request.query_params.get('user_id', None)
            if user_id:
                query = query.filter(
                    Q(user_source_id=user_id) | Q(user_destination_id=user_id),
                )
            user_status_id = request.query_params.get('user_status_id', None)
            if user_status_id:
                query = query.filter(user_status_id=user_status_id)
            else:
                query = query.filter(user_status_id__isnull=True)
            master_tell_id = request.query_params.get('master_tell_id', None)
            if master_tell_id:
                query = query.filter(master_tell_id=master_tell_id)
            else:
                query = query.filter(master_tell_id__isnull=True)
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
            for message in query.order_by('-inserted_at').all()[:limit]:
                messages.append(message)
        return Response(
            data=[serializers.Message(message).data for message in messages],
            status=HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        '''
        INSERT a Message

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
            'payload': '(see below; "Response Class" -> "Model Schema")',
            'type': 'messages',
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
        serializer = serializers.MessagesPostRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not models.Message.objects.filter(
            Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_destination_id'])
            |
            Q(user_source_id=serializer.validated_data['user_destination_id'], user_destination_id=request.user.id),
            type='Message',
        ).count():
            message = models.Message.objects.filter(
                Q(
                    user_source_id=request.user.id,
                    user_destination_id=serializer.validated_data['user_destination_id'],
                )
                |
                Q(
                    user_source_id=serializer.validated_data['user_destination_id'],
                    user_destination_id=request.user.id,
                ),
            ).order_by(
                '-inserted_at',
            ).first()
            if message:
                if message.user_source_id == request.user.id:
                    if message.type in ['Request']:
                        return Response(status=HTTP_403_FORBIDDEN)
                if message.user_destination_id == request.user.id:
                    if message.type in ['Response - Blocked']:
                        return Response(status=HTTP_403_FORBIDDEN)
        serializer = serializers.MessagesPostResponse(serializer.save(user_source=request.user))
        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, headers=headers, status=HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        '''
        UPDATE (partially) a Message

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
            'payload': '(see below; "Response Class" -> "Model Schema")',
            'type': 'messages',
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
        instance = self.get_object()
        serializer = serializers.MessagesPatchRequest(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer = serializers.MessagesPatchResponse(serializer.save())
        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, headers=headers, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a Message

        <pre>
        Input
        =====

        + id
            - Status: mandatory
            - Type: integer

        Output
        ======

        + N/A
        </pre>
        ---
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return super(Messages, self).destroy(request, *args, **kwargs)


class DevicesAPNS(CreateModelMixin, DestroyModelMixin, GenericViewSet, ListModelMixin):

    '''
    APNS Devices

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: optional

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
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.DeviceAPNS
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.DeviceAPNS
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.DeviceAPNS
        response_serializer: api.serializers.DeviceAPNS
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.DeviceAPNS

    def get_queryset(self):
        return models.DeviceAPNS.objects.filter(user_id=self.request.user.id).order_by('id').all()

    def list(self, request, *args, **kwargs):
        '''
        SELECT APNS Devices
        ---
        '''
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        '''
        SELECT an APNS Device
        ---
        '''
        return Response(data=self.get_serializer(self.get_object()).data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        '''
        INSERT an APNS Device
        ---
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, headers=headers, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE an APNS Device
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_204_NO_CONTENT)


class DevicesGCM(CreateModelMixin, DestroyModelMixin, GenericViewSet, ListModelMixin):

    '''
    GCM Devices

    <pre>
    Input
    =====

    + id
        - Type: integer
        - Status: optional

    + name
        - Type: string
        - Status: mandatory

    + device_id
        - Type: integer (hexadecimal notation)
        - Status: mandatory

    + registration_id
        - Type: string
        - Status: mandatory

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    list:
        parameters:
            - name: inserted_at
              paramType: query
              type: datetime
            - name: updated_at
              paramType: query
              type: datetime
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.DeviceGCM
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.DeviceGCM
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.DeviceGCM
        response_serializer: api.serializers.DeviceGCM
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.DeviceGCM

    def get_queryset(self):
        return models.DeviceGCM.objects.filter(user_id=self.request.user.id).order_by('id').all()

    def list(self, request, *args, **kwargs):
        '''
        SELECT GCM Devices
        ---
        '''
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        '''
        SELECT a GCM Device
        ---
        '''
        return Response(data=self.get_serializer(self.get_object()).data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        '''
        INSERT a GCM Device
        ---
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(data=serializer.data, headers=headers, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a GCM Device
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_204_NO_CONTENT)


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
