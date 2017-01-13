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

logger = logging.getLogger(__name__)

def generate_random_string(length):
    """generates  a random alphanumeric string of length `strlen`"""
    random_generator = random.SystemRandom()
    return ''.join([random_generator.choice(string.ascii_lowercase) for i in xrange(length)])


def parse_heartbeat(query):
    print query
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
            return conn
        except socket.error:
            logger.info('Error connecting to {0}'.format(host))
    logger.error('Could not connect to any hosts')


def connect():
    hosts, user, password, vhost, port, heartbeat = parse_url(RABBITMQ_URL)

    logger.info('Hosts are: {0}'.format(hosts))
    rabbit_logger = logging.getLogger('dispatcher.haigha')

    random_string = generate_random_string(10)

    connection_name = '{0}-{1}-{2}'.format(
        socket.gethostname(),
        os.getpid(),
        random_string,
    )

    heartbeat = heartbeat or 1

    conn = plain_rabbit_connection_to_hosts(
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
