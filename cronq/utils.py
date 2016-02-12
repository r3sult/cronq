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
