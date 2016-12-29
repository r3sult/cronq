# -*- coding: utf-8 -*-
import datetime
import logging
import os
import socket
import urllib

from cronq.config import DATABASE_URL
from cronq.models.category import Category
from cronq.models.event import Event
from cronq.models.job import Job

from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy.exc import InternalError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc

from uuid import uuid4


logger = logging.getLogger(__name__)


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
            Category,
            Job,
            Event,
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

    def update_job_status(self, run_id, job_id, _datetime, status, return_code=None):
        while True:
            try:
                self._update_job_status(job_id, _datetime, status, return_code)
                break
            except InternalError:
                logger.info('[cronq_job_id:{0}] [cronq_run_id:{1}] Unable to update job with result, retrying'.format(
                    job_id, run_id
                ))
                self.session.rollback()
        return True

    def _update_job_status(self, job_id, _datetime, status, return_code=None):
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

                chunks[event['run_id']] = {
                    'first': None,
                    'last': None,
                    'job_id': event['job_id']
                }

            if event['type'] == 'starting':
                chunks[event['run_id']]['first'] = event
            else:
                chunks[event['run_id']]['last'] = event

        log_url_template = os.getenv('CRONQ_LOG_URL_TEMPLATE', None)
        if log_url_template:
            self._add_log_urls(chunks, log_url_template)

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

        # newest to oldest
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
        logger.info('Trying to inject')
        while self.get_unpublished_task() is not None:
            pass

    def get_job_to_inject(self, session):
        to_run = or_(
            Job.next_run < datetime.datetime.utcnow(),
            Job.run_now == True,  # noqa
        )
        job = session.query(Job).filter(to_run).first()
        if job is None:
            return None

        logger.info('[cronq_job_id:{0}] Found a job: {1} {2}'.format(
            job.id, job.name, job.next_run))

        return job

    def update_job_time(self, session, job):
        if job.next_run is None:
            current_time = datetime.datetime.utcnow()
            logger.info('[cronq_job_id:{0}] Setting time to {1}'.format(job.id, current_time))
            job.next_run = current_time
        else:
            while job.next_run < datetime.datetime.utcnow():
                logger.info('[cronq_job_id:{0}] Adding time!'.format(job.id))
                job.next_run += job.interval
        job.run_now = False
        me = '{0}.{1}'.format(socket.gethostname(), os.getpid())
        job.locked_by = me

        # update
        try:
            session.merge(job)
            session.commit()
        except InternalError, e:
            session.rollback()
            logger.warning('[cronq_job_id:{0}] Error updating time {1} - {2}'.format(
                job.id, job.name, e))
            return None
        except Exception, e:
            session.rollback()
            logger.exception('[cronq_job_id:{0}] {1} {2}'.format(job.id, job.name, e))
            raise
        else:
            logger.info('[cronq_job_id:{0}] Next job run: {1}'.format(job.id, job.next_run))
            return job

    def get_unpublished_task(self):
        session = self._new_session()

        job = self.get_job_to_inject(session)
        if not job:
            logger.info("no job found")
            session.close()
            return

        # update job time
        job = self.update_job_time(session, job)
        if not job:
            logger.info("no job found after update time")
            session.close()
            return

        # inject
        job_doc = {
            'name': job.name,
            'command': unicode(job.command),
            'id': job.id,
        }

        # publish
        logger.info("[cronq_job_id:{0}] Trying to publish job".format(job.id))
        success = self.publisher.publish(job.routing_key, job_doc, uuid4().hex)
        if not success:
            logger.warning('[cronq_job_id:{0}] Error publishing: {1}'.format(
                job.id, job.name))
            session.close()
            return

        logger.info("[cronq_job_id:{0}] Job published".format(job.id))

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


    @staticmethod
    def _add_log_urls(chunks, log_url_template):
        for run_id, run_data in chunks.items():
            log_url = log_url_template \
                .replace('{job_id}', str(run_data['job_id'])) \
                .replace('{run_id}', str(run_id))

            if any([time_field in log_url_template for time_field in ('{start_time}', '{end_time}')]):
                if run_data.get('first'):
                    start_time = urllib.quote(run_data['first']['datetime'].strftime('%Y-%m-%dT%H:%M:%S.000Z'))
                else:
                    # default to now minus 24hrs if field is missing. this generally means bad data
                    logger.warning("No start time found for {0}, using 24 hours ago for log url".format(run_id))
                    one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
                    start_time = urllib.quote(one_day_ago.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

                if run_data.get('last'):
                    end_time = urllib.quote(run_data['last']['datetime'].strftime('%Y-%m-%dT%H:%M:%S.999Z'))
                else:
                    # default to just slightly in the future if not present. probably means still running
                    few_seconds_in_future = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
                    end_time = urllib.quote(few_seconds_in_future.strftime('%Y-%m-%dT%H:%M:%S.000Z'))
                log_url = log_url.replace('{start_time}', start_time)
                log_url = log_url.replace('{end_time}', end_time)

            run_data['log_url'] = log_url
