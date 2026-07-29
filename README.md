# ⏰ 定时提醒助手 (Timer Reminder)

一个 Windows 桌面定时提醒工具，帮助你保持健康工作习惯和按时完成报告。

## ✨ 功能

### 🏃 健康提醒
- **起立放松**：每小时整点弹出提醒，活动身体
- **喝水提醒**：每 30 分钟（整点 + 半点）弹出提醒
- **工作时间**：周一至周五 9:00–20:30（含当月最后一个周六）
- **免打扰**：午休 12:00–14:00 + 晚餐 17:30–18:00 自动暂停

### 📝 报告提醒
| 日期 | 时间 | 类型 |
|------|------|------|
| 周一 | 20:00 | 📝 日报 |
| 周二 | 20:00 | 📝 日报 |
| 周三 | 17:00 | 📝 日报 |
| 周四 | 20:00 | 📝 日报 |
| 周五 | 17:00 | 📊 周报 |

### 🔕 免打扰模式
- 右键托盘 → **免打扰模式** → 选择 30 分钟 / 1 小时 / 2 小时 / 直到下班
- 到时自动恢复，无需手动操作
- 托盘图标和提示会显示剩余时间

### ⚙️ 设置面板
- 自定义提醒文字
- 开关各类提醒
- 调整工作时间、免打扰时段
- 设置弹窗自动关闭时间

## 🚀 快速开始

### 方式一：直接运行（推荐）

从 [Releases](../../releases) 下载 `TimerReminder.exe`，双击运行即可。

程序会在系统托盘显示时钟图标，右键可进行设置和管理。

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/Ch1hiro0814/Timer.git
cd Timer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

### 开机自启

将 `TimerReminder.exe` 快捷方式放入启动目录：

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

## 📦 打包

```bash
# 一键打包
build.bat

# 或手动
pyinstaller --onefile --windowed --name "TimerReminder" \
  --add-data "config.json;." \
  --add-data "assets;assets" \
  --hidden-import pystray \
  --hidden-import PIL \
  --hidden-import PIL.Image \
  --hidden-import PIL.ImageDraw \
  main.py
```

输出：`dist/TimerReminder.exe`

## 🛠 技术栈

- **Python 3.11+** + **tkinter** 原生 GUI
- **pystray** + **Pillow** 系统托盘
- **PyInstaller** 单文件打包

## 📁 项目结构

```
├── main.py              # 入口：初始化 → 调度器 → 系统托盘
├── config.py            # 配置管理（JSON 持久化）
├── scheduler.py         # 后台调度引擎（30s 轮询）
├── popup.py             # 弹窗组件（居中置顶、倒计时关闭）
├── tray_manager.py      # 系统托盘菜单、免打扰管理
├── settings_window.py   # 设置面板 GUI
├── utils.py             # 工作日判断、时间匹配工具
├── config.json          # 默认配置
├── build.bat            # 一键打包脚本
└── requirements.txt     # Python 依赖
```

## 🔧 配置说明

配置保存在 `%APPDATA%\TimerReminder\config.json`，首次运行自动生成。

关键配置项：
- `work_start_time` / `work_end_time` — 健康提醒起止时间
- `quiet_hours_*` — 午休免打扰时段
- `quiet_hours_2_*` — 晚餐免打扰时段
- `stand_up` / `water` — 开关及提醒文字
- `daily_report` / `weekly_report` — 报告提醒日程
