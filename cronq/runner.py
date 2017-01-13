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


FILENAME_REGEX = re.compile('[\W_]+', re.UNICODE)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class CronqRunner(object):
    """handles reconnects"""

    def __init__(self):
        self._connection = None
        self._channel = None

        # logging
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(NullHandler())

    def _create_connection(self):
        self._connection = connect(close_cb=self._connection_closed_cb)
        self._channel = self._connection.channel()

    def connect(self):
        return self._create_connection()

    @property
    def connection(self):
        if self._connection:
            return self._connection

    @property
    def channel(self):
        if self._channel:
            return self._channel

    def is_connected(self):
        return self.connection and self.channel

    def make_connected(self, attempts=3):
        for _ in range(attempts):
            if self.is_connected():
                return True
            else:
                self.logger.debug("attempt to create connection")
                self._create_connection()
                time.sleep(.1)
        return False

    @staticmethod
    def tag_from_msg(msg):
        tag = msg.delivery_info['delivery_tag']
        return tag

    def ack(self, msg):
        tag = self.tag_from_msg(msg)
        if self.is_connected():
            self.channel.basic.ack(tag)

    def reject(self, msg, requeue=True):
        tag = self.tag_from_msg(msg)
        if self.is_connected():
            self.channel.basic.reject(tag, requeue=requeue)

    def publish_result(self, body):
        headers = {
            'x-send-datetime': str(datetime.datetime.utcnow()),
            'x-host': str(socket.getfqdn()),
        }
        body.update(headers)
        msg = Message(json.dumps(body))
        self.channel.basic.publish(msg, 'cronq', 'cronq_results')

    def valid_job(self, data):
        valid = True
        for key in ['cmd', 'job_id', 'run_id']:
            if not data.get(key, None):
                self.logger.debug('Missing {0}'.format(key))
                valid = False
        return valid

    def log_message(self, job_id, run_id, message, lvl=logging.INFO):
        msg = "[cronq_job_id:{0}] [cronq_run_id]:{1} {2}".format(
            job_id,
            run_id,
            message
        )
        self.logger.log(lvl, msg)

    def run_job(self, data):
        start = time.time()
        process = None

        cmd = data.get('cmd')
        job_id = data.get('job_id')
        run_id = data.get('run_id')

        self.log_message(job_id, run_id, "Starting {}".format(cmd))

        # communicate start
        self.publish_result({
            'job_id': data.get('job_id'),
            'run_id': data.get('run_id'),
            'start_time': str(datetime.datetime.utcnow()),
            'type': 'starting',
        })

        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except OSError:
            # log exception with stack trace
            self.logger.exception('[cronq_job_id:{0}] [cronq_run_id:{1}] Failed job'.format(
                data.get('job_id'), data.get('run_id')
            ))
            end = time.time()

            # communicate failure
            self.publish_result({
                'job_id': job_id,
                'run_id': run_id,
                'run_time': end - start,
                'type': 'failed',
            })

            return False

        # process job output
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Waiting'.format(
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
            except TypeError,ValueError:
                continue

            if message:
                for m in message.splitlines():
                    log_record = logging.makeLogRecord({
                        'msg': message,
                    })
                    handler.emit(log_record)
                    if log_to_stdout:
                        self.log_message(job_id, run_id, log_record.getMessage())

            time.sleep(0.00001)
            sys.stdout.flush()

        handler.close()

        # communicate finished
        end = time.time()
        self.publish_result({
            'job_id': job_id,
            'run_id': run_id,
            'return_code': process.returncode,
            'run_time': end - start,
            'type': 'finished',
        })

        self.log_message(job_id, run_id, "[cronq_exit_code:{}] Done".format(process.returncode))
        return True

    def run_something(self, msg):
        tag = msg.delivery_info['delivery_tag']
        channel = self.channel
        make_directory(LOG_PATH)

        data = json.loads(str(msg.body))
        if not self.valid_job(data):
            return self.reject(requeue=False)

        try:
            success = self.run_job(data)
        except KeyboardInterrupt:
            raise
        except:
            self.logger.exception("unhandled exception in job")
            success = False

        if not success:
            return self.reject(msg, requeue=False)
        else:
            return self.ack(msg)

    def consume(self):
        self.make_connected()

        def runner(msg):
            return self.run_something(msg)

        self.channel.basic.qos(prefetch_count=1)
        self.channel.basic.consume(
            queue=QUEUE,
            consumer=runner,
            no_ack=False
        )

        while self.is_connected():
            self.connection.read_frames()

        return False

    def _connection_closed_cb(self):
        if self._connection is None:
            reason = 'unknown'
        else:
            reason = self._connection.close_info['reply_text']
        self.logger.info('Disconnected because: {}'.format(reason))
        self._connection = None
        self._channel = None

def setup():
    runner = CronqRunner()

    max_failures = 10
    while max_failures > 0:
        runner.connect()

        try:
            broken = runner.consume()
        except KeyboardInterrupt:
            raise

        max_failures -= 1

    sys.exit(1)


def make_directory(directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass

def main():
    setup()


if __name__ == '__main__':
    main()
