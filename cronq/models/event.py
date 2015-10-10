# -*- coding: utf-8 -*-
from sqlalchemy import Column
from sqlalchemy import CHAR
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer

from cronq.models.base import Base


class Event(Base):

    __tablename__ = 'events'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    datetime = Column(DateTime)
    run_id = Column(CHAR(32))
    type = Column(CHAR(32))
    host = Column(CHAR(255))
    return_code = Column(Integer)
