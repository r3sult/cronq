# -*- coding: utf-8 -*-
import os
import random


if os.getenv('RABBITMQ_HOSTS', None) is not None:
    hosts = os.getenv('RABBITMQ_HOSTS', None).split(',')
    random.shuffle(hosts)
else:
    hosts = [os.getenv('RABBITMQ_HOST', 'localhost')]

DATABASE_URL = os.getenv(
    'CRONQ_MYSQL',
    'mysql+mysqlconnector://root@localhost/cronq')
LOG_PATH = os.getenv('LOG_PATH', '/var/log/cronq')
QUEUE = os.getenv('CRONQ_QUEUE', 'cronq_jobs')
RABBITMQ_HOSTS = hosts
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
