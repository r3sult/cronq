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
def hello():
    jobs = list(g.storage.jobs)
    return render_template('index.html', jobs=jobs)


@app.route('/job/<int:id>')
def job(id):
    job_doc = g.storage.get_job(id)
    return render_template('job.html', job=job_doc)


if __name__ == "__main__":
    app.run(debug=True)
