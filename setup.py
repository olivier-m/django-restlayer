# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

from setuptools import setup, find_packages

version = '0.8'
packages = ['restlayer'] + ['restlayer.%s' % x for x in find_packages('restlayer',)]

setup(
    name='restlayer',
    version=version,
    description='HTTP Toolkit',
    author='Olivier Meunier',
    author_email='olivier@neokraft.net',
    url='https://github.com/olivier-m/django-restlayer',
    packages=packages,
    classifiers=[
        'Development Status :: %s' % version,
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
