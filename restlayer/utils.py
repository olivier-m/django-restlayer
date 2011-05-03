# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from django import db
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator

class ModelDataLoader(object):
    def __init__(self, fields):
        self.fields = fields
    
    def __call__(self, res, request, **options):
        if isinstance(res, db.models.query.QuerySet):
            return [self(x, request, **options) for x in res]
        
        elif isinstance(res, db.models.Model):
            return dict([
                (x, self.get_field_value(res, x, request, **options))
                for x in options.get('fields', ('pk',))
            ])
        
        return res
    
    def get_field_value(self, instance, field, request, **options):
        resp = options.get('resp')
        if resp:
            f = getattr(resp, field, None)
            if callable(f):
                return f(instance, request)
        
        try:
            f = getattr(instance, field)
            if callable(f):
                return f()
            return f
        except AttributeError:
            pass
        
        raise Exception('Field %s not found.' % field)
    

def get_request_data(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.
    
    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method == "PUT":
        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'
            
        return request.POST
    elif request.method == "POST":
        return request.POST
    

def xml_dumps(data):
    def to_xml(xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("resource", {})
                to_xml(xml, item)
                xml.endElement("resource")
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                to_xml(xml, value)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))
    
    stream = StringIO.StringIO()
    
    xml = SimplerXMLGenerator(stream, "utf-8")
    xml.startDocument()
    xml.startElement("response", {})
    
    to_xml(xml, data)
    
    xml.endElement("response")
    xml.endDocument()
    
    return stream.getvalue()
