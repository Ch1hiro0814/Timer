"""System tray icon and menu management using pystray."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable

from PIL import Image, ImageDraw

from utils import parse_time_str


def _get_icon_path() -> Optional[str]:
    """Resolve the icon path (works in both dev and PyInstaller bundle)."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    for candidate in [
        base / "assets" / "icon.png",
        base / "icon.png",
    ]:
        if candidate.exists():
            return str(candidate)
    return None


def generate_default_icon(size: int = 64) -> Image.Image:
    """Generate a simple clock-shaped icon programmatically."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size // 8
    cx, cy = size // 2, size // 2
    r = size // 2 - margin

    # Outer circle
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(44, 62, 80, 255),
        outline=(52, 152, 219, 255),
        width=max(2, size // 20),
    )

    # Clock hands
    hand_width = max(2, size // 25)
    draw.line(
        [cx, cy, cx - r // 3, cy - r // 3],
        fill=(236, 240, 241, 255),
        width=hand_width,
    )
    draw.line(
        [cx, cy, cx + r // 2, cy - r // 6],
        fill=(236, 240, 241, 255),
        width=hand_width,
    )

    # Center dot
    dot_r = max(2, size // 16)
    draw.ellipse(
        [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
        fill=(231, 76, 60, 255),
    )

    return img


def _format_remaining(dt: datetime) -> str:
    """Format a datetime as a human-readable remaining time."""
    now = datetime.now()
    if dt <= now:
        return "即将结束"
    delta = dt - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    if hours > 0:
        return f"剩余 {hours} 小时 {minutes} 分钟"
    return f"剩余 {minutes} 分钟"


class TrayManager:
    """Manages the system tray icon and its context menu."""

    def __init__(
        self,
        root,
        config,
        scheduler,
        on_settings: Optional[Callable] = None,
    ):
        self._root = root
        self._config = config
        self._scheduler = scheduler
        self._on_settings = on_settings
        self._icon: Optional['pystray.Icon'] = None

        # Load or generate icon
        icon_path = _get_icon_path()
        if icon_path:
            self._icon_image = Image.open(icon_path)
        else:
            self._icon_image = generate_default_icon()

        # Periodic menu refresh for DND countdown display
        self._refresh_after_id = None
        self._was_dnd_active = False

    def run(self):
        """Start the system tray icon and block the main thread."""
        import pystray

        self._icon = pystray.Icon(
            "TimerReminder",
            self._icon_image,
            self._build_tooltip(),
            menu=self._build_menu(),
        )
        self._schedule_menu_refresh()
        self._icon.run()

    def stop(self):
        """Stop the tray icon and scheduler."""
        self._cancel_menu_refresh()
        if self._scheduler:
            self._scheduler.stop()
        if self._icon:
            self._icon.stop()

    def _build_tooltip(self) -> str:
        """Build the tray tooltip text based on current state."""
        if self._config.is_dnd_active:
            until = self._config.dnd_until
            if until:
                return f"定时提醒助手 - 🔕 免打扰中 ({_format_remaining(until)})"
            return "定时提醒助手 - 🔕 免打扰中"
        if self._config.is_paused:
            return "定时提醒助手 - ⏸ 已暂停"
        return "定时提醒助手"

    def _schedule_menu_refresh(self):
        """Periodically refresh tooltip (cheap). Only rebuild menu on state change."""
        self._refresh_after_id = self._root.after(15000, self._on_menu_refresh_tick)

    def _on_menu_refresh_tick(self):
        """Update tooltip. Rebuild menu only when DND state transitions."""
        is_dnd = self._config.is_dnd_active
        if self._icon:
            self._icon.title = self._build_tooltip()  # cheap: string assignment
            if self._was_dnd_active != is_dnd:
                # State changed — full menu rebuild
                self._icon.menu = self._build_menu()
        self._was_dnd_active = is_dnd
        self._schedule_menu_refresh()

    def _cancel_menu_refresh(self):
        if self._refresh_after_id:
            self._root.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None

    # ======================== DND Actions ========================

    def _set_dnd(self, minutes: int):
        """Enable DND for a given number of minutes."""
        until = datetime.now() + timedelta(minutes=minutes)
        self._config.dnd_until = until
        self._config.is_paused = False  # DND supersedes pause
        if self._scheduler:
            self._scheduler.reset_triggered()
        if self._icon:
            self._icon.title = self._build_tooltip()
            self._icon.menu = self._build_menu()

    def _set_dnd_until_end_of_workday(self):
        """Enable DND until the configured work end time today."""
        work_end_str = self._config.general.get("work_end_time", "20:30")
        work_end = parse_time_str(work_end_str)
        until = datetime.now().replace(
            hour=work_end.hour, minute=work_end.minute, second=0, microsecond=0
        )
        # If work end time has already passed today, it'll just expire immediately
        self._config.dnd_until = until
        self._config.is_paused = False
        if self._scheduler:
            self._scheduler.reset_triggered()
        if self._icon:
            self._icon.title = self._build_tooltip()
            self._icon.menu = self._build_menu()

    def _cancel_dnd(self):
        """Cancel the current DND mode."""
        self._config.dnd_until = None
        if self._scheduler:
            self._scheduler.reset_triggered()
        if self._icon:
            self._icon.title = self._build_tooltip()
            self._icon.menu = self._build_menu()

    # ======================== Menu Building ========================

    def _build_menu(self):
        """Build the right-click context menu."""
        import pystray

        def _toggle_pause(icon, item):
            if self._config.is_paused:
                self._config.is_paused = False
                if self._scheduler:
                    self._scheduler.reset_triggered()
            else:
                self._config.is_paused = True
                # Cancel DND when pausing (mutually exclusive)
                self._config.dnd_until = None
            icon.title = self._build_tooltip()
            icon.menu = self._build_menu()

        def _open_settings(icon, item):
            if self._on_settings:
                self._on_settings()

        def _quit(icon, item):
            self.stop()

        is_paused = self._config.is_paused
        is_dnd = self._config.is_dnd_active

        # Build menu items list
        menu_items = []

        # ---- DND active: show cancel + remaining time ----
        if is_dnd:
            dnd_until = self._config.dnd_until
            remaining = _format_remaining(dnd_until) if dnd_until else ""
            menu_items.append(
                pystray.MenuItem(
                    f"🔕 取消免打扰 ({remaining})" if remaining else "🔕 取消免打扰",
                    lambda icon, item: self._cancel_dnd(),
                )
            )
            menu_items.append(pystray.Menu.SEPARATOR)

        # ---- Pause toggle (hide when DND active since DND implies paused) ----
        if not is_dnd:
            menu_items.append(
                pystray.MenuItem(
                    "暂停提醒" if not is_paused else "▶ 恢复提醒",
                    _toggle_pause,
                    checked=lambda item: is_paused,
                )
            )
            menu_items.append(pystray.Menu.SEPARATOR)

        # ---- DND submenu (only show when not already in DND) ----
        if not is_dnd:
            dnd_submenu = pystray.Menu(
                pystray.MenuItem(
                    "30 分钟",
                    lambda icon, item: self._set_dnd(30),
                ),
                pystray.MenuItem(
                    "1 小时",
                    lambda icon, item: self._set_dnd(60),
                ),
                pystray.MenuItem(
                    "2 小时",
                    lambda icon, item: self._set_dnd(120),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "直到下班",
                    lambda icon, item: self._set_dnd_until_end_of_workday(),
                ),
            )
            menu_items.append(
                pystray.MenuItem("🔕 免打扰模式", dnd_submenu)
            )
            menu_items.append(pystray.Menu.SEPARATOR)

        # ---- Settings ----
        menu_items.append(
            pystray.MenuItem(
                "设置...",
                _open_settings,
                default=True,
            )
        )
        menu_items.append(pystray.Menu.SEPARATOR)

        # ---- Exit ----
        menu_items.append(
            pystray.MenuItem(
                "退出",
                _quit,
            )
        )

        return pystray.Menu(*menu_items)
