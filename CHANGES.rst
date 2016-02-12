Changelog
=========

0.7.0 (2016-02-11)
------------------

- Add the ability to enable job run logging to stdout. [Jose Diaz-
  Gonzalez]

- Uppercase status string. [Jose Diaz-Gonzalez]

- Structure exit code better in log message. [Jose Diaz-Gonzalez]

0.6.1 (2016-02-05)
------------------

- Move all logging setup into cronq.logsetup module. [Jose Diaz-
  Gonzalez]

0.6.0 (2016-02-05)
------------------

- Set format on all log levels. [Jose Diaz-Gonzalez]

0.4.5 (2016-02-04)
------------------

- Ensure we handle cases where the next_run is null. [Jose Diaz-
  Gonzalez]

0.4.4 (2016-02-04)
------------------

- Add better verbose logging. [Jose Diaz-Gonzalez]

0.4.3 (2016-02-04)
------------------

- Change message from info to warning. [Jose Diaz-Gonzalez]

- Close the session before returning. [Jose Diaz-Gonzalez]

- Add more logging around results aggregation. [Jose Diaz-Gonzalez]

0.4.2 (2016-02-03)
------------------

- Avoid invalid command. [Jose Diaz-Gonzalez]

0.4.1 (2016-02-03)
------------------

- Retry updating job status. [Jose Diaz-Gonzalez]

0.4.0 (2016-02-03)
------------------

- Catch deadlocks job publishing to reduce reported errors. [Jose Diaz-
  Gonzalez]

- Cleanup imports. [Jose Diaz-Gonzalez]

0.3.1 (2016-01-25)
------------------

- Minor fixes to release script. [Jose Diaz-Gonzalez]

- Fix ordering of bootstrap models. [Jose Diaz-Gonzalez]

  Closes #27

0.3.0 (2015-11-25)
------------------

- Use __name__ when retrieving a logger. [Jose Diaz-Gonzalez]

- Remove nosyd from requirements. [Jose Diaz-Gonzalez]

- Add LICENSE.txt. [Jose Diaz-Gonzalez]

- Fix formatting. [Evan Carter]

- First pass at fixing mysql backend logging. [Evan Carter]

- Switch all links to https. [Jose Diaz-Gonzalez]

- Add source code encodings to all python files. [Jose Diaz-Gonzalez]

- Fix PEP8 violations. [Jose Diaz-Gonzalez]

- Pin all python requirements. [Jose Diaz-Gonzalez]

- Add check for gitchangelog. [Jose Diaz-Gonzalez]

0.2.2 (2015-09-03)
------------------

- Ensure the rst-lint binary is available. [Jose Diaz-Gonzalez]

0.2.1 (2015-08-07)
------------------

- Do not hardcode rabbitmq host. [Jose Diaz-Gonzalez]

0.2.0 (2015-03-03)
------------------

- Actually add the logger. [Adam Cohen]

- Use a real logger instead of print statements. [Adam Cohen]

- This declaration does nothing and breaks any attempt to call this
  callback, part deux. [Adam Cohen]

- This assignment does nothing and breaks every attempt to call this
  callback as an UnboundLocalError. [Adam Cohen]

0.1.3 (2014-12-30)
------------------

- Set isolation_level to None for web requests. Closes #17. [Jose Diaz-
  Gonzalez]

0.1.2 (2014-12-30)
------------------

- Fix import issue. [Jose Diaz-Gonzalez]

- Move certain files into contrib directory. [Jose Diaz-Gonzalez]

- Remove unused config.yml file. [Jose Diaz-Gonzalez]

- README.rst: Add language for syntax highlighting. [Marc Abramowitz]

0.1.1 (2014-12-29)
------------------

- Simplify chunking code. [Jose Diaz-Gonzalez]

- Switch to retrieving configuration from config module. [Jose Diaz-
  Gonzalez]

- Add a config.py module to contain configuration for the entire app.
  [Jose Diaz-Gonzalez]

- Add missing requirements to requirements.txt. [Jose Diaz-Gonzalez]

- Validate jobs before attempting to run them. [Jose Diaz-Gonzalez]

0.1.0 (2014-11-24)
------------------

- Add an /_status endpoint. [Jose Diaz-Gonzalez]

0.0.42 (2014-10-01)
-------------------

