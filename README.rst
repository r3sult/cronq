=====
CronQ
=====

A cron-like system to run your application tasks across any node, instead of one special snowflake. This is done by keeping your tasks in MySQL and publishing them over AMQP to workers that will run your tasks and eventually save the results back into the DB. This was started as a hackathon project at SeatGeek_

Requirements
============

- Python 2.7
- RabbitMQ 3.x
- MySQL 5.x

Installation
============

Using PIP via PyPi::

    pip install cronq

Using PIP via Github::

    pip install git+git://github.com/seatgeek/cronq.git@0.15.1#egg=cronq

Adding to your ``requirements.txt`` file (run ``pip install -r requirements.txt`` afterwards)::

    git+ssh://git@github.com/seatgeek/python-cronq.git@0.15.1#egg=cronq

Usage
=====

There are various workers that are used by Cronq, as well as a web admin.

cronq-runner
============

The ``runner`` executes tasks, and should be run on hosts that will actually perform work. There is no limit to the number of runners that can execute.

The runner requires ``/var/log/cronq/`` to exist and be writable by the user executing the runner. If it is not, logs will be written to ``/tmp``.

.. code-block:: bash

    # setup rabbitmq connection info
    export RABBITMQ_HOST=localhost
    export RABBITMQ_USER=guest
    export RABBITMQ_PASS=guest

    # specify the rabbitmq queue to listen to
    export CRONQ_QUEUE=cronq_jobs # `cronq_jobs` is the default queue

    # log job output to stdout *as well as* /var/log/cronq
    export CRONQ_RUNNER_LOG_TO_STDOUT=1

    # run commands
    cronq-runner

When run, `cronq-runner` will:

- Setup a rabbitmq connection
- Listen to the `cronq_jobs` queue
- Retrieve commands from the queue
- Publish a message saying the command is started
- Run the command in a shell subprocess
- Publish a message on success/failure to the ``cronq`` exchange and ``cronq_results`` queue. This is not configurable.
- Listen for more messages

cronq-injector
==============

    The ``cronq-injector`` command will non-destructively create any necessary ``cronq`` tables, though it will need a database to perform this action against. Please note that if you do not have tables created, it is helpful to run the injector first.

The ``injector`` is used to retrieve jobs from the database and publish them to AMQP. Jobs are published in the following format:

.. code-block:: python

    # where job is a database record
    {
        'name': job.name,
        'command': unicode(job.command),
        'id': job.id,
    }

You can ostensibly run as many injectors as necessary. MySQL isolation levels are used to attain locks on job records.

.. code-block:: bash

    # setup rabbitmq connection info
    export RABBITMQ_HOST=localhost
    export RABBITMQ_USER=guest
    export RABBITMQ_PASS=guest

    # specify the database connection string
    export CRONQ_MYSQL=mysql+pymysql://cronq:cronq@localhost/cronq

    # run the comand injector
    cronq-injector

``cronq-injector`` perform a 1 second sleep between job injections, but may perform an unlimited number of job injections in that time period.

Note that jobs are not queued up at the *exact* time you specify in the database. Rather, jobs that matches the following heuristic are queued one-at-a-time until no jobs are left to be queued for that injection cycle::

    Job.next_run < NOW() OR Job.run_now = 1

cronq-results
=============

The `results` aggregator listens to the ``cronq_results`` queue for the results of ``cronq-runner`` executions. You can run as many of these as possible, as they will retrieve results one-at-a-time from rabbitmq.

.. code-block:: bash

    # setup rabbitmq connection info
    export RABBITMQ_HOST=localhost
    export RABBITMQ_USER=guest
    export RABBITMQ_PASS=guest

    # specify the database connection string
    export CRONQ_MYSQL=mysql+pymysql://cronq:cronq@localhost/cronq

    # run the results-aggregator
    cronq-results

These results can be viewed for particular commands within the web-admin, or by inspecting the database.

cronq-web
=========

The web view is a WSGI app run from ``cronq.web:app`` and requires only database access. The following is an example for running the web admin using webscale technologies:

.. code-block:: bash

    # install libevent-dev
    sudo apt-get install libevent-dev

    # install required python libraries
    sudo pip install greenlet gevent gunicorn

    # specify the database connection string
    export CRONQ_MYSQL=mysql+pymysql://cronq:cronq@localhost/cronq

    # if you have an aggregated log dashboard, you can provide a search url
    # template. it will be used in the web dashboard for linking to logs
    # the following strings will be replaced:
    #
    # {job_id} : replaced with the job's job_id
    # {run_id} : replaced with the job's run_id
    # {start_time} : replaced with job's start time in ISO format url quoted
    #                ex - "2016-08-15T08%3A00%3A11.000Z"
    # {end_time} : replaced with job's end time, or now if job is still running, in ISO format url quoted
                   ex - "2016-08-15T08%3A00%3A31.999Z"
    export CRONQ_LOG_URL_TEMPLATE="https://logs.service/search?run_id={run_id}&from={start_time}&to={end_time}"

    # run the web admin
    gunicorn --access-logfile - -w 2 --worker-class=gevent cronq.web:app

    # access the panel on http://127.0.0.1:8000

The web admin will list available commands, their result history, and a button to allow you to immediately schedule a job.

Categories Api
==============

The web admin exposes a ``category`` endpoint which allows you to replace a set of jobs with a single API call

.. code-block:: bash

    curl -v 'localhost:5000/api/category/example' -f -XPUT -H 'content-type: application/json' -d '
    {
        "category": "example",
        "jobs": [{
            "name": "Test Job",
            "schedule": "R/2013-05-29T00:00:00/PT1M",
            "command": "sleep 10",
            "routing_key": "slow"
        }]
    }'

This adds / updates a job named ``Test Job`` in the ``example`` category. The time format is ISO 8601. Any jobs no longer defined for the example category will be removed. This allows you to script job additions / removes in your VCS.


License
=======

BSD

.. _SeatGeek: https://seatgeek.com
