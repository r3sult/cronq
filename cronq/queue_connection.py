# -*- coding: utf-8 -*-
import itertools
import json
import logging
import os
import random
import socket
import string
import time
import urlparse

from cronq.config import RABBITMQ_URL
from haigha.connections.rabbit_connection import RabbitConnection
from haigha.message import Message
from cronq.rabbit_connection import parse_url

logger = logging.getLogger(__name__)


def create_host_factory(hosts):
    random.shuffle(hosts)
    hosts_itr = itertools.cycle(hosts)
    return hosts_itr.next


class QueueConnection(object):

    """A wrapper around an AMQP connection for ease of publishing

    Simple instantiation:

        RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest@localhost')
        queueconnection = QueueConnection(RABBITMQ_URL)

    Publishing requires knowing the exchange, routing_key, (headers) and
    the string body:

        # We don't really use headers
        # look up AMQP stuff if you are interested
        queueconnection.publish(
            exchange='exchange',
            routing_key='routing_key',
            headers={},
            body='String Body'
        )

    Usually we want to publish JSON so there is a method that will serialize
    a dict for you:

        # We don't really use headers
        # look up AMQP stuff if you are interested
        queueconnection.publish_json(
            exchange='exchange',
            routing_key='routing_key',
            headers={},
            body={'key': 'value'}
        )

    All of these are asynchronous publishes to the server, if you want to make
    sure that these at least make it to the server you can turn on publisher
    confirmations. Sync calls take longer so they aren't on by default. Turning
    them on is done by passing `confirm=True` to the constructor.

        RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest@localhost')
        queueconnection = QueueConnection(RABBITMQ_URL, confirm=True)

    Now publishes will return a bool of whether the publish succeeded.

        # We don't really use headers
        # look up AMQP stuff if you are interested
        succeeded = queueconnection.publish(
            exchange='exchange',
            routing_key='routing_key',
            headers={},
            body='String Body'
        )

    Without `confirm=True` the return value of publish will only indicate if
    the message was written to a connection successfully.

    """

    def __init__(self, url=None, confirm=False, **kwargs):
        if url is None:
            url = RABBITMQ_URL
        hosts, user, password, vhost, port, heartbeat = parse_url(RABBITMQ_URL)

        if heartbeat is None:
            heartbeat = kwargs.get('heartbeat', None)

        self._connection_hosts = hosts
        self._connection_user = user
        self._connection_password = password
        self._connection_path = vhost
        self._connection_port = port
        self._connection_heartbeat = heartbeat
        self._connection_name = self._generate_connection_name()

        self._connection_params = urlparse.urlparse(url)
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
        self._logger.debug('Trying to connect to {}'.format(host))
        try:
            self._connection = RabbitConnection(
                host=host,
                port=self._connection_port,
                user=self._connection_user,
                password=self._connection_password,
                vhost=self._connection_path,
                close_cb=self._close_cb,
                heartbeat=self._connection_heartbeat,
                client_properties={
                    'connection_name': self._connection_name,
                },
            )
        except socket.error as exc:
            self._logger.error('Error connecting to rabbitmq {}'.format(exc))
            return False
        self._channel = self._connection.channel()
        if self._confirm:
            self._channel.confirm.select(nowait=False)
            self._channel.basic.set_ack_listener(self._ack)
        self._logger.debug('Connected to {}'.format(host))
        return True

    def _generate_connection_name(self):
        random_generator = random.SystemRandom()
        random_string = ''.join([random_generator.choice(string.ascii_lowercase)
                                 for i in xrange(10)])
        return '{0}-{1}-{2}'.format(
            socket.gethostname(),
            os.getpid(),
            random_string,
        )

    def _try_to_connect(self, attempts=3):
        """Try to connect handling retries"""
        for _ in range(attempts):
            if self.is_connected():
                return True
            else:
                self._logger.debug("attempt to create connection")
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

    def publish(self,
                exchange,
                routing_key,
                headers,
                body,
                connect_attempts=3):
        """Publish a messages to AMQP

        Returns a bool about the success of the publish. If `confirm=True` True
        means it reached the AMQP server. If `confirm=False` it means that it
        was able to be written to a connection but makes no guarantee about the
        message making it to the server.

        """
        if not self.is_connected():
            self._try_to_connect(attempts=connect_attempts)

        if self._connection is None or self._channel is None:
            self._logger.error('Tried to publish without an AMQP connection')
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
            else:
                return False

        return True

    def publish_json(self, exchange, routing_key, headers, body):
        data = json.dumps(body)
        return self.publish(exchange, routing_key, headers, data)

    def close(self):
        self._connection.close()


class Publisher(object):

    def __init__(self):
        self.queue_connection = QueueConnection(RABBITMQ_URL, confirm=True)

    def publish(self, routing_key, job, run_id):
        cmd = {
            'run_id': str(run_id),
            'job_id': job['id'],
            'cmd': job['command'],
            'name': job['name'],
        }
        logger.debug(cmd)
        return self.queue_connection.publish_json("cronq", routing_key, {}, cmd)
