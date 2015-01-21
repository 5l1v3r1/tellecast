# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin, admindocs
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import RedirectView
from social.apps.django_app.default.models import (
    Association, Nonce, UserSocialAuth,
)

admin.autodiscover()

admin.site.unregister(Association)
admin.site.unregister(Group)
admin.site.unregister(Nonce)
admin.site.unregister(Site)
admin.site.unregister(UserSocialAuth)

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('admin:index'))),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include(admindocs.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
