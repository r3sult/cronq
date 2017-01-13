# -*- coding: utf-8 -*-
import datetime
import fcntl
import importlib
import json
import logging
import logging.handlers
import os
import random
import re
import socket
import subprocess
import sys
import time

from cronq.config import LOG_PATH
from cronq.config import QUEUE
from cronq.rabbit_connection import connect
from cronq.utils import unicodedammit

from haigha.message import Message

logger = logging.getLogger(__name__)

FILENAME_REGEX = re.compile('[\W_]+', re.UNICODE)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

logger.addHandler(NullHandler())


def channel_closed_cb(ch):
    message = "AMQP channel closed; close-info: {0}".format(ch.close_info)
    logger.warning(message)


def create_connection_closed_cb(connection):
    def connection_closed_cb():
        message = "AMQP broker connection closed; close-info: {0}".format(
            connection.close_info)
        logger.warning(message)
    return connection_closed_cb


def setup():
    conn = connect()
    if conn is None:
        return
    conn._close_cb = create_connection_closed_cb(conn)

    # Create message channel
    channel = conn.channel()

    channel.basic.qos(prefetch_count=1)
    runner = create_runner(channel)

    channel.basic.consume(
        queue=QUEUE,
        consumer=runner,
        no_ack=False,
    )

    while conn.close_info is None:
        conn.read_frames()

    sys.exit(1)


def make_directory(directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass


def create_runner(channel):  # noqa

    def run_something(msg):
        tag = msg.delivery_info['delivery_tag']

        make_directory(LOG_PATH)

        def ack():
            channel.basic.ack(tag)

        def reject(requeue=True):
            channel.basic.reject(tag, requeue=requeue)

        def publish_result(body):
            headers = {
                'x-send-datetime': str(datetime.datetime.utcnow()),
                'x-host': str(socket.getfqdn()),
            }
            body.update(headers)
            msg = Message(json.dumps(body))
            channel.basic.publish(msg, 'cronq', 'cronq_results')

        def valid_job(data):
            valid = True
            for key in ['cmd', 'job_id', 'run_id']:
                if not data.get(key, None):
                    logger.debug('Missing {0}'.format(key))
                    valid = False
            return valid

        data = json.loads(str(msg.body))
        if not valid_job(data):
            return reject(requeue=False)

        cmd = data.get('cmd')
        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Starting {2}'.format(
            data.get('job_id'), data.get('run_id'), cmd
        ))
        publish_result({
            'job_id': data.get('job_id'),
            'run_id': data.get('run_id'),
            'start_time': str(datetime.datetime.utcnow()),
            'type': 'starting',
        })
        start = time.time()
        process = None
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except OSError:
            logger.exception('[cronq_job_id:{0}] [cronq_run_id:{1}] Failed job'.format(
                data.get('job_id'), data.get('run_id')
            ))
            end = time.time()
            publish_result({
                'job_id': data.get('job_id'),
                'run_id': data.get('run_id'),
                'run_time': end - start,
                'type': 'failed',
            })
            return reject(requeue=False)

        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Waiting'.format(
            data.get('job_id'), data.get('run_id')
        ))

        splits = FILENAME_REGEX.split(data.get('name', 'UNKNOWN'))
        if len(splits) > 1:
            logfile = '-'.join(splits)
        filename = '{0}/{1}.log'.format(LOG_PATH, logfile.strip('-'))

        handler = logging.handlers.WatchedFileHandler(filename)
        log_to_stdout = bool(os.getenv('CRONQ_RUNNER_LOG_TO_STDOUT', False))

        while True:
            try:
                nextline = process.stdout.readline()
            except IOError:
                nextline = ''

            if nextline == '' and process.poll() is not None:
                break

            if nextline == '':
                time.sleep(0.1 * random.random())
                continue

            try:
                message = nextline.rstrip()
                message = unicodedammit(message)
            except:
                continue

            if message:
                for m in message.splitlines():
                    log_record = logging.makeLogRecord({
                        'msg': message,
                    })
                    handler.emit(log_record)
                    if log_to_stdout:
                        logger.info(u'[cronq_job_id:{0}] [cronq_run_id:{1}] {2}'.format(
                            data.get('job_id'), data.get('run_id'), log_record.getMessage()
                        ))

            time.sleep(0.00001)
            sys.stdout.flush()

        handler.close()

        end = time.time()
        publish_result({
            'job_id': data.get('job_id'),
            'run_id': data.get('run_id'),
            'return_code': process.returncode,
            'run_time': end - start,
            'type': 'finished',
        })
        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] [cronq_exit_code:{2}] Done'.format(
            data.get('job_id'), data.get('run_id'), process.returncode
        ))
        ack()

    return run_something

def main():
    setup()


if __name__ == '__main__':
    main()
