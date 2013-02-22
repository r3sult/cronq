from uuid import uuid4
import datetime
import os

import sqlalchemy
from sqlalchemy import (
    Column,
    CHAR,
    Date,
    DateTime,
    Integer,
    Interval,
    String,
    Time,
    Text,
)
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker

Base = declarative_base()



class Storage(object):

    def __init__(self, publisher=None):
        self.publisher = publisher

        self._engine = new_engine()
        self._maker = sessionmaker(bind=self._engine)
        self.session = self._maker()

    def bootstrap(self):
        models = [
            Job,
        ]
        for model in models:
            try:
                model.__table__.create(self._engine)
            except (OperationalError, ProgrammingError):
                pass
        self.add_job(
            'sleep',
            10,
            '(source /Users/philipcristiano/gits/cronq/venv/bin/activate && python -V)',
            id=1
        )

    def add_job(self, name, interval_seconds, command, next_run=None, id=None):
        job = Job()
        job.id = id
        job.name = name
        job.interval = datetime.timedelta(seconds=interval_seconds)
        job.command = command
        self.session.merge(job)
        self.session.commit()

    def inject(self):
        """Get a message from storage and injects it into the job stream"""
        print 'Trying to inject', datetime.datetime.utcnow()
        while self.get_unpublished_task() is not None:
            pass

    def get_unpublished_task(self):
        session = self.session
        to_run = Job.next_run < datetime.datetime.utcnow()

        job = session.query(Job).filter(to_run).first()
        if job is None:
            return
        print 'Found a job:', job.name, job.next_run
        to_run_at = job.next_run
        try:
            while job.next_run < datetime.datetime.utcnow():
                print 'Adding time!'
                job.next_run += job.interval
            print job.next_run
            print job.command
            job_doc = {
                'command': unicode(job.command),
                'id': job.id,
            }
            self.publisher.publish(job_doc, uuid4())
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exc



def new_engine():
    dsn = os.getenv('CRONQ_MYSQL', 'mysql+mysqlconnector://root@localhost/cronq')
    return create_engine(dsn)


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(255))
    interval = Column(Interval)
    next_run = Column(DateTime(), default=datetime.datetime.utcnow)
    command = Column(Text())


class Event(Base):

    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, primary_key=True)
    run_id = Column(CHAR(32))
    type = Column(CHAR(32))
    return_code = Column(Integer)
