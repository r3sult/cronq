#!/usr/bin/env python
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def run_setup():
    setup(
        name='cronq',
        version='0.0.30',
        description='A Cron-like system for running tasks',
        keywords = 'cron amqp',
        url='http://github.com/philipcristiano/cronq',
        author='Philip Cristiano',
        author_email='philipcristiano@gmail.com',
        license='BSD',
        packages=['cronq', 'cronq.backends'],
        install_requires=[
            'aniso8601==0.82',
            'flask',
            'haigha',
            'sqlalchemy',
            'mysql-connector-python',
            'python-dateutil',
            'haigha==0.7.0',
        ],
        test_suite='tests',
        long_description=read('README.md'),
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
