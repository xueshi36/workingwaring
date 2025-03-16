"""
时间跟踪模块 - 负责统计活动时间并触发相应事件
"""

import time
import threading
from datetime import datetime
import config
import log_manager

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
        log_manager.info("时间跟踪器初始化完成")
        
    def start(self):
        """启动时间跟踪"""
        if self.running:
            return
            
        self.running = True
        self.activity_monitor.start()
        self.thread = threading.Thread(target=self._tracking_loop)
        self.thread.daemon = True
        self.thread.start()
        log_manager.info("时间跟踪已启动")
        
    def stop(self):
        """停止时间跟踪"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.activity_monitor.stop()
        log_manager.info("时间跟踪已停止")
        
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
                log_manager.info(f"检测到新的一天: {current_date}，重置每日使用统计")
            
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
                        
            log_manager.debug(f"连续使用: {self.continuous_usage_minutes}分钟, 不活跃: {self.inactive_minutes}分钟")
                
    def _send_usage_alert(self):
        """发送使用时间提醒"""
        message = config.NOTIFICATION_MESSAGE.format(self.continuous_usage_minutes)
        self.notification_system.send_notification(
            config.NOTIFICATION_TITLE, 
            message
        )
        log_manager.log_activity_alert(self.continuous_usage_minutes)
        
    def _reset_usage_timer(self):
        """重置连续使用计时器"""
        prev_usage = self.continuous_usage_minutes
        self.continuous_usage_minutes = 0
        self.inactive_minutes = 0
        log_manager.log_activity_reset(f"超过{config.INACTIVITY_RESET}分钟无活动")
        log_manager.info(f"之前连续使用了{prev_usage}分钟")
        
    def _save_daily_usage(self):
        """保存每日使用数据"""
        self.usage_log[self.today] = self.daily_usage_minutes
        log_manager.info(f"保存每日使用数据: {self.today} - {self.daily_usage_minutes}分钟")
        
        # 如果有数据库管理器，更新每日汇总
        if self.db_manager:
            self.db_manager.update_daily_summary(
                self.today, 
                self.daily_usage_minutes
            )
            log_manager.info(f"已更新数据库每日汇总: {self.today}")
        
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
            prev_continuous = self.continuous_usage_minutes
            self.continuous_usage_minutes = 0
            self.inactive_minutes = 0
            self.activity_monitor.reset() 
            log_manager.log_activity_reset("用户手动重置")
            log_manager.info(f"已重置连续使用时间，之前为 {prev_continuous} 分钟") 