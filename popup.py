"""Reminder popup window using tkinter."""

import tkinter as tk
from typing import Optional, Callable

from theme import ACCENT, ACCENT_DARK, BORDER, SUCCESS, SUCCESS_DARK, SURFACE, TEXT


# Track the currently active popup to avoid stacking multiple popups
_active_popup: Optional['ReminderPopup'] = None


class ReminderPopup:
    """A centered, always-on-top popup window for reminders."""

    BG_COLOR = SURFACE
    FG_COLOR = TEXT
    ACCENT_COLOR = ACCENT
    BTN_COLOR = ACCENT
    BTN_HOVER = ACCENT_DARK
    SNOOZE_COLOR = SUCCESS
    SNOOZE_HOVER = SUCCESS_DARK

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
        main_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=32, pady=28)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = tk.Label(
            main_frame,
            text=title,
            font=("Microsoft YaHei", 17, "bold"),
            fg=self.FG_COLOR,
            bg=self.BG_COLOR,
        )
        title_label.pack(pady=(0, 8))

        # Message label
        msg_label = tk.Label(
            main_frame,
            text=message,
            font=("Microsoft YaHei", 12),
            fg="#71717A",
            bg=self.BG_COLOR,
            justify=tk.CENTER,
            wraplength=360,
        )
        msg_label.pack(pady=(0, 18))

        divider = tk.Frame(main_frame, bg=BORDER, height=1)
        divider.pack(fill=tk.X, pady=(0, 14))

        # ---- Bottom buttons ----
        btn_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        btn_frame.pack()

        # Snooze button (primary)
        snooze_btn = tk.Label(
            btn_frame,
            text="稍后提醒",
            font=("Microsoft YaHei", 10, "bold"),
            fg="white",
            bg=self.BTN_COLOR,
            padx=18,
            pady=8,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=self.FG_COLOR,
        )
        snooze_btn.pack(side=tk.LEFT, padx=(0, 10))
        snooze_btn._pressed = False

        def snooze_press(_event):
            snooze_btn._pressed = True

        def snooze_release(_event):
            if snooze_btn._pressed:
                snooze_btn._pressed = False
                self.snooze()

        snooze_btn.bind("<Button-1>", snooze_press)
        snooze_btn.bind("<ButtonRelease-1>", snooze_release)
        snooze_btn.bind("<Leave>", lambda e: setattr(snooze_btn, "_pressed", False))

        # Dismiss button (secondary with countdown)
        self._countdown_var = tk.StringVar()
        dismiss_text = f"知道了 ({auto_dismiss}s)" if auto_dismiss > 0 else "知道了"
        self._countdown_var.set(dismiss_text)

        dismiss_btn = tk.Label(
            btn_frame,
            textvariable=self._countdown_var,
            font=("Microsoft YaHei", 10),
            fg=self.FG_COLOR,
            bg=self.BG_COLOR,
            padx=18,
            pady=8,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        dismiss_btn.pack(side=tk.LEFT)
        dismiss_btn._pressed = False

        def dismiss_press(_event):
            dismiss_btn._pressed = True

        def dismiss_release(_event):
            if dismiss_btn._pressed:
                dismiss_btn._pressed = False
                self.dismiss()

        dismiss_btn.bind("<Button-1>", dismiss_press)
        dismiss_btn.bind("<ButtonRelease-1>", dismiss_release)
        dismiss_btn.bind("<Leave>", lambda e: setattr(dismiss_btn, "_pressed", False))

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


def show_reminder(
    root: tk.Tk,
    reminder_type: str,
    message: str,
    auto_dismiss: int = 30,
    schedule: Optional[Callable[[Callable], None]] = None,
):
    """
    Entry point for showing a reminder popup.
    ``schedule`` must marshal the callback onto the tkinter main thread when
    called from a background thread; otherwise the callback is queued with
    ``root.after``.
    """
    def _show():
        popup = ReminderPopup(root, reminder_type, message, auto_dismiss)
        popup.center_on_screen()
        return popup

    if schedule is not None:
        schedule(_show)
    else:
        root.after(0, _show)
