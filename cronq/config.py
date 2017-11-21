# -*- coding: utf-8 -*-
import os

from cronq.utils import to_bool


class Config(object):
    BUGSNAG_API_KEY = os.getenv('BUGSNAG_API_KEY')
    CRONQ_QUEUE = os.getenv('CRONQ_QUEUE', 'cronq_jobs')
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        os.getenv('CRONQ_MYSQL',
                  'mysql+pymysql://root@localhost/cronq')).replace(
                        'mysql://', 'mysql+pymysql://')
    DEBUG = to_bool(os.getenv('DEBUG', 0))
    LISTEN_INTERFACE = os.getenv('LISTEN_INTERFACE', '0.0.0.0')
    LOG_PATH = os.getenv('LOG_PATH', '/var/log/cronq') if not os.path.exists('/var/log/cronq') else '/tmp'  # noqa
    PORT = int(os.getenv('PORT', 5000))
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
    SECRET_KEY = os.getenv('SECRET_KEY', 'development key')
    SENTRY_DSN = os.getenv('SENTRY_DSN')
