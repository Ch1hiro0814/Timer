"""Utility functions for date/time calculations and schedule matching."""

from datetime import date, time, datetime, timedelta


def is_last_saturday_of_month(d: date) -> bool:
    """Check if the given date is the last Saturday of its month."""
    if d.weekday() != 5:  # 5 = Saturday
        return False
    # The next Saturday would fall in the next month
    next_saturday = d + timedelta(days=7)
    return next_saturday.month != d.month


def is_workday(d: date) -> bool:
    """
    Check if the given date counts as a workday for reminders.
    True for Mon–Fri (0–4), plus the last Saturday of the month.
    """
    if d.weekday() < 5:  # Monday (0) through Friday (4)
        return True
    if d.weekday() == 5 and is_last_saturday_of_month(d):
        return True
    return False


def is_in_quiet_hours(t: time, quiet_start: time, quiet_end: time) -> bool:
    """Check if the given time falls within the quiet hours range (inclusive start, exclusive end)."""
    return quiet_start <= t < quiet_end


def time_matches(t: time, target: time, tolerance_seconds: int = 30) -> bool:
    """
    Check if a time matches a target time within a tolerance window.
    Converts both to minutes since midnight for easy comparison.
    """
    t_minutes = t.hour * 60 + t.minute
    target_minutes = target.hour * 60 + target.minute
    diff = abs(t_minutes - target_minutes)
    # tolerance in minutes
    tolerance_minutes = tolerance_seconds / 60.0
    return diff < tolerance_minutes


def is_same_hour(dt1: datetime, dt2: datetime) -> bool:
    """Check if two datetimes are in the same clock hour (same day, same hour)."""
    return dt1.date() == dt2.date() and dt1.hour == dt2.hour


def is_same_period(dt1: datetime, dt2: datetime, period_minutes: int) -> bool:
    """Check if two datetimes fall within the same period block (e.g., same 30-min block)."""
    if dt1.date() != dt2.date():
        return False
    block1 = (dt1.hour * 60 + dt1.minute) // period_minutes
    block2 = (dt2.hour * 60 + dt2.minute) // period_minutes
    return block1 == block2


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    """Check if two datetimes are on the same calendar day."""
    return dt1.date() == dt2.date()


def parse_time_str(time_str: str) -> time:
    """Parse a 'HH:MM' string into a time object."""
    parts = time_str.strip().split(":")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def get_day_name_cn(weekday: int) -> str:
    """Return Chinese day name for a weekday index (0=Monday, 6=Sunday)."""
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[weekday]
