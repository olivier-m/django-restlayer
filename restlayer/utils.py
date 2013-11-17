# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django.utils.six import StringIO
from django.utils.encoding import smart_text

from django.utils.xmlutils import SimplerXMLGenerator


CONTENT_VERBS = ('POST', 'PUT', 'PATCH')


def get_request_data(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.

    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method in CONTENT_VERBS:
        if request.method == 'POST':
            return request.POST
        else:
            orig_meth = request.method
            try:
                request.method = 'POST'
                request._load_post_and_files()
                request.method = orig_meth
            except AttributeError:
                request.META['REQUEST_METHOD'] = 'POST'
                request._load_post_and_files()
                request.META['REQUEST_METHOD'] = orig_meth

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
            xml.characters(smart_text(data))

    stream = StringIO()

    xml = SimplerXMLGenerator(stream, "utf-8")
    xml.startDocument()
    xml.startElement("response", {})

    to_xml(xml, data)

    xml.endElement("response")
    xml.endDocument()

    return stream.getvalue()
