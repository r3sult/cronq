import unittest

from cronq import rabbit_connection

class TestGenerateRandomString(unittest.TestCase):

    def test_string_length(self):
        s = rabbit_connection.generate_random_string(5)
        self.assertEqual(5, len(s))

        s = rabbit_connection.generate_random_string(8)
        self.assertEqual(8, len(s))



class TestParseHeartbeat(unittest.TestCase):

    def test_heartbeat_from_rabbitmq_url(self):
        url = "amqp://foo:bar@localhost?heartbeat=100"
        vals = rabbit_connection.parse_url(url)
        self.assertEqual(100, vals[5])

    def test_heartbeat_from_rabbitmq_url(self):
        url = "amqp://foo:bar@localhost"
        vals = rabbit_connection.parse_url(url)
        self.assertIsNone(vals[5])

    def test_basic(self):
        query = "heartbeat=100"
        self.assertEqual(100, rabbit_connection.parse_heartbeat(query))

class TestParseUrl(unittest.TestCase):

    def test_full_url(self):
        url = "amqp://foo:bar@localhost:15672/?heartbeat=100"
        vals = rabbit_connection.parse_url(url)
        self.assertEqual(vals[0], ["localhost"])
        self.assertEqual(vals[1], "foo")
        self.assertEqual(vals[2], "bar")
        self.assertEqual(vals[3], "/")
        self.assertEqual(vals[4], 15672)
        self.assertEqual(vals[5], 100)

    def test_missing_stuff_url(self):
        url = "amqp://foo:bar@localhost:15672?heartbeat=100"
        vals = rabbit_connection.parse_url(url)
        self.assertEqual(vals[0], ["localhost"])
        self.assertEqual(vals[1], "foo")
        self.assertEqual(vals[2], "bar")
        self.assertEqual(vals[3], '')
        self.assertEqual(vals[4], 15672)
        self.assertEqual(vals[5], 100)

        # default port
        url = "amqp://foo:bar@localhost?heartbeat=100"
        vals = rabbit_connection.parse_url(url)
        self.assertEqual(vals[4], 5672)

        # no heartbeat
        url = "amqp://foo:bar@localhost"
        vals = rabbit_connection.parse_url(url)
        self.assertEqual(vals[5], None)
