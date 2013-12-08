Introduction
============

Django Restlayer is a very simple to use toolkit to create RESTful APIs for your Django projects
or apps.

Features
========

- Allows you to respect HTTP methods and headers within your application.
- Class based resources.
- Simple to code.
- Form validation in case you need it.

Installation
============

- For Django 1.4: ``pip install django-restlayer==0.8.5``
- For Django 1.5+: ``pip install django-restlayer``

Configuration
=============

Django Restlayer doesn't need any configuration nor any app in ``INSTALLED_APPS`` settings.

Simple example
==============

urls.py::

  from django.conf.urls import patterns, url

  urlpatterns = patterns('',
      url(r'^$', 'myapp.resources.simple', name='simple'),
  )

myapp/resources.py::

  from restlayer import Resource, Response

  # Our resource class
  class SimpleResponse(Response):
      def response_get(self, request):
          return ['foo', 'bar']

  # Resource (a callable object or a view if you prefer)
  simple = Resource(SimpleResponse)

That's it. Now, query your development server ::

  curl -s -v -H "accept:application/json" http://localhost:8000/

  > GET /api/ HTTP/1.1
  > User-Agent: curl/7.33.0
  > Host: localhost
  > accept:application/json
  >
  < HTTP/1.1 200 OK
  < Server: nginx/1.4.3
  < Date: Thu, 28 Nov 2013 14:34:15 GMT
  < Content-Type: application/json; charset=UTF-8
  < Transfer-Encoding: chunked
  < Connection: keep-alive
  < Vary: Accept-Language, Cookie
  < Content-Language: en
  <
  [
   "foo",
   "bar"
  ]

Usage
=====

Response class
--------------

All your responses should inherit ``restlayer.Response`` class. Then, add methods named
``response_VERB`` where ``VERB`` is an HTTP verb. To handle GET responses, you need to create
a ``response_get`` method, for POST, ``response_post``. Each ``response_VERB`` method acts as a view
with needed arguments. A basic example:

::

  from restlayer import Response

  class SimpleResponse(Response):
      def response_get(self, request, my_id):
          # This method will match a URL pattern with "my_id"
          return "foo"

Predefined response methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two predefined response methods:

- ``response_options`` returns an empty 204 response with ``Allow`` header.
- ``response_head`` calls ``response_get`` if any and returns it without body.

Serializers
~~~~~~~~~~~

You can set ``serializers`` and ``deserializers`` properties. They set how data are going to be
serialized (out) or unserialized (in). In this example, we add a silly serializer for text/plain:

::

  class SimpleResponse(Response):
      serializers = Response.serializers + (
        ('text/plain', lambda x: return str(x))
      )

Well, that won't work very well but you have the idea. ``serializers`` is a list of tuples of mime
types and callables getting data as only parameter. ``deserializers`` is the same thing for accepted
data types (callable takes ``request`` as only argument).

Default formats are:

- ``serializers``
    - application/json
    - application/xml
    - application/python-pickle
- ``deserializers``
   - application/x-www-form-urlencoded
   - multipart/form-data
   - application/json

Responses are valid HttpResponse objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``restlayer.Response`` instances are valid ``django.http.HttpResponse`` objects. Thus you can:

- Add any header you want to your response setting ``self['my-header']`` before returning data;
- Change status code with ``self.status_code``;
- Return ``self`` if you need to set a specific response content without using serializers.

Resource
--------

Your response class should be wrapped within a ``restlayer.Resource`` class. The resulting instance
is a callable acting like a classic view. You can extend this class to create your own resource.
Simply override ``__call__`` method.

::

  from restlayer import Resource

  class SillyResource(Resource):
      def __call__(self, request, *args, **kwargs):
          rsp = super(SillyResource, self).__call__(request, *args, **kwargs)
          rsp.status_code = 401
          rsp['Content-Type'] = 'text/plain'
          return rsp

Responses for Django models
---------------------------

If you are working with Django models, you can use ``restlayer.ModelResponse``. Using this parent
class for your responses, you can return model instance or queryset. Here is a simple example:

::

  from django.contrib.auth.models import User
  from restlayer import ModelResponse

  class SimpleResponse(ModelResponse):
      fields = ('id', 'name', 'firstname', 'email')

      def response_get(self, request):
          return User.objects.all()

That's it! Using the ``fields`` property, you set the fields you want to return in the response.

You can add custom methods to create a specific response field. This method takes two parameters:
``ìnstance`` and ``request``. Example:

::

  from django.contrib.auth.models import User
  from restlayer import ModelResponse

  class SimpleResponse(ModelResponse):
      fields = ('id', 'name', 'firstname', 'email', 'other_field')

      def other_field(self, instance, request):
          return instance.name.capitalize()

      def response_get(self, request):
          return User.objects.all()

URLs
----

You'll often need to create a ``resource_uri`` field to point to another resource in your API.
Response class provides two methods to create absolute (with FQDN) URLs:

- ``_build_absolute_uri(self, request, [location])`` only calling ``request.build_absolute_uri(location)``
  but you can override it if you need.
- ``reverse(self, request, view, [args, kwargs])`` acts as ``django.core.urlresolvers.reverse`` but
  returns an absolute URL.

Pagination
----------

You might want to paginate your responses. Restlayer Response class provides a simple method for
this task: ``paginate(self, request, object_list, [limit])`` which is a simple wrapper around
``django.core.paginator.Paginator``. Resulting response will contain the following headers:

- X-Pages-Objects
- X-Pages-Count
- X-Pages-Current
- X-Pages-Next (if next page exists)
- X-Pages-Next-URI (if next page exists)
- X-Pages-Prev (if previous page exists)
- X-Pages-Prev-URI (if previous page exists)

Use the source
==============

I admit this documentation is a bit rough. Don't hesitate to read the source code, there's no
hidden rocket science, only some basic python code :)

License
=======

Django Restlayer is released under the MIT license. See the LICENSE
file for the complete license.
