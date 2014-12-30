import datetime
import os
import socket

from sqlalchemy import or_
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from cronq.config import DATABASE_URL
from cronq.models.category import Category
from cronq.models.event import Event
from cronq.models.job import Job


class Storage(object):

    FINISHED = 'finished'
    FAILED = 'failed'
    STARTED = 'started'
    SUCCEEDED = 'succeeded'

    def __init__(self, publisher=None, isolation_level='SERIALIZABLE'):
        self.publisher = publisher

        self._engine = self._new_engine(isolation_level=isolation_level)
        self._maker = sessionmaker(bind=self._engine)
        self.session = self._new_session()

    def _new_engine(self, isolation_level='SERIALIZABLE'):
        if isolation_level is not None:
            return create_engine(DATABASE_URL, isolation_level=isolation_level)
        return create_engine(DATABASE_URL)

    def _new_session(self):
        return self._maker()

    def bootstrap(self):
        models = [
            Job,
            Event,
            Category,
        ]
        for model in models:
            try:
                model.__table__.create(self._engine)
            except (OperationalError, ProgrammingError):
                pass

    def close(self):
        self.session.close()
        self._engine.dispose()

    def add_job(self,
                name,
                interval_seconds,
                command,
                next_run,
                id=None,
                category_id=None,
                routing_key=None):
        if routing_key is None:
            routing_key = 'default'
        job = Job()
        job.id = id
        job.name = name
        job.next_run = next_run
        job.interval = datetime.timedelta(seconds=interval_seconds)
        job.command = command
        job.routing_key = routing_key
        job.category_id = category_id
        self.session.merge(job)
        self.session.commit()

    def remove_job(self, job_id):
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            self.session.delete(job)
            self.session.commit()

    def add_event(self, job_id, _datetime, run_id, type, host, return_code):
        event = Event()
        event.job_id = job_id
        event.datetime = _datetime
        event.run_id = run_id
        event.type = type
        event.host = host
        event.return_code = return_code
        self.session.add(event)
        self.session.commit()

    def update_job_status(self, job_id, _datetime, status, return_code=None):
        job = self.session.query(Job).filter_by(id=job_id).first()
        if job:
            job.current_status = status
            if status == self.STARTED:
                job.last_run_start = _datetime
                job.last_run_status = None
                job.last_run_stop = None
            if status == self.FAILED:
                job.last_run_status = status
                job.last_run_stop = _datetime
            if status == self.FINISHED:
                job.last_run_status = status
                job.last_run_stop = _datetime
                if return_code is not None:
                    job.current_status = self.FAILED
                    job.last_run_status = self.FAILED
                    if int(return_code) == 0:
                        job.current_status = self.SUCCEEDED
                        job.last_run_status = self.SUCCEEDED
            self.session.merge(job)
            self.session.commit()

    @property
    def jobs(self):
        session = self.session
        for job in session.query(Job).order_by(asc(Job.category_id)):
            yield {
                'id': job.id,
                'category_id': job.category_id,
                'name': job.name,
                'next_run': job.next_run,
                'interval': job.interval,
                'last_run_start': job.last_run_start,
                'last_run_stop': job.last_run_stop,
                'last_run_status': job.last_run_status,
                'current_status': job.current_status or 'none',
                'last_run_text': job.last_run_text(),
            }

    @property
    def categories(self):
        session = self.session
        for category in session.query(Category).order_by(asc(Category.id)):
            yield {
                'id': category.id,
                'name': category.name,
            }

    def get_job(self, id):
        job = self.session.query(Job).filter_by(id=id).first()
        return self._job_doc_for_model(job)

    def _job_doc_for_model(self, job):
        return {
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run,
            'interval': job.interval,
            'command': job.command,
        }

    def jobs_for_category(self, id=None, name=None):
        if id and name:
            assert "Don't pass both id and name"
        if name:
            id = self.category_id_for_name(name)
        for job in self.session.query(Job).filter_by(category_id=id):
            yield self._job_doc_for_model(job)

    def category_id_for_name(self, name):
        category = self.session.query(Category).filter_by(name=name).first()
        if category is None:
            category = Category(name=name)
            self.session.add(category)
            self.session.commit()
        return category.id

    def last_event_chunks_for_job(self, job_id, number):
        events = self.session.query(Event).filter_by(job_id=job_id).\
            order_by(desc(Event.id)).limit(number)
        events = [doc for doc in self.event_models_to_docs(events)]

        if len(events) == 0:
            return []

        chunks = {}
        for event in events:
            if event['run_id'] not in chunks:
                chunks[event['run_id']] = {'first': None, 'last': None}

            if event['type'] == 'starting':
                chunks[event['run_id']]['first'] = event
            else:
                chunks[event['run_id']]['last'] = event

        docs = [chunk for i, chunk in chunks.iteritems()]

        def chunk_compare(x, y):
            first = x.get('first', x.get('last'))
            last = y.get('first', y.get('last'))
            if first is None and last is None:
                return 0
            if first is None:
                return -1
            if last is None:
                return 1
            return int((first['datetime'] - last['datetime']).total_seconds())

        docs = sorted(docs, cmp=chunk_compare, reverse=True)

        return docs

    def events_for_run_id(self, run_id):
        events = self.session.query(Event).filter_by(run_id=run_id).\
            order_by(Event.id)
        return self.event_models_to_docs(events)

    def failures(self):
        events = self.session.query(Event)\
            .filter_by(type=self.FINISHED)\
            .filter(Event.return_code != 0)\
            .order_by(desc(Event.id)).limit(50)
        return self.event_models_to_docs(events)

    def run_job_now(self, id):
        event = self.session.query(Job).filter_by(id=id).first()
        event.run_now = True
        self.session.commit()

    def inject(self):
        """Get a message from storage and injects it into the job stream"""
        print 'Trying to inject', datetime.datetime.utcnow()
        while self.get_unpublished_task() is not None:
            pass

    def get_unpublished_task(self):
        session = self._new_session()
        to_run = or_(
            Job.next_run < datetime.datetime.utcnow(),
            Job.run_now == True,
        )

        job = session.query(Job).filter(to_run).first()
        if job is None:
            session.close()
            return
        print 'Found a job:', job.name, job.next_run

        while job.next_run < datetime.datetime.utcnow():
            print 'Adding time!'
            job.next_run += job.interval
        print job.next_run
        job_doc = {
            'name': job.name,
            'command': unicode(job.command),
            'id': job.id,
        }
        job.run_now = False
        me = '{0}.{1}'.format(socket.gethostname(), os.getpid())
        job.locked_by = me
        try:
            session.commit()
            self.publisher.publish(job.routing_key, job_doc, uuid4().hex)
        except Exception:
            session.rollback()
            raise
        session.close()
        return True

    def event_models_to_docs(self, events):
        for event in events:
            doc = {
                'id': event.id,
                'datetime': event.datetime,
                'run_id': event.run_id,
                'host': event.host,
                'return_code': event.return_code,
                'type': event.type,
                'job_id': event.job_id,
                'status': self.get_status(event.type, event.return_code),
            }
            yield doc

    def get_status(self, _type, return_code=None):
        if _type == self.SUCCEEDED:
            return self.SUCCEEDED
        elif return_code is None:
            return _type
        elif _type == self.FINISHED:
            if int(return_code) == 0:
                return self.SUCCEEDED

        return self.FINISHED
