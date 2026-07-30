"""Utility functions for date/time calculations and schedule matching."""

import ctypes
import ctypes.wintypes
from datetime import date, time, datetime, timedelta


def is_last_saturday_of_month(d: date) -> bool:
    """Check if the given date is the last Saturday of its month."""
    if d.weekday() != 5:
        return False
    next_saturday = d + timedelta(days=7)
    return next_saturday.month != d.month


def is_workday(d: date) -> bool:
    """
    Check if the given date counts as a workday for reminders.
    True for Mon–Fri (0–4), plus the last Saturday of the month.
    """
    if d.weekday() < 5:
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
    """
    t_minutes = t.hour * 60 + t.minute
    target_minutes = target.hour * 60 + target.minute
    diff = abs(t_minutes - target_minutes)
    tolerance_minutes = tolerance_seconds / 60.0
    return diff < tolerance_minutes


def is_same_period(dt1: datetime, dt2: datetime, period_minutes: int) -> bool:
    """Check if two datetimes fall within the same period block."""
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


def get_last_saturday_of_month(year: int, month: int) -> date:
    """Return the date of the last Saturday in the given month."""
    if month == 12:
        first_of_next = date(year + 1, 1, 1)
    else:
        first_of_next = date(year, month + 1, 1)
    last_day = first_of_next - timedelta(days=1)
    days_from_sat = (last_day.weekday() - 5) % 7
    return last_day - timedelta(days=days_from_sat)


def in_last_saturday_week(today: date) -> bool:
    """Check if today belongs to the week that contains the last Saturday of the month."""
    last_sat = get_last_saturday_of_month(today.year, today.month)
    monday_of_week = today - timedelta(days=today.weekday())
    last_sat_monday = last_sat - timedelta(days=last_sat.weekday())
    return monday_of_week == last_sat_monday


def get_day_name_cn(weekday: int) -> str:
    """Return Chinese day name for a weekday index (0=Monday, 6=Sunday)."""
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[weekday]


# ---- Single-instance lock (Windows named mutex) ----

_MUTEX_NAME = "Global\\TimerReminderApp_SingleInstance"


def acquire_single_instance_lock() -> bool:
    """
    Try to acquire a named Windows mutex. Returns True if this is the
    first instance, False if another instance is already running.
    """
    kernel32 = ctypes.windll.kernel32
    CreateMutexW = kernel32.CreateMutexW
    CreateMutexW.argtypes = [ctypes.wintypes.LPVOID, ctypes.wintypes.BOOL, ctypes.wintypes.LPCWSTR]
    CreateMutexW.restype = ctypes.wintypes.HANDLE

    GetLastError = kernel32.GetLastError
    ERROR_ALREADY_EXISTS = 183

    handle = CreateMutexW(None, True, _MUTEX_NAME)
    if GetLastError() == ERROR_ALREADY_EXISTS:
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
        return False
    return True
