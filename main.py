"""Timer Reminder Application - Entry Point.

Architecture:
  - Main thread: tkinter mainloop (popups, settings windows, event processing)
  - Background daemon thread: pystray system tray icon
  - Background daemon thread: reminder scheduler

Single-instance: second launch writes a signal file; first instance detects it
and brings the settings window to front.
"""

import tkinter as tk
import sys
import os
import queue
import threading
import traceback
from datetime import datetime
from pathlib import Path


def _get_app_dir() -> Path:
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    d = app_data / "TimerReminder"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_log_path() -> Path:
    return _get_app_dir() / "app.log"


def _setup_logging():
    log_path = _get_log_path()

    def log(msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def excepthook(exc_type, exc_value, exc_tb):
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        log(f"UNHANDLED ERROR: {''.join(tb_lines)}")
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = excepthook
    log("=" * 50)
    log("App starting")
    return log


def main():
    log = _setup_logging()
    signal_path = _get_app_dir() / "show.signal"

    # ---- Single-instance check ----
    from utils import acquire_single_instance_lock
    if not acquire_single_instance_lock():
        # Another instance is running — signal it to show the window
        try:
            signal_path.write_text("show")
        except Exception:
            pass
        log("Another instance is running — sent show signal, exiting")
        return

    # Clean up any stale signal file from previous runs
    try:
        signal_path.unlink(missing_ok=True)
    except Exception:
        pass

    try:
        # ---- Config ----
        log("Loading config...")
        from config import ConfigManager
        config = ConfigManager()
        log("Config loaded OK")

        # ---- Tkinter root ----
        log("Creating tk root...")
        root = tk.Tk()
        root.withdraw()
        root.title("定时提醒助手")
        log("Tk root created OK")

        # ---- Main-thread task queue for background threads ----
        call_queue = queue.Queue()

        def call_on_main(fn):
            call_queue.put(fn)

        def drain_main_queue():
            try:
                while True:
                    fn = call_queue.get_nowait()
                    try:
                        fn()
                    except Exception as e:
                        log(f"Main queue callback error: {e}\n{traceback.format_exc()}")
            except queue.Empty:
                pass
            root.after(100, drain_main_queue)

        root.after(100, drain_main_queue)

        # ---- Scheduler ----
        log("Starting scheduler...")
        from scheduler import ReminderScheduler
        scheduler = ReminderScheduler(config, root, log=log, main_call=call_on_main)
        scheduler.start()
        log("Scheduler started OK")

        # ---- Settings (singleton) ----
        from settings_window import SettingsWindow
        settings = SettingsWindow(root, config, on_save_callback=lambda: None)

        def open_settings():
            def _do():
                try:
                    settings.show()
                except Exception as e:
                    log(f"Error opening settings: {e}")
            call_on_main(_do)

        # ---- Tray in background thread ----
        log("Starting tray thread...")
        from tray_manager import TrayManager
        tray = TrayManager(root, config, scheduler, on_settings=open_settings)
        tray.start_menu_refresh()

        tray_thread = threading.Thread(
            target=_run_tray, args=(tray, log),
            daemon=True, name="TrayThread",
        )
        tray_thread.start()
        log("Tray thread started OK")

        # ---- Show settings on startup (after a short delay so tray is ready) ----
        root.after(800, open_settings)

        # ---- Poll for "show" signal from second instances ----
        def poll_signal():
            try:
                if signal_path.exists():
                    signal_path.unlink()
                    open_settings()
            except Exception:
                pass
            root.after(2000, poll_signal)

        root.after(2000, poll_signal)

        # ---- Poll tray thread health ----
        def poll_tray():
            if tray_thread.is_alive():
                root.after(2000, poll_tray)
            else:
                log("Tray thread died, shutting down...")
                scheduler.stop()
                root.destroy()

        root.after(3000, poll_tray)
        log("Running tkinter mainloop...")
        root.mainloop()

    except Exception as e:
        log(f"FATAL startup error: {e}\n{traceback.format_exc()}")
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "启动失败",
                f"定时提醒助手启动失败：\n\n{e}\n\n"
                f"详细日志请查看：\n{_get_log_path()}"
            )
        except Exception:
            pass

    log("App exited")


def _run_tray(tray, log):
    try:
        tray.run()
    except Exception as e:
        log(f"Tray thread error: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
