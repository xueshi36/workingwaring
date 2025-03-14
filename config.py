"""
电脑使用时间监控工具的配置文件
"""

# 时间监控设置（分钟）
ACTIVITY_CHECK_INTERVAL = 1  # 每隔多少分钟检查一次活动
CONTINUOUS_USAGE_ALERT = 60  # 连续使用多少分钟后提醒
INACTIVITY_RESET = 10  # 多少分钟无活动后重置计时器

# 用户界面设置
APP_NAME = "电脑使用时间监控工具"
NOTIFICATION_TITLE = "休息提醒"
NOTIFICATION_MESSAGE = "您已连续使用电脑{}分钟，建议休息一下眼睛和身体！"

# 数据和报告设置
DATABASE_PATH = "usage_data.db"  # 数据库文件路径
REPORTS_DIR = "reports"  # 报告输出目录
REPORT_DAYS = 30  # 报告显示的天数

# 调试模式
DEBUG = False  # 设置为True以显示详细日志

# 系统托盘图标设置
TRAY_TOOLTIP = "电脑使用时间监控"
TRAY_ICON_PATH = "icon.ico"  # 如果有图标的话 

# 自动报告设置
AUTO_REPORT_ENABLED = True  # 是否启用自动报告生成
AUTO_REPORT_INTERVAL = 30  # 自动报告生成间隔(分钟)

# UI窗口设置
UI_WINDOW_TITLE = "电脑使用时间监控"
UI_UPDATE_INTERVAL = 1  # UI更新间隔(秒) 