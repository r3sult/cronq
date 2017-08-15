web: gunicorn --access-logfile - -w 1 --bind 0.0.0.0:$PORT --worker-class=gevent cronq.web:app
results: cronq-results
injector: cronq-injector
runner: cronq-runner
