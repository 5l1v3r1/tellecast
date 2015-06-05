# -*- coding: utf-8 -*-

from contextlib import closing
from datetime import date, datetime, timedelta
from math import atan2, cos, pi, sin, sqrt
from random import randint, uniform

from arrow import get
from django.conf import settings
from django.contrib.auth import login
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy
from geopy.distance import vincenty
from numpy import mean
from rest_framework.decorators import api_view, permission_classes
from rest_framework.mixins import (
    CreateModelMixin, DestroyModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from social.apps.django_app.default.models import DjangoStorage
from social.backends.utils import get_backend
from social.strategies.django_strategy import DjangoStrategy
from ujson import loads

from api import celery, models, serializers
from api.algorithms.clusters import get_clusters


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
    return Response(
        data=serializers.RegisterResponse(serializer.save(force_insert=True, user=request.user)).data,
        status=HTTP_201_CREATED,
    )


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
    login(request, user)
    return Response(data=serializers.AuthenticateResponse(user).data, status=HTTP_200_OK)


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

    + settings
        - Type: dictionary
        - Status: optional

        Example:

        {
            'show_last_name': true,
            'show_profile_photo': true,
            'show_email': true,
            'show_phone_number': true,
            'notifications_invitations': true,
            'notifications_shared_profiles': true,
            'notifications_messages': true,
            'notifications_offers': true,
            'notifications_saved_you': true,
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
        response_serializer: api.serializers.Null
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
    serializer_class = serializers.UsersResponse

    def retrieve(self, request, *args, **kwargs):
        '''
        SELECT User
        ---
        '''
        return Response(
            data=self.get_serializer(
                self.get_object(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        '''
        UPDATE a User
        ---
        '''
        serializer = serializers.UsersRequest(self.get_object(), data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        return Response(
            data=serializers.UsersResponse(
                serializer.save(),
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a User
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_200_OK)

    def get_queryset(self):
        ids = []
        for block in models.Block.objects.filter(
            Q(user_source_id=self.request.user.id) | Q(user_destination_id=self.request.user.id),
        ).order_by(
            '-timestamp',
        ).all():
            if block.user_source.id == self.request.user.id:
                if block.user_destination.id not in ids:
                    ids.append(block.user_destination.id)
            if block.user_destination.id == self.request.user.id:
                if block.user_source.id not in ids:
                    ids.append(block.user_source.id)
        return models.User.objects.exclude(id__in=ids).order_by('id').all()


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
    if request.user.is_authenticated():
        if is_blocked(request.user.id, id):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
    return Response(
        data=serializers.UsersProfile(
            get_object_or_404(models.User, id=id),
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


class UsersTellzones(GenericViewSet):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.Tellzone

    def get(self, request, *args, **kwargs):
        '''
        SELECT favorited tellzones

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UsersTellzonesGet
        '''
        return Response(
            data=[
                serializers.UsersTellzonesGet(
                    user_tellzone.tellzone,
                    context={
                        'request': request,
                    },
                ).data
                for user_tellzone in models.UserTellzone.objects.filter(
                    user_id=request.user.id, favorited_at__isnull=False,
                ).order_by(
                    '-id',
                ).all()
            ],
            status=HTTP_200_OK,
        )

    def post(self, request, id):
        '''
        View/Favorite a Tellzone

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
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
        return Response(
            data=serializers.UsersTellzonesResponse(serializer.create_or_update()).data, status=HTTP_201_CREATED,
        )

    def delete(self, request, id):
        '''
        Unview/Unfavorite a Tellzone

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

        + N/A
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
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
        serializer.delete()
        return Response(data={}, status=HTTP_200_OK)


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def users_tellzones_delete(request, id):
    '''
    Unview/Unfavorite a Tellzone

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

    + N/A
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
    if not serializer.is_valid():
        return Response(data=serializer.errors, status=HTTP_400_BAD_REQUEST)
    serializer.delete()
    return Response(data={}, status=HTTP_200_OK)


class UsersOffers(GenericViewSet):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.UsersOffersGet

    def get(self, request, *args, **kwargs):
        '''
        SELECT saved offers

        <pre>
        Input
        =====

        + N/A

        Output
        ======

        (see below; "Response Class" -> "Model Schema")
        </pre>
        ---
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.UsersOffersGet
        '''
        return Response(
            data=[
                serializers.UsersOffersGet(
                    user_offer.offer,
                    context={
                        'request': request,
                    },
                ).data
                for user_offer in models.UserOffer.objects.filter(
                    user_id=request.user.id, saved_at__isnull=False,
                ).order_by(
                    '-id',
                ).all()
            ],
            status=HTTP_200_OK,
        )

    def post(self, request, id):
        '''
        Save/Redeem an Offer

        <pre>
        Input
        =====

        + offer_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - Save
                - Redeem

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
        return Response(
            data=serializers.UsersOffersResponse(serializer.create_or_update()).data, status=HTTP_201_CREATED,
        )

    def delete(self, request, id):
        '''
        Unsave/Forfeit an Offer

        <pre>
        Input
        =====

        + offer_id
            - Type: integer
            - Status: mandatory

        + action
            - Type: string
            - Status: mandatory
            - Choices:
                - Save
                - Redeem

        Output
        ======

        + N/A
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
        serializer.delete()
        return Response(data={}, status=HTTP_200_OK)


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def users_offers_delete(request, id):
    '''
    Unsave/Forfeit an Offer

    <pre>
    Input
    =====

    + offer_id
        - Type: integer
        - Status: mandatory

    + action
        - Type: string
        - Status: mandatory
        - Choices:
            - Save
            - Redeem

    Output
    ======

    + N/A
    </pre>
    ---
    omit_parameters:
        - form
    parameters:
        - name: body
          paramType: body
          pytype: api.serializers.UsersOffersRequest
    response_serializer: api.serializers.Null
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
    serializer.delete()
    return Response(data={}, status=HTTP_200_OK)


class Notifications(GenericViewSet):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = None
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.Notification

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

        type = C

            + contents
                + user <- This user shared an offer with you.
                    - id
                    - first_name
                    - last_name
                    - photo
                + offer <- This offer was shared.
                    - id
                    - name
                    - description
                    - photo
                    - code
                    - inserted_at
                    - updated_at
                    - expires_at
                    - is_saved
                    - is_redeemed
                    + tellzone
                        - id
                        - name
                        - photo
                        - location
                        - phone
                        - url
                        - hours
                        - point
                        - inserted_at
                        - updated_at
                        - offers
                        - views
                        - favorites
                        - is_viewed
                        - is_favorited

        type = D

            + contents
                + offer <- This offer was shared.
                    - id
                    - name
                    - description
                    - photo
                    - code
                    - inserted_at
                    - updated_at
                    - expires_at
                    - is_saved
                    - is_redeemed
                    + tellzone <- This Tellzone shared an offer with you.
                        - id
                        - name
                        - photo
                        - location
                        - phone
                        - url
                        - hours
                        - point
                        - inserted_at
                        - updated_at
                        - offers
                        - views
                        - favorites
                        - is_viewed
                        - is_favorited

        type = E

            + contents
                + offer <- This offer was shared.
                    - id
                    - name
                    - description
                    - photo
                    - code
                    - inserted_at
                    - updated_at
                    - expires_at
                    - is_saved
                    - is_redeemed
                    + tellzone <- This Tellzone shared an offer with you.
                        - id
                        - name
                        - photo
                        - location
                        - phone
                        - url
                        - hours
                        - point
                        - inserted_at
                        - updated_at
                        - offers
                        - views
                        - favorites
                        - is_viewed
                        - is_favorited

        type = F

            + contents
                + offer <- Tellecast shared this offer with you.
                    - id
                    - name
                    - description
                    - photo
                    - code
                    - inserted_at
                    - updated_at
                    - expires_at
                    - is_saved
                    - is_redeemed
                    + tellzone <- This Tellzone shared an offer with you.
                        - id
                        - name
                        - photo
                        - location
                        - phone
                        - url
                        - hours
                        - point
                        - inserted_at
                        - updated_at
                        - offers
                        - views
                        - favorites
                        - is_viewed
                        - is_favorited

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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.Notification
        '''
        notifications = []
        query = models.Notification.objects.filter(user_id=request.user.id)
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
        for notification in query.order_by('-timestamp').all()[:limit]:
            notifications.append(notification)
        return Response(
            data=[serializers.Notification(notification).data for notification in notifications],
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        Bulk update `status` attributes of Notifications

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
        response_serializer: api.serializers.Notification
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        data = []
        for item in request.DATA:
            try:
                notification = models.Notification.objects.get(id=item['id'], user_id=request.user.id)
                notification.status = item['status']
                notification.save()
                data.append(serializers.Notification(notification).data)
            except models.Notification.DoesNotExist:
                pass
        return Response(data=data, status=HTTP_200_OK)


@api_view(('GET',))
@permission_classes((IsAuthenticated,))
def home(request):
    '''
    Retrieve the home of a User

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
    response_serializer: api.serializers.HomeResponse
    responseMessages:
        - code: 400
          message: Invalid Input
    '''

    def get_days(today):
        return [(today - timedelta(days=index + 1)).isoformat() for index in range(0, 7)]

    def get_weeks(today):
        dates = [
            get(today - timedelta(days=today.weekday())).replace(weeks=-1 - index).date()
            for index in range(0, 8)
        ]
        return [
            [date.isoformat() for date in dates],
            dates[-1].isoformat(),
            get(dates[0]).replace(days=-1, weeks=1).date().isoformat(),
        ]

    def get_months(today):
        dates = [get(today).replace(day=1, months=-1 - index).date() for index in range(0, 12)]
        return [
            [date.isoformat() for date in dates],
            dates[-1].isoformat(),
            get(dates[0]).replace(days=-1, months=1).date().isoformat(),
        ]

    serializer = serializers.HomeRequest(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    point = fromstr('POINT(%(longitude)s %(latitude)s)' % {
        'latitude': serializer.validated_data['latitude'],
        'longitude': serializer.validated_data['longitude'],
    })
    today = date.today()
    days = get_days(today)
    weeks = get_weeks(today)
    months = get_months(today)
    if serializer.validated_data['dummy']:
        views_today = randint(1, 150)
        views_days = {}
        for day in days:
            views_days[day] = randint(1, 150)
        views_weeks = {}
        for week in weeks[0]:
            views_weeks[week] = randint(1, 150)
        views_months = {}
        for month in months[0]:
            views_months[month] = randint(1, 150)
        views_total = views_today + sum(views_days.values()) + sum(views_weeks.values()) + sum(views_months.values())
        saves_today = randint(1, 50)
        saves_days = {}
        for day in days:
            saves_days[day] = randint(1, 50)
        saves_weeks = {}
        for week in weeks[0]:
            saves_weeks[week] = randint(1, 50)
        saves_months = {}
        for month in months[0]:
            saves_months[month] = randint(1, 50)
        saves_total = saves_today + sum(saves_days.values()) + sum(saves_weeks.values()) + sum(saves_months.values())
        users_near = randint(1, 50)
        users_area = users_near + randint(1, 150)
        tellzones = [tellzone for tellzone in models.Tellzone.objects.distance(point).order_by('?')[0:5]]
        offers = [offer for offer in models.Offer.objects.order_by('?')[0:5]]
        connections = {}
        for user in models.User.objects.exclude(id=request.user.id).order_by('?')[0:5]:
            connections[user.id] = {
                'user': user,
                'timestamp': datetime.now() - timedelta(days=randint(1, 31)),
                'point': user.point,
                'tellzone': models.Tellzone.objects.order_by('?').first(),
            }
    else:
        views_total = models.Tellcard.objects.filter(
            user_destination_id=request.user.id, viewed_at__isnull=False,
        ).count()
        views_today = models.Tellcard.objects.filter(
            user_destination_id=request.user.id, viewed_at__startswith=today,
        ).count()
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
        saves_total = models.Tellcard.objects.filter(
            user_destination_id=request.user.id, saved_at__isnull=False,
        ).count()
        saves_today = models.Tellcard.objects.filter(
            user_destination_id=request.user.id, saved_at__startswith=today,
        ).count()
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
        users_near = models.UserLocation.objects.filter(
            ~Q(user_id=request.user.id),
            point__distance_lte=(point, D(ft=300)),
            is_casting=True,
            timestamp__gt=datetime.now() - timedelta(minutes=1),
        ).distance(
            point,
        ).order_by(
            'distance',
        ).distinct(
            'user_id'
        ).count()
        users_area = models.UserLocation.objects.filter(
            ~Q(user_id=request.user.id),
            point__distance_lte=(point, D(mi=10)),
            is_casting=True,
            timestamp__gt=datetime.now() - timedelta(minutes=1),
        ).distance(
            point,
        ).order_by(
            'distance',
        ).distinct(
            'user_id'
        ).count()
        tellzones = [
            tellzone
            for tellzone in models.Tellzone.objects.filter(
                point__distance_lte=(point, D(mi=10)),
            ).distance(
                point,
            ).select_related(
                'offers',
            ).order_by(
                'distance',
            ).all()
        ]
        offers = [
            user_offer.offer
            for user_offer in models.UserOffer.objects.filter(
                user_id=request.user.id, saved_at__isnull=False,
            ).order_by(
                '-saved_at',
            ).all()
        ]
        connections = {}
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    api_users_locations_2.user_id,
                    api_users_locations_2.timestamp,
                    api_users_locations_2.point,
                    api_users_locations_2.tellzone_id
                FROM api_users_locations api_users_locations_1
                INNER JOIN api_users_locations api_users_locations_2 ON
                    api_users_locations_1.user_id != api_users_locations_2.user_id
                    AND
                    ST_DWithin(api_users_locations_1.point, api_users_locations_2.point, 91.44)
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
                        'user': models.User.objects.filter(id=record[0]).first(),
                        'timestamp': record[1],
                        'point': record[2],
                        'tellzone': models.Tellzone.objects.filter(id=record[3]).first(),
                    }
    return Response(
        data=serializers.HomeResponse(
            {
                'views': {
                    'total': views_total,
                    'today': views_today,
                    'days': views_days,
                    'weeks': views_weeks,
                    'months': views_months,
                },
                'saves': {
                    'total': saves_total,
                    'today': saves_today,
                    'days': saves_days,
                    'weeks': saves_weeks,
                    'months': saves_months,
                },
                'users': {
                    'near': users_near,
                    'area': users_area,
                },
                'tellzones': tellzones,
                'offers': offers,
                'connections': sorted(
                    connections.values(), key=lambda connection: connection['timestamp'], reverse=True,
                ),
            },
            context={
                'request': request,
            },
        ).data,
        status=HTTP_200_OK,
    )


class Radar(APIView):

    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        '''
        GET Items

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
        serializer = serializers.RadarGetRequest(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        point = fromstr('POINT(%(longitude)s %(latitude)s)' % {
            'latitude': serializer.validated_data['latitude'],
            'longitude': serializer.validated_data['longitude'],
        })
        users = {}
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                '''
                SELECT
                    api_users_locations.user_id,
                    ST_AsGeoJSON(api_users_locations.point),
                    ST_Distance(ST_GeomFromText(%s, 4326), point) * 0.3048
                FROM api_users_locations
                LEFT OUTER JOIN api_blocks ON
                    (api_blocks.user_source_id = %s AND api_blocks.user_destination_id = api_users_locations.user_id)
                    OR
                    (api_blocks.user_source_id = api_users_locations.user_id AND api_blocks.user_destination_id = %s)
                WHERE
                    user_id != %s
                    AND
                    ST_DWithin(ST_GeomFromText(%s, 4326), point, %s)
                    AND
                    is_casting IS TRUE
                    AND
                    api_users_locations.timestamp > NOW() - INTERVAL '1 minute'
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
                    p = fromstr('POINT(%(longitude)s %(latitude)s)' % {
                        'latitude': p['coordinates'][1],
                        'longitude': p['coordinates'][0],
                    })
                    users[record[0]] = (
                        models.User.objects.filter(id=record[0]).first(),
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
                p = fromstr('POINT(%(longitude)s %(latitude)s)' % {
                    'latitude': point.y + y,
                    'longitude': point.x + x,
                })
                if record[0] not in users:
                    users[record[0]] = (
                        models.User.objects.filter(id=record[0]).first(),
                        p,
                        self.get_degrees(point, p),
                        vincenty((point.x, point.y), (p.x, p.y)).ft,
                    )
        offers = []
        for tellzone in models.Tellzone.objects.filter(
            point__distance_lte=(point, D(ft=serializer.validated_data['radius'])),
        ).distance(
            point,
        ).select_related(
            'offers',
        ).order_by(
            'distance',
        ).all():
            for offer in tellzone.offers.order_by('id').all():
                offers.append((
                    offer,
                    tellzone.point,
                    self.get_degrees(point, tellzone.point),
                    self.get_radius(tellzone.distance),
                ))
        eps = (
            (serializer.validated_data['widths_group'] * serializer.validated_data['radius']) /
            serializer.validated_data['widths_radar']
        )
        return Response(
            data=serializers.RadarGetResponse(
                {
                    'users': self.get_containers(get_clusters(users.values(), eps)),
                    'offers': self.get_containers(get_clusters(offers, eps)),
                },
                context={
                    'request': request,
                },
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        POST Location

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
        serializer = serializers.RadarPostRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_location = serializer.save(user=request.user)
        return Response(
            data=serializers.RadarPostResponse(
                models.Tellzone.objects.filter(
                    point__distance_lte=(user_location.point, D(ft=models.Tellzone.radius())),
                ).distance(
                    user_location.point,
                ).all(),
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
        return 360 - (((atan2((point_1.y - point_2.y), (point_1.x - point_2.x)) * (180 / pi)) + 360) % 360)

    def get_radius(self, distance):
        return getattr(distance, 'ft')


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
        response_serializer: api.serializers.Null
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
        return Response(data=serializer.data, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE an APNS Device
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_200_OK)

    def get_queryset(self):
        return models.DeviceAPNS.objects.filter(user_id=self.request.user.id).order_by('id').all()


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
        response_serializer: api.serializers.Null
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
        return Response(data=serializer.data, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a GCM Device
        ---
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_200_OK)

    def get_queryset(self):
        return models.DeviceGCM.objects.filter(user_id=self.request.user.id).order_by('id').all()


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

    + is_visible
        - Type: boolean (default = True)
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
        response_serializer: api.serializers.Null
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
    Bulk update `position` attribute of Master Tells

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
            master_tell = models.MasterTell.objects.get(id=item['id'], owned_by_id=request.user.id)
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
        - Type: boolean (default = True)
        - Status: optional

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
        response_serializer: api.serializers.Null
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
    Bulk update `position` attribute of Slave Tells

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
            slave_tell = models.SlaveTell.objects.get(id=item['id'], owned_by_id=request.user.id)
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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.Message
        '''
        messages = []
        if request.query_params.get('recent', True):
            for user in models.User.objects.exclude(id=request.user.id).order_by('id').all():
                message = models.Message.objects.filter(
                    Q(user_source_id=request.user.id, user_destination_id=user.id) |
                    Q(user_source_id=user.id, user_destination_id=request.user.id),
                ).order_by(
                    '-inserted_at',
                ).first()
                if message:
                    messages.append(message)
            messages = sorted(messages, key=lambda message: message.inserted_at, reverse=True)
        else:
            query = models.Message.objects.filter(
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
            for message in query.order_by('-inserted_at').all()[:limit]:
                messages.append(message)
        return Response(data=[serializers.Message(message).data for message in messages], status=HTTP_200_OK)

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
        serializer = serializers.MessagesPostRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        if is_blocked(request.user.id, serializer.validated_data['user_destination_id']):
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `user_destination_id`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if not models.Message.objects.filter(
            Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_destination_id']) |
            Q(user_source_id=serializer.validated_data['user_destination_id'], user_destination_id=request.user.id),
            type__in=[
                'Response - Accepted',
                'Response - Deferred',
                'Response - Rejected',
                'Message',
            ],
        ).count():
            message = models.Message.objects.filter(
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
                    if message.type in ['Request']:
                        return Response(status=HTTP_403_FORBIDDEN)
                if message.user_destination_id == request.user.id:
                    if message.type in ['Response - Blocked']:
                        return Response(status=HTTP_403_FORBIDDEN)
        return Response(
            data=serializers.MessagesPostResponse(serializer.save(user_source=request.user)).data,
            status=HTTP_201_CREATED,
        )

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
        instance = self.get_object()
        serializer = serializers.MessagesPatchRequest(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        if 'user_source_is_hidden' in request.data or 'user_destination_is_hidden' in request.data:
            celery.push_notifications.delay(
                user_id=request.user.id,
                json={
                    'aps': {},
                    'type': 'updateMessage',
                },
            )
        return Response(data=serializers.MessagesPatchResponse(message).data, status=HTTP_200_OK)

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
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        return super(Messages, self).destroy(request, *args, **kwargs)

    def get_queryset(self):
        ids = []
        for block in models.Block.objects.filter(
            Q(user_source_id=self.request.user.id) | Q(user_destination_id=self.request.user.id),
        ).order_by(
            '-timestamp',
        ).all():
            if block.user_source.id == self.request.user.id:
                if block.user_destination.id not in ids:
                    ids.append(block.user_destination.id)
            if block.user_destination.id == self.request.user.id:
                if block.user_source.id not in ids:
                    ids.append(block.user_source.id)
        return models.Message.objects.exclude(id__in=ids).order_by('-inserted_at').all()


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def messages_bulk_is_hidden(request):
    '''
    Bulk update `user_source_is_hidden` and `user_destination_is_hidden` attributes of Messages

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
    serializer = serializers.MessagesBulkRequest(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = []
    for message in models.Message.objects.filter(
        Q(user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_id']) |
        Q(user_source_id=serializer.validated_data['user_id'], user_destination_id=request.user.id),
    ).order_by(
        '-inserted_at',
    ).all():
        if message.user_source_id == request.user.id:
            message.user_source_is_hidden = True
        if message.user_destination_id == request.user.id:
            message.user_destination_is_hidden = True
        message.save()
        data.append(serializers.MessagesBulkResponse(message).data)
    celery.push_notifications.delay(
        user_id=request.user.id,
        json={
            'aps': {},
            'type': 'updateThread',
        },
    )
    return Response(data=data, status=HTTP_200_OK)


@api_view(('POST',))
@permission_classes((IsAuthenticated,))
def messages_bulk_status(request):
    '''
    Bulk update `status` attributes of Messages

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
    serializer = serializers.MessagesBulkRequest(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = []
    for message in models.Message.objects.filter(
        Q(user_source_id=serializer.validated_data['user_id'], user_destination_id=request.user.id),
    ).order_by(
        '-inserted_at',
    ).all():
        message.status = 'Read'
        message.save()
        data.append(serializers.MessagesBulkResponse(message).data)
    return Response(data=data, status=HTTP_200_OK)


class SharesUsers(GenericViewSet, ListModelMixin, CreateModelMixin):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.SharesUsersGet

    def get(self, request, *args, **kwargs):
        '''
        SELECT Shares

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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SharesUsersGet
        '''
        type = request.QUERY_PARAMS['type'] if 'type' in request.QUERY_PARAMS else ''
        if not type or type not in ['Source', 'Destination']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `type`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                context={
                    'request': request,
                },
                many=True,
            )
            return self.get_paginated_response(serializer.data)
        return Response(
            data=self.get_serializer(
                queryset,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        INSERT a Share

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
        instance = serializer.create()
        return Response(
            data=serializers.SharesOffersPostResponse({
                'email': {
                    'subject': 'Tellecast - Shares/Users - %(id)s' % {
                        'id': instance.id,
                    },
                    'body': 'Tellecast - Shares/Users - %(id)s' % {
                        'id': instance.id,
                    },
                },
                'sms': 'Tellecast - Shares/Users - %(id)s' % {
                    'id': instance.id,
                },
                'facebook_com': 'tellecast://shares/users/%(id)s' % {
                    'id': instance.id,
                },
                'twitter_com': 'tellecast://shares/users/%(id)s' % {
                    'id': instance.id,
                },
            }).data,
            status=HTTP_200_OK,
        )

    def get_queryset(self):
        if 'type' in self.request.QUERY_PARAMS:
            if self.request.QUERY_PARAMS['type'] == 'Source':
                return models.ShareUser.objects.filter(
                    user_source_id=self.request.user.id,
                ).order_by('-timestamp').all()
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.ShareUser.objects.filter(
                    user_destination_id=self.request.user.id,
                ).order_by('-timestamp').all()
        return models.ShareUser.objects.filter(user_source_id=self.request.user.id).order_by('-timestamp').all()


class SharesOffers(GenericViewSet, ListModelMixin, CreateModelMixin):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.SharesOffersGet

    def get(self, request, *args, **kwargs):
        '''
        SELECT Shares

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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.SharesOffersGet
        '''
        type = request.QUERY_PARAMS['type'] if 'type' in request.QUERY_PARAMS else ''
        if not type or type not in ['Source', 'Destination']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `type`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                context={
                    'request': request,
                },
                many=True,
            )
            return self.get_paginated_response(serializer.data)
        return Response(
            data=self.get_serializer(
                queryset,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        '''
        INSERT a Share

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: optional

        + object_id
            - Description: ID of the offer that is being shared
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
              pytype: api.serializers.SharesOffersPostRequest
        response_serializer: api.serializers.SharesOffersPostResponse
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        serializer = serializers.SharesOffersPostRequest(
            context={
                'request': request,
            },
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.create()
        return Response(
            data=serializers.SharesOffersPostResponse({
                'email': {
                    'subject': 'Tellecast - Shares/Offers - %(id)s' % {
                        'id': instance.id,
                    },
                    'body': 'Tellecast - Shares/Offers - %(id)s' % {
                        'id': instance.id,
                    },
                },
                'sms': 'Tellecast - Shares/Offers - %(id)s' % {
                    'id': instance.id,
                },
                'facebook_com': 'tellecast://shares/offers/%(id)s' % {
                    'id': instance.id,
                },
                'twitter_com': 'tellecast://shares/offers/%(id)s' % {
                    'id': instance.id,
                },
            }).data,
            status=HTTP_200_OK,
        )

    def get_queryset(self):
        if 'type' in self.request.QUERY_PARAMS:
            if self.request.QUERY_PARAMS['type'] == 'Source':
                return models.ShareOffer.objects.filter(
                    user_source_id=self.request.user.id,
                ).order_by('-timestamp').all()
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.ShareOffer.objects.filter(
                    user_destination_id=self.request.user.id,
                ).order_by('-timestamp').all()
        return models.ShareOffer.objects.filter(user_source_id=self.request.user.id).order_by('-timestamp').all()


class Tellcards(DestroyModelMixin, GenericViewSet, ListModelMixin, UpdateModelMixin):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.TellcardsResponse

    def list(self, request, *args, **kwargs):
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
        parameters:
            - name: type
              paramType: query
              required: true
              type: string
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.TellcardsResponse
        '''
        type = request.QUERY_PARAMS['type'] if 'type' in request.QUERY_PARAMS else ''
        if not type or type not in ['Source', 'Destination']:
            return Response(
                data={
                    'error': ugettext_lazy('Invalid `type`'),
                },
                status=HTTP_400_BAD_REQUEST,
            )
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page,
                context={
                    'request': request,
                },
                many=True,
            )
            return self.get_paginated_response(serializer.data)
        return Response(
            data=self.get_serializer(
                queryset,
                context={
                    'request': request,
                },
                many=True,
            ).data,
            status=HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        '''
        INSERT a Tellcard

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
        serializer.create()
        return Response(data={}, status=HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        '''
        DELETE a Tellcard

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

        + N/A
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
        return Response(data={}, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a Tellcard

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        + N/A
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        instance = self.get_object()
        if instance:
            instance.saved_at = None
        instance.save()
        return Response(data={}, status=HTTP_200_OK)

    def get_queryset(self):
        if 'type' in self.request.QUERY_PARAMS:
            if self.request.QUERY_PARAMS['type'] == 'Source':
                return models.Tellcard.objects.filter(
                    user_source_id=self.request.user.id, saved_at__isnull=False,
                ).order_by('-id').all()
            if self.request.QUERY_PARAMS['type'] == 'Destination':
                return models.Tellcard.objects.filter(
                    user_destination_id=self.request.user.id, saved_at__isnull=False,
                ).order_by('-id').all()
        return models.Tellcard.objects.filter(
            user_source_id=self.request.user.id, saved_at__isnull=False,
        ).order_by('-id').all()


class Blocks(DestroyModelMixin, GenericViewSet, ListModelMixin, UpdateModelMixin):

    lookup_field = 'id'
    page_kwarg = 'page'
    paginate_by = 100
    paginate_by_param = 'per_page'
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = serializers.BlocksResponse

    def list(self, request, *args, **kwargs):
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
        responseMessages:
            - code: 400
              message: Invalid Input
        serializer: api.serializers.BlocksResponse
        '''
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(data=self.get_serializer(queryset, many=True).data, status=HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        '''
        INSERT a Block

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
        serializer.create()
        return Response(data={}, status=HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        '''
        DELETE a Block

        <pre>
        Input
        =====

        + user_destination_id
            - Type: integer
            - Status: mandatory

        Output
        ======

        + N/A
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
        models.Block.objects.filter(
            user_source_id=request.user.id, user_destination_id=serializer.validated_data['user_destination_id'],
        ).delete()
        return Response(data={}, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE a Block

        <pre>
        Input
        =====

        + id
            - Type: integer
            - Status: mandatory

        Output
        ======

        + N/A
        </pre>
        ---
        response_serializer: api.serializers.Null
        responseMessages:
            - code: 400
              message: Invalid Input
        '''
        self.get_object().delete()
        return Response(data={}, status=HTTP_200_OK)

    def get_queryset(self):
        return models.Block.objects.filter(user_source_id=self.request.user.id).order_by('-timestamp').all()


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
        point__distance_lte=(point, D(ft=serializer.data['radius'])),
    ).distance(
        point,
    ).all():
        data.append(
            serializers.TellzonesResponse(
                tellzone,
                context={
                    'request': request,
                },
            ).data
        )
    return Response(data=data, status=HTTP_200_OK)


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


def is_blocked(one, two):
    if models.Block.objects.filter(
        Q(user_source_id=one, user_destination_id=two) | Q(user_source_id=two, user_destination_id=one),
    ).count():
        return True
    return False
