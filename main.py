"""Timer Reminder Application - Entry Point.

Architecture:
  - Main thread: tkinter mainloop (popups, settings windows, event processing)
  - Background daemon thread: pystray system tray icon
  - Background daemon thread: reminder scheduler

This ensures tkinter UI is always responsive since it has its own dedicated event loop.
"""

import tkinter as tk
import sys
import os
import threading
import traceback
from datetime import datetime
from pathlib import Path


def _get_log_path() -> Path:
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    log_dir = app_data / "TimerReminder"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


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

        # ---- Scheduler ----
        log("Starting scheduler...")
        from scheduler import ReminderScheduler
        scheduler = ReminderScheduler(config, root)
        scheduler.start()
        log("Scheduler started OK")

        # ---- Settings callback ----
        from settings_window import SettingsWindow

        def open_settings():
            # Schedule on main thread — tkinter widgets must be created
            # on the main thread, but pystray menu callbacks fire on tray thread.
            def _do():
                try:
                    settings = SettingsWindow(root, config, on_save_callback=lambda: None)
                    settings.show()
                except Exception as e:
                    log(f"Error opening settings: {e}")
            root.after(0, _do)

        # ---- Tray in background thread ----
        # On Windows, pystray works fine from a daemon thread.
        # Keeping it off the main thread lets tkinter's mainloop process
        # UI events smoothly (popups, settings windows).
        log("Starting tray thread...")
        from tray_manager import TrayManager
        tray = TrayManager(root, config, scheduler, on_settings=open_settings)

        tray_thread = threading.Thread(
            target=_run_tray, args=(tray, log),
            daemon=True, name="TrayThread",
        )
        tray_thread.start()
        log("Tray thread started OK")

        # ---- Mainloop on main thread ----
        # tkinter needs its event loop running to process:
        #   - Popup creation/destruction
        #   - Settings window interactions
        #   - Countdown timers (root.after callbacks)
        #   - Tray menu auto-refresh
        log("Running tkinter mainloop...")

        def poll_tray():
            """Periodic check if tray is still alive."""
            if tray_thread.is_alive():
                root.after(2000, poll_tray)
            else:
                log("Tray thread died, shutting down...")
                scheduler.stop()
                root.destroy()

        root.after(2000, poll_tray)
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
    """Run pystray icon in a background thread."""
    try:
        tray.run()
    except Exception as e:
        log(f"Tray thread error: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
