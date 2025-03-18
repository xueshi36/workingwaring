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
import ctypes
import traceback
# import pymsgbox

import config
import log_manager
from activity_monitor import ActivityMonitor
from time_tracker import TimeTracker
from notification import NotificationSystem
from db_manager import DatabaseManager
from visualization import UsageVisualizer
from logger_config import get_logger

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

logger = get_logger('main')

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
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            log_manager.info(f"创建报告目录: {reports_dir}")
        
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
        self.quit_flag = False
        
        # 注册退出处理
        atexit.register(self.cleanup)
        log_manager.info("系统初始化完成")
        
        # 设置应用程序id，确保任务栏图标正确显示
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.monitor.workingtime")
        except Exception as e:
            logger.error(f"设置应用程序ID失败: {e}")
        
        # 加载图标文件
        self.icon_path = self._get_icon_path()
        logger.info(f"应用程序图标路径: {self.icon_path}")
        
        # 设置窗口图标
        try:
            self.monitor_window.root.iconbitmap(self.icon_path)
        except Exception as e:
            logger.error(f"设置窗口图标失败: {e}")
        
    def _get_icon_path(self):
        """获取图标路径，优先使用当前目录下的icon.ico，如不存在则使用资源目录中的图标"""
        # 首先检查当前目录
        if os.path.exists("icon.ico"):
            return os.path.abspath("icon.ico")
        
        # 检查打包后的资源目录
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                return icon_path
        
        # 默认返回None，让tkinter使用默认图标
        logger.warning("未找到图标文件，将使用默认图标")
        return None
    
    def start(self):
        """启动监控服务"""
        # 声明全局变量必须在函数开头
        global TRAY_AVAILABLE
        
        log_manager.info("启动电脑使用时间监控服务...")
        
        # 启动时间跟踪器
        self.time_tracker.start()
        
        # 先创建系统托盘图标（在UI显示前）
        if TRAY_AVAILABLE:
            try:
                log_manager.info("创建系统托盘图标")
                # 直接在主线程创建托盘图标
                self._create_tray_icon()
                # 给系统托盘图标一些时间初始化
                time.sleep(0.5)
            except Exception as e:
                log_manager.error(f"创建系统托盘图标失败: {e}")
                # 在异常处理中修改全局变量
                TRAY_AVAILABLE = False
                set_tray_available(False)
        else:
            log_manager.warning("系统托盘不可用，窗口关闭时程序将退出")
        
        # 启动监视器窗口
        self.monitor_window.start()
        
    def _create_tray_icon(self):
        """创建系统托盘图标"""
        try:
            # 确保图标文件存在
            if not self.icon_path or not os.path.exists(self.icon_path):
                icon_path = "icon.ico" if os.path.exists("icon.ico") else None
                if not icon_path:
                    logger.error("找不到图标文件，无法创建系统托盘图标")
                    return False
            else:
                icon_path = self.icon_path
            
            logger.info(f"正在创建系统托盘图标，使用图标: {icon_path}")
            
            # 加载图标
            icon_image = Image.open(icon_path)
            
            # 创建菜单项
            def show_window(icon, item):
                self.show_window()
            
            def exit_app(icon, item):
                self.quit_flag = True
                icon.stop()
                self.cleanup()
            
            # 创建菜单
            menu = (
                pystray.MenuItem("显示窗口", show_window),
                pystray.MenuItem("退出", exit_app)
            )
            
            # 创建图标
            self.tray_icon = pystray.Icon(
                "monitor",
                icon_image,
                "电脑使用时间监控",
                menu
            )
            
            # 设置图标的安装回调函数，确保图标可见
            def setup(icon):
                icon.visible = True
                logger.info("系统托盘图标已成功创建并显示")
            
            self.tray_icon.setup = setup
            
            # 运行图标（在新线程中）
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            # 等待图标显示
            time.sleep(0.5)
            
            logger.info("系统托盘图标创建完成")
            return True
        except Exception as e:
            logger.error(f"创建系统托盘图标失败: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def show_window(self):
        """显示窗口"""
        logger.info("显示主窗口")
        self.monitor_window.show()
    
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

    # 设置DPI感知，确保界面在高分辨率屏幕上正常显示
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass 