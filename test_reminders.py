import datetime as dt
import unittest

import scheduler as sched
import tray_manager as tray
from utils import get_work_end_time_str, is_in_quiet_hours, parse_time_str


class StubConfig:
    def __init__(self, health_enabled=True):
        self.data = {
            "general": {
                "work_start_time": "09:00",
                "work_end_time": "20:30",
                "work_end_time_early": "17:30",
                "work_end_time_mon": "20:30",
                "work_end_time_tue": "20:30",
                "work_end_time_wed": "17:30",
                "work_end_time_thu": "20:30",
                "work_end_time_fri": "17:30",
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
                    "4": {"time": "17:00", "message": "daily"},
                },
            },
            "weekly_report": {
                "enabled": True,
                "schedule": {
                    "4": {"time": "17:00", "message": "weekly"},
                    "5": {"time": "18:00", "message": "weekly-sat"},
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
        self._evaluate_with_config(StubConfig(health_enabled=health_enabled), when)

    def _evaluate_with_config(self, config, when):
        FakeDateTime.now_value = when
        scheduler = sched.ReminderScheduler(
            config,
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

    def test_special_report_times_are_configurable(self):
        config = StubConfig(health_enabled=False)
        config.data["daily_report"]["schedule"]["4"]["time"] = "16:30"
        config.data["weekly_report"]["schedule"]["5"]["time"] = "19:00"

        self._evaluate_with_config(
            config,
            dt.datetime(2026, 8, 28, 16, 30, 0),
        )
        self.assertEqual(self.captured[-1][1], "daily")

        self._evaluate_with_config(
            config,
            dt.datetime(2026, 8, 29, 19, 0, 0),
        )
        self.assertEqual(self.captured[-1][1], "weekly-sat")

    def test_start_does_not_suppress_weekly_report_later_same_day(self):
        scheduler = sched.ReminderScheduler(
            StubConfig(health_enabled=False),
            None,
            main_call=lambda fn: None,
        )
        FakeDateTime.now_value = dt.datetime(2026, 8, 7, 9, 0, 0)
        scheduler._initialize_last_triggered(FakeDateTime.now_value)

        FakeDateTime.now_value = dt.datetime(2026, 8, 7, 17, 0, 0)
        scheduler._evaluate_rules()

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

    def test_work_end_times_are_independent(self):
        config = StubConfig()
        config.data["general"].update({
            "work_end_time_mon": "20:00",
            "work_end_time_tue": "19:00",
            "work_end_time_wed": "16:00",
            "work_end_time_thu": "19:30",
            "work_end_time_fri": "18:00",
        })
        manager = tray.TrayManager(None, config, None)
        cases = [
            (dt.date(2026, 8, 3), "20:00"),
            (dt.date(2026, 8, 4), "19:00"),
            (dt.date(2026, 8, 5), "16:00"),
            (dt.date(2026, 8, 6), "19:30"),
            (dt.date(2026, 8, 7), "18:00"),
        ]
        for day, expected in cases:
            FakeDate.today_value = day
            self.assertEqual(
                manager._get_work_end_for_today().strftime("%H:%M"),
                expected,
            )

    def test_work_end_time_falls_back_to_legacy_key(self):
        config = StubConfig()
        config.data["general"].pop("work_end_time_wed")
        self.assertEqual(
            get_work_end_time_str(config.data["general"], 2),
            "17:30",
        )


if __name__ == "__main__":
    unittest.main()
