"""
时间跟踪模块 - 负责统计活动时间并触发相应事件
"""

import time
import threading
import logging
from datetime import datetime
import config

class TimeTracker:
    def __init__(self, activity_monitor, notification_system, db_manager=None):
        """初始化时间跟踪器"""
        self.activity_monitor = activity_monitor
        self.notification_system = notification_system
        self.db_manager = db_manager  # 新增数据库管理器
        self.continuous_usage_minutes = 0
        self.inactive_minutes = 0
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.daily_usage_minutes = 0
        self.usage_log = {}  # 格式: {日期: 使用分钟数}
        self.today = datetime.now().strftime("%Y-%m-%d")
        
    def start(self):
        """启动时间跟踪"""
        if self.running:
            return
            
        self.running = True
        self.activity_monitor.start()
        self.thread = threading.Thread(target=self._tracking_loop)
        self.thread.daemon = True
        self.thread.start()
        logging.info("时间跟踪已启动")
        
    def stop(self):
        """停止时间跟踪"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.activity_monitor.stop()
        logging.info("时间跟踪已停止")
        
    def _tracking_loop(self):
        """主时间跟踪循环"""
        while self.running:
            # 等待固定的检查间隔
            time.sleep(config.ACTIVITY_CHECK_INTERVAL * 60)
            
            # 检查当前日期，如果是新的一天则重置每日统计
            current_date = datetime.now().strftime("%Y-%m-%d")
            if current_date != self.today:
                self._save_daily_usage()
                self.today = current_date
                self.daily_usage_minutes = 0
            
            # 检查活动状态
            activity_data = self.activity_monitor.check_activity_minute()
            is_active = activity_data["is_active"]
            
            # 记录到数据库
            if self.db_manager:
                self.db_manager.record_minute_activity(
                    datetime.now(),
                    is_active,
                    activity_data["mouse_moves"],
                    activity_data["key_presses"]
                )
            
            with self.lock:
                if is_active:
                    # 用户活跃，增加连续使用时间
                    self.continuous_usage_minutes += 1
                    self.daily_usage_minutes += 1
                    self.inactive_minutes = 0
                    
                    # 检查是否需要发送提醒
                    if (self.continuous_usage_minutes > 0 and 
                        self.continuous_usage_minutes % config.CONTINUOUS_USAGE_ALERT == 0):
                        self._send_usage_alert()
                else:
                    # 用户不活跃，增加不活跃时间
                    self.inactive_minutes += 1
                    
                    # 检查是否需要重置计时器
                    if self.inactive_minutes >= config.INACTIVITY_RESET:
                        self._reset_usage_timer()
                        
            logging.debug(f"连续使用: {self.continuous_usage_minutes}分钟, 不活跃: {self.inactive_minutes}分钟")
                
    def _send_usage_alert(self):
        """发送使用时间提醒"""
        message = config.NOTIFICATION_MESSAGE.format(self.continuous_usage_minutes)
        self.notification_system.send_notification(
            config.NOTIFICATION_TITLE, 
            message
        )
        logging.info(f"发送使用提醒: {self.continuous_usage_minutes}分钟")
        
    def _reset_usage_timer(self):
        """重置连续使用计时器"""
        prev_usage = self.continuous_usage_minutes
        self.continuous_usage_minutes = 0
        self.inactive_minutes = 0
        logging.info(f"重置使用计时器。之前连续使用了{prev_usage}分钟")
        
    def _save_daily_usage(self):
        """保存每日使用数据"""
        self.usage_log[self.today] = self.daily_usage_minutes
        logging.info(f"保存每日使用数据: {self.today} - {self.daily_usage_minutes}分钟")
        
    def get_usage_stats(self):
        """获取使用统计数据"""
        with self.lock:
            return {
                "continuous_usage_minutes": self.continuous_usage_minutes,
                "inactive_minutes": self.inactive_minutes,
                "daily_usage_minutes": self.daily_usage_minutes,
                "usage_log": self.usage_log.copy()
            }
        
    def reset(self):
        """重置所有计时器"""
        with self.lock:
            self.continuous_usage_minutes = 0
            self.inactive_minutes = 0
            self.activity_monitor.reset() 