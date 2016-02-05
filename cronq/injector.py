# -*- coding: utf-8 -*-
import logging
import time


class Injector(object):

    def __init__(self, storage):
        self.storage = storage
        storage.bootstrap()

    def run(self):
        while True:
            self.storage.inject()
            time.sleep(1)


def main():
    from cronq.backends.mysql import Storage
    from cronq.queue_connection import Publisher

    logger = logging.getLogger('cronq.injector')
    logger.info('Creating injector')
    injector = Injector(Storage(Publisher()))

    logger.info('Running injector')
    injector.run()


if __name__ == '__main__':
    main()
