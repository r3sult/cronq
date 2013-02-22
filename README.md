# CronQ

A cron-like system to run you application tasks across any node, instead of one
special snowflake. This is done by keeping your tasks in MySQL and publishing
them over AMQP to workers that will run your tasks and eventually save the
results back into the DB. This was started as a hackathon project at
[SeatGeek](http://seatgeek.com)

# Installation

    pip install cronq

Workers that need to be started

* `cronq-runner` - executes each task
* `cronq-injector` - checks for new tasks in the DB and publishes to AMQP
* `cronq-results` - Saves events from the runner

These take the envvars `RABBITMQ_HOST` and `CRONQ_MYQL`. `CRONQ_MYQL` should
be a MySQL Connector DSN starting with `mysql+mysqlconnector://`.

`cronq-runner` will also use the variable `CRONQ_QUEUE` to determine which
queue to consume. The default is `cronq_jobs`.

The web view is a WSGI app run from `cronq.web:app` and requires the same envvars.
