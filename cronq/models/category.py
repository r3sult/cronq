# -*- coding: utf-8 -*-
from cronq.models.base import Base

from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy.orm import relationship


class Category(Base):

    __tablename__ = 'categories'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    jobs = relationship("Job")

    id = Column(Integer, primary_key=True)
    name = Column(CHAR(255), unique=True)