- Add .env to gitignore. [Adam Cohen]

- This should be checking the length. [Adam Cohen]

0.0.41 (2014-09-09)
-------------------

- Add release script. [Jose Diaz-Gonzalez]

- Change setup.py. [Jose Diaz-Gonzalez]

  - move version to cronq/__init__.py
  - allow using distutils
  - do not immediately read in file
  - use rat instead of md


- Minor rst fixes. [Jose Diaz-Gonzalez]

- Move readme to rst format. [Jose Diaz-Gonzalez]

- Use == instead of is for sqlalchemy query. [Jose Diaz-Gonzalez]

- Properly handle failed run return_code when setting job status. [Jose
  Diaz-Gonzalez]

- Fix width of job status. [Jose Diaz-Gonzalez]

0.0.39 (2014-09-05)
-------------------

- Fix timestamp display on index page. [Jose Diaz-Gonzalez]

- Fix next_run setting. [Jose Diaz-Gonzalez]

- Do not attempt to output time if the values are invalid. [Jose Diaz-
  Gonzalez]

- Do not print table creation errors. [Jose Diaz-Gonzalez]

- Remove bad install_requires. [Jose Diaz-Gonzalez]

0.0.34 (2014-09-05)
-------------------

- Add missing python requirements. [Jose Diaz-Gonzalez]

0.0.33 (2014-09-05)
-------------------

- Add missing package entry. [Jose Diaz-Gonzalez]

0.0.32 (2014-09-05)
-------------------

- Change author and urls to SeatGeek. [Jose Diaz-Gonzalez]

0.0.31 (2014-09-05)
-------------------

- Convert UTC times to local timezone. [Jose Diaz-Gonzalez]

  javascript date handling allows you to specify the timezone in the date time string and will correctly handle parsing to local time when performing a toString.


- Group jobs by category on index page. [Jose Diaz-Gonzalez]

- Use smaller status balls everywhere. [Jose Diaz-Gonzalez]

- Remove old css. [Jose Diaz-Gonzalez]

- Much nicer list view of events that occurred. [Jose Diaz-Gonzalez]

  - Group events by ID
  - Show a running time for each job run
  - Use human readable dates/times everywhere
  - Show the appropriate status ball for each run
  - Fix the button css to be a bit more flat and less bootstrappy

  Still need to fix dates to convert from UTC to local time.


- Reference cronq modules with cronq prefix. [Jose Diaz-Gonzalez]

- Extract models into their own namespace. [Jose Diaz-Gonzalez]

  This will allow us to build separate backends - postgres for instance - without needing to redefine models


- Use moment.js to provide human-readable task running info. [Jose Diaz-
  Gonzalez]

- Add missing utils.py. [Jose Diaz-Gonzalez]

- Slightly better looking task definition. [Jose Diaz-Gonzalez]

  Still need to work on actual task running information, though the command information looks more spiffy


- Fix header height to center h1s. [Jose Diaz-Gonzalez]

- Better index page. [Jose Diaz-Gonzalez]

  - Show the last status of a task
  - Show the current running state of the task
  - "Better" display of each task
  - Use Roboto font from Google to display text


- Change heading. [Jose Diaz-Gonzalez]

- Remove commented out code. [Jose Diaz-Gonzalez]

- Use minified css files. [Jose Diaz-Gonzalez]

- Properly handle return codes for finished tasks and set the job status
  to succeeded. [Jose Diaz-Gonzalez]

- Expose job status and run info to the job index. [Jose Diaz-Gonzalez]

- Keep track of the current job status as well as the last job status.
  [Jose Diaz-Gonzalez]

  Useful for dashboards. Whenever tracking the last_run, reset if the status is "starting", as otherwise the information will be incorrect.


- Add status and run info to each job. [Jose Diaz-Gonzalez]

- Datetime => _datetime. [Jose Diaz-Gonzalez]

- Add relations between models. [Jose Diaz-Gonzalez]

- Order jobs on ui by name. [Jose Diaz-Gonzalez]

- PEP8. [Jose Diaz-Gonzalez]

0.0.30 (2014-06-25)
-------------------

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

0.0.29 (2014-06-17)
-------------------

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

  0.7.1 had a bc-incompatible change when they made it PEP-8. Who knows what else broke

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

  0.7.1 had a bc-incompatible change when they made it PEP-8. Who knows what else broke

