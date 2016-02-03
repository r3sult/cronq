# -*- coding: utf-8 -*-
import datetime

from cronq.models.base import Base

from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship


class Job(Base):

    __tablename__ = 'jobs'
    __table_args__ = (UniqueConstraint('category_id', 'name'), {
        'mysql_engine': 'InnoDB'})

    events = relationship("Event")

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(255))
    interval = Column(Interval)
    next_run = Column(DateTime(), default=datetime.datetime.utcnow)
    last_run_start = Column(DateTime(), default=None)
    last_run_stop = Column(DateTime(), default=None)
    last_run_status = Column(CHAR(32))
    current_status = Column(CHAR(32))
    routing_key = Column(CHAR(32), default='default')
    command = Column(Text())
    run_now = Column(Integer)
    locked_by = Column(CHAR(64))
    category_id = Column(Integer, ForeignKey('categories.id'))

    def last_run_text(self):
        hours_ago = ''
        if self.last_run_stop is not None:
            hours_ago = '<span {0} {1} {2} {3}>{4} UTC</span>'.format(
                'class="datetime"',
                'data-toggle="tooltip"',
                'data-placement="right"',
                'data-date="{0} UTC" title="{0} UTC"'.format(
                    self.last_run_stop),
                self.last_run_stop)

        status_map = {
            'started': 'Running now',
            'starting': 'Running now',
            'failed': 'Last run failed',
            'finished': 'Error',
            'none': 'Waiting...',
            'succeeded': 'About {0}'.format(hours_ago),
        }

        if self.current_status:
            return status_map[self.current_status]

        return status_map['none']
