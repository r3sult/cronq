# -*- coding: utf-8 -*-
import json
import logging
from uuid import UUID
import sys

from cronq.backends.mysql import Storage
from cronq.rabbit_connection import CronqConsumer
from dateutil.parser import parse

logger = logging.getLogger(__name__)


class CronqAggregator(CronqConsumer):

    def __init__(self):
        super(CronqAggregator, self).__init__()
        self.storage = Storage()

    def run_something(self, msg):
        data = json.loads(str(msg.body))

        job_id = data['job_id']
        run_id = UUID(hex=data['run_id'])

        self.log_message(job_id, run_id,
                         "Write job result to database {}".format(str(msg.body)))

        self.storage.add_event(
            job_id,
            parse(data.get('x-send-datetime')),
            run_id.hex,
            data.get('type'),
            data.get('x-host'),
            data.get('return_code'),
        )

        self.log_message(job_id, run_id, "Attempting to update status on job")

        self.storage.update_job_status(
            run_id,
            data.get('job_id'),
            parse(data.get('x-send-datetime')),
            data.get('type'),
            data.get('return_code', None))

        self.log_message(job_id, run_id, "Acking message on job")
        self.ack(msg)


def setup():
    runner = CronqAggregator()

    max_failures = 10
    while max_failures > 0:
        runner.connect()
        runner.consume(queue="cronq_results")
        max_failures -= 1

    runner.logger.warning("Too many errors, exiting")
    sys.exit(1)


def main():
    setup()

if __name__ == '__main__':
    main()
