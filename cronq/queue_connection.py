# -*- coding: utf-8 -*-
import json
import logging
import socket

from cronq.config import RABBITMQ_HOSTS
from cronq.config import RABBITMQ_PASS
from cronq.config import RABBITMQ_USER

logger = logging.getLogger(__name__)

import itertools
import random
import time
import urlparse

from haigha.connections.rabbit_connection import RabbitConnection
from haigha.message import Message

def create_host_factory(hosts):
    random.shuffle(hosts)
    hosts_itr = itertools.cycle(hosts)
    return hosts_itr.next

class QueueConnection(object):
    """A wrapper around an AMQP connection for ease of publishing

    Simple instantiation:

        queueconnection = QueueConnection(os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost'))

    Publishing requires konwing the exchange, routing_key, (headers) and the string body

        queueconnection.publish(
            exchange='exchange',
            routing_key='routing_key',
            headers={}, # We don't really use these, look up AMQP stuff if you are interested
            body='String Body'
        )

    Usually we want to publish JSON so there is a method that will serialize a dict for you

        queueconnection.publish_json(
            exchange='exchange',
            routing_key='routing_key',
            headers={}, # We don't really use these, look up AMQP stuff if you are interested
            body={'key': 'value'}
        )

    All of these are asynchronous publishes to the server, if you want to make sure that
    these at least make it to the server you can turn on publisher confirmations. Sync
    calls take longer so they aren't on by default. Turning them on is done by passing
    `confirm=True` to the constructor.

        queueconnection = QueueConnection(os.getenv('RABBITMQHOST', 'localhost'), confirm=True)

    Now publishes will return a bool of whether the publish succeeded.

        succeeded = queueconnection.publish(
            exchange='exchange',
            routing_key='routing_key',
            headers={}, # We don't really use these, look up AMQP stuff if you are interested
            body='String Body'
        )

    Without `confirm=True` the return value of publish will only indicate if the message
    was written to a connection successfully.

    """
    def __init__(self, url=None, confirm=False):

        if url is not None:
            _connection_params = urlparse.urlparse(url)
            # workaround for bug in 12.04
            self._connection_path = _connection_params.path
            self._connection_query = _connection_params.query
            if '?' in self._connection_path and self._connection_query == '':
                self._connection_path, self._connection_query = self._connection_path.split('?', 1)

            self._connection_hosts = _connection_params.hostname.split(',')
            self._connection_user=_connection_params.username
            self._connection_password=_connection_params.password

        else:
            self._connection_hosts = RABBITMQ_HOSTS
            self._connection_user = RABBITMQ_USER
            self._connection_password = RABBITMQ_PASS
            self._connection_path = "/"

        self._connect_attempt_delay = 0.1

        self._get_next_host = create_host_factory(self._connection_hosts)

        self._confirm = confirm
        self._logger = logger

        self._create_connection()

        self._acked = False
        self._last_confirmed_message = None

    def _create_connection(self):
        "Tries to create a connection, returns True on success"
        self._connection = None
        self._last_confirmed_message = None
        host = self._get_next_host()
        self._logger.info('Trying to connect to {}'.format(host))
        try:
            self._connection = RabbitConnection(
                host=host,
                user=self._connection_user,
                password=self._connection_password,
                vhost=self._connection_path,
                close_cb=self._close_cb,
            )
        except socket.error as exc:
            self._logger.info('Error connecting {}'.format(exc))
            return False
        self._channel = self._connection.channel()
        if self._confirm:
            self._channel.confirm.select(nowait=False)
            self._channel.basic.set_ack_listener(self._ack)
        self._logger.info('Connected to {}'.format(host))
        return True

    def _try_to_connect(self, attempts=3):
        """Try to connect handling retries"""
        for _ in range(attempts):
            if self.is_connected():
                return
            else:
                self._create_connection()
                time.sleep(self._connect_attempt_delay)

    def _ack(self, message_id):
        self._last_confirmed_message = message_id

    def is_connected(self):
        if self._connection is None or self._channel is None:
            return False
        return True

    def _close_cb(self):
        if self._connection is None:
            reason = 'unknown'
        else:
            reason = self._connection.close_info['reply_text']
        self._logger.info('Disconnected because: {}'.format(reason))
        self._connection = None
        self._channel = None

    def publish(self, exchange, routing_key, headers, body, connect_attempts=3):
        """Publish a messages to AMQP

        Returns a bool about the success of the publish. If `confirm=True` True
        means it reached the AMQP server. If `confirm=False` it means that it
        was able to be written to a connection but makes no guarantee about the
        message making it to the server.

        """
        if not self.is_connected():
            self._try_to_connect(attempts=connect_attempts)

        if self._connection is None or self._channel is None:
            self._logger.info('Tried to publish without an AMQP connection')
            return False
        msg_number = self._channel.basic.publish(
            Message(body, application_headers=headers),
            exchange=exchange,
            routing_key=routing_key
        )
        if self._confirm:
            if self.is_connected():
                self._connection.read_frames()
                return self._last_confirmed_message == msg_number
            return False
        else:
            return True

    def publish_json(self, exchange, routing_key, headers, body):
        data = json.dumps(body)
        return self.publish(exchange, routing_key, headers, data)

    def close(self):
        self._connection.close()

class Publisher(object):

    def __init__(self):
        self._connection = QueueConnection(confirm=True)

    def publish(self, routing_key, job, run_id):
        cmd = {
            'run_id': str(run_id),
            'job_id': job['id'],
            'cmd': job['command'],
            'name': job['name'],
        }
        logger.debug(cmd)
        return self._connection.publish_json("cronq", routing_key, {}, cmd)

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
