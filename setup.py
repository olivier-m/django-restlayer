# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from __future__ import (print_function, division, absolute_import, unicode_literals)

from setuptools import setup

with open('restlayer/version.py') as fp:
    g = {}
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='django-restlayer',
    version=version,
    description='HTTP Toolkit',
    author='Olivier Meunier',
    author_email='olivier@neokraft.net',
    url='https://github.com/olivier-m/django-restlayer',
    license='MIT License',
    install_requires=[
        'django >= 1.5, < 1.7',
        'python-mimeparse >= 0.1.4',
    ],
    packages=['restlayer'],
    test_suite='tests.runtests',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
