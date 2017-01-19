import json
import os
import time

from haigha.connections.rabbit_connection import RabbitConnection
from haigha.message import Message

connection = Connection(
    user=os.getenv('RABBITMQ_USER'),
    password=os.getenv('RABBITMQ_PASS'),
    vhost='/',
    host=os.getenv('RABBITMQ_HOSTS', 'localhost').split(',')[0],
    heartbeat=None,
    debug=True)

ch = connection.channel()
ch.exchange.declare('cronq', 'direct')
ch.queue.declare('cronq_jobs', auto_delete=False)
ch.queue.declare('cronq_results', auto_delete=False)
ch.queue.bind('cronq_jobs', 'cronq', 'cronq_jobs')
ch.queue.bind('cronq_results', 'cronq', 'cronq_results')

while True:
    print 'publish'
    cmd = {
        "cmd": "sleep 1",
        "job_id": 1024,
        "name": "[TEST] A test job",
        "run_id": "1234"
    }
    ch.basic.publish(
        Message(json.dumps(cmd), application_headers={
            'src': 'test'
        }),
        exchange='cronq',
        routing_key='test'
    )
    time.sleep(1)
