# -*- coding: utf-8 -*-
import os
import random


if os.getenv('RABBITMQ_HOSTS', None) is not None:
    hosts = os.getenv('RABBITMQ_HOSTS', None).split(',')
    random.shuffle(hosts)
else:
    hosts = [os.getenv('RABBITMQ_HOST', 'localhost')]

default_log_path = '/var/log/cronq'
if not os.path.exists('/var/log/cronq'):
    default_log_path = '/tmp'

DATABASE_URL = os.getenv(
    'CRONQ_MYSQL',
    'mysql+mysqlconnector://root@localhost/cronq')
LOG_PATH = os.getenv('LOG_PATH', default_log_path)
QUEUE = os.getenv('CRONQ_QUEUE', 'cronq_jobs')
RABBITMQ_HOSTS = hosts
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

default_rabbitmq_url = 'amqp://{0}:{1}@{2}/'.format(
    RABBITMQ_USER,
    RABBITMQ_PASS,
    ','.join(RABBITMQ_HOSTS)
)

RABBITMQ_URL = os.getenv('RABBITMQ_URL', default_rabbitmq_url)
