#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='kfchess_server',
    version='0.0.1',
    license='BSD 2-Clause License',
    description='A kung fu chess server implementation',
    author='Yuval Wyborski',
    author_email='yvw.bor@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    keywords=[
        'chess', 'server', 'kung-fu-chess' # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    install_requires=[
        'attrs==17.4.0',
        'click==6.7',
        'enum34==1.1.6',
        'eventlet==0.22.0',
        'Flask==0.12.2',
        'Flask-SocketIO==2.9.3',
        'greenlet==0.4.12',
        'gunicorn==19.7.1',
        'itsdangerous==0.24',
        'Jinja2==2.10',
        'MarkupSafe==1.0',
        'pluggy==0.6.0',
        'py==1.5.2',
        'pytest==3.3.2',
        'python-engineio==2.0.2',
        'python-socketio==1.8.4',
        'six==1.11.0',
        'Werkzeug==0.14.1'
        # eg: 'aspectlib==1.1.1', 'six>=1.7',
    ],
    extras_require={
        # eg:
        #   'rst': ['docutils>=0.11'],
        #   ':python_version=="2.6"': ['argparse'],
    }
)