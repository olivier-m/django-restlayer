# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator


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
