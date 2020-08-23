# encoding=utf-8

__all__ = ["date_now"]

from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time


def date_now():
    now = datetime.now()
    stamp = mktime(now.timetuple())
    return format_date_time(stamp)
