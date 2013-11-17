# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from django import db

from restlayer.api import Response


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

        if hasattr(instance, field):
            f = getattr(instance, field)
        else:
            raise ValueError('Field {0} not found.'.format(field))

        if callable(f):
            return f()
        return f


class ModelResponse(Response):
    fields = ('id',)

    def __init__(self, *args, **kwargs):
        super(ModelResponse, self).__init__(*args, **kwargs)
        self.data_loader = ModelDataLoader(self.fields)

    def serialize(self, request, res, **options):
        return super(ModelResponse, self).serialize(
            request, res,
            fields=self.fields, resp=self, **options
        )

    def get_data(self, request, res, **options):
        if callable(self.data_loader):
            fields = options.pop('fields', self.fields)
            return self.data_loader(res, request, fields=fields, resp=self, **options)
