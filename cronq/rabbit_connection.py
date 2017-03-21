# -*- coding: utf-8 -*-
import logging
import os
import random
import socket
import string
import time
import urlparse

from cronq.config import RABBITMQ_URL

from haigha.connections.rabbit_connection import RabbitConnection

# cronq jobs can be very long, override heartbeat settings
# to keep rabbitmq connections alive (or there might be problems)
CONSUMER_HEARTBEAT = 50000


class NullHandler(logging.Handler):

    def emit(self, record):
        pass

logger = logging.getLogger(__name__)


def generate_random_string(length):
    """generates  a random alphanumeric string of length `strlen`"""
    random_generator = random.SystemRandom()
    return ''.join([random_generator.choice(string.ascii_lowercase) for i in xrange(length)])


def parse_heartbeat(query):
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


def plain_rabbit_connection_to_hosts(hosts, **kwargs):
    for host in hosts:
        logger.info('Trying to connect to host: {0}'.format(host))
        try:
            conn = RabbitConnection(host=host, **kwargs)
            logger.info("...success")
            return conn
        except socket.error:
            logger.info('Error connecting to {0}'.format(host))
    logger.error('Could not connect to any hosts')


def connect(**kwargs):
    hosts, user, password, vhost, port, heartbeat = parse_url(RABBITMQ_URL)

    logger.info('Hosts are: {0}'.format(hosts))
    rabbit_logger = logging.getLogger('dispatcher.haigha')

    random_string = generate_random_string(10)

    connection_name = '{0}-{1}-{2}'.format(
        socket.gethostname(),
        os.getpid(),
        random_string,
    )

    heartbeat = heartbeat or None

    # override connection string sometimes
    if kwargs.get('heartbeat'):
        heartbeat = kwargs.get('heartbeat')

    close_cb = kwargs.get('close_cb')

    conn = plain_rabbit_connection_to_hosts(
        hosts,
        port=port,
        user=user,
        password=password,
        vhost=vhost,
        heartbeat=heartbeat,
        logger=rabbit_logger,
        close_cb=close_cb,
        client_properties={
            'connection_name': connection_name
        }
    )

    return conn


class CronqConsumer(object):

    """handles reconnects"""

    def __init__(self):
        self._connection = None
        self._channel = None

        # logging
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(NullHandler())

    def _create_connection(self):
        self._connection = connect(
            close_cb=self._connection_closed_cb,
            heartbeat=CONSUMER_HEARTBEAT)
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

    def publish(self, msg, exchange, routing_key):
        self.channel.basic.publish(msg, exchange, routing_key)

    def log_message(self, job_id, run_id, message, lvl=logging.INFO):
        msg = "[cronq_job_id:{0}] [cronq_run_id:{1}] {2}".format(
            job_id,
            run_id,
            message
        )
        self.logger.log(lvl, msg)

    def run_something(self, msg):
        raise NotImplementedError()

    def consume(self, queue):
        self.make_connected()

        def runner(msg):
            return self.run_something(msg)

        self.channel.basic.qos(prefetch_count=1)
        self.channel.basic.consume(
            queue=queue,
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
