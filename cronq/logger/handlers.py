# -*- coding: utf-8 -*-
import logging


class NullHandler(logging.Handler):

    def emit(self, record):
        pass
