import time
import json

from haigha.connection import Connection
from haigha.message import Message
from uuid import uuid4

connection = Connection(
    user='guest',
    password='guest',
    vhost='/',
    host='rabbit-host',
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
        'job_id': str(uuid4()),
        'cmd': 'sleep 1'
    }
    ch.basic.publish(Message(json.dumps(cmd), application_headers={
        'src': 'test'
    }), 'cronq', 'cronq')
    time.sleep(1)
