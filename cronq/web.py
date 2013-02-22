from backends.mysql import Storage

from flask import Flask, g, render_template, request
app = Flask(__name__)


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


@app.route('/job/<int:id>')
def job(id):
    job_doc = g.storage.get_job(id)
    events = g.storage.last_events_for_job(id, 10)
    return render_template('job.html', job=job_doc, events=events)

@app.route('/run/<string:id>')
def run_id(id):
    events = g.storage.events_for_run_id(id)
    return render_template('run_id.html', events=events)


if __name__ == "__main__":
    app.run(debug=True)
