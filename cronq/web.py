import datetime

from backends.mysql import Storage

from flask import Flask, g, render_template, request, redirect, url_for, flash
app = Flask(__name__)

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



if __name__ == "__main__":
    app.run(debug=True)
