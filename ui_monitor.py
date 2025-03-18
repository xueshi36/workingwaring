"""
用户界面监视器 - 显示实时使用状态和统计数据
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import os
from datetime import datetime, timedelta
import log_manager
import config

class MonitorWindow:
    def __init__(self, time_tracker, visualizer):
        """初始化监视器窗口
        
        参数:
            time_tracker: 时间跟踪器实例
            visualizer: 可视化器实例
        """
        self.time_tracker = time_tracker
        self.visualizer = visualizer
        self.root = None
        self.running = False
        self.thread = None
        self.next_report_time = None
        
        # 初始化UI
        self._init_ui()
        
        # 设置下一次报告生成时间(整点)
        self._set_next_report_time()
        
        log_manager.info("UI监视器窗口初始化完成")
        
    def _init_ui(self):
        """初始化UI界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("电脑使用时间监控")
        self.root.geometry("430x430")  # 增加窗口高度以容纳新内容
        self.root.resizable(False, False)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            log_manager.warning("未找到图标文件，使用默认图标")
        
        # 窗口关闭时处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 创建样式
        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 14, "bold"))
        style.configure("Info.TLabel", font=("微软雅黑", 12))
        style.configure("Warning.TLabel", font=("微软雅黑", 12), foreground="red")
        style.configure("Header.TLabel", font=("微软雅黑", 10, "bold"))
        style.configure("Data.TLabel", font=("微软雅黑", 10))
        style.configure("Config.TLabel", font=("微软雅黑", 9), foreground="#555555")
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="电脑使用时间监控", style="Title.TLabel")
        title_label.pack(pady=(0, 15))
        
        # 当前状态框架
        status_frame = ttk.LabelFrame(main_frame, text="当前状态", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        # 连续使用时间
        usage_frame = ttk.Frame(status_frame)
        usage_frame.pack(fill=tk.X)
        
        ttk.Label(usage_frame, text="连续使用时间:", style="Header.TLabel").pack(side=tk.LEFT)
        self.usage_time_label = ttk.Label(usage_frame, text="0分钟", style="Data.TLabel")
        self.usage_time_label.pack(side=tk.RIGHT)
        
        # 今日总使用时间
        daily_frame = ttk.Frame(status_frame)
        daily_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(daily_frame, text="今日总使用时间:", style="Header.TLabel").pack(side=tk.LEFT)
        self.daily_time_label = ttk.Label(daily_frame, text="0分钟", style="Data.TLabel")
        self.daily_time_label.pack(side=tk.RIGHT)
        
        # 最近一次活动
        activity_frame = ttk.Frame(status_frame)
        activity_frame.pack(fill=tk.X)
        
        ttk.Label(activity_frame, text="最近活动:", style="Header.TLabel").pack(side=tk.LEFT)
        self.activity_label = ttk.Label(activity_frame, text="刚刚", style="Data.TLabel")
        self.activity_label.pack(side=tk.RIGHT)
        
        # 提醒信息
        self.alert_label = ttk.Label(status_frame, text="", style="Warning.TLabel")
        self.alert_label.pack(fill=tk.X, pady=(10, 0))
        
        # 当前配置框架
        config_frame = ttk.LabelFrame(main_frame, text="当前配置", padding=10)
        config_frame.pack(fill=tk.X, pady=5)
        
        # 活动检查间隔
        check_interval_frame = ttk.Frame(config_frame)
        check_interval_frame.pack(fill=tk.X, pady=2)
        ttk.Label(check_interval_frame, text="活动检查间隔:", style="Config.TLabel").pack(side=tk.LEFT)
        self.check_interval_label = ttk.Label(check_interval_frame, 
                                     text=f"每{config.ACTIVITY_CHECK_INTERVAL}分钟检查一次活动状态", 
                                     style="Config.TLabel")
        self.check_interval_label.pack(side=tk.RIGHT)
        
        # 连续使用提醒
        usage_alert_frame = ttk.Frame(config_frame)
        usage_alert_frame.pack(fill=tk.X, pady=2)
        ttk.Label(usage_alert_frame, text="连续使用提醒:", style="Config.TLabel").pack(side=tk.LEFT)
        self.usage_alert_label = ttk.Label(usage_alert_frame, 
                                 text=f"连续使用{config.CONTINUOUS_USAGE_ALERT}分钟后提醒", 
                                 style="Config.TLabel")
        self.usage_alert_label.pack(side=tk.RIGHT)
        
        # 无活动重置
        inactivity_frame = ttk.Frame(config_frame)
        inactivity_frame.pack(fill=tk.X, pady=2)
        ttk.Label(inactivity_frame, text="无活动重置:", style="Config.TLabel").pack(side=tk.LEFT)
        self.inactivity_label = ttk.Label(inactivity_frame, 
                               text=f"无活动{config.INACTIVITY_RESET}分钟后重置计时器", 
                               style="Config.TLabel")
        self.inactivity_label.pack(side=tk.RIGHT)
        
        # 报告框架
        report_frame = ttk.LabelFrame(main_frame, text="报告", padding=10)
        report_frame.pack(fill=tk.X, pady=10)
        
        # 下次报告生成时间
        next_report_frame = ttk.Frame(report_frame)
        next_report_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(next_report_frame, text="下次自动报告:", style="Header.TLabel").pack(side=tk.LEFT)
        self.next_report_label = ttk.Label(next_report_frame, text="计算中...", style="Data.TLabel")
        self.next_report_label.pack(side=tk.RIGHT)
        
        # 最新报告信息
        last_report_frame = ttk.Frame(report_frame)
        last_report_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(last_report_frame, text="最新报告:", style="Header.TLabel").pack(side=tk.LEFT)
        self.last_report_label = ttk.Label(last_report_frame, text="暂无报告", style="Data.TLabel")
        self.last_report_label.pack(side=tk.RIGHT)
        
        # 报告存储位置
        report_path_frame = ttk.Frame(report_frame)
        report_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(report_path_frame, text="存储位置:", style="Header.TLabel").pack(side=tk.LEFT)
        self.report_path_label = ttk.Label(report_path_frame, 
                                 text=os.path.abspath(config.REPORTS_DIR), 
                                 style="Data.TLabel")
        self.report_path_label.pack(side=tk.RIGHT)
        
        # 报告按钮
        button_frame = ttk.Frame(report_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        gen_report_btn = ttk.Button(button_frame, text="生成报告", command=self._generate_report)
        gen_report_btn.pack(side=tk.LEFT, padx=5)
        
        view_report_btn = ttk.Button(button_frame, text="查看报告", command=self._view_report)
        view_report_btn.pack(side=tk.LEFT, padx=5)
        
        settings_btn = ttk.Button(button_frame, text="设置", command=self._open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=5)
        
        reset_btn = ttk.Button(button_frame, text="重置计时器", command=self._reset_timer)
        reset_btn.pack(side=tk.RIGHT, padx=5)
        
        # 版权信息
        copyright_label = ttk.Label(main_frame, text=f"© {datetime.now().year} 电脑使用时间监控工具", style="Data.TLabel")
        copyright_label.pack(side=tk.BOTTOM, pady=(15, 0))
        
        log_manager.info("UI界面元素创建完成")
        
    def start(self):
        """启动监视器窗口"""
        if self.running:
            return
            
        self.running = True
        
        # 启动更新线程
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
        
        log_manager.info("UI监视器窗口启动")
        # 启动主循环
        self.root.mainloop()
        
    def stop(self):
        """停止监视器窗口"""
        log_manager.info("准备停止UI监视器窗口")
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
        if self.root:
            self.root.quit()
            
        log_manager.info("UI监视器窗口已停止")
            
    def _update_loop(self):
        """更新UI信息的循环"""
        while self.running:
            try:
                self._update_ui()
                
                # 检查是否需要生成报告
                now = datetime.now()
                if self.next_report_time and now >= self.next_report_time:
                    log_manager.info("自动触发报告生成时间到达")
                    self._generate_report()
                    self._set_next_report_time()
                    
                # 更新间隔(1秒)
                time.sleep(1)
            except Exception as e:
                log_manager.error(f"更新UI时出错: {e}")
                
    def _update_ui(self):
        """更新UI显示的信息"""
        if not self.root:
            return
            
        try:
            # 获取最新统计数据
            stats = self.time_tracker.get_usage_stats()
            
            # 更新连续使用时间
            continuous_mins = stats["continuous_usage_minutes"]
            self.usage_time_label.config(text=f"{continuous_mins}分钟")
            
            # 更新今日总使用时间
            daily_mins = stats["daily_usage_minutes"]
            self.daily_time_label.config(text=f"{daily_mins}分钟")
            
            # 更新最近活动
            idle_time = self.time_tracker.activity_monitor.get_idle_time()
            if idle_time < 60:
                activity_text = "刚刚"
            elif idle_time < 3600:
                activity_text = f"{int(idle_time // 60)}分钟前"
            else:
                activity_text = f"{int(idle_time // 3600)}小时前"
            self.activity_label.config(text=activity_text)
            
            # 更新配置显示
            self.check_interval_label.config(text=f"每{config.ACTIVITY_CHECK_INTERVAL}分钟检查一次活动状态")
            self.usage_alert_label.config(text=f"连续使用{config.CONTINUOUS_USAGE_ALERT}分钟后提醒")
            self.inactivity_label.config(text=f"无活动{config.INACTIVITY_RESET}分钟后重置计时器")
            
            # 更新提醒信息
            if continuous_mins >= 55 and continuous_mins < 60:
                self.alert_label.config(text=f"即将达到1小时连续使用，请准备休息")
                log_manager.debug("显示即将达到连续使用预警")
            elif continuous_mins >= 60:
                self.alert_label.config(text=f"已连续使用{continuous_mins}分钟，建议休息一下")
                log_manager.debug(f"显示连续使用警告: {continuous_mins}分钟")
            else:
                self.alert_label.config(text="")
                
            # 更新下次报告时间
            if self.next_report_time:
                time_left = self.next_report_time - datetime.now()
                mins_left = max(0, int(time_left.total_seconds() // 60))
                self.next_report_label.config(text=f"{self.next_report_time.strftime('%H:%M')} (还剩{mins_left}分钟)")
            
            # 更新最新报告信息
            try:
                report_dir = config.REPORTS_DIR
                if os.path.exists(report_dir):
                    report_files = [f for f in os.listdir(report_dir) if f.endswith('.html')]
                    if report_files:
                        # 按修改时间排序，获取最新报告
                        latest_report = sorted(report_files, 
                                               key=lambda x: os.path.getmtime(os.path.join(report_dir, x)), 
                                               reverse=True)[0]
                        mod_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(report_dir, latest_report)))
                        self.last_report_label.config(text=f"{latest_report} ({mod_time.strftime('%m-%d %H:%M')})")
                    else:
                        self.last_report_label.config(text="暂无报告")
                else:
                    self.last_report_label.config(text="报告目录不存在")
            except Exception as e:
                log_manager.error(f"更新报告信息失败: {e}")
                self.last_report_label.config(text="报告信息获取失败")
            
        except Exception as e:
            log_manager.error(f"更新UI数据时出错: {e}")
            
    def _on_close(self):
        """窗口关闭时的处理"""
        # 关闭窗口但不终止程序
        log_manager.info("用户关闭UI窗口，隐藏到系统托盘")
        self.root.withdraw()
        
    def _generate_report(self):
        """生成使用报告"""
        try:
            log_manager.info("通过UI界面请求生成报告")
            report_path = self.visualizer.generate_usage_stats_html()
            log_manager.info(f"已生成报告: {report_path}")
            
            # 更新UI显示
            self.alert_label.config(text=f"报告已生成: {os.path.basename(report_path)}")
            
            # 同时更新报告显示
            if os.path.exists(report_path):
                mod_time = datetime.fromtimestamp(os.path.getmtime(report_path))
                self.last_report_label.config(
                    text=f"{os.path.basename(report_path)} ({mod_time.strftime('%m-%d %H:%M')})"
                )
        except Exception as e:
            log_manager.error_detail("报告生成", f"生成报告失败: {e}")
            self.alert_label.config(text=f"生成报告失败: {e}")
            
    def _view_report(self):
        """查看最新报告"""
        try:
            log_manager.info("用户请求查看最新报告")
            
            # 检查是否存在报告
            report_dir = config.REPORTS_DIR
            if os.path.exists(report_dir):
                report_files = [f for f in os.listdir(report_dir) if f.endswith('.html')]
                if not report_files:
                    # 没有现有报告，生成一个新的
                    log_manager.info("没有找到现有报告，生成新报告")
                    report_path = self.visualizer.generate_usage_stats_html()
                else:
                    # 找到最新的报告
                    latest_report = sorted(report_files, 
                                          key=lambda x: os.path.getmtime(os.path.join(report_dir, x)), 
                                          reverse=True)[0]
                    report_path = os.path.join(report_dir, latest_report)
                    log_manager.info(f"找到最新报告: {report_path}")
            else:
                # 报告目录不存在，创建并生成新报告
                os.makedirs(report_dir, exist_ok=True)
                log_manager.info(f"创建报告目录: {report_dir}")
                report_path = self.visualizer.generate_usage_stats_html()
            
            # 在浏览器中打开
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            log_manager.info(f"已在浏览器中打开报告: {report_path}")
            
            # 更新UI显示
            if os.path.exists(report_path):
                mod_time = datetime.fromtimestamp(os.path.getmtime(report_path))
                self.last_report_label.config(
                    text=f"{os.path.basename(report_path)} ({mod_time.strftime('%m-%d %H:%M')})"
                )
                
        except Exception as e:
            log_manager.error_detail("报告查看", f"查看报告失败: {e}")
            self.alert_label.config(text=f"查看报告失败: {e}")
            
    def _reset_timer(self):
        """重置计时器"""
        try:
            log_manager.info("用户通过UI界面请求重置计时器")
            self.time_tracker.reset()
            self.alert_label.config(text="计时器已重置")
            log_manager.log_activity_reset("用户通过UI界面手动重置")
        except Exception as e:
            log_manager.error_detail("计时器重置", f"重置计时器失败: {e}")
            
    def _set_next_report_time(self):
        """设置下一次报告生成时间(每小时整点)"""
        now = datetime.now()
        # 下一个整点
        self.next_report_time = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        log_manager.info(f"设置下次报告生成时间: {self.next_report_time}")
        
    def show(self):
        """显示窗口(如果被隐藏)"""
        if self.root:
            log_manager.info("显示主窗口")
            self.root.deiconify()

    def _open_settings(self):
        """打开设置窗口"""
        try:
            log_manager.info("用户请求打开设置窗口")
            from settings_ui import SettingsWindow
            settings_window = SettingsWindow(self.root)
            settings_window.run()
            log_manager.info("设置窗口已关闭")
            
            # 刷新UI显示的配置
            self.check_interval_label.config(text=f"每{config.ACTIVITY_CHECK_INTERVAL}分钟检查一次活动状态")
            self.usage_alert_label.config(text=f"连续使用{config.CONTINUOUS_USAGE_ALERT}分钟后提醒")
            self.inactivity_label.config(text=f"无活动{config.INACTIVITY_RESET}分钟后重置计时器")
            
        except Exception as e:
            log_manager.error_detail("设置窗口", f"打开设置窗口失败: {e}")
            self.alert_label.config(text=f"打开设置窗口失败: {e}") 