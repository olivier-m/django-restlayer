# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

import json
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sys
import traceback

import mimeparse

from django.conf import settings
from django.core.mail import mail_admins
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotAllowed, Http404

from restlayer.exc import HttpException, Http406
from restlayer.utils import ModelDataLoader, get_request_data, xml_dumps

class BaseResponse(type):
    def __new__(cls, names, bases, attrs):
        new_class = super(BaseResponse, cls).__new__(cls, names, bases, attrs)
        
        new_class.methods = []
        
        # Prepare HEAD response based on GET when possible.
        if not hasattr(new_class, 'response_head') and hasattr(new_class, 'response_get'):
            new_class.response_head = new_class._response_head
        
        for meth in dir(new_class):
            if meth.startswith('response_') and callable(getattr(new_class, meth)):
                new_class.methods.append(meth[9:])
        
        return new_class
    

class Response(HttpResponse):
    __metaclass__ = BaseResponse
    
    serializers = (
        ('application/json', lambda x: json.dumps(x, indent=1, cls=DjangoJSONEncoder)),
        ('application/xml', xml_dumps),
        ('application/python-pickle', pickle.dumps)
    )
    
    deserializers = (
        ('application/x-www-form-urlencoded', get_request_data),
        ('application/json', lambda req: json.loads(req.raw_post_data or "{}")),
    )
    
    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        self.mime = 'application/json'
        self.charset = 'UTF8'
        
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
        
        self['content-type'] = '%s; charset=%s' % (self.mime, self.charset)
        return renderer(result)
    
    def init_response(self, request):
        accept = request.META.get('HTTP_ACCEPT', None)
        if not accept:
            raise Http406
        
        try:
            self.mime = mimeparse.best_match([x[0] for x in self.serializers], accept)
            if not self.mime:
                raise ValueError
        except ValueError:
            raise Http406
        
        # Reading data
        if request.method in ('POST', 'PUT'):
            content_type = request.META.get('CONTENT_TYPE', '').split(';',1)[0]
            
            deserializers = dict(self.deserializers)
            deserializer = deserializers.get(content_type)
            # We may have a default deserializer
            if not deserializer:
                deserializer = deserializers.get('*/*')
            
            if not deserializer:
                raise Http406
            try:
                request.data = deserializer(request)
            except BaseException, e:
                raise HttpException(str(e), 400)
    
    def make_response(self, request, *args, **kwargs):
        if request.method.lower() not in self.methods:
            return HttpResponseNotAllowed(self.methods)
        
        meth = getattr(self, 'response_%s' % request.method.lower())
        
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
        except Http406, e:
            self.status_code = e.args[1]
            self.content = ''
            self['content-type'] = 'text/plain'
        except HttpException, e:
            self.status_code = e.args[1]
            self.content = self.serialize(request, e.args[0])
        except BaseException, e:
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
    

class ModelResponse(Response):
    fields = ('id',)
    
    def __init__(self, *args, **kwargs):
        super(ModelResponse, self).__init__(*args, **kwargs)
        self.data_loader = ModelDataLoader(self.fields)
    
    def serialize(self, request, res, **options):
        return super(ModelResponse, self).serialize(request, res, fields=self.fields, resp=self, **options)
    

class Resource(object):
    csrf_exempt = True
    
    def __init__(self, resp_class):
        self.resp_class = resp_class
    
    def __call__(self, request, *args, **kwargs):
        try:
            return self.resp_class().make_response(request, *args, **kwargs)
        except BaseException, e:
            return self.handle_exception(e, request)
    
    def handle_exception(self, exc, request):
        trace = '\n'.join(traceback.format_exception(*sys.exc_info()))
        if hasattr(exc, 'resp_obj'):
            resp = exc.resp_obj
            resp.status_code = 500
            resp.content = ''
            resp.set_common_headers(request)
        else:
            resp = HttpResponse('', status=500, content_type='text/plain')
            resp.content = ''
        
        if settings.DEBUG:
            resp.content = trace
        else:
            subject = 'Error (%s IP): %s' % ((request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
            try:
                request_repr = repr(request)
            except:
                request_repr = "Request repr() unavailable"
            message = "%s\n\n%s" % (trace, request_repr)
            mail_admins(subject, message, fail_silently=True)
        
        resp['Content-Type'] = 'text/plain'
        return resp
    