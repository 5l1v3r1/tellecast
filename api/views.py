# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
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
        - Status: mandatory
        - Choices:
            - Private
            - Public

    + photos (see /api/users/photos/ for more details)
        - Type: list (a list of photo objects)
        - Status: optional

    + social_profiles (see /api/users/social-profiles/ for more details)
        - Type: list (a list of social profile objects)
        - Status: mandatory (at least "linkedin.com" is mandatory)

    + status (see /api/users/status/ for more details)
        - Type: dictionary (one status object)
        - Status: optional

    + urls (see /api/users/urls/ for more details)
        - Type: list (a list of url objects)
        - Status: optional

    + master tells (see /api/users/master-tells/ for more details)
        - Type: list (a list of master tell objects; with a list of slave tell objects)
        - Status: optional

    + slave tells (see /api/users/slave-tells/ for more details)
        - Type: list (a list of slave tell objects; as "slave_tells" under "master_tells" [above])
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
    Authenticate an existing User using an OAuth 1/OAuth 2 access token

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


class Users(DestroyModelMixin, GenericViewSet, ListModelMixin, RetrieveModelMixin, UpdateModelMixin):

    '''
    Users

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
        - Status: mandatory
        - Choices:
            - Private
            - Public

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.User
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.User
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.User
        response_serializer: api.serializers.User
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.User
        response_serializer: api.serializers.User
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    queryset = models.User.objects.all()
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.User


@api_view(('GET',))
@permission_classes(())
def users_profile(request, id):
    '''
    Retrieve the profile of a User
    ---
    responseMessages:
        - code: 400
          message: Invalid Input
    serializer: api.serializers.UserSimple
    '''
    return Response(data=serializers.UserSimple(get_object_or_404(models.User, id=id)).data, status=HTTP_200_OK)


class UsersPhotos(ModelViewSet):

    '''
    Users Photos

    <pre>
    Input
    =====

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
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        response_serializer: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        response_serializer: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        response_serializer: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UserPhoto

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserPhoto.objects.filter(user_id=self.request.user.id).order_by('position').all()


class UsersSocialProfiles(ModelViewSet):

    '''
    Users Social Profiles

    <pre>
    Input
    =====

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

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        response_serializer: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        response_serializer: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        response_serializer: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UserSocialProfile

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserSocialProfile.objects.filter(user_id=self.request.user.id).order_by('netloc').all()


class UsersStatuses(ModelViewSet):

    '''
    Users Statuses

    <pre>
    Input
    =====

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

    Output
    ======

    (see below; "Response Class" -> "Model Schema")
    </pre>
    ---
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        response_serializer: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        response_serializer: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        response_serializer: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UserStatus

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserStatus.objects.filter(user_id=self.request.user.id).order_by('id').all()


class UsersStatusesAttachments(ModelViewSet):

    '''
    Users Statuses Attachments

    <pre>
    Input
    =====

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
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        response_serializer: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        response_serializer: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        response_serializer: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UserStatusAttachment

    def perform_create(self, serializer):
        serializer.save(user_status__user=self.request.user)

    def get_queryset(self):
        return models.UserStatusAttachment.objects.filter(
            user_status__user_id=self.request.user.id,
        ).order_by('position').all()


class UsersURLs(ModelViewSet):

    '''
    Users URLs

    <pre>
    Input
    =====

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
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        response_serializer: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        response_serializer: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        response_serializer: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    '''

    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UserURL

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserURL.objects.filter(user_id=self.request.user.id).order_by('position').all()


class MasterTells(ModelViewSet):

    '''
    Master Tells

    <pre>
    Input
    =====

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
