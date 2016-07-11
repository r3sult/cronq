# -*- coding: utf-8 -*-
import json
import logging
from uuid import UUID

from cronq.backends.mysql import Storage
from cronq.queue_connection import connect
from dateutil.parser import parse

logger = logging.getLogger(__name__)


def setup():
    conn = connect()
    if conn is None:
        return
    conn._close_cb = create_connection_closed_cb(conn)

    # Create message channel
    channel = conn.channel()

    channel.basic.qos(prefetch_count=1)
    runner = create_aggregator(channel)

    channel.basic.consume(
        queue='cronq_results',
        consumer=runner,
        no_ack=False,
    )

    while True:
        conn.read_frames()


def create_connection_closed_cb(connection):
    def connection_closed_cb():
        message = "AMQP broker connection closed; close-info: {0}".format(
            connection.close_info)
        logger.warning(message)
    return connection_closed_cb


def create_aggregator(channel):
    storage = Storage()

    def run_something(msg):
        tag = msg.delivery_info['delivery_tag']

        def ack():
            channel.basic.ack(tag)

        data = json.loads(str(msg.body))
        run_id = UUID(hex=data['run_id'])

        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Write job result to database: {2}'.format(
            data.get('job_id'), run_id, str(msg.body)
        ))

        storage.add_event(
            data.get('job_id'),
            parse(data.get('x-send-datetime')),
            run_id.hex,
            data.get('type'),
            data.get('x-host'),
            data.get('return_code'),
        )

        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Attempting to update status on job'.format(  # noqa
            data.get('job_id'), run_id
        ))
        storage.update_job_status(
            run_id,
            data.get('job_id'),
            parse(data.get('x-send-datetime')),
            data.get('type'),
            data.get('return_code', None))

        logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Acking message on job'.format(
            data.get('job_id'), run_id
        ))
        ack()

    return run_something


def main():
    setup()

if __name__ == '__main__':
    main()
