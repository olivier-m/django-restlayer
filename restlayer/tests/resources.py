# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.shortcuts import get_object_or_404

from restlayer import Resource, Response, ModelResponse, FormValidationError

from restlayer.tests import SimpleModel, SimpleForm


class SimpleResponse(Response):
    def response_get(self, request):
        return ['foo', 'bar']


class SimplePost(Response):
    def response_post(self, request):
        self.status_code = 201
        self['Location'] = self.reverse(request, 'simple_post')
        return request.data


class SimpleEcho(Response):
    def echo(self, request):
        self.status_code = 200
        return {
            'data': request.data,
            'method': request.method
        }

    response_put = echo
    response_patch = echo


class SimpleError(Response):
    def response_get(self, request):
        raise Exception('Woops')


class SimpleSerializerText(Response):
    serializers = (
        ('text/plain', lambda x: x),
    )

    def response_get(self, request):
        return 'test'


class SimpleSerializerAny(Response):
    serializers = (
        ('*/*', lambda x: x),
    )

    def response_get(self, request):
        return 'any'


class SimpleObjectList(ModelResponse):
    fields = ('id', 'foo', 'bar', 'resource_uri')

    def resource_uri(self, instance, request):
        return self.reverse(request, 'simple_object', args=(instance.pk,))

    def response_get(self, request):
        return self.paginate(request, SimpleModel.objects.all(), 10)

    def response_post(self, request):
        form = SimpleForm(data=request.data)
        if not form.is_valid():
            raise FormValidationError(form)

        instance = form.save()
        self.status_code = 201
        self['Location'] = self.reverse(request, 'simple_object', args=(instance.pk,))
        return instance.pk


class SimpleObject(ModelResponse):
    fields = ('id', 'foo', 'bar', 'resource_uri')

    def resource_uri(self, instance, request):
        return self.reverse(request, 'simple_object', args=(instance.pk,))

    def response_get(self, request, pk):
        instance = get_object_or_404(SimpleModel, pk=pk)
        return instance

    def response_put(self, request, pk):
        instance = get_object_or_404(SimpleModel, pk=pk)
        form = SimpleForm(instance=instance, data=request.data)
        if not form.is_valid():
            raise FormValidationError(form)

        instance = form.save()
        self.status_code = 200
        self['Location'] = self.resource_uri(instance, request)
        return instance

    def response_delete(self, request, pk):
        instance = get_object_or_404(SimpleModel, pk=pk)
        instance.delete()

        self.status_code = 204
        return self


simple = Resource(SimpleResponse)
simple_post = Resource(SimplePost)
simple_echo = Resource(SimpleEcho)
simple_error = Resource(SimpleError)
simple_s_text = Resource(SimpleSerializerText)
simple_s_any = Resource(SimpleSerializerAny)

simple_object_list = Resource(SimpleObjectList)
simple_object = Resource(SimpleObject)
