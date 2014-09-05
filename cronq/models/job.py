import datetime

from sqlalchemy import Column
from sqlalchemy import CHAR
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Interval
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from cronq.models.base import Base


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
