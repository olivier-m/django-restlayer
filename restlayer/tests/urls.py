# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from django.conf.urls import patterns, url


urlpatterns = patterns('restlayer.tests.resources',
    url(r'^$', 'simple', name='simple'),
    url(r'^post$', 'simple_post', name='simple_post'),
    url(r'^echo$', 'simple_echo', name='simple_echo'),
    url(r'^error$', 'simple_error'),
    url(r'^serialize/text$', 'simple_s_text'),
    url(r'^serialize/any$', 'simple_s_any'),

    url(r'^objects$', 'simple_object_list', name='simple_objects'),
    url(r'^objects/(\d+)$', 'simple_object', name='simple_object'),
)
