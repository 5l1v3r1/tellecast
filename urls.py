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

urlpatterns = patterns(
    '',
    url(
        r'^$',
        RedirectView.as_view(permanent=True, url=reverse_lazy('admin:index'))
    ),
    url(r'^admin/', include(site.urls)),
    url(r'^api/ads/$', views.ads),
    url(r'^api/authenticate/(?P<backend>[^/]+)/$', views.authenticate),
    url(
        r'^api/blocks/delete/$',
        views.Blocks.as_view({
            'post': 'delete',
        }),
    ),
    url(
        r'^api/blocks/$',
        views.Blocks.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/deauthenticate/$', views.deauthenticate),
    url(
        r'^api/devices/apns/(?P<id>[^/]+)/$',
        views.DevicesAPNS.as_view({
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/devices/apns/$',
        views.DevicesAPNS.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(
        r'^api/devices/gcm/(?P<id>[^/]+)/$',
        views.DevicesGCM.as_view({
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/devices/gcm/$',
        views.DevicesGCM.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/home/connections/$', views.home_connections),
    url(r'^api/home/statistics/frequent/$', views.home_statistics_frequent),
    url(r'^api/home/statistics/infrequent/$', views.home_statistics_infrequent),
    url(r'^api/home/tellzones/$', views.home_tellzones),
    url(r'^api/master-tells/ids/$', views.master_tells_ids),
    url(r'^api/master-tells/positions/$', views.master_tells_positions),
    url(
        r'^api/master-tells/(?P<id>[^/]+)/$',
        views.MasterTells.as_view({
            'put': 'put',
            'patch': 'patch',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/master-tells/$',
        views.MasterTells.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(
        r'^api/messages/(?P<id>[^/]+)/$',
        views.Messages.as_view({
            'patch': 'patch',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/messages/$',
        views.Messages.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/messages/bulk/is_hidden/$', views.messages_bulk_is_hidden),
    url(r'^api/messages/bulk/status/$', views.messages_bulk_status),
    url(
        r'^api/notifications/$',
        views.Notifications.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(
        r'^api/radar/$', views.Radar.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/register/$', views.register),
    url(
        r'^api/shares/users/$',
        views.SharesUsers.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/slave-tells/ids/$', views.slave_tells_ids),
    url(r'^api/slave-tells/positions/$', views.slave_tells_positions),
    url(
        r'^api/slave-tells/(?P<id>[^/]+)/$',
        views.SlaveTells.as_view({
            'put': 'put',
            'patch': 'patch',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/slave-tells/$',
        views.SlaveTells.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(
        r'^api/tellcards/delete/$',
        views.Tellcards.as_view({
            'post': 'delete',
        }),
    ),
    url(
        r'^api/tellcards/$',
        views.Tellcards.as_view({
            'get': 'get',
            'post': 'post',
        }),
    ),
    url(r'^api/tellzones/(?P<id>[^/]+)/master-tells/$', views.tellzones_master_tells),
    url(r'^api/tellzones/$', views.tellzones),
    url(r'^api/users/(?P<id>[^/]+)/profile/$', views.users_profile),
    url(
        r'^api/users/(?P<id>[^/]+)/tellzones/delete/$',
        views.UsersTellzones.as_view({
            'post': 'delete',
        }),
    ),
    url(
        r'^api/users/(?P<id>[^/]+)/tellzones/$',
        views.UsersTellzones.as_view({
            'get': 'get',
            'post': 'post',
            'delete': 'delete',
        }),
    ),
    url(
        r'^api/users/(?P<id>[^/]+)/$',
        views.Users.as_view({
            'get': 'get',
            'put': 'put',
            'delete': 'delete',
        }),
    ),
    url(r'^swagger/', include(urls)),
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
