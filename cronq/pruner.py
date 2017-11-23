# -*- coding: utf-8 -*-
import argparse
import logging
import sys

from cronq.backends.mysql import Storage
from cronq.models.event import Event
from cronq.models.job import Job

from sqlalchemy import between
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc

logger = logging.getLogger(__name__)


def prune_record(event_id, max_event_id, event_range, storage):
    last = event_id + event_range
    if last > max_event_id:
        last = max_event_id

    stmt = Event.__table__.delete().where(between(Event.id, event_id, last))
    storage._engine.execute(stmt)
    logger.info('Pruning {0} - {1}'.format(event_id, last))
    storage.session.commit()
    return last


def prune(first, last, interval):
    storage = Storage(isolation_level=None)

    event_id = first
    while event_id <= last:
        try:
            event_id = prune_record(event_id, last, interval, storage)
        except (KeyboardInterrupt, SystemExit):
            storage.session.commit()
            return
        except Exception as e:
            logger.warning(e)
            return
        if event_id == last:
            break

    storage.session.commit()


def prune_keep_record(job_id, keep, storage):
    event = storage.session.query(Event).filter_by(job_id=job_id).\
        order_by(asc(Event.id)).limit(1).first()

    min_id = None
    if event is not None:
        min_id = event.id

    events = storage.session.query(Event).filter_by(job_id=job_id).\
        order_by(desc(Event.id)).limit(keep)
    event_ids = [e.id for e in events]
    if len(event_ids) == 0:
        logger.info('No events for {0}'.format(job_id))
        return

    max_id = min(event_ids)
    if min_id == max_id:
        logger.info('Min and max event ids for {0} are the same: {1} - {2}'.format(  # noqa
            job_id, min_id, max_id))
        return

    if min_id > max_id:
        logger.info('Min event id for {0} is larger than max event id: {1} - {2}'.format(  # noqa
            job_id, min_id, max_id))
        return

    logger.info('Job ID {0}, Pruning events {1} - {2}'.format(
        job_id, min_id, max_id))

    stmt = Event.__table__.delete()\
                          .where(between(Event.id, min_id, max_id))\
                          .where(Event.job_id == job_id)
    storage._engine.execute(stmt)
    storage.session.commit()


def prune_keep(keep):
    storage = Storage(isolation_level=None)
    jobs = storage.session.query(Job).order_by(asc(Job.id))
    for job in jobs:
        prune_keep_record(job.id, keep, storage)


def prune_type(args):
    is_keep = args['keep'] is not None
    is_interval = True
    interval_args = []
    for k in ['first', 'last']:
        if args[k] is None:
            is_interval = False
            interval_args.append(False)
        else:
            interval_args.append(True)

    type_ = None
    error = None
    if not is_interval and True in interval_args:
        error = 'If any "range" args are specified, all must be specified'

    if is_keep:
        if is_interval:
            error = 'Cannot specify both "keep" arg and "range" args'
        else:
            type_ = 'keep'
    else:
        if not is_interval:
            error = 'Must specify either "keep" arg or "range" args'
        else:
            type_ = 'range'

    return type_, error


def main():
    parser = argparse.ArgumentParser(description='Prunes the cronq datastore')
    parser.add_argument('--keep',
                        type=int,
                        default=None,
                        help='number of event entries to keep')
    parser.add_argument('--first',
                        type=int,
                        default=None,
                        help='first entry to prune')
    parser.add_argument('--interval',
                        type=int,
                        default=100,
                        help='interval to delete by')
    parser.add_argument('--last',
                        type=int,
                        default=None,
                        help='last entry to prune')
    args = parser.parse_args()
    args = vars(args)

    type_, error = prune_type(args)
    if error is not None:
        logger.warning(error)
        sys.exit(1)

    if type_ == 'keep':
        prune_keep(args['keep'])
    else:
        prune(args['first'], args['last'], args['range'])


if __name__ == '__main__':
    main()
