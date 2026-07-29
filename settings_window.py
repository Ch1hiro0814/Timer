"""Settings window for configuring reminder rules."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional


class SettingsWindow:
    """A Toplevel window with tabbed settings for the reminder app."""

    BG_COLOR = "#2C3E50"
    FG_COLOR = "#ECF0F1"
    ACCENT_COLOR = "#3498DB"
    BTN_COLOR = "#2980B9"

    def __init__(self, root: tk.Tk, config, on_save_callback=None):
        self._root = root
        self._config = config
        self._on_save_callback = on_save_callback
        self._window: Optional[tk.Toplevel] = None
        self._notebook: Optional[ttk.Notebook] = None

    def show(self):
        """Create and display the settings window."""
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return

        self._window = tk.Toplevel(self._root)
        self._window.title("定时提醒 - 设置")
        self._window.geometry("520x480")
        self._window.configure(bg=self.BG_COLOR)
        self._window.resizable(True, True)
        self._window.minsize(480, 420)

        # Style the notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 6], font=("Microsoft YaHei", 10))
        style.map("TNotebook.Tab", background=[("selected", self.ACCENT_COLOR)])

        # Create notebook (tabs)
        self._notebook = ttk.Notebook(self._window)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---- Tab 1: Health Reminders ----
        self._health_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._health_tab, text="  健康提醒  ")
        self._build_health_tab()

        # ---- Tab 2: Report Reminders ----
        self._report_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._report_tab, text="  报告提醒  ")
        self._build_report_tab()

        # ---- Tab 3: General ----
        self._general_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._general_tab, text="  通用设置  ")
        self._build_general_tab()

        # ---- Bottom buttons ----
        btn_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame,
            text="保存设置",
            command=self._on_save,
            font=("Microsoft YaHei", 11, "bold"),
            fg="white",
            bg="#27AE60",
            activebackground="#219A52",
            activeforeground="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame,
            text="取消",
            command=self._on_cancel,
            font=("Microsoft YaHei", 10),
            fg=self.FG_COLOR,
            bg="#7F8C8D",
            activebackground="#6C7A7A",
            activeforeground="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=5)

        # Center on screen
        self._window.update_idletasks()
        w = self._window.winfo_width()
        h = self._window.winfo_height()
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        self._window.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ======================== Health Tab ========================

    def _build_health_tab(self):
        frame = self._health_tab
        self._stand_up_enabled_var = tk.BooleanVar(value=self._config.stand_up_config.get("enabled", True))
        self._stand_up_msg_var = tk.StringVar(value=self._config.stand_up_config.get("message", ""))
        self._water_enabled_var = tk.BooleanVar(value=self._config.water_config.get("enabled", True))
        self._water_msg_var = tk.StringVar(value=self._config.water_config.get("message", ""))

        # Stand-up section
        section = tk.LabelFrame(frame, text="起立放松提醒", font=("Microsoft YaHei", 11, "bold"),
                                fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Checkbutton(section, text="启用", variable=self._stand_up_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(section, text="提醒间隔: 每 60 分钟 (每小时整点)", font=("Microsoft YaHei", 9),
                 fg="#BDC3C7", bg=self.BG_COLOR).pack(anchor=tk.W, pady=(2, 5))
        tk.Label(section, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W)
        s_msg = tk.Text(section, height=3, font=("Microsoft YaHei", 10),
                        fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD, relief=tk.FLAT, padx=5, pady=5)
        s_msg.insert("1.0", self._stand_up_msg_var.get())
        s_msg.pack(fill=tk.X, pady=(0, 5))
        self._stand_up_msg_text = s_msg

        # Water section
        section2 = tk.LabelFrame(frame, text="喝水提醒", font=("Microsoft YaHei", 11, "bold"),
                                 fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section2.pack(fill=tk.X, padx=10, pady=5)

        tk.Checkbutton(section2, text="启用", variable=self._water_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(section2, text="提醒间隔: 每 30 分钟 (整点和半点)", font=("Microsoft YaHei", 9),
                 fg="#BDC3C7", bg=self.BG_COLOR).pack(anchor=tk.W, pady=(2, 5))
        tk.Label(section2, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W)
        w_msg = tk.Text(section2, height=3, font=("Microsoft YaHei", 10),
                        fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD, relief=tk.FLAT, padx=5, pady=5)
        w_msg.insert("1.0", self._water_msg_var.get())
        w_msg.pack(fill=tk.X, pady=(0, 5))
        self._water_msg_text = w_msg

    # ======================== Report Tab ========================

    def _build_report_tab(self):
        frame = self._report_tab
        daily_cfg = self._config.daily_report_config
        weekly_cfg = self._config.weekly_report_config

        self._daily_enabled_var = tk.BooleanVar(value=daily_cfg.get("enabled", True))
        self._weekly_enabled_var = tk.BooleanVar(value=weekly_cfg.get("enabled", True))

        schedule = daily_cfg.get("schedule", {})
        weekly_schedule = weekly_cfg.get("schedule", {})

        # Daily report
        section = tk.LabelFrame(frame, text="日报提醒", font=("Microsoft YaHei", 11, "bold"),
                                fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Checkbutton(section, text="启用", variable=self._daily_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)

        schedule_text = (
            "📅 周一 20:00  |  周二 20:00  |  周三 17:00  |  周四 20:00"
        )
        tk.Label(section, text=schedule_text, font=("Microsoft YaHei", 9),
                 fg="#BDC3C7", bg=self.BG_COLOR).pack(anchor=tk.W, pady=(2, 5))

        tk.Label(section, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W)
        # Use Monday's message as default
        default_daily_msg = schedule.get("0", {}).get("message", "")
        d_msg = tk.Text(section, height=3, font=("Microsoft YaHei", 10),
                        fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD, relief=tk.FLAT, padx=5, pady=5)
        d_msg.insert("1.0", default_daily_msg)
        d_msg.pack(fill=tk.X, pady=(0, 5))
        self._daily_msg_text = d_msg

        # Weekly report
        section2 = tk.LabelFrame(frame, text="周报提醒", font=("Microsoft YaHei", 11, "bold"),
                                 fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section2.pack(fill=tk.X, padx=10, pady=5)

        tk.Checkbutton(section2, text="启用", variable=self._weekly_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)

        tk.Label(section2, text="📅 周五 17:00", font=("Microsoft YaHei", 9),
                 fg="#BDC3C7", bg=self.BG_COLOR).pack(anchor=tk.W, pady=(2, 5))

        default_weekly_msg = weekly_schedule.get("4", {}).get("message", "")
        w_msg = tk.Text(section2, height=3, font=("Microsoft YaHei", 10),
                        fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD, relief=tk.FLAT, padx=5, pady=5)
        w_msg.insert("1.0", default_weekly_msg)
        w_msg.pack(fill=tk.X, pady=(0, 5))
        self._weekly_msg_text = w_msg

    # ======================== General Tab ========================

    def _build_general_tab(self):
        frame = self._general_tab
        general = self._config.general

        section = tk.LabelFrame(frame, text="工作时间", font=("Microsoft YaHei", 11, "bold"),
                                fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Work start
        row1 = tk.Frame(section, bg=self.BG_COLOR)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="工作开始时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._work_start_var = tk.StringVar(value=general.get("work_start_time", "09:00"))
        tk.Entry(row1, textvariable=self._work_start_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        # Work end
        row2 = tk.Frame(section, bg=self.BG_COLOR)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="工作结束时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._work_end_var = tk.StringVar(value=general.get("work_end_time", "18:00"))
        tk.Entry(row2, textvariable=self._work_end_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        # Quiet hours section
        section2 = tk.LabelFrame(frame, text="午休免打扰", font=("Microsoft YaHei", 11, "bold"),
                                 fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section2.pack(fill=tk.X, padx=10, pady=5)

        row3 = tk.Frame(section2, bg=self.BG_COLOR)
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="开始时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._quiet_start_var = tk.StringVar(value=general.get("quiet_hours_start", "12:00"))
        tk.Entry(row3, textvariable=self._quiet_start_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        row4 = tk.Frame(section2, bg=self.BG_COLOR)
        row4.pack(fill=tk.X, pady=2)
        tk.Label(row4, text="结束时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._quiet_end_var = tk.StringVar(value=general.get("quiet_hours_end", "14:00"))
        tk.Entry(row4, textvariable=self._quiet_end_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        # Second quiet hours (dinner break)
        section2b = tk.LabelFrame(frame, text="晚餐免打扰", font=("Microsoft YaHei", 11, "bold"),
                                  fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section2b.pack(fill=tk.X, padx=10, pady=5)

        row3b = tk.Frame(section2b, bg=self.BG_COLOR)
        row3b.pack(fill=tk.X, pady=2)
        tk.Label(row3b, text="开始时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._quiet2_start_var = tk.StringVar(value=general.get("quiet_hours_2_start", "17:30"))
        tk.Entry(row3b, textvariable=self._quiet2_start_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        row4b = tk.Frame(section2b, bg=self.BG_COLOR)
        row4b.pack(fill=tk.X, pady=2)
        tk.Label(row4b, text="结束时间:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._quiet2_end_var = tk.StringVar(value=general.get("quiet_hours_2_end", "18:00"))
        tk.Entry(row4b, textvariable=self._quiet2_end_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

        # Auto dismiss
        section3 = tk.LabelFrame(frame, text="弹窗设置", font=("Microsoft YaHei", 11, "bold"),
                                 fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        section3.pack(fill=tk.X, padx=10, pady=5)

        row5 = tk.Frame(section3, bg=self.BG_COLOR)
        row5.pack(fill=tk.X, pady=2)
        tk.Label(row5, text="自动关闭(秒):", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR, width=14, anchor=tk.E).pack(side=tk.LEFT)
        self._auto_dismiss_var = tk.StringVar(value=str(general.get("auto_dismiss_seconds", 30)))
        tk.Entry(row5, textvariable=self._auto_dismiss_var, font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg="#34495E", width=8, relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)
        tk.Label(row5, text="(0 = 不自动关闭)", font=("Microsoft YaHei", 9),
                 fg="#BDC3C7", bg=self.BG_COLOR).pack(side=tk.LEFT)

    # ======================== Actions ========================

    def _on_save(self):
        """Validate and save all settings."""
        try:
            # Validate time formats
            for var, name in [
                (self._work_start_var, "工作开始时间"),
                (self._work_end_var, "工作结束时间"),
                (self._quiet_start_var, "午休免打扰开始"),
                (self._quiet_end_var, "午休免打扰结束"),
                (self._quiet2_start_var, "晚餐免打扰开始"),
                (self._quiet2_end_var, "晚餐免打扰结束"),
            ]:
                self._validate_time(var.get(), name)

            # Validate auto dismiss
            ads = int(self._auto_dismiss_var.get())
            if ads < 0:
                raise ValueError("自动关闭秒数不能为负数")

            # ---- Save general settings ----
            self._config.set("general", "work_start_time", value=self._work_start_var.get().strip())
            self._config.set("general", "work_end_time", value=self._work_end_var.get().strip())
            self._config.set("general", "quiet_hours_start", value=self._quiet_start_var.get().strip())
            self._config.set("general", "quiet_hours_end", value=self._quiet_end_var.get().strip())
            self._config.set("general", "quiet_hours_2_start", value=self._quiet2_start_var.get().strip())
            self._config.set("general", "quiet_hours_2_end", value=self._quiet2_end_var.get().strip())
            self._config.set("general", "auto_dismiss_seconds", value=ads)

            # ---- Save health settings ----
            self._config.set("stand_up", "enabled", value=self._stand_up_enabled_var.get())
            self._config.set("stand_up", "message",
                             value=self._stand_up_msg_text.get("1.0", tk.END).strip())
            self._config.set("water", "enabled", value=self._water_enabled_var.get())
            self._config.set("water", "message",
                             value=self._water_msg_text.get("1.0", tk.END).strip())

            # ---- Save report settings ----
            daily_msg = self._daily_msg_text.get("1.0", tk.END).strip()
            weekly_msg = self._weekly_msg_text.get("1.0", tk.END).strip()

            self._config.set("daily_report", "enabled", value=self._daily_enabled_var.get())
            self._config.set("weekly_report", "enabled", value=self._weekly_enabled_var.get())

            # Update messages for each day
            schedule = self._config.daily_report_config.get("schedule", {})
            for day_key in schedule:
                schedule[day_key]["message"] = daily_msg
            self._config.set("daily_report", "schedule", value=schedule)

            weekly_schedule = self._config.weekly_report_config.get("schedule", {})
            for day_key in weekly_schedule:
                weekly_schedule[day_key]["message"] = weekly_msg
            self._config.set("weekly_report", "schedule", value=weekly_schedule)

            self._config.save()

            if self._on_save_callback:
                self._on_save_callback()

            self._window.destroy()
            self._window = None

            messagebox.showinfo("设置已保存", "所有设置已成功保存！")

        except ValueError as e:
            messagebox.showerror("输入错误", str(e))

    def _on_cancel(self):
        """Close without saving."""
        if self._window:
            self._window.destroy()
            self._window = None

    @staticmethod
    def _validate_time(time_str: str, field_name: str):
        """Validate a 'HH:MM' time string."""
        time_str = time_str.strip()
        if not time_str:
            raise ValueError(f"{field_name} 不能为空")
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except (ValueError, IndexError):
            raise ValueError(f"{field_name} 格式错误，请使用 HH:MM 格式（如 09:00）")
