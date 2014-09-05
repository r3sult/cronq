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
