# -*- coding: utf-8 -*-
import os


DATABASE_URL = os.getenv(
    'DATABASE_URL',
    os.getenv('CRONQ_MYSQL',
              'mysql+pymysql://root@localhost/cronq')).replace(
                    'mysql://', 'mysql+pymysql://')

LOG_PATH = os.getenv('LOG_PATH', '/var/log/cronq') if not os.path.exists('/var/log/cronq') else '/tmp'  # noqa
QUEUE = os.getenv('CRONQ_QUEUE', 'cronq_jobs')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
