import json
import logging
import os
import random
import socket

from haigha.connection import Connection as haigha_Connection
from haigha.connections import RabbitConnection
from haigha.message import Message

logger = logging.getLogger('cronq')

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
        print cmd
        self._publish(routing_key, cmd)

    def _publish(self, routing_key, body):
        msg = Message(json.dumps(body), {})
        self._channel.basic.publish(msg, 'cronq', routing_key)


def connect():
    hosts_string = os.getenv('RABBITMQ_HOSTS', None)
    if hosts_string is not None:
        hosts = hosts_string.split(',')
        logger.info('Hosts are: {0}'.format(hosts))
        random.shuffle(hosts)
    else:
        hosts = [os.getenv('RABBITMQ_HOST', 'localhost')]
    user = os.getenv('RABBITMQ_USER', 'guest')
    password = os.getenv('RABBITMQ_PASS', 'guest')
    rabbit_logger = logging.getLogger('amqp-dispatcher.haigha')
    conn = connect_to_hosts(
        RabbitConnection,
        hosts,
        user=user,
        password=password,
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
