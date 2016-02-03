# -*- coding: utf-8 -*-
import datetime

import aniso8601


def next_run_and_duration_from_8601(interval):
    gen = aniso8601.parse_repeating_interval(interval)
    start = next(gen)
    second = next(gen)
    duration = second - start
    now = datetime.datetime.utcnow()
    diff_from_now = now - start
    number_of_iterations = number_of_iterations_in_time(
        duration,
        diff_from_now)
    next_run = apply_delta_to_datetime(
        duration,
        start,
        number_of_iterations + 1)
    return next_run, duration


def number_of_iterations_in_time(duration, time):
    """Return the number of times full duration is in time"""
    return int(time.total_seconds() / duration.total_seconds())


def apply_delta_to_datetime(delta, dt, times):
    full_td = delta * times
    final_dt = dt + full_td
    return final_dt
