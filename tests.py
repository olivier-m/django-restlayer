# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

import sys
import warnings

warnings.simplefilter('always')

from django.conf import settings

try:
    from django.utils.functional import empty
except ImportError:
    empty = None


APPS = (
    'restlayer',
)


def setup_test_environment():
    # reset settings
    settings._wrapped = empty

    settings_dict = {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            },
        },
        'INSTALLED_APPS': APPS,
        'MIDDLEWARE_CLASSES': (
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ),
        'ROOT_URLCONF': '',
    }

    settings.configure(**settings_dict)


def runtests():
    setup_test_environment()

    try:
        from django.test.runner import DiscoverRunner as TestRunner
        test_args = ['restlayer.tests']
    except ImportError:  # Django < 1.6
        from django.test.simple import DjangoTestSuiteRunner as TestRunner
        test_args = ['restlayer']

    runner = TestRunner(verbosity=1, interactive=True, failfast=False)
    failures = runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    runtests()
