# -*- coding: utf-8 -*-

from django.conf.urls import include, patterns, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'api.views.home', name='home'),
    # url(r'^api/', include('api.foo.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
