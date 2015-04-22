# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib.admin import autodiscover, site
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.routers import SimpleRouter
from rest_framework_swagger import urls
from social.apps.django_app.default.models import Association, Nonce

from api import views

JSONRenderer.charset = 'utf-8'

autodiscover()

site.unregister(Association)
site.unregister(Group)
site.unregister(Nonce)
site.unregister(Site)
site.unregister(Token)

router = SimpleRouter()
router.register(r'devices/apns', views.DevicesAPNS, base_name='devices-apns')
router.register(r'devices/gcm', views.DevicesGCM, base_name='devices-gcm')
router.register(r'master-tells', views.MasterTells, base_name='master-tells')
router.register(r'slave-tells', views.SlaveTells, base_name='slave-tells')
router.register(r'messages', views.Messages, base_name='messages')

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    url(r'^admin/', include(site.urls)),
    url(r'^swagger/', include(urls)),
    url(r'^api/register/$', views.register),
    url(r'^api/authenticate/(?P<backend>[^/]+)/$', views.authenticate),
    url(
        r'^api/users/$',
        views.Users.as_view({
            'get': 'list',
        }),
    ),
    url(
        r'^api/users/(?P<id>[^/]+)/$',
        views.Users.as_view({
            'get': 'retrieve',
            'put': 'update',
            'delete': 'destroy',
        }),
    ),
    url(r'^api/users/(?P<id>[^/]+)/profile/$', views.users_profile),
    url(r'^api/users/(?P<id>[^/]+)/tellzones/$', views.users_tellzones),
    url(r'^api/users/(?P<id>[^/]+)/offers/$', views.users_offers),
    url(r'^api/radar/$', views.Radar.as_view()),
    url(r'^api/master-tells/ids/$', views.master_tells_ids),
    url(r'^api/master-tells/positions/$', views.master_tells_positions),
    url(r'^api/slave-tells/ids/$', views.slave_tells_ids),
    url(r'^api/slave-tells/positions/$', views.slave_tells_positions),
    url(r'^api/messages/bulk/is_hidden/$', views.messages_bulk_is_hidden),
    url(r'^api/messages/bulk/status/$', views.messages_bulk_status),
    url(
        r'^api/tellcards/$',
        views.Tellcards.as_view({
            'get': 'list',
            'post': 'create',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/tellcards/(?P<id>[^/]+)/$',
        views.Tellcards.as_view({
            'delete': 'destroy',
        }),
    ),
    url(
        r'^api/blocks/$',
        views.Blocks.as_view({
            'get': 'list',
            'post': 'create',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/blocks/(?P<id>[^/]+)/$',
        views.Blocks.as_view({
            'delete': 'destroy',
        }),
    ),
    url(r'^api/tellzones/$', views.tellzones),
    url(r'^api/', include(router.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {
                'document_root': settings.MEDIA_ROOT,
            },
        ),
    )

handler400 = 'api.views.handler400'
handler403 = 'api.views.handler403'
handler404 = 'api.views.handler404'
handler500 = 'api.views.handler500'
