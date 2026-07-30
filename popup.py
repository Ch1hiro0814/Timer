"""Reminder popup window using tkinter."""

import tkinter as tk
from typing import Optional, Callable


# Track the currently active popup to avoid stacking multiple popups
_active_popup: Optional['ReminderPopup'] = None


class ReminderPopup:
    """A centered, always-on-top popup window for reminders."""

    BG_COLOR = "#2C3E50"
    FG_COLOR = "#ECF0F1"
    ACCENT_COLOR = "#3498DB"
    BTN_COLOR = "#2980B9"
    BTN_HOVER = "#1A6FA0"
    SNOOZE_COLOR = "#27AE60"
    SNOOZE_HOVER = "#219A52"

    def __init__(
        self,
        root: tk.Tk,
        title: str,
        message: str,
        auto_dismiss: int = 30,
        on_snooze: Optional[Callable] = None,
    ):
        global _active_popup

        # Dismiss any existing popup first
        if _active_popup is not None:
            try:
                _active_popup.dismiss()
            except Exception:
                pass

        self._root = root
        self._title = title
        self._message = message
        self._auto_dismiss = auto_dismiss
        self._on_snooze = on_snooze
        self._after_id: Optional[str] = None
        self._countdown_remaining = auto_dismiss

        # Create toplevel window
        self._window = tk.Toplevel(root)
        self._window.title(title)
        self._window.configure(bg=self.BG_COLOR)
        self._window.resizable(False, False)
        self._window.attributes("-topmost", True)

        # X button → dismiss
        self._window.protocol("WM_DELETE_WINDOW", self.dismiss)

        # ---- Build UI ----
        main_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = tk.Label(
            main_frame,
            text=title,
            font=("Microsoft YaHei", 16, "bold"),
            fg=self.ACCENT_COLOR,
            bg=self.BG_COLOR,
        )
        title_label.pack(pady=(0, 10))

        # Message label
        msg_label = tk.Label(
            main_frame,
            text=message,
            font=("Microsoft YaHei", 12),
            fg=self.FG_COLOR,
            bg=self.BG_COLOR,
            justify=tk.CENTER,
            wraplength=350,
        )
        msg_label.pack(pady=(0, 15))

        # ---- Bottom buttons ----
        btn_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        btn_frame.pack()

        # Snooze button (left, green)
        snooze_btn = tk.Button(
            btn_frame,
            text="🕐 5分钟后",
            command=self.snooze,
            font=("Microsoft YaHei", 10, "bold"),
            fg="white",
            bg=self.SNOOZE_COLOR,
            activebackground=self.SNOOZE_HOVER,
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        snooze_btn.pack(side=tk.LEFT, padx=(0, 8))
        snooze_btn.bind("<Enter>", lambda e: snooze_btn.configure(bg=self.SNOOZE_HOVER))
        snooze_btn.bind("<Leave>", lambda e: snooze_btn.configure(bg=self.SNOOZE_COLOR))

        # Dismiss button (right, blue with countdown)
        self._countdown_var = tk.StringVar()
        dismiss_text = f"知道了 ({auto_dismiss}s)" if auto_dismiss > 0 else "知道了"
        self._countdown_var.set(dismiss_text)

        dismiss_btn = tk.Button(
            btn_frame,
            textvariable=self._countdown_var,
            command=self.dismiss,
            font=("Microsoft YaHei", 10),
            fg="white",
            bg=self.BTN_COLOR,
            activebackground=self.BTN_HOVER,
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        dismiss_btn.pack(side=tk.LEFT)
        dismiss_btn.bind("<Enter>", lambda e: dismiss_btn.configure(bg=self.BTN_HOVER))
        dismiss_btn.bind("<Leave>", lambda e: dismiss_btn.configure(bg=self.BTN_COLOR))

        # Focus the window
        self._window.focus_force()
        self._window.lift()

        # Register as active
        _active_popup = self

        # Start countdown
        if auto_dismiss > 0:
            self._update_countdown(auto_dismiss)

    def _update_countdown(self, remaining: int):
        """Update the countdown on the dismiss button."""
        if remaining <= 0:
            self.dismiss()
            return
        self._countdown_remaining = remaining
        self._countdown_var.set(f"知道了 ({remaining}s)")
        self._after_id = self._window.after(1000, lambda: self._update_countdown(remaining - 1))

    def snooze(self):
        """Snooze: dismiss now, re-show same reminder in 5 minutes."""
        # Save info before dismissing
        title = self._title
        message = self._message
        auto_dismiss = self._auto_dismiss
        root = self._root
        on_snooze = self._on_snooze

        self.dismiss()

        # Re-show after 5 minutes
        root.after(300000, lambda: (
            ReminderPopup(root, title, message, auto_dismiss, on_snooze).center_on_screen()
        ))

        # Notify callback (e.g., to track snooze in scheduler)
        if on_snooze:
            on_snooze()

    def dismiss(self):
        """Dismiss and destroy the popup."""
        global _active_popup
        if _active_popup is self:
            _active_popup = None
        try:
            if self._after_id:
                self._window.after_cancel(self._after_id)
                self._after_id = None
            self._window.destroy()
        except tk.TclError:
            pass

    def center_on_screen(self):
        """Center the window on the primary screen."""
        self._window.update_idletasks()
        width = self._window.winfo_width()
        height = self._window.winfo_height()
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self._window.geometry(f"+{x}+{y}")


def show_reminder(root: tk.Tk, reminder_type: str, message: str, auto_dismiss: int = 30):
    """
    Thread-safe entry point for showing a reminder popup.
    Schedules the popup creation on the tkinter main thread.
    """
    def _show():
        popup = ReminderPopup(root, reminder_type, message, auto_dismiss)
        popup.center_on_screen()
        return popup

    root.after(0, _show)
