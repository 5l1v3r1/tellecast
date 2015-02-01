# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib.admin import autodiscover, site
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView
from rest_framework.authtoken.models import Token
from rest_framework.routers import SimpleRouter
from social.apps.django_app.default.models import (
    Association, Nonce, UserSocialAuth,
)

from api import views

autodiscover()

site.unregister(Association)
site.unregister(Group)
site.unregister(Nonce)
site.unregister(Site)
site.unregister(Token)
site.unregister(UserSocialAuth)

router = SimpleRouter()
router.register(r'master-tells', views.MasterTells, base_name='master-tells')
router.register(r'slave-tells', views.SlaveTells, base_name='slave-tells')
router.register(r'users/photos', views.UsersPhotos, base_name='users-photos')
router.register(
    r'users/social-profiles',
    views.UsersSocialProfiles,
    base_name='users-social-profiles',
)
router.register(
    r'users/statuses/attachments',
    views.UsersStatusesAttachments,
    base_name='users-statuses-attachments',
)
router.register(
    r'users/statuses', views.UsersStatuses, base_name='users-statuses',
)
router.register(r'users/urls', views.UsersURLs, base_name='users-urls')
router.register(r'users', views.Users, base_name='users')

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    url(r'^admin/', include(site.urls)),
    url(r'^api/authenticate/(?P<backend>[^/]+)/$', views.authenticate),
    url(r'^api/master-tells/ids/$', views.master_tells_ids),
    url(r'^api/master-tells/positions/$', views.master_tells_positions),
    url(r'^api/register/', views.register),
    url(r'^api/slave-tells/ids/$', views.slave_tells_ids),
    url(r'^api/slave-tells/positions/$', views.slave_tells_positions),
    url(r'^api/users/(?P<id>\d+)/profile/$', views.users_profile),
    url(r'^api/', include(router.urls)),
    url(r'^swagger/', include('rest_framework_swagger.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
