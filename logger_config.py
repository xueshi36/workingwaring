"""
日志配置模块 - 提供统一的日志配置接口
"""

import logging
import os
from datetime import datetime

# 日志目录
LOGS_DIR = "logs"

def setup_logging(debug_mode=False):
    """设置日志系统
    
    参数:
        debug_mode: 是否启用调试模式
    """
    # 确保日志目录存在
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    # 日志文件名（使用当前日期）
    log_file = os.path.join(LOGS_DIR, f"usage_monitor_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    # 设置日志级别
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    return logging.getLogger("root")

def get_logger(name):
    """获取指定名称的日志记录器
    
    参数:
        name: 日志记录器名称
        
    返回:
        logging.Logger: 日志记录器实例
    """
    # 如果根日志记录器未配置，先配置
    if not logging.getLogger().handlers:
        setup_logging()
        
    return logging.getLogger(name) 