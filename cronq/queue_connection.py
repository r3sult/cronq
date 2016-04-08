# -*- coding: utf-8 -*-
import json
import logging
import socket

from cronq.config import RABBITMQ_HOSTS
from cronq.config import RABBITMQ_PASS
from cronq.config import RABBITMQ_USER

from haigha.connections import RabbitConnection
from haigha.message import Message

logger = logging.getLogger(__name__)


class Publisher(object):

    def __init__(self):
        self._connection = connect()
        self._channel = self._connection.channel()

    def publish(self, routing_key, job, run_id):
        cmd = {
            'run_id': str(run_id),
            'job_id': job['id'],
            'cmd': job['command'],
            'name': job['name'],
        }
        logger.debug(cmd)

        def _publish_callback():
            logger.info('[cronq_job_id:{0}] Job published {1}'.format(job['id'], job['name']))

        self._publish(routing_key, cmd, _publish_callback)

    def _publish(self, routing_key, body, cb):
        msg = Message(json.dumps(body), {})
        self._channel.basic.publish_synchronous(msg, 'cronq', routing_key, cb=cb)


def connect():
    logger.info('Hosts are: {0}'.format(RABBITMQ_HOSTS))
    rabbit_logger = logging.getLogger('amqp-dispatcher.haigha')
    conn = connect_to_hosts(
        RabbitConnection,
        RABBITMQ_HOSTS,
        user=RABBITMQ_USER,
        password=RABBITMQ_PASS,
        logger=rabbit_logger,
        heartbeat=43200,
    )
    return conn


def connect_to_hosts(connector, hosts, **kwargs):
    for host in hosts:
        logger.info('Trying to connect to host: {0}'.format(host))
        try:
            conn = connector(host=host, **kwargs)
            return conn
        except socket.error:
            logger.info('Error connecting to {0}'.format(host))
    logger.error('Could not connect to any hosts')
