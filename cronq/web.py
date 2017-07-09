# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time

from cronq import interval_parser
from cronq.backends.mysql import Storage
from cronq.utils import chunks_to_runs
from cronq.utils import json_serial
from cronq.utils import query_category_id
from cronq.utils import query_id
from cronq.utils import query_page
from cronq.utils import query_per_page
from cronq.utils import query_sort
from cronq.utils import split_command
from cronq.utils import task_status
from cronq.utils import took

from flask import Flask
from flask import Response
from flask import abort
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

app = Flask(__name__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)
app.secret_key = 'not a secret'
app.jinja_env.filters['split_command'] = split_command
app.jinja_env.globals.update(task_status=task_status)
app.jinja_env.globals.update(took=took)

logger = logging.getLogger(__name__)


@app.before_request
def create_storage():
    if request.path.startswith('/static/'):
        return
    g.storage = Storage(isolation_level=None)


@app.after_request
def remove_storage(request):
    if hasattr(g, 'storage'):
        try:
            g.storage.close()
        except Exception:
            logger.exception("exception in remove storage")
    return request


@app.route('/')
def index():
    jobs = list(g.storage.jobs())
    categories = list(g.storage.categories())
    categories = {category['id']: category for category in categories}
    return render_template('index.html', jobs=jobs, categories=categories)


@app.route('/_status')
def status():
    return Response(
        json.dumps({'status': 'OK'}),
        mimetype='application/json',
    )


@app.route('/job/<int:id>', methods=['GET', 'POST'])
def job(id):
    if request.method == 'POST' and request.form.get('run_now') is not None:
        g.storage.run_job_now(id)
        flash('Job submitted at {0}'.format(datetime.datetime.utcnow()))
        return redirect(url_for('job', id=id))

    job_doc = g.storage.get_job(id)
    chunks = g.storage.last_event_chunks_for_job(id, 20)
    title = job_doc.get('name', '')
    return render_template('job.html', job=job_doc, chunks=chunks, title=title)


@app.route('/run/<string:id>')
def run_id(id):
    events = list(g.storage.events_for_run_id(id))
    job_id = events[0]['job_id']
    job = g.storage.get_job(job_id)
    return render_template('run_id.html', events=events, job=job)


@app.route('/failures')
def failures():
    failure_events = list(g.storage.failures())
    names = {job['id']: job['name'] for job in g.storage.jobs()}
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
        next_run, duration = interval_parser.next_run_and_duration_from_8601(
            job['schedule'])
        existing_job = job_lookup.get(name, {})
        new_id = existing_job.get('id')
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


@app.route('/api/categories', methods=['GET'])
def api_categories():
    _id = query_id(request.args)
    categories = g.storage.categories(_id=_id)
    return Response(
        json.dumps({
            'data': {
                'categories': list(categories)
            },
        }, default=json_serial),
        mimetype='application/json',
    )


@app.route('/api/categories/<string:name>', methods=['GET'])
def api_category_show(name):
    category = g.storage.categories_first(name)
    return Response(
        json.dumps({
            'data': {
                'category': {
                    'id': category.id,
                    'name': category.name,
                },
            },
        }, default=json_serial),
        mimetype='application/json',
    )


@app.route('/api/jobs', methods=['GET'])
def api_jobs():

    per_page = query_per_page(request.args)
    page = query_page(request.args)
    sort = query_sort(request.args, allowed_fields=['id', 'name', 'category_id'])
    category_id = query_category_id(request.args)
    _id = query_id(request.args)

    jobs = g.storage.jobs(
        _id=_id,
        category_id=category_id,
        page=page,
        per_page=per_page,
        sort=sort)

    return Response(
        json.dumps({
            'data': {
                'jobs': list(jobs),
            },
        }, default=json_serial),
        mimetype='application/json'
    )


@app.route('/api/jobs/<int:id>', methods=['GET'])
def api_job_show(id):
    jobs = list(g.storage.jobs(_id=id, per_page=1))
    if len(jobs) != 1:
        return Response(
            json.dumps({
                'error': {
                    'message': 'Job not found for id {0}'.format(id),
                },
            }, default=json_serial),
            mimetype='application/json'
        )

    return Response(
        json.dumps({
            'data': {
                'job': job[0],
            },
        }, default=json_serial),
        mimetype='application/json'
    )


@app.route('/api/jobs/<int:id>/runs', methods=['GET'])
def api_job_runs(id):
    jobs = list(g.storage.jobs(_id=id, per_page=1))

    if len(jobs) != 1:
        return Response(
            json.dumps({
                'error': {
                    'message': 'Job not found for id {0}'.format(id),
                },
            }, default=json_serial),
            mimetype='application/json'
        )

    chunks = g.storage.last_event_chunks_for_job(id, 20)
    runs = chunks_to_runs(chunks)
    return Response(
        json.dumps({
            'data': {
                'job': jobs[0],
                'runs': runs,
            }
        }, default=json_serial),
        mimetype='application/json'
    )


@app.route('/api/jobs/<int:id>/run', methods=['POST'])
def api_job_run(id):
    jobs = list(g.storage.jobs(_id=id, per_page=1))

    if len(jobs) != 1:
        return Response(
            json.dumps({
                'error': {
                    'message': 'Job not found for id {0}'.format(id),
                },
            }, default=json_serial),
            mimetype='application/json'
        )

    g.storage.run_job_now(id)
    return Response(
        json.dumps({
            'success': {
                'message': 'Job submitted at {0}'.format(datetime.datetime.utcnow()),
            },
        }, default=json_serial),
        mimetype='application/json'
    )


def remove_jobs(storage, jobs):
    for job in jobs:
        g.storage.remove_job(job['id'])


def validate_unique_job_names(jobs):
    job_names = [job['name'] for job in jobs]
    return len(job_names) == len(set(job_names))


if __name__ == "__main__":
    app.run(debug=True)
