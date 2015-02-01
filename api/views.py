# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import (
    DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from social.apps.django_app.default.models import DjangoStorage
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy

from api import models, serializers


class MasterTells(ModelViewSet):
    '''
    Master Tells

    <pre>
    Mandatory Fields
    ================

    + contents
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.MasterTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.MasterTell
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.MasterTell

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, owned_by=self.request.user,
        )

    def get_queryset(self):
        return models.MasterTell.objects.filter(
            owned_by_id=self.request.user.id,
        ).order_by('position').all()


class SlaveTells(ModelViewSet):
    '''
    Slave Tells

    <pre>
    Mandatory Fields
    ================

    + type
    + string

    Choices
    =======

    + type:
      - File
      - String
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.SlaveTell
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SlaveTell
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.SlaveTell

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, owned_by=self.request.user,
        )

    def get_queryset(self):
        return models.SlaveTell.objects.filter(
            owned_by_id=self.request.user.id,
        ).order_by('position').all()


class Users(
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    '''
    Users

    <pre>
    Mandatory Fields
    ================

    + email
    + email_status
    + password

    Choices
    =======

    + email_status
      - Private
      - Public
    + gender
      - Female
      - Male
    </pre>
    ---
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.User
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.User
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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.User
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    queryset = models.User.objects.filter(
        is_active=True, is_staff=False, is_superuser=False,
    ).all()
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.User


class UsersPhotos(ModelViewSet):
    '''
    Users Photos

    <pre>
    Mandatory Fields
    ================

    + string
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserPhoto
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserPhoto
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.UserPhoto

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserPhoto.objects.filter(
            user_id=self.request.user.id,
        ).order_by('position').all()


class UsersSocialProfiles(ModelViewSet):
    '''
    Users Social Profiles

    <pre>
    Mandatory Fields
    ================

    + netloc
    + url

    Choices
    =======

    + netloc:
      - facebook.com
      - google.com
      - instagram.com
      - linkedin.com
      - twitter.com
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserSocialProfile
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserSocialProfile
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    queryset = models.UserSocialProfile.objects.all()
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.UserSocialProfile

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserSocialProfile.objects.filter(
            user_id=self.request.user.id,
        ).order_by('netloc').all()


class UsersStatuses(ModelViewSet):
    '''
    Users Statuses

    <pre>
    Mandatory Fields
    ================

    + string
    + title
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatus
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatus
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.UserStatus

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserStatus.objects.filter(
            user_id=self.request.user.id,
        ).order_by('id').all()


class UsersStatusesAttachments(ModelViewSet):
    '''
    Users Statuses Attachments

    <pre>
    Mandatory Fields
    ================

    + string
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserStatusAttachment
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserStatusAttachment
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
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
    Mandatory Fields
    ================

    + string
    </pre>
    ---
    create:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    destroy:
        responseMessages:
            - code: 400
              message: Invalid Input
    list:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    partial_update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    retrieve:
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    update:
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
              pytype: api.serializers.UserURL
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UserURL
    '''
    lookup_field = 'id'
    permission_classes = (IsAuthenticated, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.UserURL

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return models.UserURL.objects.filter(
            user_id=self.request.user.id,
        ).order_by('position').all()


@api_view(('POST', ))
@csrf_exempt
@permission_classes(())
def authenticate(request, backend):
    '''
    Authenticate an existing user using an OAuth 1/OAuth 2 access token

    <pre>
    Mandatory Fields
    ================

    + access_token

    Choices
    =======

    + backend:
      - linkedin-oauth2
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
    backend = get_backend(
        settings.AUTHENTICATION_BACKENDS, backend,
    )(strategy=DjangoStrategy(storage=DjangoStorage()))
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
    if not user or not user.is_active:
        return Response(
            data={
                'error': ugettext_lazy('Invalid `user`'),
            },
            status=HTTP_401_UNAUTHORIZED,
        )
    login(request, user)
    return Response(
        data=serializers.AuthenticateResponse(user).data,
        status=HTTP_200_OK,
    )


@api_view(('POST', ))
@csrf_exempt
@permission_classes((IsAuthenticated, ))
def master_tells_positions(request):
    '''
    Bulk update positions of Master Tells

    <pre>
    Input
    =====

    [
        {
            "id": 0,
            "position": 0
        },
        ...,
        {
            "id": 0,
            "position": 0
        }
    ]
    </pre>
    ---
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


@api_view(('POST', ))
@csrf_exempt
@permission_classes(())
def register(request):
    '''
    Register a User

    <pre>
    Mandatory Fields
    ================

    + email
    + email_status

    Choices
    =======

    + email_status:
      - Private
      - Public

    + gender:
      - Female
      - Male

    + master_tells.slave_tells.type:
      - File
      - String

    + social_profiles.netloc:
      - facebook.com
      - google.com
      - instagram.com
      - linkedin.com
      - twitter.com
    </pre>
    ---
    parameters:
        - name: body
          pytype: api.serializers.Register
          paramType: body
    response_serializer: api.serializers.UserFull
    responseMessages:
        - code: 400
          message: Invalid Input
    '''
    serializer = serializers.Register(data=request.DATA)
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
    return Response(
        data=serializers.UserFull(user).data, status=HTTP_201_CREATED,
    )


@api_view(('POST', ))
@csrf_exempt
@permission_classes((IsAuthenticated, ))
def slave_tells_positions(request):
    '''
    Bulk update positions of Slave Tells

    <pre>
    Input
    =====

    [
        {
            "id": 0,
            "position": 0
        },
        ...,
        {
            "id": 0,
            "position": 0
        }
    ]
    </pre>
    ---
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


@api_view(('GET', ))
@csrf_exempt
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
    return Response(
        data=serializers.UserSimple(
            get_object_or_404(
                models.User,
                id=id,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
        ).data,
        status=HTTP_200_OK,
    )
