# -*- coding: utf-8 -*-
import datetime
import fcntl
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
from cronq.rabbit_connection import CronqConsumer
from cronq.utils import unicodedammit

from haigha.message import Message

FILENAME_REGEX = re.compile('[\W_]+', re.UNICODE)


class CronqRunner(CronqConsumer):

    """handles reconnects"""

    def publish_result(self, body):
        headers = {
            'x-send-datetime': str(datetime.datetime.utcnow()),
            'x-host': str(socket.getfqdn()),
        }
        body.update(headers)
        msg = Message(json.dumps(body))
        self.publish(msg, 'cronq', 'cronq_results')

    def valid_job(self, data):
        valid = True
        for key in ['cmd', 'job_id', 'run_id']:
            if not data.get(key, None):
                self.logger.debug('Missing {0}'.format(key))
                valid = False
        return valid

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

        self.log_message(job_id, run_id, "Waiting")

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
            except (TypeError, ValueError):
                continue

            if message:
                for m in message.splitlines():
                    log_record = logging.makeLogRecord({
                        'msg': message,
                    })
                    handler.emit(log_record)
                    if log_to_stdout:
                        self.log_message(
                            job_id, run_id, log_record.getMessage())

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
            self.logger.warning("rejecting message")
            return self.reject(msg, requeue=False)
        else:
            self.logger.info("acking message")
            return self.ack(msg)


def setup():
    runner = CronqRunner()

    max_failures = 1000
    while max_failures > 0:
        runner.connect()
        runner.consume(queue=QUEUE)
        max_failures -= 1

    runner.logger.warning("Too many errors, exiting")
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
