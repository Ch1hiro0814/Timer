"""Configuration management for Timer Reminder."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def _get_app_data_dir() -> Path:
    """Get the application data directory. Creates it if it doesn't exist."""
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    config_dir = app_data / "TimerReminder"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_bundled_config_path() -> Optional[Path]:
    """Get the path to the bundled config.json (works both in dev and PyInstaller bundle)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base = Path(sys._MEIPASS)
    else:
        # Running as script
        base = Path(__file__).parent
    config_path = base / "config.json"
    return config_path if config_path.exists() else None


class ConfigManager:
    """Manages application configuration with JSON persistence."""

    def __init__(self):
        self._data: dict = {}
        self._user_config_path = _get_app_data_dir() / "config.json"
        self.load()

    def load(self):
        """Load configuration from user config file, falling back to bundled default."""
        if self._user_config_path.exists():
            try:
                with open(self._user_config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                return
            except (json.JSONDecodeError, IOError):
                pass  # Fall through to default

        # Load bundled default
        bundled = _get_bundled_config_path()
        if bundled:
            with open(bundled, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = self._default_config()

        # Save a copy to user config dir
        self.save()

    def save(self):
        """Persist current configuration to user config file."""
        self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._user_config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _default_config() -> dict:
        """Return a hardcoded default config (fallback if config.json is missing)."""
        return {
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
                "language": "zh",
            },
            "stand_up": {
                "enabled": True,
                "interval_minutes": 60,
                "message": "该站起来活动一下啦！\n伸个懒腰，走动走动吧~ 🏃",
            },
            "water": {
                "enabled": True,
                "interval_minutes": 30,
                "message": "该喝水了！\n补充水分，保持健康~ 💧",
            },
            "daily_report": {
                "enabled": True,
                "schedule": {
                    "0": {"time": "20:00", "message": "该写日报了！\n回顾今天的工作内容，记录成果~ 📝"},
                    "1": {"time": "20:00", "message": "该写日报了！\n回顾今天的工作内容，记录成果~ 📝"},
                    "2": {"time": "17:00", "message": "该写日报了！\n回顾今天的工作内容，记录成果~ 📝"},
                    "3": {"time": "20:00", "message": "该写日报了！\n回顾今天的工作内容，记录成果~ 📝"},
                },
            },
            "weekly_report": {
                "enabled": True,
                "schedule": {
                    "4": {"time": "17:00", "message": "该写周报了！\n总结本周工作，规划下周计划~ 📊"},
                },
            },
        }

    # ---- Convenience accessors ----

    @property
    def data(self) -> dict:
        return self._data

    def get(self, *keys: str, default=None):
        """Get a nested config value like config.get('general', 'work_start_time')."""
        node = self._data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, *keys: str, value):
        """Set a nested config value and auto-save."""
        node = self._data
        for key in keys[:-1]:
            if key not in node:
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value
        self.save()

    @property
    def general(self) -> dict:
        return self._data.get("general", {})

    @property
    def stand_up_config(self) -> dict:
        return self._data.get("stand_up", {})

    @property
    def water_config(self) -> dict:
        return self._data.get("water", {})

    @property
    def daily_report_config(self) -> dict:
        return self._data.get("daily_report", {})

    @property
    def weekly_report_config(self) -> dict:
        return self._data.get("weekly_report", {})

    @property
    def is_paused(self) -> bool:
        return self._data.get("_paused", False)

    @is_paused.setter
    def is_paused(self, value: bool):
        self._data["_paused"] = value
        self.save()

    # ---- Do Not Disturb (免打扰) ----

    @property
    def dnd_until(self) -> Optional[datetime]:
        """Return the DND expiration datetime, or None if DND is not active."""
        raw = self._data.get("_dnd_until")
        if raw is None:
            return None
        try:
            return datetime.fromisoformat(raw)
        except (ValueError, TypeError):
            return None

    @dnd_until.setter
    def dnd_until(self, value: Optional[datetime]):
        """Set DND expiration datetime. Set to None to cancel DND."""
        if value is None:
            self._data.pop("_dnd_until", None)
        else:
            self._data["_dnd_until"] = value.isoformat()
        self.save()

    @property
    def is_dnd_active(self) -> bool:
        """Check if Do Not Disturb mode is currently active (not expired)."""
        until = self.dnd_until
        if until is None:
            return False
        if datetime.now() >= until:
            # DND has expired — auto-clear
            self.dnd_until = None
            return False
        return True
