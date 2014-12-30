Changelog
=========

0.1.3 (2014-12-30)
------------------

- Set isolation_level to None for web requests. Closes #17. [Jose Diaz-
  Gonzalez]

0.1.2 (2014-12-30)
------------------

- Release version 0.1.2. [Jose Diaz-Gonzalez]

- Fix import issue. [Jose Diaz-Gonzalez]

- Move certain files into contrib directory. [Jose Diaz-Gonzalez]

- Remove unused config.yml file. [Jose Diaz-Gonzalez]

- Merge pull request #23 from msabramo/patch-1. [Jose Diaz-Gonzalez]

  README.rst: Add language for syntax highlighting

0.1.1 (2014-12-29)
------------------

- Release version 0.1.1. [Jose Diaz-Gonzalez]

- Simplify chunking code. [Jose Diaz-Gonzalez]

- Switch to retrieving configuration from config module. [Jose Diaz-
  Gonzalez]

- Add a config.py module to contain configuration for the entire app.
  [Jose Diaz-Gonzalez]

- Add missing requirements to requirements.txt. [Jose Diaz-Gonzalez]

- Validate jobs before attempting to run them. [Jose Diaz-Gonzalez]

0.1.0 (2014-11-24)
------------------

- Release version 0.1.0. [Jose Diaz-Gonzalez]

- Add an /_status endpoint. [Jose Diaz-Gonzalez]

0.0.42 (2014-10-01)
-------------------

- Release version 0.0.42. [Jose Diaz-Gonzalez]

- Add .env to gitignore. [Adam Cohen]

- This should be checking the length. [Adam Cohen]

0.0.41 (2014-09-09)
-------------------

- Release version 0.0.41. [Jose Diaz-Gonzalez]

- Add release script. [Jose Diaz-Gonzalez]

- Update MANIFEST.in. [Jose Diaz-Gonzalez]

- Change setup.py. [Jose Diaz-Gonzalez]

  - move version to cronq/__init__.py - allow using distutils - do not
  immediately read in file - use rat instead of md

- Minor rst fixes. [Jose Diaz-Gonzalez]

- Move readme to rst format. [Jose Diaz-Gonzalez]

- Use == instead of is for sqlalchemy query. [Jose Diaz-Gonzalez]

- Release 0.0.40. [Jose Diaz-Gonzalez]

- Properly handle failed run return_code when setting job status. [Jose
  Diaz-Gonzalez]

- Fix width of job status. [Jose Diaz-Gonzalez]

0.0.39 (2014-09-05)
-------------------

- Release 0.0.39. [Jose Diaz-Gonzalez]

- Fix timestamp display on index page. [Jose Diaz-Gonzalez]

- Release 0.0.38. [Jose Diaz-Gonzalez]

- Fix next_run setting. [Jose Diaz-Gonzalez]

- Release 0.0.37. [Jose Diaz-Gonzalez]

- Do not attempt to output time if the values are invalid. [Jose Diaz-
  Gonzalez]

- Release 0.0.36. [Jose Diaz-Gonzalez]

- Do not print table creation errors. [Jose Diaz-Gonzalez]

- Release 0.0.35. [Jose Diaz-Gonzalez]

- Remove bad install_requires. [Jose Diaz-Gonzalez]

0.0.34 (2014-09-05)
-------------------

- Release 0.0.34. [Jose Diaz-Gonzalez]

- Add missing python requirements. [Jose Diaz-Gonzalez]

0.0.33 (2014-09-05)
-------------------

- Release 0.0.33. [Jose Diaz-Gonzalez]

- Add missing package entry. [Jose Diaz-Gonzalez]

0.0.32 (2014-09-05)
-------------------

- Release 0.0.32. [Jose Diaz-Gonzalez]

- Change author and urls to SeatGeek. [Jose Diaz-Gonzalez]

0.0.31 (2014-09-05)
-------------------

- Release 0.0.31. [Jose Diaz-Gonzalez]

- Merge pull request #22 from seatgeek/ui-changes. [Jose Diaz-Gonzalez]

  UI changes

0.0.30 (2014-06-25)
-------------------

- Release 0.0.30. [Jose Diaz-Gonzalez]

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

0.0.29 (2014-06-17)
-------------------

- Release 0.0.29. [Jose Diaz-Gonzalez]

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

  0.7.1 had a bc-incompatible change when they made it PEP-8. Who knows
  what else broke

- Pin haigha to 0.7.0. [Jose Diaz-Gonzalez]

  0.7.1 had a bc-incompatible change when they made it PEP-8. Who knows
  what else broke

- Release 0.0.28. [Jose Diaz-Gonzalez]

- Actually upgrade aniso8601. [Jose Diaz-Gonzalez]

- Release version 0.0.27. [Jose Diaz-Gonzalez]

- Merge pull request #21 from seatgeek/master. [Jose Diaz-Gonzalez]

  Use Integer instead of Integer(1) for run_now

- Merge pull request #20 from seatgeek/master. [Jose Diaz-Gonzalez]

  Update aniso8601 to properly support weeks

- Added note about cronq-injector creating tables. [Jose Diaz-Gonzalez]

- Updated readme. [Jose Diaz-Gonzalez]

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

- V0.0.22. [Philip Cristiano]

- Web: Remove jobs no longer defined in category. [Philip Cristiano]

- Web: Error if names are duplicated. [Philip Cristiano]

- Add categories. [Philip Cristiano]

  First step, add ability to add categories and job in them with a
  single request.

- Mysql: Prevent deadlocks from leaving a serializable session open.
  [Philip Cristiano]

  Doing a select could cause MySQL to lock when we don't need it to.

- Mysql: Run less of the code in a try block. [Philip Cristiano]

- V0.0.21. [Philip Cristiano]

- Web: Add page to list failures. [Philip Cristiano]

- Web: Add link back to job. [Philip Cristiano]

- Mysql: Remove duplicate setting of key. [Philip Cristiano]

- V0.0.20: Publish after committing. [Philip Cristiano]

  I thought this was how I was doing it. This definitely is related to
  #9

- V0.0.19: Set MySQL isolation leve. [Philip Cristiano]

  May actually fix #9

- V0.0.18: Set locked_by to catch race conditions. [Philip Cristiano]

  closes #9

- Timeout is an int short, use a shorter one. [Philip Cristiano]

  12 hours should be enough

- V0.0.16. [Philip Cristiano]

- Handle longer running jobs. [Philip Cristiano]

  The heartbeat would kick the connection off causing a bunch of
  problems. This can be dealt with later since it's still a problem, but
  it takes 1 full day to cause it

- Close handler after process ends. [Philip Cristiano]

  May be causing a bug where the process appears to hang

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


