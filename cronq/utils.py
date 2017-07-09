# -*- coding: utf-8 -*-
import datetime


def split_command(string):
    commands = string.strip().split(';')
    ret = []
    for command in commands:
        ret.extend(command.strip().split(' && '))
    return ret


def task_status(first, last=None):
    if last is None:
        return first['status']

    if last['status'] == 'finished':
        if int(last['return_code']) == 0:
            return 'succeeded'
        return 'failed'
    return last['status']


def took(first_time, last_time):
    if type(first_time) is not datetime.datetime:
        return ""

    if type(last_time) is not datetime.datetime:
        return ""

    elapsed_time = last_time - first_time
    return int(elapsed_time.total_seconds())


def unicodedammit(x):
    """encode as string, decode as unicode bytes"""
    try:
        decoded = decode_string(x, ignore=False)
        return decoded
    except Exception:
        # decide with ignore
        decoded = decode_string(x, ignore=True)
        return decoded
    return decoded


def decode_string(newstr, ignore=False):
    """attempt to decode the string with three different options
        ascii
        utf8mb4
        utf8
        latin1
    If none of these works raise an error
    """

    # this is already unicode. return
    if type(newstr) is unicode:
        return newstr

    encodings = ['ascii', 'utf8mb4', 'utf8', 'latin1']
    for encoding in encodings:
        try:
            if ignore:
                dec_str = newstr.decode(encoding, 'ignore')
            else:
                dec_str = newstr.decode(encoding)
            return dec_str
        except:
            pass

    raise Exception("can't decode this string at all")


def chunks_to_runs(chunks):
    runs = []
    for chunk in chunks:
        run_id = None
        host = None
        for entry in ['first', 'last']:
            if chunk.get(entry, None) is None:
                continue

            if run_id is None:
                run_id = chunk.get(entry, {}).get('run_id', None)
            if host is None:
                host = chunk.get(entry, {}).get('host', None)

        status = 'pending'
        completed_at = None
        return_code = None
        completed_event_id = None
        if chunk.get('last', {}):
            status = chunk.get('last', {}).get('status', 'pending')
            completed_at = chunk.get('last', {}).get('datetime', None)
            return_code = chunk.get('last', {}).get('return_code', None)
            completed_event_id = chunk.get('last', {}).get('id', None)

        started_at = None
        started_event_id = None
        first = chunk.get('first', None)
        if first is not None:
            started_at = chunk.get('first', {}).get('datetime', None)
            started_event_id = chunk.get('first', {}).get('id', None)

        runs.append({
            'id': run_id,
            'job_id': chunk.get('job_id'),
            'status': status,
            'completed_at': completed_at,
            'completed_event_id': completed_event_id,
            'started_at': started_at,
            'started_event_id': started_event_id,
            'return_code': return_code,
            'host': host,
        })

    return runs


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if hasattr(obj, 'isoformat'):
        serial = obj.isoformat()
        return serial
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    raise TypeError ("Type %s not serializable" % type(obj))


def query_id(args):
    _id = args.get('id', None)
    if _id is not None:
        _id = int(_id)

    return _id


def query_category_id(args):
    category_id = args.get('category.id')
    if category_id is not None:
        category_id = int(category_id)

    return category_id


def query_category_name(args):
    return args.get('category.name', None)


def query_page(args):
    page = int(args.get('page', 0))
    if page < 0:
        page = 0

    return page


def query_per_page(args):
    per_page = int(args.get('per_page', 10))
    if per_page > 100:
        per_page = 100

    return per_page

def query_sort(args, allowed_fields=None):
    field, order = args.get('sort', 'id.asc').split('.', 1)
    if not order:
        order = 'asc'

    if allowed_fields is None:
        allowed_fields = ['id', 'name']

    if field not in allowed_fields:
        field = 'id'

    return '{0}.{1}'.format(field, order)

