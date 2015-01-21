# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin, admindocs
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView
from rest_framework import routers, serializers, viewsets
from social.apps.django_app.default.models import (
    Association, Nonce, UserSocialAuth,
)

from api.views import UserViewSet

admin.autodiscover()

admin.site.unregister(Association)
admin.site.unregister(Group)
admin.site.unregister(Nonce)
admin.site.unregister(Site)
admin.site.unregister(UserSocialAuth)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = patterns(
    '',
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^$', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    url(r'^', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include(admindocs.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
