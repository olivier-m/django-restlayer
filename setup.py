# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

from setuptools import setup

with open('restlayer/version.py') as fp:
    g = {}
    exec(fp.read(), g)
    version = g['__version__']

def readme():
    with open('README.rst', 'r') as fp:
        return fp.read()

setup(
    name='django-restlayer',
    version=version,
    description='HTTP REST toolkit for Django',
    long_description=readme(),
    author='Olivier Meunier',
    author_email='olivier@neokraft.net',
    url='https://github.com/olivier-m/django-restlayer',
    license='MIT License',
    install_requires=[
        'django >= 1.4, < 1.7',
        'mimeparse',
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
