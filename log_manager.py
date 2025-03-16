"""
日志管理器 - 负责统一管理程序日志

提供统一的日志配置和记录方法
"""

import os
import logging
import sys
from datetime import datetime

# 日志级别常量
INFO = logging.INFO
DEBUG = logging.DEBUG
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# 存储日志记录器实例
_logger = None

def setup_logger(debug_mode=False, log_file=None):
    """
    设置日志记录器
    
    参数:
        debug_mode: 是否启用调试模式
        log_file: 日志文件路径，默认为logs目录下的当天日期命名的文件
    """
    global _logger
    
    # 如果已经设置过，直接返回
    if _logger is not None:
        return _logger
    
    # 创建logger
    _logger = logging.getLogger('computer_usage_monitor')
    
    # 设置日志级别
    level = logging.DEBUG if debug_mode else logging.INFO
    _logger.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_file is None:
        # 确保日志目录存在
        logs_dir = 'logs'
        if getattr(sys, 'frozen', False):
            # 如果是打包后的EXE
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        logs_dir = os.path.join(base_path, logs_dir)
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # 使用日期命名日志文件
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'usage_monitor_{today}.log')
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    
    # 记录程序启动日志
    _logger.info("==========================================")
    _logger.info("电脑使用时间监控程序启动")
    _logger.info(f"日志级别: {'调试模式' if debug_mode else '正常模式'}")
    _logger.info(f"日志文件: {log_file}")
    _logger.info("==========================================")
    
    return _logger

def get_logger():
    """
    获取日志记录器实例
    
    如果尚未设置，则使用默认配置设置
    """
    global _logger
    
    if _logger is None:
        return setup_logger()
    
    return _logger

# 便捷的日志记录函数
def info(message):
    """记录信息级别日志"""
    get_logger().info(message)
    
def debug(message):
    """记录调试级别日志"""
    get_logger().debug(message)
    
def warning(message):
    """记录警告级别日志"""
    get_logger().warning(message)
    
def error(message):
    """记录错误级别日志"""
    get_logger().error(message)
    
def critical(message):
    """记录严重错误级别日志"""
    get_logger().critical(message)

# 特定事件的日志记录函数
def log_app_start(version="1.0.0"):
    """记录应用程序启动事件"""
    info(f"应用程序启动 [版本 {version}]")
    
def log_app_exit():
    """记录应用程序退出事件"""
    info("应用程序正常退出")
    
def log_activity_alert(minutes):
    """记录连续活动预警事件"""
    warning(f"连续活动预警: 已连续使用电脑 {minutes} 分钟")
    
def log_activity_reset(reason="用户无活动"):
    """记录活动计时器重置事件"""
    info(f"活动计时器已重置: {reason}")
    
def log_report_generation(report_path):
    """记录报告生成事件"""
    info(f"已生成使用报告: {report_path}")
    
def log_config_change(key, value):
    """记录配置变更事件"""
    info(f"配置已更改: {key} = {value}")
    
def log_error_detail(error_type, details):
    """记录详细错误信息"""
    error(f"{error_type}错误: {details}")
    
def log_system_info():
    """记录系统信息"""
    import platform
    system_info = f"操作系统: {platform.system()} {platform.version()}"
    python_info = f"Python版本: {platform.python_version()}"
    info(system_info)
    info(python_info) 