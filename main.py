"""
电脑使用时间监控工具 - 主程序入口

监控用户连续使用电脑的时间，并在适当时间提醒用户休息。
记录使用数据并提供可视化统计报告。
"""

import sys
import time
import threading
import argparse
import atexit
import webbrowser
import os
from datetime import datetime

import config
import log_manager
from activity_monitor import ActivityMonitor
from time_tracker import TimeTracker
from notification import NotificationSystem
from db_manager import DatabaseManager
from visualization import UsageVisualizer

# 版本信息
VERSION = "1.1.0"

# 尝试导入系统托盘相关库
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    log_manager.warning("未安装pystray或PIL库，将不使用系统托盘图标")

# 导入UI监视器
from ui_monitor import MonitorWindow, set_tray_available

# 设置UI模块中的系统托盘状态
set_tray_available(TRAY_AVAILABLE)

class ComputerUsageMonitor:
    def __init__(self):
        """初始化电脑使用时间监控工具"""
        # 设置日志
        log_manager.setup_logger(debug_mode=config.DEBUG)
        log_manager.log_app_start(VERSION)
        log_manager.log_system_info()
        
        # 创建输出目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的EXE
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        reports_dir = os.path.join(base_path, config.REPORTS_DIR if hasattr(config, 'REPORTS_DIR') else "reports")
        try:
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir, exist_ok=True)
                log_manager.info(f"创建报告目录: {reports_dir}")
            else:
                # 测试目录权限
                test_file = os.path.join(reports_dir, "test.txt")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                except Exception as e:
                    log_manager.warning(f"报告目录权限测试失败，尝试替代路径: {e}")
                    # 尝试使用用户目录
                    alt_reports_dir = os.path.join(os.path.expanduser("~"), "usage_monitor_reports")
                    try:
                        if not os.path.exists(alt_reports_dir):
                            os.makedirs(alt_reports_dir, exist_ok=True)
                        reports_dir = alt_reports_dir
                        log_manager.info(f"将使用替代报告目录: {reports_dir}")
                    except Exception as e2:
                        log_manager.error(f"创建替代报告目录也失败: {e2}")
                        # 使用当前目录
                        reports_dir = os.path.abspath(".")
                        log_manager.warning(f"将使用当前目录: {reports_dir}")
        except Exception as e:
            log_manager.error(f"创建报告目录失败: {e}")
            # 尝试使用当前目录
            reports_dir = os.path.abspath(".")
            log_manager.warning(f"将使用当前目录作为报告目录: {reports_dir}")
        
        # 确保日志目录存在
        logs_dir = os.path.join(base_path, "logs")
        try:
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir, exist_ok=True)
                log_manager.info(f"创建日志目录: {logs_dir}")
        except Exception as e:
            log_manager.error(f"创建日志目录失败: {e}")
            # 尝试使用用户目录
            try:
                alt_logs_dir = os.path.join(os.path.expanduser("~"), "usage_monitor_logs")
                if not os.path.exists(alt_logs_dir):
                    os.makedirs(alt_logs_dir, exist_ok=True)
                logs_dir = alt_logs_dir
                log_manager.info(f"将使用替代日志目录: {logs_dir}")
            except Exception as e2:
                log_manager.error(f"创建替代日志目录也失败: {e2}")
                # 使用当前目录
                logs_dir = os.path.abspath(".")
                log_manager.warning(f"将使用当前目录作为日志目录: {logs_dir}")
        
        # 初始化组件
        log_manager.info("正在初始化系统组件...")
        self.db_manager = DatabaseManager()  # 数据库管理器
        self.notification_system = NotificationSystem()  # 通知系统
        self.activity_monitor = ActivityMonitor()  # 活动监控器
        self.time_tracker = TimeTracker(  # 时间跟踪器
            self.activity_monitor, 
            self.notification_system,
            self.db_manager  # 传入数据库管理器以记录活动
        )
        self.visualizer = UsageVisualizer(  # 数据可视化器
            self.db_manager,
            output_dir=reports_dir
        )
        
        # 创建UI监视器窗口
        self.monitor_window = MonitorWindow(
            self.time_tracker,
            self.visualizer
        )
        
        # 系统托盘图标
        self.tray_icon = None
        
        # 注册退出处理
        atexit.register(self.cleanup)
        log_manager.info("系统初始化完成")
        
    def start(self):
        """启动监控服务"""
        log_manager.info("启动电脑使用时间监控服务...")
        
        # 先启动时间跟踪器
        self.time_tracker.start()
        
        # 创建系统托盘图标 - 修改启动顺序
        if TRAY_AVAILABLE:
            log_manager.info("创建系统托盘图标线程")
            
            # 确保图标文件存在
            if not os.path.exists("icon.ico"):
                icon_alt_paths = [
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"),
                    os.path.join(os.path.dirname(sys.executable), "icon.ico"),
                    "D:\\工作文件\\icon.ico"
                ]
                for path in icon_alt_paths:
                    if os.path.exists(path):
                        try:
                            import shutil
                            shutil.copy(path, "icon.ico")
                            log_manager.info(f"已从{path}复制图标文件")
                            break
                        except Exception as copy_err:
                            log_manager.warning(f"复制图标文件失败: {copy_err}")
            
            # 启动托盘图标线程
            tray_thread = threading.Thread(target=self._create_tray_icon)
            tray_thread.daemon = True
            tray_thread.start()
            
            # 等待托盘图标初始化
            time.sleep(1.0)
            log_manager.info("等待系统托盘图标初始化完成")
            
            # 确认系统托盘状态
            if not hasattr(self, 'tray_icon') or self.tray_icon is None:
                log_manager.warning("系统托盘图标初始化可能失败，UI将在前台启动")
            else:
                log_manager.info("系统托盘图标线程已启动")
        else:
            log_manager.warning("不支持系统托盘，UI将在前台启动")
        
        # 启动监视器窗口
        log_manager.info("启动UI监视器窗口")
        self.monitor_window.start()
        
    def _create_tray_icon(self):
        """创建系统托盘图标和菜单"""
        try:
            log_manager.info("开始创建系统托盘图标...")
            # 创建一个简单的图标
            image = self._create_icon_image()
            
            # 定义托盘菜单
            menu_items = [
                pystray.MenuItem("显示主窗口", self._show_main_window),
                pystray.MenuItem("显示使用统计", self._show_usage_stats),
                pystray.MenuItem("查看统计报告", self._show_usage_report),
                pystray.MenuItem("设置", self._open_settings),
                pystray.MenuItem("重置计时器", self._reset_timer),
                pystray.MenuItem("退出", self._exit_app)
            ]
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                name=config.APP_NAME,
                icon=image,
                title=config.TRAY_TOOLTIP,
                menu=pystray.Menu(*menu_items)
            )
            
            log_manager.info("系统托盘图标已创建，进入托盘图标主循环")
            # 启动托盘图标（会阻塞当前线程）
            self.tray_icon.run()
        except Exception as e:
            log_manager.error(f"创建系统托盘图标失败: {e}")
            global TRAY_AVAILABLE
            TRAY_AVAILABLE = False
            # 设置UI模块中的状态
            set_tray_available(False)
            # 显示UI窗口，防止程序完全无法访问
            if hasattr(self, 'monitor_window'):
                self.monitor_window.show()
        
    def _create_icon_image(self):
        """创建一个简单的图标图像"""
        try:
            # 首先尝试加载外部图标文件
            icon_path = "icon.ico"
            if os.path.exists(icon_path):
                log_manager.info(f"找到图标文件: {icon_path}")
                try:
                    return Image.open(icon_path)
                except Exception as ico_err:
                    log_manager.warning(f"无法打开图标文件: {ico_err}")
                    # 尝试寻找其它可能的路径
                    alt_paths = [
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"),
                        os.path.join(os.path.dirname(sys.executable), "icon.ico"),
                        "D:\\工作文件\\icon.ico"
                    ]
                    for alt_path in alt_paths:
                        if os.path.exists(alt_path):
                            log_manager.info(f"尝试替代图标路径: {alt_path}")
                            try:
                                return Image.open(alt_path)
                            except:
                                continue
        except Exception as e:
            log_manager.warning(f"加载图标文件失败: {e}，将使用默认图标")
        
        log_manager.info("使用内置默认图标")
        # 创建默认图标
        width = 64
        height = 64
        color1 = (0, 128, 255)
        color2 = (255, 255, 255)
        
        image = Image.new('RGB', (width, height), color2)
        dc = ImageDraw.Draw(image)
        
        # 绘制一个简单的图标
        dc.rectangle([10, 10, width-10, height-10], fill=color1)
        
        return image
    
    def _show_main_window(self, icon, item):
        """显示主窗口"""
        log_manager.info("用户请求：显示主窗口")
        # 确保托盘图标保持可见
        icon.visible = True
        self.monitor_window.show()
        
    def _show_usage_stats(self, icon, item):
        """显示使用统计信息"""
        log_manager.info("用户请求：显示使用统计")
        stats = self.time_tracker.get_usage_stats()
        message = (
            f"连续使用时间: {stats['continuous_usage_minutes']}分钟\n"
            f"今日总使用时间: {stats['daily_usage_minutes']}分钟"
        )
        self.notification_system.send_notification("使用统计", message)
        
    def _show_usage_report(self, icon, item):
        """生成并显示使用统计报告"""
        log_manager.info("用户请求：生成并显示使用统计报告")
        # 通知用户正在生成报告
        self.notification_system.send_notification(
            "正在生成报告", 
            "正在生成使用统计报告，请稍候..."
        )
        
        try:
            # 生成HTML报告
            report_path = self.visualizer.generate_usage_stats_html()
            
            # 在浏览器中打开报告
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            
            log_manager.log_report_generation(report_path)
        except Exception as e:
            # 生成报告失败时通知用户
            error_msg = f"无法生成统计报告: {e}"
            self.notification_system.send_notification(
                "生成报告失败", 
                error_msg
            )
            log_manager.log_error_detail("报告生成", error_msg)
        
    def _reset_timer(self, icon, item):
        """重置计时器"""
        log_manager.info("用户请求：重置计时器")
        self.time_tracker.reset()
        self.notification_system.send_notification("计时器已重置", "连续使用时间已重置为0")
        log_manager.log_activity_reset("用户手动重置")
        
    def _exit_app(self, icon, item):
        """退出应用"""
        log_manager.info("用户请求：退出应用")
        # 确保正确停止托盘图标
        icon.stop()
        self.cleanup()
        sys.exit(0)
        
    def _open_settings(self, icon, item):
        """打开设置窗口"""
        log_manager.info("用户请求：打开设置窗口")
        # 显示主窗口
        self.monitor_window.show()
        
        # 打开设置
        self.monitor_window._open_settings()
        
    def cleanup(self):
        """清理资源并退出"""
        log_manager.info("正在关闭电脑使用时间监控工具...")
        
        # 停止时间跟踪
        if hasattr(self, 'time_tracker'):
            self.time_tracker.stop()
            
        # 停止监视器窗口
        if hasattr(self, 'monitor_window'):
            self.monitor_window.stop()
            
        # 等待所有线程完成
        time.sleep(1)
            
        # 关闭数据库连接
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
            
        # 关闭系统托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.tray_icon.stop()
            
        log_manager.log_app_exit()

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="电脑使用时间监控工具")
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--report', action='store_true', help='生成并显示使用报告')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果指定了版本参数，显示版本信息并退出
    if args.version:
        print(f"电脑使用时间监控工具 v{VERSION}")
        sys.exit(0)
    
    # 如果指定了调试模式，覆盖配置设置
    if args.debug:
        config.DEBUG = True
    
    # 创建监控器
    monitor = ComputerUsageMonitor()
    
    # 如果指定了报告参数，生成并显示报告
    if args.report:
        import webbrowser
        log_manager.info("通过命令行参数请求生成报告")
        report_path = monitor.visualizer.generate_usage_stats_html()
        log_manager.log_report_generation(report_path)
        webbrowser.open(f"file://{os.path.abspath(report_path)}")
    else:
        # 否则正常启动监控
        monitor.start() 