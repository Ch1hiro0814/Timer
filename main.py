"""Timer Reminder Application - Entry Point.

A Windows desktop app that provides periodic health reminders (stand up, drink water)
during work hours and report-writing reminders on specific weekdays.
"""

import tkinter as tk
import sys
import os

from config import ConfigManager
from scheduler import ReminderScheduler
from tray_manager import TrayManager
from settings_window import SettingsWindow


def main():
    # ---- Load configuration ----
    config = ConfigManager()

    # ---- Create hidden tkinter root (required for popups and tray) ----
    root = tk.Tk()
    root.withdraw()  # Hide the empty root window
    root.title("定时提醒助手")

    # ---- Create scheduler ----
    scheduler = ReminderScheduler(config, root)
    scheduler.start()

    # ---- Settings callback ----
    def open_settings():
        settings = SettingsWindow(root, config, on_save_callback=lambda: None)
        settings.show()

    # ---- Create system tray ----
    tray = TrayManager(root, config, scheduler, on_settings=open_settings)

    # ---- Handle clean exit ----
    def on_closing():
        scheduler.stop()
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # ---- Start tray (blocks until exit) ----
    try:
        tray.run()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        try:
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
