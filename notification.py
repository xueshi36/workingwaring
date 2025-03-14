"""
通知系统 - 负责发送桌面通知
"""

import logging
import platform
from datetime import datetime

# 尝试导入plyer，如果失败提供备用方案
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    logging.warning("未安装plyer库，将使用备用通知方法")

class NotificationSystem:
    def __init__(self):
        """初始化通知系统"""
        self.system = platform.system()
        self.notification_history = []
        logging.info(f"通知系统初始化，操作系统: {self.system}")
        
    def send_notification(self, title, message, timeout=10):
        """发送桌面通知
        
        参数:
            title (str): 通知标题
            message (str): 通知内容
            timeout (int): 通知显示时间(秒)
        """
        # 记录通知历史
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.notification_history.append({
            "timestamp": timestamp,
            "title": title,
            "message": message
        })
        
        # 使用plyer发送通知
        if PLYER_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="电脑使用时间监控",
                    timeout=timeout
                )
                logging.info(f"发送通知: {title}")
                return True
            except Exception as e:
                logging.error(f"通知发送失败: {e}")
                self._fallback_notification(title, message)
                return False
        else:
            # 使用备用通知方法
            return self._fallback_notification(title, message)
            
    def _fallback_notification(self, title, message):
        """备用通知方法，基于不同操作系统"""
        try:
            if self.system == "Windows":
                self._windows_notification(title, message)
            elif self.system == "Darwin":  # macOS
                self._macos_notification(title, message)
            elif self.system == "Linux":
                self._linux_notification(title, message)
            else:
                logging.warning(f"未知操作系统: {self.system}，无法发送通知")
                return False
            return True
        except Exception as e:
            logging.error(f"备用通知失败: {e}")
            return False
            
    def _windows_notification(self, title, message):
        """Windows系统的备用通知方法"""
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0)
        
    def _macos_notification(self, title, message):
        """macOS系统的备用通知方法"""
        import os
        os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
        
    def _linux_notification(self, title, message):
        """Linux系统的备用通知方法"""
        import os
        os.system(f"""notify-send "{title}" "{message}" """)
        
    def get_notification_history(self):
        """获取通知历史"""
        return self.notification_history.copy() 