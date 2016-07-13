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
    def __init__(self, url=None, confirm=False):
        if url is None:
            url = RABBITMQ_URL
        hosts, user, password, vhost, port, heartbeat = parse_url(RABBITMQ_URL)
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
        random_string = ''.join([random_generator.choice(string.ascii_lowercase) for i in xrange(10)])
        return '{0}-{1}-{2}'.format(
            socket.gethostname(),
            os.getpid(),
            random_string,
        )

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
            return False
        return True

    def publish_json(self, exchange, routing_key, headers, body):
        data = json.dumps(body)
        return self.publish(exchange, routing_key, headers, data)

    def publish_delayed(self,
                        exchange,
                        routing_key,
                        headers,
                        body,
                        seconds,
                        connect_attempts=3):
        """Publish a messages to AMQP after a delay in seconds

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

        # Ensure that the delayed exchange exists
        self._channel.exchange.declare('delayed',
                                       'topic',
                                       auto_delete=False,
                                       nowait=False,
                                       durable=True)

        expire_add = 1000  # in seconds

        # Create the delayed queue
        # This queue will expire 10 seconds after the message
        expire_millis = seconds * expire_add
        delayed_queue_name, _, _ = self._channel.queue.declare(
            auto_delete=True, nowait=False, arguments={
                "x-dead-letter-exchange": exchange,
                "x-dead-letter-routing-key": routing_key,
                # Expire after message TTL + 10s
                "x-expires": expire_millis + expire_add
            }
        )

        # Bind queue to channel
        self._channel.queue.bind(exchange='delayed',
                                 routing_key=delayed_queue_name,
                                 queue=delayed_queue_name,
                                 nowait=False)

        # Publish to delayed exchange
        message = Message(body,
                          application_headers=headers,
                          expiration=str(seconds * expire_add))
        msg_number = self._channel.basic.publish(
            message,
            exchange="delayed",
            routing_key=delayed_queue_name
        )

        # Confirm publish
        if self._confirm:
            if self.is_connected():
                self._connection.read_frames()
                return self._last_confirmed_message == msg_number
            return False
        return True

    def publish_json_delayed(self,
                             exchange,
                             routing_key,
                             headers,
                             body,
                             seconds):
        data = json.dumps(body)
        return self.publish_delayed(exchange,
                                    routing_key,
                                    headers,
                                    data,
                                    seconds)

    def close(self):
        self._connection.close()


class Publisher(object):

    def __init__(self):
        self._connection = QueueConnection(RABBITMQ_URL, confirm=True)

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
    hosts, user, password, vhost, port, heartbeat = parse_url(RABBITMQ_URL)

    logger.info('Hosts are: {0}'.format(hosts))
    rabbit_logger = logging.getLogger('amqp-dispatcher.haigha')

    random_generator = random.SystemRandom()
    random_string = ''.join([random_generator.choice(string.ascii_lowercase) for i in xrange(10)])
    connection_name = '{0}-{1}-{2}'.format(
        socket.gethostname(),
        os.getpid(),
        random_string,
    )

    conn = connect_to_hosts(
        RabbitConnection,
        hosts,
        port=port,
        user=user,
        password=password,
        vhost=vhost,
        heartbeat=heartbeat,
        logger=rabbit_logger,
        client_properties={
            'connection_name': connection_name
        }
    )
    return conn


def generate_random_string(length):
    """generates  a random alphanumeric string of length `strlen`"""
    random_generator = random.SystemRandom()
    return ''.join([random_generator.choice(string.ascii_lowercase) for i in xrange(length)])


def connect_to_hosts(connector, hosts, **kwargs):
    for host in hosts:
        logger.info('Trying to connect to host: {0}'.format(host))
        try:
            conn = connector(host=host, **kwargs)
            return conn
        except socket.error:
            logger.info('Error connecting to {0}'.format(host))
    logger.error('Could not connect to any hosts')


def parse_url(rabbitmq_url):
    """returns tuple containing
    HOSTS, USER, PASSWORD, VHOST
    """
    hosts = user = password = vhost = None
    port = 5672

    cp = urlparse.urlparse(rabbitmq_url)
    hosts_string = cp.hostname
    hosts = hosts_string.split(",")
    if cp.port:
        port = int(cp.port)
    user = cp.username
    password = cp.password
    vhost = cp.path
    query = cp.query

    port = 5672
    if cp.port:
        port = cp.port

    # workaround for bug in 12.04
    if '?' in vhost and query == '':
        vhost, query = vhost.split('?', 1)

    heartbeat = parse_heartbeat(query)
    return (hosts, user, password, vhost, port, heartbeat)


def parse_heartbeat(query):
    logger = logging.getLogger('amqp-dispatcher')

    default_heartbeat = None
    heartbeat = default_heartbeat
    if query:
        qs = urlparse.parse_qs(query)
        heartbeat = qs.get('heartbeat', default_heartbeat)
    else:
        logger.debug('No heartbeat specified, using broker defaults')

    if isinstance(heartbeat, (list, tuple)):
        if len(heartbeat) == 0:
            logger.warning('No heartbeat value set, using default')
            heartbeat = default_heartbeat
        elif len(heartbeat) == 1:
            heartbeat = heartbeat[0]
        else:
            logger.warning('Multiple heartbeat values set, using broker default: {0}'.format(
                heartbeat
            ))
            heartbeat = default_heartbeat

    if type(heartbeat) == str and heartbeat.lower() == 'none':
        return None

    if heartbeat is None:
        return heartbeat

    try:
        heartbeat = int(heartbeat)
    except ValueError:
        logger.warning('Unable to cast heartbeat to int, using broker default: {0}'.format(
            heartbeat
        ))
        heartbeat = default_heartbeat

    return heartbeat
