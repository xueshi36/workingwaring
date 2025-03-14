"""
电脑使用时间监控工具 - 主程序入口

监控用户连续使用电脑的时间，并在适当时间提醒用户休息。
记录使用数据并提供可视化统计报告。
"""

import sys
import time
import logging
import threading
import argparse
import atexit
import webbrowser
import os
from datetime import datetime

import config
from activity_monitor import ActivityMonitor
from time_tracker import TimeTracker
from notification import NotificationSystem
from db_manager import DatabaseManager
from visualization import UsageVisualizer
from ui_monitor import MonitorWindow  # 新增导入

# 尝试导入系统托盘相关库
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    logging.warning("未安装pystray或PIL库，将不使用系统托盘图标")

class ComputerUsageMonitor:
    def __init__(self):
        """初始化电脑使用时间监控工具"""
        # 设置日志级别
        log_level = logging.DEBUG if config.DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("usage_monitor.log", encoding="utf-8")
            ]
        )
        
        logging.info("初始化电脑使用时间监控工具")
        
        # 创建输出目录
        reports_dir = config.REPORTS_DIR if hasattr(config, 'REPORTS_DIR') else "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # 初始化组件
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
        
    def start(self):
        """启动监控服务"""
        logging.info("启动电脑使用时间监控服务")
        
        # 发送启动通知
        self.notification_system.send_notification(
            "电脑使用时间监控已启动", 
            f"系统将监控您的使用时间，并在连续使用{config.CONTINUOUS_USAGE_ALERT}分钟后提醒您休息。"
        )
        
        # 启动时间跟踪
        self.time_tracker.start()
        
        # 启动监视器窗口
        # 注意：这应该先于系统托盘图标启动，因为它会进入mainloop
        self.monitor_window.start()
        
        # 如果支持系统托盘，则在单独线程中创建托盘图标
        if TRAY_AVAILABLE:
            tray_thread = threading.Thread(target=self._create_tray_icon)
            tray_thread.daemon = True
            tray_thread.start()
        else:
            # 如果不支持系统托盘，则直接显示监视器窗口
            logging.info("不支持系统托盘，将直接显示监视器窗口")
                
    def _create_tray_icon(self):
        """创建系统托盘图标和菜单"""
        # 创建一个简单的图标
        image = self._create_icon_image()
        
        # 定义托盘菜单
        menu_items = [
            pystray.MenuItem("显示主窗口", self._show_main_window),
            pystray.MenuItem("显示使用统计", self._show_usage_stats),
            pystray.MenuItem("查看统计报告", self._show_usage_report),
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
        
        # 启动托盘图标（会阻塞当前线程）
        self.tray_icon.run()
        
    def _create_icon_image(self):
        """创建一个简单的图标图像"""
        # 创建一个64x64的白色背景图像
        width = 64
        height = 64
        color1 = (0, 128, 255)
        color2 = (255, 255, 255)
        
        image = Image.new('RGB', (width, height), color2)
        dc = ImageDraw.Draw(image)
        
        # 绘制一个简单的时钟图标
        dc.ellipse((8, 8, width-8, height-8), fill=color1)
        dc.ellipse((16, 16, width-16, height-16), fill=color2)
        
        # 时针 - 修复坐标问题
        dc.rectangle((width/2-2, height/2-15, width/2+2, height/2), fill=color1)
        # 分针 - 保持水平方向
        dc.rectangle((width/2, height/2-1, width/2+15, height/2+1), fill=color1)
        
        return image
    
    def _show_main_window(self, icon, item):
        """显示主窗口"""
        self.monitor_window.show()
        
    def _show_usage_stats(self, icon, item):
        """显示使用统计信息"""
        stats = self.time_tracker.get_usage_stats()
        message = (
            f"连续使用时间: {stats['continuous_usage_minutes']}分钟\n"
            f"今日总使用时间: {stats['daily_usage_minutes']}分钟"
        )
        self.notification_system.send_notification("使用统计", message)
        
    def _show_usage_report(self, icon, item):
        """生成并显示使用统计报告"""
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
            
            logging.info(f"已打开统计报告: {report_path}")
        except Exception as e:
            # 生成报告失败时通知用户
            self.notification_system.send_notification(
                "生成报告失败", 
                f"无法生成统计报告: {e}"
            )
            logging.error(f"生成报告失败: {e}")
        
    def _reset_timer(self, icon, item):
        """重置计时器"""
        self.time_tracker.reset()
        self.notification_system.send_notification("计时器已重置", "连续使用时间已重置为0")
        
    def _exit_app(self, icon, item):
        """退出应用"""
        icon.stop()
        self.cleanup()
        sys.exit(0)
        
    def cleanup(self):
        """清理资源并退出"""
        logging.info("正在关闭电脑使用时间监控工具...")
        
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
            
        logging.info("电脑使用时间监控工具已关闭")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="电脑使用时间监控工具")
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--report', action='store_true', help='生成并显示使用报告')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果指定了调试模式，覆盖配置设置
    if args.debug:
        config.DEBUG = True
    
    # 创建监控器
    monitor = ComputerUsageMonitor()
    
    # 如果指定了报告参数，生成并显示报告
    if args.report:
        import webbrowser
        report_path = monitor.visualizer.generate_usage_stats_html()
        webbrowser.open(f"file://{os.path.abspath(report_path)}")
    else:
        # 否则正常启动监控
        monitor.start() 