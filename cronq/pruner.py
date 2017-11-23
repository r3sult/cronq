# -*- coding: utf-8 -*-
import argparse
import logging

from cronq.backends.mysql import Storage
from cronq.models.event import Event
from sqlalchemy import between

logger = logging.getLogger(__name__)


def prune_record(event_id, max_event_id, storage):
    last = event_id + 100
    if last > max_event_id:
        last = max_event_id

    stmt = Event.__table__.delete().where(between(Event.id, event_id, last))
    storage._engine.execute(stmt)
    logger.info('Pruning {0} - {1}'.format(event_id, last))
    storage.session.commit()
    return last


def prune(first, last):
    storage = Storage(isolation_level=None)

    event_id = first
    while event_id <= last:
        try:
            event_id = prune_record(event_id, last, storage)
        except (KeyboardInterrupt, SystemExit):
            storage.session.commit()
            return
        except Exception as e:
            logger.warning(e)
            return
        if event_id == last:
            break

    storage.session.commit()


def main():
    parser = argparse.ArgumentParser(description='Prunes the cronq datastore')
    parser.add_argument('--first',
                        type=int,
                        default='0',
                        help='first entry to prune')
    parser.add_argument('--last',
                        type=int,
                        default='0',
                        help='last entry to prune')
    args = parser.parse_args()
    args = vars(args)
    prune(args['first'], args['last'])


if __name__ == '__main__':
    main()
