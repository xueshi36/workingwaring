"""
通知系统 - 负责发送桌面通知
"""

import platform
import os
import sys
import subprocess
import tempfile
from datetime import datetime
import log_manager

# 尝试导入plyer，如果失败提供备用方案
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    log_manager.warning("未安装plyer库，将使用备用通知方法")

# 检测Windows版本
def get_windows_version():
    """获取Windows版本信息"""
    if platform.system() != "Windows":
        return None
    
    version = platform.version()
    win32_version = platform.win32_ver()[0]
    
    if win32_version == "10" or "10." in version:
        return 10
    elif win32_version == "11" or "11." in version:
        return 11
    elif win32_version == "8" or win32_version == "8.1" or "6.2" in version or "6.3" in version:
        return 8
    elif win32_version == "7" or "6.1" in version:
        return 7
    else:
        # 尝试通过更详细的方法检测
        try:
            import ctypes
            version_info = ctypes.windll.kernel32.GetVersion()
            major = version_info & 0xFF
            minor = (version_info >> 8) & 0xFF
            build = (version_info >> 16) & 0xFFFF
            
            if major == 10 and build >= 22000:
                return 11  # Windows 11
            elif major == 10:
                return 10  # Windows 10
            elif major == 6 and minor == 3:
                return 8.1  # Windows 8.1
            elif major == 6 and minor == 2:
                return 8  # Windows 8
            elif major == 6 and minor == 1:
                return 7  # Windows 7
            else:
                return None
        except:
            return None

# 获取Windows版本
WINDOWS_VERSION = get_windows_version()
if WINDOWS_VERSION:
    log_manager.info(f"检测到Windows {WINDOWS_VERSION}")
else:
    log_manager.warning("无法精确检测Windows版本")

# Windows 7通知支持 - 生成VBS脚本
def create_win7_notification_script(title, message, timeout=10):
    """创建Windows 7通知脚本"""
    vbs_script = f'''
    Set objShell = CreateObject("WScript.Shell")
    objShell.Popup "{message}", {timeout}, "{title}", 64
    '''
    
    # 创建临时脚本文件
    fd, path = tempfile.mkstemp(suffix='.vbs')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(vbs_script)
        return path
    except Exception as e:
        log_manager.error(f"创建Win7通知脚本失败: {e}")
        return None

# Windows 10通知脚本
def create_win10_notification_script(title, message, timeout=10):
    """创建Windows 10通知PowerShell脚本"""
    # 转义PowerShell中的特殊字符
    safe_title = title.replace('"', '`"').replace("'", "`'")
    safe_message = message.replace('"', '`"').replace("'", "`'")
    
    ps_script = f'''
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
    
    $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
    $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
    
    # 添加标题和消息
    $elements = $xml.GetElementsByTagName('text')
    $elements[0].AppendChild($xml.CreateTextNode('{safe_title}'))
    $elements[1].AppendChild($xml.CreateTextNode('{safe_message}'))
    
    # 设置通知不自动消失
    $node = $xml.SelectSingleNode('/toast')
    $node.SetAttribute('duration', 'long')
    
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('电脑使用时间监控').Show($toast)
    '''
    
    # 创建临时脚本文件
    fd, path = tempfile.mkstemp(suffix='.ps1')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(ps_script)
        return path
    except Exception as e:
        log_manager.error(f"创建Win10通知脚本失败: {e}")
        return None

class NotificationSystem:
    def __init__(self):
        """初始化通知系统"""
        self.system = platform.system()
        self.notification_history = []
        
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
        
        # 根据平台选择合适的通知方法
        if self.system == "Windows":
            return self._send_windows_notification(title, message, timeout)
        else:
            # 非Windows系统使用plyer或其他方法
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
    
    def _send_windows_notification(self, title, message, timeout=10):
        """根据Windows版本选择最佳通知方法"""
        # 首先尝试使用plyer
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
                log_manager.warning(f"通过plyer发送通知失败: {e}，尝试特定Windows方法")
        
        # 根据Windows版本选择合适的通知方法
        if WINDOWS_VERSION in [10, 11]:
            return self._send_win10_notification(title, message, timeout)
        elif WINDOWS_VERSION in [7, 8, 8.1]:
            return self._send_legacy_windows_notification(title, message, timeout)
        else:
            # 无法确定版本，使用消息框作为后备
            return self._send_message_box(title, message)
    
    def _send_win10_notification(self, title, message, timeout=10):
        """使用PowerShell脚本发送Windows 10+通知"""
        try:
            script_path = create_win10_notification_script(title, message, timeout)
            if script_path:
                # 使用PowerShell执行脚本
                cmd = f'powershell -ExecutionPolicy Bypass -File "{script_path}"'
                subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                log_manager.info(f"发送通知(Win10 PowerShell): {title}")
                
                # 延迟删除脚本文件
                try:
                    import threading
                    def delete_file():
                        import time
                        time.sleep(timeout + 5)  # 等待通知显示完毕再删除
                        try:
                            os.remove(script_path)
                        except:
                            pass
                    threading.Thread(target=delete_file, daemon=True).start()
                except:
                    pass
                    
                return True
            else:
                # 脚本创建失败，使用消息框
                return self._send_message_box(title, message)
        except Exception as e:
            log_manager.error(f"Windows 10通知失败: {e}")
            return self._send_message_box(title, message)
    
    def _send_legacy_windows_notification(self, title, message, timeout=10):
        """发送Windows 7/8通知"""
        try:
            script_path = create_win7_notification_script(title, message, timeout)
            if script_path:
                subprocess.Popen(['wscript', script_path], shell=True)
                log_manager.info(f"发送通知(Win7 VBS): {title}")
                
                # 延迟删除脚本文件
                try:
                    import threading
                    def delete_file():
                        import time
                        time.sleep(timeout + 5)  # 等待通知显示完毕再删除
                        try:
                            os.remove(script_path)
                        except:
                            pass
                    threading.Thread(target=delete_file, daemon=True).start()
                except:
                    pass
                
                return True
            else:
                return self._send_message_box(title, message)
        except Exception as e:
            log_manager.error(f"传统Windows通知失败: {e}")
            return self._send_message_box(title, message)
            
    def _send_message_box(self, title, message):
        """使用MessageBox显示通知（适用于所有Windows版本）"""
        try:
            import ctypes
            # 使用无模态对话框，避免阻塞
            MB_SYSTEMMODAL = 0x00001000
            MB_ICONINFORMATION = 0x00000040
            # 在消息框中增加图标
            result = ctypes.windll.user32.MessageBoxW(0, message, title, MB_SYSTEMMODAL | MB_ICONINFORMATION)
            log_manager.info(f"发送通知(MessageBox): {title}")
            return True
        except Exception as e:
            log_manager.error(f"通过消息框发送通知失败: {e}")
            return False
            
    def _fallback_notification(self, title, message, timeout=10):
        """备用通知方法，基于不同操作系统"""
        try:
            if self.system == "Darwin":  # macOS
                return self._macos_notification(title, message)
            elif self.system == "Linux":
                return self._linux_notification(title, message)
            else:
                log_manager.warning(f"未知操作系统: {self.system}，无法发送通知")
                return False
        except Exception as e:
            log_manager.error(f"备用通知失败: {e}")
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
            
            # 尝试使用notify-send的持久选项
            os.system(f"""notify-send -t 0 "{safe_title}" "{safe_message}" """)
            log_manager.info(f"发送通知(Linux): {title}")
            return True
        except Exception as e:
            log_manager.error(f"Linux通知失败: {e}")
            return False
        
    def get_notification_history(self):
        """获取通知历史"""
        return self.notification_history.copy() 