from datetime import datetime

def days_between(d1, d2):
    delta = d2 - d1
    return abs(delta.days)

def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def human_readable_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"
from datetime import timedelta

def next_day(date):
    return date + timedelta(days=1)

def previous_day(date):
    return date - timedelta(days=1)

def is_weekend(date):
    return date.weekday() >=5

def days_until(date):
    from datetime import datetime
    return (date - datetime.now().date()).days
