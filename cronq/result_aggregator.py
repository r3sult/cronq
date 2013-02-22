import json
from uuid import UUID

from dateutil.parser import parse

from backends.mysql import Storage
from queue_connection import connect


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
        print "AMQP broker connection closed; close-info: %s" % (
          connection.close_info,)
        connection = None
    return connection_closed_cb

def create_aggregator(channel):
    storage = Storage()

    def run_something(msg):
        tag = msg.delivery_info['delivery_tag']
        def ack():
            channel.basic.ack(tag)

        data = json.loads(str(msg.body))
        run_id = UUID(hex=data['run_id'])
        print 'id', run_id
        print data
        storage.add_event(
            data.get('job_id'),
            parse(data.get('x-send-datetime')),
            run_id.hex,
            data.get('type'),
            data.get('x-host'),
            data.get('return_code'),
        )

        ack()

    return run_something

def main():
    setup()

if __name__ == '__main__':
    main()
