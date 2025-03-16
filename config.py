"""
配置文件接口 - 提供对配置的统一访问

这个模块作为配置的接口层，实际配置由config_manager管理
"""

from config_manager import config_manager, DEFAULT_CONFIG

# 时间监控设置（分钟）
ACTIVITY_CHECK_INTERVAL = config_manager.get("ACTIVITY_CHECK_INTERVAL", 1)  
CONTINUOUS_USAGE_ALERT = config_manager.get("CONTINUOUS_USAGE_ALERT", 60)  
INACTIVITY_RESET = config_manager.get("INACTIVITY_RESET", 10)  

# 用户界面设置
APP_NAME = config_manager.get("APP_NAME", "电脑使用时间监控工具")
NOTIFICATION_TITLE = config_manager.get("NOTIFICATION_TITLE", "休息提醒")
NOTIFICATION_MESSAGE = config_manager.get("NOTIFICATION_MESSAGE", "您已连续使用电脑{}分钟，建议休息一下眼睛和身体！")

# 数据和报告设置
DATABASE_PATH = config_manager.get("DATABASE_PATH", "usage_data.db")
REPORTS_DIR = config_manager.get("REPORTS_DIR", "reports")
REPORT_DAYS = config_manager.get("REPORT_DAYS", 30)

# 自动报告设置
AUTO_REPORT_ENABLED = config_manager.get("AUTO_REPORT_ENABLED", True)
AUTO_REPORT_INTERVAL = config_manager.get("AUTO_REPORT_INTERVAL", 60)

# 调试模式
DEBUG = config_manager.get("DEBUG", False)

# 系统托盘图标设置
TRAY_TOOLTIP = config_manager.get("TRAY_TOOLTIP", "电脑使用时间监控")
TRAY_ICON_PATH = config_manager.get("TRAY_ICON_PATH", "icon.ico")

# UI窗口设置
UI_WINDOW_TITLE = config_manager.get("UI_WINDOW_TITLE", "电脑使用时间监控")
UI_UPDATE_INTERVAL = config_manager.get("UI_UPDATE_INTERVAL", 1)

# 用于保存配置的函数
def save_config(key, value):
    """保存配置项
    
    参数:
        key (str): 配置项名称
        value: 配置项值
        
    返回:
        bool: 是否保存成功
    """
    result = config_manager.set(key, value)
    
    # 更新本模块中的变量
    if result and key in globals():
        globals()[key] = value
        
    return result

# 重新加载配置
def reload_config():
    """重新加载配置文件"""
    config_manager.load_config()
    
    # 更新本模块中的所有变量
    for key in DEFAULT_CONFIG.keys():
        if key in globals():
            globals()[key] = config_manager.get(key)

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