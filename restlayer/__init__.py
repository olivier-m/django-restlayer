# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from distutils.version import LooseVersion
import django

if LooseVersion(django.get_version()) < LooseVersion('1.5'):
    raise ImportError('Minimal Django version for django-restlayer is 1.5')

from .api import (
    HttpException, Http406, FormValidationError,
    Response, Resource
)
from .models import ModelResponse

from .version import __version__
