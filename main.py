"""Timer Reminder Application - Entry Point.

A Windows desktop app that provides periodic health reminders (stand up, drink water)
during work hours and report-writing reminders on specific weekdays.
"""

import tkinter as tk
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path


def _get_log_path() -> Path:
    """Get the path to the log file in the app data directory."""
    app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    log_dir = app_data / "TimerReminder"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def _setup_logging():
    """Redirect unhandled exceptions to a log file."""
    log_path = _get_log_path()

    def log(msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass  # Can't write to log — nothing we can do

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
        log("Loading config...")
        from config import ConfigManager
        config = ConfigManager()
        log("Config loaded OK")

        log("Creating tk root...")
        root = tk.Tk()
        root.withdraw()
        root.title("定时提醒助手")
        log("Tk root created OK")

        log("Starting scheduler...")
        from scheduler import ReminderScheduler
        scheduler = ReminderScheduler(config, root)
        scheduler.start()
        log("Scheduler started OK")

        log("Setting up tray...")
        from tray_manager import TrayManager
        from settings_window import SettingsWindow

        def open_settings():
            try:
                settings = SettingsWindow(root, config, on_save_callback=lambda: None)
                settings.show()
            except Exception as e:
                log(f"Error opening settings: {e}")

        # Wrap in root.after because pystray callbacks run on a background thread,
        # and tkinter widget creation MUST happen on the main thread.
        def open_settings_safe():
            root.after(0, open_settings)

        tray = TrayManager(root, config, scheduler, on_settings=open_settings_safe)
        log("Tray created OK")

        def on_closing():
            log("Shutting down...")
            scheduler.stop()
            try:
                root.destroy()
            except Exception:
                pass

        root.protocol("WM_DELETE_WINDOW", on_closing)

        log("Running tray (main loop)...")
        try:
            tray.run()
        except KeyboardInterrupt:
            log("Keyboard interrupt")
        except Exception as e:
            log(f"Tray run error: {e}\n{traceback.format_exc()}")
        finally:
            log("Cleanup...")
            scheduler.stop()
            try:
                root.destroy()
            except Exception:
                pass

    except Exception as e:
        log(f"FATAL startup error: {e}\n{traceback.format_exc()}")
        # Show a message box if possible
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


if __name__ == "__main__":
    main()