v0.0.28 (2014-01-02)
--------------------

- Actually upgrade aniso8601. [Jose Diaz-Gonzalez]

v0.0.27 (2014-01-02)
--------------------

- Use Integer instead of Integer(1) for run_now. [Jose Diaz-Gonzalez]

v0.0.26 (2014-01-02)
--------------------

- Bump version. [zackkitzmiller]

- Added note about cronq-injector creating tables. [Jose Diaz-Gonzalez]

- Remove zip file. [Jose Diaz-Gonzalez]

- V0.0.25. [Philip Cristiano]

- Web: Allow POST as well. [Philip Cristiano]

- Web: Log a little. [Philip Cristiano]

- Web: Don't be cute. [Philip Cristiano]

- V0.0.23. [Philip Cristiano]

- Readme: Example category should use fail flag for curl. [Philip
  Cristiano]

  Silent failures for this wouldn't be great

- Api: Set routing_key for category jobs. [Philip Cristiano]

v0.0.22 (2013-05-30)
--------------------

- V0.0.22. [Philip Cristiano]

- Web: Remove jobs no longer defined in category. [Philip Cristiano]

- Web: Error if names are duplicated. [Philip Cristiano]

- Add categories. [Philip Cristiano]

  First step, add ability to add categories and job in them with a single request.

- Mysql: Prevent deadlocks from leaving a serializable session open.
  [Philip Cristiano]

  Doing a select could cause MySQL to lock when we don't need it to.

- Mysql: Run less of the code in a try block. [Philip Cristiano]

v0.0.21 (2013-03-10)
--------------------

- V0.0.21. [Philip Cristiano]

- Web: Add page to list failures. [Philip Cristiano]

- Web: Add link back to job. [Philip Cristiano]

- Mysql: Remove duplicate setting of key. [Philip Cristiano]

v0.0.20 (2013-02-26)
--------------------

- V0.0.20: Publish after committing. [Philip Cristiano]

  I thought this was how I was doing it. This definitely is related to #9

v0.0.19 (2013-02-26)
--------------------

- V0.0.19: Set MySQL isolation leve. [Philip Cristiano]

  May actually fix #9

v0.0.18 (2013-02-25)
--------------------

- V0.0.18: Set locked_by to catch race conditions. [Philip Cristiano]

  closes #9

v0.0.17 (2013-02-25)
--------------------

- Timeout is an int short, use a shorter one. [Philip Cristiano]

  12 hours should be enough

v0.0.16 (2013-02-25)
--------------------

- V0.0.16. [Philip Cristiano]

- Handle longer running jobs. [Philip Cristiano]

  The heartbeat would kick the connection off causing a bunch of problems. This can be dealt with later since it's still a problem, but it takes 1 full day to cause it

v0.0.15 (2013-02-24)
--------------------

- Close handler after process ends. [Philip Cristiano]

  May be causing a bug where the process appears to hang

v0.0.14 (2013-02-24)
--------------------

- Exit on connection error. [Philip Cristiano]

  closes #8

- V0.0.13. [Philip Cristiano]

- Runner: Log to /var/log/cronq for each process. [Philip Cristiano]

  Uses a watchedFileHandler so it can be log rotated

- Fix typo. [Philip Cristiano]

- Run jobs now in web interface. [Philip Cristiano]

- Support multiple RabbitMQ queues. [Philip Cristiano]

  To allow routing of jobs to the correct nodes and splitting of tasks

- Page for each run. [Philip Cristiano]

- Something to read. [Philip Cristiano]

- Fix showing return code. [Philip Cristiano]

- Aggregate job results for web view. [Philip Cristiano]

- Web: Name links to index. [Philip Cristiano]

- Working on web app. [Philip Cristiano]

- Web view. [Philip Cristiano]

- Don't add test job. [Philip Cristiano]

- Working injector and runner together woooo. [Philip Cristiano]

- Runner working. [Philip Cristiano]

- Runner will run a task… constantly at this point. [Philip Cristiano]

- Make: Add upload target. [Philip Cristiano]

- Make: Fix path to Python. [Philip Cristiano]

- Basic project layout. [Philip Cristiano]

- Initial commit. [philipcristiano]


