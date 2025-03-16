"""
配置管理器 - 负责读取和保存配置文件

处理配置文件的读取、保存和默认值管理
"""

import os
import json
import logging
import sys
import log_manager

# 默认配置
DEFAULT_CONFIG = {
    "ACTIVITY_CHECK_INTERVAL": 1,
    "CONTINUOUS_USAGE_ALERT": 60,
    "INACTIVITY_RESET": 10,
    "APP_NAME": "电脑使用时间监控工具",
    "NOTIFICATION_TITLE": "休息提醒",
    "NOTIFICATION_MESSAGE": "您已连续使用电脑{}分钟，建议休息一下眼睛和身体！",
    "DATABASE_PATH": "usage_data.db",
    "REPORTS_DIR": "reports",
    "REPORT_DAYS": 30,
    "AUTO_REPORT_ENABLED": True,
    "AUTO_REPORT_INTERVAL": 60,
    "DEBUG": False,
    "TRAY_TOOLTIP": "电脑使用时间监控",
    "TRAY_ICON_PATH": "icon.ico",
    "UI_WINDOW_TITLE": "电脑使用时间监控",
    "UI_UPDATE_INTERVAL": 1
}

class ConfigManager:
    """配置管理器类，负责处理配置的读取和保存"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = {}
        self.config_file = self._get_config_file_path()
        self.load_config()
        
    def _get_config_file_path(self):
        """获取配置文件路径"""
        # 如果是打包后的EXE，使用执行文件所在目录
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境，使用脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        return os.path.join(base_path, "config.json")
        
    def load_config(self):
        """加载配置文件"""
        try:
            # 如果配置文件存在，加载它
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # 更新配置，保留默认值作为后备
                self.config = DEFAULT_CONFIG.copy()
                
                # 将加载的配置转换为大写键，与默认配置匹配
                for key, value in loaded_config.items():
                    upper_key = key.upper()
                    # 如果是默认配置中的键，使用加载的值
                    if upper_key in self.config:
                        self.config[upper_key] = value
                    else:
                        # 否则使用原始的键（可能是新增的配置）
                        self.config[key] = value
                        
                log_manager.info(f"已加载配置文件: {self.config_file}")
            else:
                # 如果配置文件不存在，使用默认配置并创建文件
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
                log_manager.info(f"已创建默认配置文件: {self.config_file}")
        except Exception as e:
            # 如果发生错误，使用默认配置
            self.config = DEFAULT_CONFIG.copy()
            log_manager.error(f"加载配置文件失败，使用默认配置: {e}")
            
    def save_config(self):
        """保存配置到文件"""
        try:
            # 创建转换为小写键的配置，更符合JSON标准
            save_config = {}
            for key, value in self.config.items():
                # 转换键为小写形式
                save_config[key.lower()] = value
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, ensure_ascii=False, indent=4)
                
            log_manager.info(f"已保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            log_manager.error(f"保存配置文件失败: {e}")
            return False
            
    def get(self, key, default=None):
        """获取配置项
        
        参数:
            key (str): 配置项键名
            default: 默认值，如果配置项不存在则返回此值
            
        返回:
            配置项的值
        """
        # 尝试使用大写键
        upper_key = key.upper()
        if upper_key in self.config:
            return self.config[upper_key]
        
        # 尝试使用原始键
        if key in self.config:
            return self.config[key]
            
        # 都不存在，返回默认值
        return default
        
    def set(self, key, value):
        """设置配置项
        
        参数:
            key (str): 配置项键名
            value: 配置项值
            
        返回:
            bool: 是否设置成功
        """
        try:
            # 优先使用大写键
            upper_key = key.upper()
            if upper_key in self.config:
                self.config[upper_key] = value
                log_manager.log_config_change(upper_key, value)
            else:
                # 不在默认配置中，使用原始键
                self.config[key] = value
                log_manager.log_config_change(key, value)
                
            # 保存更改
            return self.save_config()
        except Exception as e:
            log_manager.error(f"设置配置项失败 {key}: {e}")
            return False
    
    def reset_to_default(self):
        """重置所有配置为默认值"""
        self.config = DEFAULT_CONFIG.copy()
        log_manager.info("已将所有设置重置为默认值")
        return self.save_config()
        
# 创建全局配置管理器实例
config_manager = ConfigManager() 