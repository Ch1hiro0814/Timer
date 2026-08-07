"""Background scheduler that checks reminder rules every 30 seconds."""

import threading
import time as _time
import traceback
from datetime import datetime
from typing import Callable, Optional

from utils import (
    is_workday,
    is_in_quiet_hours,
    time_matches,
    is_same_period,
    is_same_day,
    parse_time_str,
    get_work_end_time_str,
    in_last_saturday_week,
    is_last_saturday_of_month,
)
from popup import show_reminder


class ReminderScheduler:
    """Runs in a background thread, evaluating reminder rules every 30 seconds."""

    def __init__(
        self,
        config,
        root,
        log=None,
        main_call: Optional[Callable[[Callable], None]] = None,
    ):
        self._config = config
        self._root = root
        self._log = log
        self._main_call = main_call
        self._thread: Optional[threading.Thread] = None
        self._running = False
        # Track last triggered times to prevent duplicates
        # Keys: "stand_up", "water", "daily_report", "weekly_report"
        self._last_triggered: dict[str, Optional[datetime]] = {
            "stand_up": None,
            "water": None,
            "daily_report": None,
            "weekly_report": None,
        }
        self._lock = threading.Lock()

    def start(self):
        """Start the scheduler in a daemon background thread."""
        if self._running:
            return
        now = datetime.now()
        self._initialize_last_triggered(now)
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ReminderScheduler")
        self._thread.start()

    def _initialize_last_triggered(self, now: datetime):
        """Set duplicate-prevention baselines at startup.

        Health reminders use the current time so the first interval starts
        cleanly; report reminders stay unset so a report scheduled later on
        the same day can still fire.
        """
        with self._lock:
            self._last_triggered["stand_up"] = now
            self._last_triggered["water"] = now
            self._last_triggered["daily_report"] = None
            self._last_triggered["weekly_report"] = None

    def stop(self):
        """Stop the scheduler."""
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _run_loop(self):
        """Main scheduler loop — fires every 30 seconds."""
        while self._running:
            try:
                if not self._config.is_paused and not self._config.is_dnd_active:
                    self._evaluate_rules()
            except Exception:
                if self._log:
                    self._log(f"Scheduler error:\n{traceback.format_exc()}")
            _time.sleep(30)

    def _evaluate_rules(self):
        """Evaluate all reminder rules against the current time."""
        now = datetime.now()
        today = now.date()
        current_time = now.time()

        # ---- 1. Check if today is a workday ----
        if not is_workday(today):
            return

        # ---- 2. Check quiet hours (multiple periods) ----
        quiet_start = parse_time_str(self._config.general.get("quiet_hours_start", "12:00"))
        quiet_end = parse_time_str(self._config.general.get("quiet_hours_end", "14:00"))
        quiet2_start = parse_time_str(self._config.general.get("quiet_hours_2_start", "17:30"))
        quiet2_end = parse_time_str(self._config.general.get("quiet_hours_2_end", "18:00"))
        in_quiet = is_in_quiet_hours(current_time, quiet_start, quiet_end) \
            or is_in_quiet_hours(current_time, quiet2_start, quiet2_end)

        # ---- 3. Define work hours (vary by day) ----
        weekday = now.weekday()  # 0=Mon ... 6=Sun
        weekday_str = str(weekday)
        work_start = parse_time_str(self._config.general.get("work_start_time", "09:00"))
        if is_last_saturday_of_month(today):
            work_end = parse_time_str(self._config.general.get("work_end_time_saturday", "18:30"))
        else:
            work_end = parse_time_str(get_work_end_time_str(self._config.general, weekday))

        # Collect reminders to show (batch them in case of coincidence)
        reminders_to_show: list[tuple[str, str]] = []

        # ---- Health reminders (only during work hours, not in quiet hours) ----
        if not in_quiet and work_start <= current_time <= work_end:
            # Stand-up reminder: configurable interval
            if self._config.stand_up_config.get("enabled", True):
                interval = self._config.stand_up_config.get("interval_minutes", 60)
                if not self._was_triggered_this_period("stand_up", now, interval):
                    reminders_to_show.append((
                        "⏰ 起立放松",
                        self._config.stand_up_config.get(
                            "message", "该站起来活动一下啦！\n伸个懒腰，走动走动吧~ 🏃"
                        ),
                    ))
                    self._mark_triggered("stand_up", now)

            # Water reminder: configurable interval
            if self._config.water_config.get("enabled", True):
                interval = self._config.water_config.get("interval_minutes", 30)
                if not self._was_triggered_this_period("water", now, interval):
                    reminders_to_show.append((
                        "💧 喝水提醒",
                        self._config.water_config.get(
                            "message", "该喝水了！\n补充水分，保持健康~ 💧"
                        ),
                    ))
                    self._mark_triggered("water", now)

        # ---- Report reminders ----
        last_sat_week = in_last_saturday_week(today)

        # Determine what kind of report today deserves
        daily_day = weekday_str in self._config.daily_report_config.get("schedule", {})
        weekly_day = weekday_str in self._config.weekly_report_config.get("schedule", {})

        # In the week containing the last Saturday:
        #   Friday  → daily report (not weekly)
        #   Saturday → weekly report
        if last_sat_week:
            if weekday == 4:  # Friday
                weekly_day = False
                daily_day = True
            elif weekday == 5 and is_last_saturday_of_month(today):  # Last Saturday
                daily_day = False
                weekly_day = True

        # Daily report
        if self._config.daily_report_config.get("enabled", True) and daily_day:
            schedule = self._config.daily_report_config.get("schedule", {})
            if weekday_str in schedule:
                entry = schedule[weekday_str]
                target_time = parse_time_str(entry["time"])
            else:
                # Use Friday 17:00 for last-Saturday-week daily report
                daily_msg = self._config.daily_report_config.get(
                    "schedule", {}
                ).get("0", {}).get(
                    "message",
                    "该写日报了！\n回顾今天的工作内容，记录成果~ 📝",
                )
                target_time = parse_time_str("17:00")
                entry = {"message": daily_msg}
            if time_matches(current_time, target_time):
                if not self._was_triggered_today("daily_report", now):
                    reminders_to_show.append((
                        "📝 日报提醒",
                        entry.get("message", "该写日报了！\n回顾今天的工作内容，记录成果~ 📝"),
                    ))
                    self._mark_triggered("daily_report", now)

        # Weekly report
        if self._config.weekly_report_config.get("enabled", True) and weekly_day:
            schedule = self._config.weekly_report_config.get("schedule", {})
            if weekday_str in schedule:
                entry = schedule[weekday_str]
                target_time = parse_time_str(entry["time"])
            else:
                # Use Friday's weekly schedule time for Saturday
                friday_entry = schedule.get("4", {})
                target_time = parse_time_str(friday_entry.get("time", "17:00"))
                entry = friday_entry
            msg = entry.get("message", "该写周报了！\n总结本周工作，规划下周计划~ 📊")
            if weekday == 5:  # Saturday weekly → 18:00
                saturday_entry = schedule.get("5", {})
                target_time = parse_time_str(saturday_entry.get("time", "18:00"))
                msg = saturday_entry.get(
                    "message",
                    "该写周报了！\n今天是本月最后一个工作日，总结本周工作吧~ 📊",
                )
            if time_matches(current_time, target_time):
                if not self._was_triggered_today("weekly_report", now):
                    reminders_to_show.append(("📊 周报提醒", msg))
                    self._mark_triggered("weekly_report", now)

        # ---- Show reminders ----
        if reminders_to_show:
            auto_dismiss = self._config.general.get("auto_dismiss_seconds", 30)

            if len(reminders_to_show) == 1:
                title, message = reminders_to_show[0]
                show_reminder(
                    self._root, title, message, auto_dismiss,
                    schedule=self._main_call,
                )
            else:
                # Combine multiple reminders into one popup
                titles = [r[0] for r in reminders_to_show]
                messages = [r[1] for r in reminders_to_show]
                combined_title = " · ".join(titles)
                combined_message = "\n\n".join(
                    f"【{t.split(' ', 1)[1] if ' ' in t else t}】\n{m}"
                    for t, m in reminders_to_show
                )
                show_reminder(
                    self._root, combined_title, combined_message, auto_dismiss,
                    schedule=self._main_call,
                )

    # ---- Duplicate prevention helpers (thread-safe) ----

    def _was_triggered_this_period(self, key: str, now: datetime, period_min: int) -> bool:
        """Check if this reminder was already triggered in the current period block."""
        with self._lock:
            last = self._last_triggered.get(key)
            if last is None:
                return False
            return is_same_period(last, now, period_min)

    def _was_triggered_today(self, key: str, now: datetime) -> bool:
        """Check if this reminder was already triggered today."""
        with self._lock:
            last = self._last_triggered.get(key)
            if last is None:
                return False
            return is_same_day(last, now)

    def _mark_triggered(self, key: str, now: datetime):
        """Record that a reminder was just triggered."""
        with self._lock:
            self._last_triggered[key] = now

    def reset_triggered(self):
        """Reset all last-triggered timestamps (useful after unpausing)."""
        with self._lock:
            for key in self._last_triggered:
                self._last_triggered[key] = None
