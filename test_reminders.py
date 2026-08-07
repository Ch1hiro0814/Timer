import datetime as dt
import unittest

import scheduler as sched
import tray_manager as tray
from utils import is_in_quiet_hours, parse_time_str


class StubConfig:
    def __init__(self, health_enabled=True):
        self.data = {
            "general": {
                "work_start_time": "09:00",
                "work_end_time": "20:30",
                "work_end_time_early": "17:30",
                "work_end_time_saturday": "18:30",
                "quiet_hours_start": "12:00",
                "quiet_hours_end": "14:00",
                "quiet_hours_2_start": "17:30",
                "quiet_hours_2_end": "18:00",
                "auto_dismiss_seconds": 30,
            },
            "stand_up": {
                "enabled": health_enabled,
                "interval_minutes": 60,
                "message": "stand",
            },
            "water": {
                "enabled": health_enabled,
                "interval_minutes": 30,
                "message": "water",
            },
            "daily_report": {
                "enabled": True,
                "schedule": {
                    "0": {"time": "20:00", "message": "daily"},
                    "1": {"time": "20:00", "message": "daily"},
                    "2": {"time": "17:00", "message": "daily"},
                    "3": {"time": "20:00", "message": "daily"},
                },
            },
            "weekly_report": {
                "enabled": True,
                "schedule": {
                    "4": {"time": "17:00", "message": "weekly"},
                },
            },
        }

    @property
    def general(self):
        return self.data["general"]

    @property
    def stand_up_config(self):
        return self.data["stand_up"]

    @property
    def water_config(self):
        return self.data["water"]

    @property
    def daily_report_config(self):
        return self.data["daily_report"]

    @property
    def weekly_report_config(self):
        return self.data["weekly_report"]

    @property
    def is_paused(self):
        return False

    @property
    def is_dnd_active(self):
        return False


class FakeDateTime(dt.datetime):
    now_value = None

    @classmethod
    def now(cls, tz=None):
        return cls.now_value


class FakeDate(dt.date):
    today_value = None

    @classmethod
    def today(cls):
        return cls.today_value


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.orig_sched_datetime = sched.datetime
        self.orig_show_reminder = sched.show_reminder
        self.orig_tray_date = tray.date
        self.captured = []

        sched.datetime = FakeDateTime
        sched.show_reminder = self._capture_show
        tray.date = FakeDate

    def tearDown(self):
        sched.datetime = self.orig_sched_datetime
        sched.show_reminder = self.orig_show_reminder
        tray.date = self.orig_tray_date

    def _capture_show(self, root, title, message, auto_dismiss=30, schedule=None):
        self.captured.append((title, message))

    def _evaluate(self, when, health_enabled=False):
        FakeDateTime.now_value = when
        scheduler = sched.ReminderScheduler(
            StubConfig(health_enabled=health_enabled),
            None,
            main_call=lambda fn: None,
        )
        scheduler._last_triggered = {key: None for key in scheduler._last_triggered}
        scheduler._evaluate_rules()

    def test_normal_workday_schedules_without_error(self):
        self._evaluate(dt.datetime(2026, 8, 5, 10, 0, 0), health_enabled=True)
        self.assertTrue(self.captured)

    def test_last_saturday_week_friday_uses_daily_message(self):
        self._evaluate(dt.datetime(2026, 8, 28, 17, 0, 0))
        self.assertEqual(len(self.captured), 1)
        self.assertEqual(self.captured[0][1], "daily")

    def test_last_saturday_schedules_weekly_report(self):
        self._evaluate(dt.datetime(2026, 8, 29, 18, 0, 0))
        self.assertEqual(len(self.captured), 1)
        self.assertIn("周报", self.captured[0][0])

    def test_overnight_quiet_hours(self):
        self.assertTrue(
            is_in_quiet_hours(
                parse_time_str("23:00"),
                parse_time_str("22:00"),
                parse_time_str("08:00"),
            )
        )
        self.assertFalse(
            is_in_quiet_hours(
                parse_time_str("09:00"),
                parse_time_str("22:00"),
                parse_time_str("08:00"),
            )
        )

    def test_tray_work_end_follows_weekday(self):
        manager = tray.TrayManager(None, StubConfig(), None)
        cases = [
            (dt.date(2026, 8, 4), "20:30"),
            (dt.date(2026, 8, 5), "17:30"),
            (dt.date(2026, 8, 7), "17:30"),
            (dt.date(2026, 8, 29), "18:30"),
        ]
        for day, expected in cases:
            FakeDate.today_value = day
            self.assertEqual(
                manager._get_work_end_for_today().strftime("%H:%M"),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
