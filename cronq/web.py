import datetime
import logging

from flask import Flask, g, render_template, request, redirect, url_for, flash, abort

from cronq import interval_parser
from backends.mysql import Storage

app = Flask(__name__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)


app.secret_key = 'not a secret'

@app.before_request
def create_storage():
    if request.path.startswith('/static/'):
        return
    g.storage = Storage()

@app.after_request
def remove_storage(request):
    if hasattr(g, 'storage'):
        try:
            g.storage.close()
        except Exception as exc:
            print exc
    return request

@app.route('/')
def index():
    jobs = list(g.storage.jobs)
    return render_template('index.html', jobs=jobs)


@app.route('/job/<int:id>', methods=['GET', 'POST'])
def job(id):
    if request.method == 'POST' and request.form.get('run_now') is not None:
        g.storage.run_job_now(id)
        flash('Job submitted at {0}'.format(datetime.datetime.utcnow()))
        return redirect(url_for('job', id=id))

    job_doc = g.storage.get_job(id)
    events = g.storage.last_events_for_job(id, 10)
    return render_template('job.html', job=job_doc, events=events)

@app.route('/run/<string:id>')
def run_id(id):
    events = list(g.storage.events_for_run_id(id))
    job_id = events[0]['job_id']
    job = g.storage.get_job(job_id)
    return render_template('run_id.html', events=events, job=job)

@app.route('/failures')
def failures():
    failure_events = list(g.storage.failures())
    names = { job['id']: job['name'] for job in g.storage.jobs }
    for event in failure_events:
        event['job_name'] = names[event['job_id']]
    return render_template('failures.html', events=failure_events)

@app.route('/api/category/<string:name>', methods=['PUT', 'POST'])
def category(name):
    data = request.json
    existing_jobs = g.storage.jobs_for_category(name=name)
    category_id = g.storage.category_id_for_name(name)
    job_lookup = {}

    if not validate_unique_job_names(data.get('jobs', [])):
        abort(400)

    for job in existing_jobs:
        job_lookup[job['name']] = job

    for job in data.get('jobs', []):
        name = job['name']
        next_run, duration = interval_parser.next_run_and_duration_from_8601(job['schedule'])
        existing_job = job_lookup.get(name, {})
        new_id = existing_job.get('id')
        new_next_run = next_run
        new_interval = duration.total_seconds()
        command = job['command']
        g.storage.add_job(
            name,
            new_interval,
            command,
            next_run,
            new_id,
            category_id,
            routing_key=job.get('routing_key')
        )
        if existing_job:
            del job_lookup[name]

    remove_jobs(g.storage, job_lookup.itervalues())

    return '{"status": "success"}'


def remove_jobs(storage, jobs):
    for job in jobs:
        g.storage.remove_job(job['id'])


def validate_unique_job_names(jobs):
    job_names = [job['name'] for job in jobs]
    return len(job_names) == len(set(job_names))


if __name__ == "__main__":
    app.run(debug=True)
