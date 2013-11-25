# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import json
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sys

import mimeparse

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotAllowed, Http404
from django.utils.encoding import smart_text
from django.utils.six import add_metaclass

from restlayer.utils import get_request_data, xml_dumps, CONTENT_VERBS


class FormError(dict):
    pass


class HttpException(Exception):
    def __init__(self, msg, status=500):
        super(HttpException, self).__init__(msg, status)


class Http406(HttpException):
    def __init__(self):
        super(HttpException, self).__init__('', 406)


class FormValidationError(HttpException):
    def __init__(self, form):
        super(FormValidationError, self).__init__(FormError(form.errors), 400)


class BaseResponse(type):
    def __new__(mcs, names, bases, attrs):
        new_class = super(BaseResponse, mcs).__new__(mcs, names, bases, attrs)

        new_class.methods = []

        # Prepare HEAD response based on GET when possible.
        if not hasattr(new_class, 'response_head') and hasattr(new_class, 'response_get'):
            new_class.response_head = new_class._response_head

        for meth in dir(new_class):
            if meth.startswith('response_') and callable(getattr(new_class, meth)):
                new_class.methods.append(meth[9:])

        return new_class


@add_metaclass(BaseResponse)
class Response(HttpResponse):
    serializers = (
        ('application/json', lambda x: json.dumps(x, indent=1, cls=DjangoJSONEncoder)),
        ('application/xml', xml_dumps),
        ('application/python-pickle', pickle.dumps)
    )

    deserializers = (
        ('application/x-www-form-urlencoded', get_request_data),
        ('multipart/form-data', get_request_data),
        ('application/json', lambda req: json.loads(smart_text(req.body) or '{}')),
    )

    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        self.mime = 'application/json'
        self.charset = 'UTF-8'

        self.data_loader = lambda x, req, **k: x

    def response_options(self, request, *args, **kwargs):
        self['Allow'] = ', '.join([x.upper() for x in self.methods])
        self.status_code = 204
        return self

    def _response_head(self, request, *args, **kwargs):
        if not hasattr(self, 'response_get'):
            raise Http406

        response = self.response_get(request, *args, **kwargs)
        response.content = ''
        return response

    def serialize(self, request, res, **options):
        # Get Python Data
        result = None
        if callable(self.data_loader):
            result = self.data_loader(res, request, **options)

        # Formatting result
        renderer = dict(self.serializers).get(self.mime)
        if not renderer:
            raise Http406

        self['content-type'] = '{0}; charset={1}'.format(self.mime, self.charset)
        return renderer(result)

    def init_response(self, request):
        accept = request.META.get('HTTP_ACCEPT', None)
        if not accept and '*/*' in [x[0] for x in self.serializers]:
            accept = '*/*'

        # OPTIONS special case
        if request.method == 'OPTIONS':
            if len(self.serializers) > 0:
                # OPTIONS should always return a response
                accept = self.serializers[0][0]

        if not accept:
            raise Http406

        # Prepare response now
        try:
            self.mime = mimeparse.best_match([x[0] for x in self.serializers], accept)
            if not self.mime:
                raise ValueError
        except ValueError:
            raise Http406

        # Reading data
        if request.method in CONTENT_VERBS:
            content_type = request.META.get('CONTENT_TYPE', '').split(';', 1)[0]

            deserializers = dict(self.deserializers)
            deserializer = deserializers.get(content_type)
            # We may have a default deserializer
            if not deserializer:
                deserializer = deserializers.get('*/*')

            if not deserializer:
                raise Http406
            try:
                request.data = deserializer(request)
            except BaseException as e:
                raise HttpException(str(e), 400)

    def make_response(self, request, *args, **kwargs):
        if request.method.lower() not in self.methods:
            return HttpResponseNotAllowed([x.upper() for x in self.methods])

        meth = getattr(self, 'response_{0}'.format(request.method.lower()))

        try:
            self.init_response(request)
            res = meth(request, *args, **kwargs)
            if isinstance(res, HttpResponse):
                if hasattr(res, 'set_common_headers'):
                    res.set_common_headers(request)
                if request.method == 'HEAD':
                    res.content = ''
                return res
            self.content = self.serialize(request, res)
        except Http404:
            self.status_code = 404
            self.content = self.serialize(request, "Resource not found")
        except Http406 as e:
            self.status_code = e.args[1]
            self.content = ''
            self['content-type'] = 'text/plain'
        except HttpException as e:
            self.status_code = e.args[1]
            self.content = self.serialize(request, e.args[0])
        except BaseException as e:
            e.resp_obj = self
            raise

        self.set_common_headers(request)
        return self

    def get_common_headers(self, request):
        return {}

    def set_common_headers(self, request):
        for k, v in self.get_common_headers(request).items():
            if k not in self:
                self[k] = v

    def paginate(self, request, object_list, limit=50):
        """
        Pagination helper
        """
        paginator = Paginator(object_list, limit)
        try:
            page_no = int(request.GET.get('page', 1))
        except ValueError:
            page_no = 1
        try:
            page = paginator.page(page_no)
        except (InvalidPage, EmptyPage):
            page = paginator.page(1)

        self['X-Pages-Objects'] = paginator.count
        self['X-Pages-Count'] = paginator.num_pages
        self['X-Pages-Current'] = page.number

        GET = request.GET.copy()
        if page.has_next():
            GET['page'] = page.number + 1
            self['X-Pages-Next'] = page.number + 1
            self['X-Pages-Next-URI'] = '{0}?{1}'.format(
                self._build_absolute_uri(request, request.path),
                GET.urlencode()
            )
        if page.has_previous():
            GET['page'] = page.number - 1
            self['X-Pages-Prev'] = page.number - 1
            self['X-Pages-Prev-URI'] = '{0}?{1}'.format(
                self._build_absolute_uri(request, request.path),
                GET.urlencode()
            )

        return page.object_list

    def _build_absolute_uri(self, request, location=None):
        return request.build_absolute_uri(location)

    def reverse(self, request, view, args=None, kwargs=None):
        return self._build_absolute_uri(request, reverse(view, args=args, kwargs=kwargs))


class Resource(object):
    csrf_exempt = True

    def __init__(self, resp_class):
        self.resp_class = resp_class

    def __call__(self, request, *args, **kwargs):
        try:
            return self.resp_class().make_response(request, *args, **kwargs)
        except BaseException as e:
            return self.handle_exception(e, request)

    def handle_exception(self, exc, request):
        from django.utils.log import getLogger
        from django.conf import settings

        logger = getLogger('django.request')
        exc_info = sys.exc_info()

        logger.error(
            'Internal Server Error: %s', request.path,
            exc_info=exc_info,
            extra={
                'status_code': 500,
                'request': request
            }
        )

        resp = HttpResponse('', status=500, content_type='text/plain')
        resp.content = ''

        if hasattr(exc, 'resp_obj'):
            resp = exc.resp_obj
            resp.status_code = 500
            resp.set_common_headers(request)
        else:
            resp = HttpResponse('', status=500, content_type='text/plain')

        resp.content = 'An error occured.'

        if settings.DEBUG:
            from django.views.debug import ExceptionReporter
            reporter = ExceptionReporter(request, *exc_info)
            resp.content = reporter.get_traceback_text()

        resp['Content-Type'] = 'text/plain'
        return resp
