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
        self.db_manager = db_manager  # 数据库管理器
        self.continuous_usage_minutes = 0
        self.inactive_minutes = 0
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.daily_usage_minutes = 0
        self.usage_log = {}  # 格式: {日期: 使用分钟数}
        # 在初始化时获取当前日期
        self.today = datetime.now().strftime("%Y-%m-%d")
        # 上次检查的日期，用于确保日期变更检测的可靠性
        self.last_check_date = self.today
        
        # 连续通知相关属性
        self.continuous_notification_active = False  # 是否当前启用了连续通知
        self.last_notification_time = 0  # 上次发送通知的时间点（分钟）
        
        log_manager.info("时间跟踪器初始化完成")
        
    def start(self):
        """启动时间跟踪"""
        if self.running:
            return
            
        self.running = True
        # 确保启动时获取最新日期
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.last_check_date = self.today
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
            
            # 日期变更处理
            if current_date != self.today:
                log_manager.info(f"检测到日期变更: {self.today} -> {current_date}")
                
                # 保存前一天的使用数据
                self._save_daily_usage()
                
                # 更新日期并重置计数器
                self.today = current_date
                self.last_check_date = current_date
                self.daily_usage_minutes = 0
                
                # 确保活动监控器在新的一天正常工作
                self.activity_monitor.reset()
                
                log_manager.info(f"已重置每日使用统计，新日期: {current_date}")
            
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
                # 再次检查日期，确保在长时间暂停后恢复时能正确处理日期变更
                check_date = datetime.now().strftime("%Y-%m-%d")
                if check_date != self.last_check_date:
                    log_manager.info(f"锁内检测到日期变更: {self.last_check_date} -> {check_date}")
                    # 如果日期已变更但还未处理，先保存昨日数据
                    if self.today != check_date:
                        self._save_daily_usage()
                        self.today = check_date
                        self.daily_usage_minutes = 0
                        # 确保活动监控器在新的一天正常工作
                        self.activity_monitor.reset()
                        log_manager.info(f"锁内已重置每日使用统计，新日期: {check_date}")
                    self.last_check_date = check_date
                
                if is_active:
                    # 用户活跃，增加连续使用时间
                    self.continuous_usage_minutes += 1
                    self.daily_usage_minutes += 1
                    self.inactive_minutes = 0
                    
                    # 记录调试信息
                    log_manager.debug(f"检测到活动：日期={self.today}, 连续使用={self.continuous_usage_minutes}分钟, 今日使用={self.daily_usage_minutes}分钟")
                    
                    # 检查是否需要发送提醒
                    if (self.continuous_usage_minutes > 0 and 
                        self.continuous_usage_minutes % config.CONTINUOUS_USAGE_ALERT == 0):
                        self._send_usage_alert()
                        # 第一次达到阈值时，启用连续通知（如果配置允许）
                        if (config.ENABLE_CONTINUOUS_NOTIFICATION and 
                            not self.continuous_notification_active and 
                            self.continuous_usage_minutes == config.CONTINUOUS_USAGE_ALERT):
                            self.continuous_notification_active = True
                            self.last_notification_time = self.continuous_usage_minutes
                            log_manager.info("已启用连续通知功能")
                    
                    # 检查是否需要发送连续通知
                    elif (self.continuous_notification_active and 
                         (self.continuous_usage_minutes - self.last_notification_time) >= config.CONTINUOUS_NOTIFICATION_INTERVAL):
                        self._send_continuous_notification()
                        self.last_notification_time = self.continuous_usage_minutes
                        
                else:
                    # 用户不活跃，增加不活跃时间
                    self.inactive_minutes += 1
                    
                    # 检查是否需要重置计时器
                    if self.inactive_minutes >= config.INACTIVITY_RESET:
                        self._reset_usage_timer()
                        
            log_manager.debug(f"连续使用: {self.continuous_usage_minutes}分钟, 不活跃: {self.inactive_minutes}分钟, 今日使用: {self.daily_usage_minutes}分钟")
                
    def _send_usage_alert(self):
        """发送使用时间提醒"""
        message = config.NOTIFICATION_MESSAGE.format(self.continuous_usage_minutes)
        self.notification_system.send_notification(
            config.NOTIFICATION_TITLE, 
            message
        )
        log_manager.log_activity_alert(self.continuous_usage_minutes)
        
    def _send_continuous_notification(self):
        """发送连续通知提醒"""
        try:
            # 使用配置中的消息模板
            message = config.CONTINUOUS_NOTIFICATION_MESSAGE.format(
                self.continuous_usage_minutes,
                config.INACTIVITY_RESET
            )
            
            result = self.notification_system.send_notification(
                config.CONTINUOUS_NOTIFICATION_TITLE, 
                message,
                timeout=15  # 延长通知显示时间
            )
            log_manager.info(f"发送连续通知: 已连续使用{self.continuous_usage_minutes}分钟")
            return result
        except Exception as e:
            log_manager.error(f"发送连续通知失败: {e}")
            return False
        
    def _reset_usage_timer(self):
        """重置连续使用计时器"""
        prev_usage = self.continuous_usage_minutes
        self.continuous_usage_minutes = 0
        self.inactive_minutes = 0
        
        # 停用连续通知
        if self.continuous_notification_active:
            self.continuous_notification_active = False
            self.last_notification_time = 0
            log_manager.info("已停用连续通知功能")
            
        log_manager.log_activity_reset(f"超过{config.INACTIVITY_RESET}分钟无活动")
        log_manager.info(f"之前连续使用了{prev_usage}分钟")
        
    def _save_daily_usage(self):
        """保存每日使用数据"""
        log_manager.info(f"保存每日使用数据: {self.today} - {self.daily_usage_minutes}分钟")
        self.usage_log[self.today] = self.daily_usage_minutes
        
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
            # 确保返回最新日期的数据
            current_date = datetime.now().strftime("%Y-%m-%d")
            if current_date != self.today:
                log_manager.info(f"获取统计数据时检测到日期变更: {self.today} -> {current_date}")
                self._save_daily_usage()
                self.today = current_date
                self.daily_usage_minutes = 0
            
            return {
                "continuous_usage_minutes": self.continuous_usage_minutes,
                "inactive_minutes": self.inactive_minutes,
                "daily_usage_minutes": self.daily_usage_minutes,
                "usage_log": self.usage_log.copy(),
                "continuous_notification_active": self.continuous_notification_active,
                "current_date": self.today
            }
        
    def reset(self):
        """重置所有计时器"""
        with self.lock:
            prev_continuous = self.continuous_usage_minutes
            self.continuous_usage_minutes = 0
            self.inactive_minutes = 0
            
            # 确保当前日期是最新的
            current_date = datetime.now().strftime("%Y-%m-%d")
            if current_date != self.today:
                self._save_daily_usage()
                self.today = current_date
                self.daily_usage_minutes = 0
                log_manager.info(f"重置时检测到日期变更: {self.today}")
            
            # 停用连续通知
            if self.continuous_notification_active:
                self.continuous_notification_active = False
                self.last_notification_time = 0
                log_manager.info("用户手动重置: 已停用连续通知功能")
                
            self.activity_monitor.reset() 
            log_manager.log_activity_reset("用户手动重置")
            log_manager.info(f"已重置连续使用时间，之前为 {prev_continuous} 分钟") 