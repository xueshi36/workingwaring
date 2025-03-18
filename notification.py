"""
通知系统 - 负责发送桌面通知
"""

import platform
import os
import sys
from datetime import datetime
import log_manager

# 尝试导入plyer，如果失败提供备用方案
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    log_manager.warning("未安装plyer库，将使用备用通知方法")

# 尝试导入 win10toast 作为Windows上的备用选项
WIN10TOAST_AVAILABLE = False
if platform.system() == "Windows":
    try:
        from win10toast import ToastNotifier
        WIN10TOAST_AVAILABLE = True
    except ImportError:
        WIN10TOAST_AVAILABLE = False
        log_manager.warning("未安装win10toast库，将使用更基本的通知方法")

# 检测Windows版本
def get_windows_version():
    """获取Windows版本信息"""
    if platform.system() != "Windows":
        return None
    
    version = platform.version()
    win32_version = platform.win32_ver()[0]
    
    if win32_version == "10" or "10." in version:
        return 10
    elif win32_version == "8" or win32_version == "8.1" or "6.2" in version or "6.3" in version:
        return 8
    elif win32_version == "7" or "6.1" in version:
        return 7
    else:
        return None

# 获取Windows版本
WINDOWS_VERSION = get_windows_version()
if WINDOWS_VERSION:
    log_manager.info(f"检测到Windows {WINDOWS_VERSION}")

class NotificationSystem:
    def __init__(self):
        """初始化通知系统"""
        self.system = platform.system()
        self.notification_history = []
        self.win_toaster = None
        
        # 如果是Windows 10+，初始化ToastNotifier
        if WIN10TOAST_AVAILABLE and WINDOWS_VERSION and WINDOWS_VERSION >= 10:
            self.win_toaster = ToastNotifier()
        
        log_manager.info(f"通知系统初始化，操作系统: {self.system}")
        
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
                log_manager.info(f"发送通知(plyer): {title}")
                return True
            except Exception as e:
                log_manager.warning(f"通过plyer发送通知失败: {e}，尝试备用方法")
                return self._fallback_notification(title, message, timeout)
        else:
            # 使用备用通知方法
            return self._fallback_notification(title, message, timeout)
            
    def _fallback_notification(self, title, message, timeout=10):
        """备用通知方法，基于不同操作系统"""
        try:
            if self.system == "Windows":
                return self._windows_notification(title, message, timeout)
            elif self.system == "Darwin":  # macOS
                return self._macos_notification(title, message)
            elif self.system == "Linux":
                return self._linux_notification(title, message)
            else:
                log_manager.warning(f"未知操作系统: {self.system}，无法发送通知")
                return False
        except Exception as e:
            log_manager.error(f"备用通知失败: {e}")
            return False
            
    def _windows_notification(self, title, message, timeout=10):
        """Windows系统的备用通知方法，基于不同Windows版本使用不同方法"""
        # 使用win10toast（适用于Windows 10/11）
        if self.win_toaster:
            try:
                self.win_toaster.show_toast(
                    title, 
                    message, 
                    duration=min(timeout, 20),  # win10toast最大支持20秒
                    threaded=True  # 使用线程避免阻塞
                )
                log_manager.info(f"发送通知(win10toast): {title}")
                return True
            except Exception as e:
                log_manager.warning(f"通过win10toast发送通知失败: {e}，尝试PowerShell方法")
        
        # 尝试使用PowerShell (Windows 8+)
        if WINDOWS_VERSION and WINDOWS_VERSION >= 8:
            try:
                # 转义PowerShell中的特殊字符
                safe_title = title.replace('"', '`"').replace("'", "`'")
                safe_message = message.replace('"', '`"').replace("'", "`'")
                
                # PowerShell命令构建
                ps_command = f'''
                powershell -Command "
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
                
                $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
                $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
                $elements = $xml.GetElementsByTagName('text')
                $elements[0].AppendChild($xml.CreateTextNode('{safe_title}'))
                $elements[1].AppendChild($xml.CreateTextNode('{safe_message}'))
                
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('电脑使用时间监控').Show($toast)
                "
                '''
                
                # 静默运行PowerShell
                os.system(ps_command + " > nul 2>&1")
                log_manager.info(f"发送通知(PowerShell): {title}")
                return True
            except Exception as e:
                log_manager.warning(f"通过PowerShell发送通知失败: {e}，尝试消息框方法")
        
        # 最后使用消息框（适用于所有Windows版本）
        try:
            import ctypes
            # 使用无模态对话框，避免阻塞
            MB_SYSTEMMODAL = 0x00001000
            result = ctypes.windll.user32.MessageBoxW(0, message, title, MB_SYSTEMMODAL)
            log_manager.info(f"发送通知(MessageBox): {title}")
            return True
        except Exception as e:
            log_manager.error(f"通过消息框发送通知失败: {e}")
            return False
        
    def _macos_notification(self, title, message):
        """macOS系统的备用通知方法"""
        try:
            # 转义shell中的特殊字符
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_message = message.replace('"', '\\"').replace("'", "\\'")
            
            os.system(f"""osascript -e 'display notification "{safe_message}" with title "{safe_title}"'""")
            log_manager.info(f"发送通知(macOS): {title}")
            return True
        except Exception as e:
            log_manager.error(f"macOS通知失败: {e}")
            return False
        
    def _linux_notification(self, title, message):
        """Linux系统的备用通知方法"""
        try:
            # 转义shell中的特殊字符
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_message = message.replace('"', '\\"').replace("'", "\\'")
            
            os.system(f"""notify-send "{safe_title}" "{safe_message}" """)
            log_manager.info(f"发送通知(Linux): {title}")
            return True
        except Exception as e:
            log_manager.error(f"Linux通知失败: {e}")
            return False
        
    def get_notification_history(self):
        """获取通知历史"""
        return self.notification_history.copy() 