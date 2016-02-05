# -*- coding: utf-8 -*-
import datetime
import logging
import os


def setup_logging():
    if os.getenv('LOGGING_FILE_CONFIG'):
        logging.config.fileConfig(os.getenv('LOGGING_FILE_CONFIG'))
    else:
        logformat = "[%(asctime)s] %(name)s [pid:%(process)d] - %(levelname)s - %(message)s"  # noqa
        datefmt = "%Y-%m-%d %H:%M:%S"
        levels = [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
            logging.NOTSET,
        ]
        for level in levels:
            logging.basicConfig(level=level,
                                format=logformat,
                                datefmt=datefmt)


def split_command(string):
    commands = string.strip().split(';')
    ret = []
    for command in commands:
        ret.extend(command.strip().split(' && '))
    return ret


def task_status(first, last=None):
    if last is None:
        return first['status']

    if last['status'] == 'finished':
        if int(last['return_code']) == 0:
            return 'succeeded'
        return 'failed'
    return last['status']


def took(first_time, last_time):
    if type(first_time) is not datetime.datetime:
        return ""

    if type(last_time) is not datetime.datetime:
        return ""

    elapsed_time = last_time - first_time
    return int(elapsed_time.total_seconds())
