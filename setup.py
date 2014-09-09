#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013 SeatGeek

# This file is part of cronq.

from cronq import __version__
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def open_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


def run_setup():
    setup(
        name='cronq',
        version=__version__,
        description='A Cron-like system for running tasks',
        keywords='cron amqp',
        url='http://github.com/seatgeek/cronq',
        author='SeatGeek',
        author_email='opensource@seatgeek.com',
        license='BSD',
        packages=['cronq', 'cronq.backends', 'cronq.models'],
        install_requires=[
            'Flask==0.10.1',
            'Jinja2==2.7.3',
            'MarkupSafe==0.23',
            'SQLAlchemy==0.9.7',
            'Werkzeug==0.9.6',
            'aniso8601==0.82',
            'argparse==1.2.1',
            'gevent==1.0.1',
            'greenlet==0.4.3',
            'gunicorn==19.1.1',
            'haigha==0.7.0',
            'itsdangerous==0.24',
            'mysql-connector-python==1.2.3',
            'python-dateutil==2.2',
            'six==1.7.3',
            'wsgiref==0.1.2',
        ],
        test_suite='tests',
        long_description=open_file('README.rst').read(),
        include_package_data=True,
        zip_safe=True,
        classifiers=[
        ],
        entry_points="""
        [console_scripts]
           cronq-runner=cronq.runner:main
           cronq-injector=cronq.injector:main
           cronq-results=cronq.result_aggregator:main
        """,
    )

if __name__ == '__main__':
    run_setup()
