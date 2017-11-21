# -*- coding: utf-8 -*-
import datetime
import json
import logging

from cronq import interval_parser
from cronq.backends.mysql import Storage
from cronq.utils import json_serial
from cronq.utils import query_category_id
from cronq.utils import query_category_name
from cronq.utils import query_id
from cronq.utils import query_page
from cronq.utils import query_per_page
from cronq.utils import query_sort
from cronq.utils import split_command
from cronq.utils import task_status
from cronq.utils import took

from flask import Blueprint
from flask import Response
from flask import abort
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

blueprint_http = Blueprint('blueprint_http', __name__)
blueprint_http.add_app_template_filter(split_command, 'split_command')
blueprint_http.add_app_template_filter(task_status, 'task_status')
blueprint_http.add_app_template_filter(took, 'took')

logger = logging.getLogger(__name__)


@blueprint_http.before_request
def create_storage():
    if request.path.startswith('/static/'):
        return
    g.storage = Storage(isolation_level=None)


@blueprint_http.after_request
def remove_storage(request):
    if hasattr(g, 'storage'):
        try:
            g.storage.close()
        except Exception:
            logger.exception("exception in remove storage")
    return request


@blueprint_http.route('/')
def index():
    jobs = list(g.storage.jobs())
    categories = list(g.storage.categories())
    categories = {category['id']: category for category in categories}
    return render_template('index.html', jobs=jobs, categories=categories)


@blueprint_http.route('/_status')
def status():
    return Response(
        json.dumps({'status': 'OK'}),
        mimetype='application/json',
    )


@blueprint_http.route('/job/<int:id>', methods=['GET', 'POST'])
def job(id):
    if request.method == 'POST' and request.form.get('run_now') is not None:
        g.storage.run_job_now(id)
        flash('Job submitted at {0}'.format(datetime.datetime.utcnow()))
        return redirect(url_for('.job', id=id))

    job_doc = g.storage.get_job(id)
    chunks = g.storage.last_event_chunks_for_job(id, 20)
    title = job_doc.get('name', '')
    return render_template('job.html', job=job_doc, chunks=chunks, title=title)


@blueprint_http.route('/run/<string:id>')
def run_id(id):
    events = list(g.storage.events_for_run_id(id))
    job_id = events[0]['job_id']
    job = g.storage.get_job(job_id)
    return render_template('run_id.html', events=events, job=job)


@blueprint_http.route('/failures')
def failures():
    failure_events = list(g.storage.failures())
    names = {job['id']: job['name'] for job in g.storage.jobs()}
    for event in failure_events:
        event['job_name'] = names[event['job_id']]
    return render_template('failures.html', events=failure_events)


@blueprint_http.route('/api/category/<string:name>', methods=['PUT', 'POST'])
def category(name):
    data = request.json
    logger.info("Retrieving jobs")
    existing_jobs = g.storage.jobs_for_category(name=name)

    logger.info("Retrieving category")
    category_id = g.storage.category_id_for_name(name)
    job_lookup = {}

    logger.info("Validating jobs")
    if not validate_unique_job_names(data.get('jobs', [])):
        abort(400)

    logger.info("Indexing existing jobs")
    for job in existing_jobs:
        job_lookup[job['name']] = job

    logger.info("Processing posted jobs")
    for job in data.get('jobs', []):
        name = job['name']
        logger.info("Calcuating next run for {0}".format(name))
        next_run, duration = interval_parser.next_run_and_duration_from_8601(
            job['schedule'])
        existing_job = job_lookup.get(name, {})
        new_id = existing_job.get('id')
        new_interval = duration.total_seconds()
        command = job['command']

        logger.info("Adding job {0}".format(name))
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

    logger.info("Removing old jobs: {0}".format(job_lookup.keys()))
    remove_jobs(g.storage, job_lookup.itervalues())

    return '{"status": "success"}'


@blueprint_http.route('/api/categories', methods=['GET'])
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


@blueprint_http.route('/api/categories/<string:name>', methods=['GET'])
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


@blueprint_http.route('/api/jobs', methods=['GET'])
def api_jobs():

    per_page = query_per_page(request.args)
    page = query_page(request.args)
    sort = query_sort(request.args, allowed_fields=['id', 'name', 'category_id'])
    category_id = query_category_id(request.args)
    _id = query_id(request.args)

    category_name = query_category_name(request.args)
    if category_name:
        category = g.storage.categories_first(category_name)
        if category is None:
            return Response(
                json.dumps({
                    'data': {
                        'jobs': [],
                    },
                }, default=json_serial),
                mimetype='application/json'
            )
        category_id = category.id

    jobs = g.storage.jobs(
        _id=_id,
        category_id=category_id,
        page=page,
        per_page=per_page,
        sort=sort,
        include_runs=True)

    return Response(
        json.dumps({
            'data': {
                'jobs': list(jobs),
            },
        }, default=json_serial),
        mimetype='application/json'
    )


@blueprint_http.route('/api/jobs/<int:id>', methods=['GET'])
def api_job_show(id):
    jobs = list(g.storage.jobs(_id=id, per_page=1, include_runs=True))
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


@blueprint_http.route('/api/jobs/<int:id>/run', methods=['POST'])
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
