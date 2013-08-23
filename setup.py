# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.

from setuptools import setup, find_packages

execfile('restlayer/version.py')
packages = find_packages(exclude=['*.tests'])

setup(
    name='django-restlayer',
    version=__version__,
    description='HTTP Toolkit',
    author='Olivier Meunier',
    author_email='olivier@neokraft.net',
    url='https://github.com/olivier-m/django-restlayer',
    license='MIT License',
    packages=packages,
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
