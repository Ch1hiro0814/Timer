"""Embedded web settings window backed by a local Flask server."""

import secrets
import multiprocessing
import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from utils import parse_time_str


def _get_web_ui_dir() -> Path:
    """Resolve the web UI directory in both dev and PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / "web_ui"


def _run_webview(port: int, token: str):
    """Run the settings window in a native PyWebView process."""
    import webview

    url = f"http://127.0.0.1:{port}/?token={token}"
    window = webview.create_window(
        "定时提醒 - 设置",
        url,
        width=580,
        height=600,
        min_size=(500, 480),
    )
    webview.start()


class SettingsWindow:
    """Serve the settings page locally and show it in an embedded web window."""

    def __init__(self, root, config, on_save_callback=None):
        self._config = config
        self._on_save_callback = on_save_callback
        self._server = None
        self._thread = None
        self._port = None
        self._webview_process = None
        self._token = secrets.token_urlsafe(16)
        self._app = self._create_app()

    def _create_app(self):
        app = Flask(__name__)
        web_ui = _get_web_ui_dir()

        def _authorized():
            header = request.headers.get("X-Auth-Token", "")
            query = request.args.get("token", "")
            return header == self._token or query == self._token

        @app.get("/")
        def index():
            if not _authorized():
                return "Forbidden", 403
            return send_from_directory(web_ui, "index.html")

        @app.get("/api/config")
        def get_config():
            if not _authorized():
                return jsonify({"message": "Forbidden"}), 403
            return jsonify(self._config.data)

        @app.post("/api/config")
        def save_config():
            if not _authorized():
                return jsonify({"message": "Forbidden"}), 403
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({"message": "配置格式错误"}), 400
            try:
                self._apply_config(data)
            except ValueError as e:
                return jsonify({"message": str(e)}), 400
            if self._on_save_callback:
                self._on_save_callback()
            return jsonify({"ok": True})

        return app

    def show(self):
        if self._server is None:
            self._server = make_server("127.0.0.1", 0, self._app, threaded=True)
            self._port = self._server.server_port
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name="WebSettings",
            )
            self._thread.start()
        if self._webview_process is None or not self._webview_process.is_alive():
            self._webview_process = multiprocessing.Process(
                target=_run_webview,
                args=(self._port, self._token),
                daemon=True,
            )
            self._webview_process.start()

    def _apply_config(self, data: dict):
        general = data.get("general") or {}
        stand_up = data.get("stand_up") or {}
        water = data.get("water") or {}
        daily_report = data.get("daily_report") or {}
        weekly_report = data.get("weekly_report") or {}

        time_fields = [
            ("work_start_time", "工作开始时间"),
            ("work_end_time_mon", "周一结束时间"),
            ("work_end_time_tue", "周二结束时间"),
            ("work_end_time_wed", "周三结束时间"),
            ("work_end_time_thu", "周四结束时间"),
            ("work_end_time_fri", "周五结束时间"),
            ("work_end_time_saturday", "月末周六结束时间"),
            ("quiet_hours_start", "午休免打扰开始"),
            ("quiet_hours_end", "午休免打扰结束"),
            ("quiet_hours_2_start", "晚餐免打扰开始"),
            ("quiet_hours_2_end", "晚餐免打扰结束"),
        ]
        for key, name in time_fields:
            self._validate_time(general.get(key), name)

        start = parse_time_str(general.get("work_start_time"))
        for key in [
            "work_end_time_mon",
            "work_end_time_tue",
            "work_end_time_wed",
            "work_end_time_thu",
            "work_end_time_fri",
            "work_end_time_saturday",
        ]:
            if parse_time_str(general.get(key)) <= start:
                raise ValueError(f"{key} 必须晚于工作开始时间")

        for day, name in [
            ("0", "日报 周一"),
            ("1", "日报 周二"),
            ("2", "日报 周三"),
            ("3", "日报 周四"),
            ("4", "日报 周五"),
        ]:
            entry = (daily_report.get("schedule") or {}).get(day, {})
            self._validate_time(entry.get("time"), name)

        for day, name in [("4", "周报 周五"), ("5", "周报 周六")]:
            entry = (weekly_report.get("schedule") or {}).get(day, {})
            self._validate_time(entry.get("time"), name)

        try:
            stand_interval = int(stand_up.get("interval_minutes", 60))
            water_interval = int(water.get("interval_minutes", 30))
        except (TypeError, ValueError):
            raise ValueError("提醒间隔必须是数字")
        if stand_interval < 1 or water_interval < 1:
            raise ValueError("提醒间隔必须大于 0 分钟")

        try:
            auto_dismiss = int(general.get("auto_dismiss_seconds", 30))
        except (TypeError, ValueError):
            raise ValueError("自动关闭秒数必须是数字")
        if auto_dismiss < 0:
            raise ValueError("自动关闭秒数不能为负数")

        cfg = self._config.data
        cfg["general"] = {**cfg.get("general", {}), **general}
        cfg["stand_up"] = {**cfg.get("stand_up", {}), **stand_up}
        cfg["water"] = {**cfg.get("water", {}), **water}

        daily_cfg = cfg.setdefault("daily_report", {})
        daily_cfg["enabled"] = daily_report.get("enabled", True)
        daily_schedule = daily_cfg.setdefault("schedule", {})
        for day, entry in (daily_report.get("schedule") or {}).items():
            target = daily_schedule.setdefault(day, {})
            target["time"] = entry["time"]
            target["message"] = entry["message"]

        weekly_cfg = cfg.setdefault("weekly_report", {})
        weekly_cfg["enabled"] = weekly_report.get("enabled", True)
        weekly_schedule = weekly_cfg.setdefault("schedule", {})
        for day, entry in (weekly_report.get("schedule") or {}).items():
            target = weekly_schedule.setdefault(day, {})
            target["time"] = entry["time"]
            if "message" in entry:
                target["message"] = entry["message"]

        self._config.save()

    @staticmethod
    def _validate_time(value, name):
        try:
            parse_time_str(value)
        except (TypeError, ValueError, IndexError, AttributeError):
            raise ValueError(f"{name}格式错误，请使用 HH:MM")
