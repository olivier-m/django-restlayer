# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
import json
import pickle
from urlparse import urlparse

from django.test import Client, TestCase
from django.test.client import FakePayload

__all__ = ('SimpleTest', 'SimpleObjectTest')


class BaseClient(Client):
    # Needed for Django 1.4 & 1.5 compat
    def patch(self, path, data={}, content_type='application/octet-stream', **extra):
        "Construct a PATCH request."
        if hasattr(super(BaseClient, self), 'patch'):
            return super(BaseClient, self).patch(path, data, content_type, **extra)

        patch_data = self._encode_data(data, content_type)

        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(patch_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input':     FakePayload(patch_data),
        }
        r.update(extra)
        return self.request(**r)


class BaseTestCase(TestCase):
    urls = 'restlayer.tests.urls'

    def setUp(self):
        self.client = BaseClient()


class SimpleTest(BaseTestCase):
    def test_base(self):
        # Invalid accept
        r = self.client.get('/')
        self.assertEqual(r.status_code, 406)

        r = self.client.get('/', HTTP_ACCEPT='text/plain')
        self.assertEqual(r.status_code, 406)

        # OPTIONS
        r = self.client.options('/')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r['allow'], 'GET, HEAD, OPTIONS')

        # should work with bad Accept too
        r = self.client.options('/', HTTP_ACCEPT='fuuuuu')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r['allow'], 'GET, HEAD, OPTIONS')

    def test_format(self):
        r = self.client.get('/', HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content), ['foo', 'bar'])

        r = self.client.get('/', HTTP_ACCEPT='application/python-pickle')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(pickle.loads(r.content), ['foo', 'bar'])

        r = self.client.get('/', HTTP_ACCEPT='application/xml')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, '<?xml version="1.0" encoding="utf-8"?>\n<response><resource>foo</resource><resource>bar</resource></response>')

    def test_not_allowed(self):
        r = self.client.post('/', {'foo': 'bar'}, HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r['allow'], 'GET, HEAD, OPTIONS')

    def test_post_form(self):
        r = self.client.post('/post', 'foo=bar', HTTP_ACCEPT='application/json',
                            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(json.loads(r.content), {'foo': 'bar'})
        self.assertEqual(r['Location'], 'http://testserver/post')

    def test_post_json(self):
        r = self.client.post('/post', json.dumps({'foo': 'bar'}), HTTP_ACCEPT='application/json',
                            content_type='application/json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(json.loads(r.content), {'foo': 'bar'})
        self.assertEqual(r['Location'], 'http://testserver/post')

    def test_put_patch(self):
        r = self.client.put('/echo', 'foo=1', HTTP_ACCEPT='application/json',
                            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['method'], 'PUT')

        r = self.client.patch('/echo', 'foo=1', HTTP_ACCEPT='application/json',
                            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(json.loads(r.content)['method'], 'PATCH')

    def test_errors(self):
        r = self.client.get('/error', HTTP_ACCEPT='application/json')
        self.assertEqual(r['content-type'], 'text/plain')
        self.assertEqual(r.content, 'An error occured.')

        with self.settings(DEBUG=True):
            r = self.client.get('/error', HTTP_ACCEPT='application/json')
            self.assertEqual(r['content-type'], 'text/plain')
            self.assertTrue(r.content.startswith('Exception at /error'))
            self.assertTrue(len(r.content) > 1000)

    def test_serializers(self):
        r = self.client.get('/serialize/text', HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 406)

        r = self.client.get('/serialize/text', HTTP_ACCEPT='text/plain')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'test')

        r = self.client.get('/serialize/any')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, 'any')


class SimpleObjectTest(BaseTestCase):
    def create_object(self, **data):
        return self.client.post('/objects', data, HTTP_ACCEPT='application/json')

    def test_object_list(self):
        r = self.client.get('/objects', HTTP_ACCEPT='application/json')

        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.has_header('x-pages-count') and r['x-pages-count'] == '1')
        self.assertTrue(r.has_header('x-pages-current') and r['x-pages-current'] == '1')
        self.assertTrue(r.has_header('x-pages-objects') and r['x-pages-objects'] == '0')

        self.assertEqual(json.loads(r.content), [])

    def test_object_create(self):
        r = self.create_object(foo='foo1', bar=2)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.has_header('location'))
        loc = r['location']

        r = self.client.get(loc, HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)

        self.assertEqual(data['foo'], 'foo1')
        self.assertEqual(data['bar'], 2)
        self.assertEqual(data['resource_uri'], loc)

    def test_object_update(self):
        r = self.create_object(foo='foo1', bar=1)
        loc = r['location']

        r = self.client.put(loc, 'foo=foo2&bar=3', HTTP_ACCEPT='application/json',
                            content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content)

        self.assertEqual(data['foo'], 'foo2')
        self.assertEqual(data['bar'], 3)
        self.assertEqual(data['resource_uri'], loc)

    def test_object_delete(self):
        r = self.create_object(foo='foo1', bar=1)
        loc = r['location']

        r = self.client.delete(loc, HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 204)

    def test_404(self):
        r = self.client.get('/objects/10', HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(json.loads(r.content), 'Resource not found')

    def test_pagination(self):
        for i in range(0, 32):
            self.create_object(foo='foo-{0}'.format(i), bar=i)

        r = self.client.get('/objects', HTTP_ACCEPT='application/json')

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['x-pages-count'], '4')
        self.assertEqual(r['x-pages-objects'], '32')
        self.assertEqual(r['x-pages-current'], '1')
        self.assertTrue(r.has_header('x-pages-next') and r.has_header('x-pages-next-uri'))

        r = self.client.get(r['x-pages-next-uri'], HTTP_ACCEPT='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['x-pages-current'], '2')
        self.assertTrue(r.has_header('x-pages-next') and r.has_header('x-pages-next-uri'))
        self.assertTrue(r.has_header('x-pages-prev') and r.has_header('x-pages-prev-uri'))

        self.assertEqual(len(json.loads(r.content)), 10)
