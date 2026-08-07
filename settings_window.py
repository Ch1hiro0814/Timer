"""Settings window for configuring reminder rules."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from utils import parse_time_str


class SettingsWindow:
    """A Toplevel window with tabbed settings for the reminder app.

    Tab layout:
      - 健康提醒: enable/disable + message text for stand-up & water
      - 报告提醒: enable/disable + message text for daily & weekly reports
      - 通用设置: ALL time settings (work hours, quiet hours, intervals, report times)
    """

    BG_COLOR = "#2C3E50"
    FG_COLOR = "#ECF0F1"
    ACCENT_COLOR = "#3498DB"
    BTN_COLOR = "#2980B9"

    DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    def __init__(self, root: tk.Tk, config, on_save_callback=None):
        self._root = root
        self._config = config
        self._on_save_callback = on_save_callback
        self._window: Optional[tk.Toplevel] = None
        self._notebook: Optional[ttk.Notebook] = None

    # ======================== Show / Hide ========================

    def show(self):
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return

        self._window = tk.Toplevel(self._root)
        self._window.title("定时提醒 - 设置")
        self._window.geometry("540x520")
        self._window.configure(bg=self.BG_COLOR)
        self._window.resizable(True, True)
        self._window.minsize(480, 460)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", padding=[15, 6], font=("Microsoft YaHei", 10))
        style.map("TNotebook.Tab", background=[("selected", self.ACCENT_COLOR)])

        self._notebook = ttk.Notebook(self._window)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._health_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._health_tab, text="  健康提醒  ")
        self._build_health_tab()

        self._report_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._report_tab, text="  报告提醒  ")
        self._build_report_tab()

        self._general_tab = tk.Frame(self._notebook, bg=self.BG_COLOR)
        self._notebook.add(self._general_tab, text="  通用设置  ")
        self._build_general_tab()

        # Bottom buttons
        btn_frame = tk.Frame(self._window, bg=self.BG_COLOR, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        # Save status label (hidden by default)
        self._save_status_var = tk.StringVar()
        save_status = tk.Label(
            btn_frame, textvariable=self._save_status_var,
            font=("Microsoft YaHei", 10, "bold"), fg="#2ECC71", bg=self.BG_COLOR,
        )
        save_status.pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="保存设置", command=self._on_save,
            font=("Microsoft YaHei", 11, "bold"), fg="white", bg="#27AE60",
            activebackground="#219A52", activeforeground="white",
            relief=tk.FLAT, padx=20, pady=5, cursor="hand2",
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame, text="关闭", command=self._on_cancel,
            font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg="#7F8C8D",
            activebackground="#6C7A7A", activeforeground="white",
            relief=tk.FLAT, padx=15, pady=5, cursor="hand2",
        ).pack(side=tk.RIGHT, padx=5)

        self._window.update_idletasks()
        w = self._window.winfo_width()
        h = self._window.winfo_height()
        sw = self._window.winfo_screenwidth()
        sh = self._window.winfo_screenheight()
        self._window.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        self._window.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ======================== Health Tab (content only) ========================

    def _build_health_tab(self):
        frame = self._health_tab

        self._stand_up_enabled_var = tk.BooleanVar(
            value=self._config.stand_up_config.get("enabled", True))
        self._water_enabled_var = tk.BooleanVar(
            value=self._config.water_config.get("enabled", True))

        # Stand-up
        s = tk.LabelFrame(frame, text="起立放松提醒", font=("Microsoft YaHei", 11, "bold"),
                          fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        s.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Checkbutton(s, text="启用", variable=self._stand_up_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(s, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W, pady=(5, 0))
        self._stand_up_msg_text = tk.Text(s, height=3, font=("Microsoft YaHei", 10),
                                          fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD,
                                          relief=tk.FLAT, padx=5, pady=5)
        self._stand_up_msg_text.insert("1.0", self._config.stand_up_config.get("message", ""))
        self._stand_up_msg_text.pack(fill=tk.X, pady=(0, 2))

        # Water
        s2 = tk.LabelFrame(frame, text="喝水提醒", font=("Microsoft YaHei", 11, "bold"),
                           fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        s2.pack(fill=tk.X, padx=10, pady=5)
        tk.Checkbutton(s2, text="启用", variable=self._water_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(s2, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W, pady=(5, 0))
        self._water_msg_text = tk.Text(s2, height=3, font=("Microsoft YaHei", 10),
                                       fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD,
                                       relief=tk.FLAT, padx=5, pady=5)
        self._water_msg_text.insert("1.0", self._config.water_config.get("message", ""))
        self._water_msg_text.pack(fill=tk.X, pady=(0, 2))

    # ======================== Report Tab (content only) ========================

    def _build_report_tab(self):
        frame = self._report_tab

        daily_cfg = self._config.daily_report_config
        weekly_cfg = self._config.weekly_report_config
        schedule = daily_cfg.get("schedule", {})
        weekly_schedule = weekly_cfg.get("schedule", {})

        self._daily_enabled_var = tk.BooleanVar(value=daily_cfg.get("enabled", True))
        self._weekly_enabled_var = tk.BooleanVar(value=weekly_cfg.get("enabled", True))

        # Daily report
        s = tk.LabelFrame(frame, text="日报提醒", font=("Microsoft YaHei", 11, "bold"),
                          fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        s.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Checkbutton(s, text="启用", variable=self._daily_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(s, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W, pady=(5, 0))
        self._daily_msg_text = tk.Text(s, height=3, font=("Microsoft YaHei", 10),
                                       fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD,
                                       relief=tk.FLAT, padx=5, pady=5)
        self._daily_msg_text.insert("1.0", schedule.get("0", {}).get("message", ""))
        self._daily_msg_text.pack(fill=tk.X, pady=(0, 2))

        # Weekly report
        s2 = tk.LabelFrame(frame, text="周报提醒", font=("Microsoft YaHei", 11, "bold"),
                           fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=10)
        s2.pack(fill=tk.X, padx=10, pady=5)
        tk.Checkbutton(s2, text="启用", variable=self._weekly_enabled_var,
                       font=("Microsoft YaHei", 10), fg=self.FG_COLOR, bg=self.BG_COLOR,
                       selectcolor=self.BG_COLOR, activebackground=self.BG_COLOR).pack(anchor=tk.W)
        tk.Label(s2, text="提醒文字:", font=("Microsoft YaHei", 10),
                 fg=self.FG_COLOR, bg=self.BG_COLOR).pack(anchor=tk.W, pady=(5, 0))
        self._weekly_msg_text = tk.Text(s2, height=3, font=("Microsoft YaHei", 10),
                                        fg=self.FG_COLOR, bg="#34495E", wrap=tk.WORD,
                                        relief=tk.FLAT, padx=5, pady=5)
        self._weekly_msg_text.insert("1.0", weekly_schedule.get("4", {}).get("message", ""))
        self._weekly_msg_text.pack(fill=tk.X, pady=(0, 2))

    # ======================== General Tab (ALL time settings) ========================

    def _build_general_tab(self):
        frame = self._general_tab
        general = self._config.general

        canvas = tk.Canvas(frame, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.BG_COLOR)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        self._root.unbind_all("<MouseWheel>")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ---- Work hours ----
        self._work_start_var = self._make_var(general, "work_start_time", "09:00")
        self._work_end_var = self._make_var(general, "work_end_time", "20:30")
        self._work_end_early_var = self._make_var(general, "work_end_time_early", "17:30")
        self._work_end_sat_var = self._make_var(general, "work_end_time_saturday", "18:30")
        self._add_section(scroll_frame, "工作时间", [
            ("开始时间", self._work_start_var),
            ("周二/四 结束", self._work_end_var),
            ("周三/五 结束", self._work_end_early_var),
            ("月末周六 结束", self._work_end_sat_var),
        ])

        # ---- Health intervals ----
        stand_up_interval = str(self._config.stand_up_config.get("interval_minutes", 60))
        water_interval = str(self._config.water_config.get("interval_minutes", 30))
        self._stand_up_interval_var = tk.StringVar(value=stand_up_interval)
        self._water_interval_var = tk.StringVar(value=water_interval)
        self._add_section(scroll_frame, "健康提醒间隔", [
            ("起立放松(分钟)", self._stand_up_interval_var),
            ("喝水提醒(分钟)", self._water_interval_var),
        ])

        # ---- Quiet hours 1 ----
        self._quiet_start_var = self._make_var(general, "quiet_hours_start", "12:00")
        self._quiet_end_var = self._make_var(general, "quiet_hours_end", "14:00")
        self._add_section(scroll_frame, "午休免打扰", [
            ("开始时间", self._quiet_start_var),
            ("结束时间", self._quiet_end_var),
        ])

        # ---- Quiet hours 2 ----
        self._quiet2_start_var = self._make_var(general, "quiet_hours_2_start", "17:30")
        self._quiet2_end_var = self._make_var(general, "quiet_hours_2_end", "18:00")
        self._add_section(scroll_frame, "晚餐免打扰", [
            ("开始时间", self._quiet2_start_var),
            ("结束时间", self._quiet2_end_var),
        ])

        # ---- Report schedule ----
        daily_cfg = self._config.daily_report_config
        weekly_cfg = self._config.weekly_report_config
        daily_schedule = daily_cfg.get("schedule", {})
        weekly_schedule = weekly_cfg.get("schedule", {})

        self._daily_time_vars = {}
        daily_rows = []
        for dk, dn in [("0", "周一"), ("1", "周二"), ("2", "周三"), ("3", "周四")]:
            self._daily_time_vars[dk] = tk.StringVar(
                value=daily_schedule.get(dk, {}).get("time", "20:00"))
            daily_rows.append((dn, self._daily_time_vars[dk]))
        self._add_section(scroll_frame, "日报时间", daily_rows)

        self._weekly_time_vars = {}
        weekly_rows = []
        for wk, wn in [("4", "周五")]:
            self._weekly_time_vars[wk] = tk.StringVar(
                value=weekly_schedule.get(wk, {}).get("time", "17:00"))
            weekly_rows.append((wn, self._weekly_time_vars[wk]))
        self._add_section(scroll_frame, "周报时间", weekly_rows)

        # ---- Auto dismiss ----
        self._auto_dismiss_var = tk.StringVar(value=str(general.get("auto_dismiss_seconds", 30)))
        self._add_section(scroll_frame, "弹窗设置", [
            ("自动关闭(秒)", self._auto_dismiss_var),
        ])

    def _make_var(self, cfg_dict, key, default):
        return tk.StringVar(value=cfg_dict.get(key, default))

    def _add_section(self, parent, title, rows):
        """Add a section with labelled Entry rows. Each row is (label, StringVar)."""
        sec = tk.LabelFrame(parent, text=title,
                            font=("Microsoft YaHei", 11, "bold"),
                            fg=self.ACCENT_COLOR, bg=self.BG_COLOR, padx=10, pady=8)
        sec.pack(fill=tk.X, padx=10, pady=4)
        for label_text, var in rows:
            row = tk.Frame(sec, bg=self.BG_COLOR)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{label_text}:", font=("Microsoft YaHei", 10),
                     fg=self.FG_COLOR, bg=self.BG_COLOR, width=14,
                     anchor=tk.E).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, font=("Microsoft YaHei", 10),
                     fg=self.FG_COLOR, bg="#34495E", width=9,
                     relief=tk.FLAT, justify=tk.CENTER).pack(side=tk.LEFT, padx=5)

    # ======================== Save ========================

    def _on_save(self):
        try:
            general_vars = [
                (self._work_start_var, "work_start_time", "工作开始时间"),
                (self._work_end_var, "work_end_time", "周二/四 结束时间"),
                (self._work_end_early_var, "work_end_time_early", "周一/三/五 结束时间"),
                (self._work_end_sat_var, "work_end_time_saturday", "月末周六 结束时间"),
                (self._quiet_start_var, "quiet_hours_start", "午休免打扰开始"),
                (self._quiet_end_var, "quiet_hours_end", "午休免打扰结束"),
                (self._quiet2_start_var, "quiet_hours_2_start", "晚餐免打扰开始"),
                (self._quiet2_end_var, "quiet_hours_2_end", "晚餐免打扰结束"),
            ]

            # Validate times
            for var, _key, name in general_vars:
                self._validate_time(var.get(), name)

            for dk, dn in [("0", "周一"), ("1", "周二"), ("2", "周三"), ("3", "周四")]:
                self._validate_time(self._daily_time_vars[dk].get(), f"日报 {dn}")
            for wk, wn in [("4", "周五")]:
                self._validate_time(self._weekly_time_vars[wk].get(), f"周报 {wn}")

            # Validate work hours are not inverted
            work_start = parse_time_str(self._work_start_var.get().strip())
            for var, name in [
                (self._work_end_var, "周二/四 结束时间"),
                (self._work_end_early_var, "周三/五 结束时间"),
                (self._work_end_sat_var, "月末周六 结束时间"),
            ]:
                if parse_time_str(var.get().strip()) <= work_start:
                    raise ValueError(f"{name}必须晚于工作开始时间")

            # Validate intervals
            stand_up_int = int(self._stand_up_interval_var.get())
            water_int = int(self._water_interval_var.get())
            if stand_up_int < 1 or water_int < 1:
                raise ValueError("提醒间隔必须大于 0 分钟")
            if 60 % stand_up_int != 0 and stand_up_int % 60 != 0:
                pass  # any interval is fine, just give a heads-up
            ads = int(self._auto_dismiss_var.get())
            if ads < 0:
                raise ValueError("自动关闭秒数不能为负数")

            # ---- Save general ----
            for var, key, _name in general_vars:
                self._config.set("general", key, value=var.get().strip())
            self._config.set("general", "auto_dismiss_seconds", value=ads)

            # ---- Save health ----
            self._config.set("stand_up", "enabled", value=self._stand_up_enabled_var.get())
            self._config.set("stand_up", "interval_minutes", value=stand_up_int)
            self._config.set("stand_up", "message",
                             value=self._stand_up_msg_text.get("1.0", tk.END).strip())
            self._config.set("water", "enabled", value=self._water_enabled_var.get())
            self._config.set("water", "interval_minutes", value=water_int)
            self._config.set("water", "message",
                             value=self._water_msg_text.get("1.0", tk.END).strip())

            # ---- Save report ----
            daily_msg = self._daily_msg_text.get("1.0", tk.END).strip()
            weekly_msg = self._weekly_msg_text.get("1.0", tk.END).strip()
            self._config.set("daily_report", "enabled", value=self._daily_enabled_var.get())
            self._config.set("weekly_report", "enabled", value=self._weekly_enabled_var.get())

            schedule = self._config.daily_report_config.get("schedule", {})
            for dk in schedule:
                if dk in self._daily_time_vars:
                    schedule[dk]["time"] = self._daily_time_vars[dk].get().strip()
                schedule[dk]["message"] = daily_msg
            self._config.set("daily_report", "schedule", value=schedule)

            weekly_schedule = self._config.weekly_report_config.get("schedule", {})
            for wk in weekly_schedule:
                if wk in self._weekly_time_vars:
                    weekly_schedule[wk]["time"] = self._weekly_time_vars[wk].get().strip()
                weekly_schedule[wk]["message"] = weekly_msg
            self._config.set("weekly_report", "schedule", value=weekly_schedule)

            self._config.save()

            if self._on_save_callback:
                self._on_save_callback()

            # Show success briefly, keep window open
            self._save_status_var.set("✓ 已保存")
            self._window.after(2000, lambda: self._save_status_var.set(""))

        except ValueError as e:
            messagebox.showerror("输入错误", str(e))

    def _on_cancel(self):
        self._root.unbind_all("<MouseWheel>")
        if self._window:
            self._window.destroy()
            self._window = None

    @staticmethod
    def _validate_time(time_str: str, field_name: str):
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
