"""
设置界面 - 提供可视化界面修改配置
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import config

class SettingsWindow:
    def __init__(self, parent=None):
        """初始化设置窗口
        
        参数:
            parent: 父窗口，如果有的话
        """
        # 创建窗口
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("设置")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        try:
            self.window.iconbitmap("icon.ico")
        except:
            pass  # 如果没有图标文件，忽略错误
            
        # 初始化界面
        self.settings_vars = {}
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI界面"""
        # 创建样式
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5)
        style.configure("TFrame", padding=10)
        style.configure("Settings.TLabel", font=("微软雅黑", 9))
        
        # 创建主框架和滚动区域
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页控件
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 标签页1：时间设置
        time_tab = ttk.Frame(tab_control)
        tab_control.add(time_tab, text="时间设置")
        
        # 标签页2：通知设置
        notify_tab = ttk.Frame(tab_control)
        tab_control.add(notify_tab, text="通知设置")
        
        # 标签页3：报告设置
        report_tab = ttk.Frame(tab_control)
        tab_control.add(report_tab, text="报告设置")
        
        # 标签页4：其他设置
        other_tab = ttk.Frame(tab_control)
        tab_control.add(other_tab, text="其他设置")
        
        # ==== 时间设置标签页 ====
        # 活动检查间隔
        self._add_number_setting(
            time_tab,
            "活动检查间隔 (分钟):",
            "ACTIVITY_CHECK_INTERVAL",
            0,
            1, 10
        )
        
        # 连续使用提醒时间
        self._add_number_setting(
            time_tab, 
            "连续使用提醒时间(分钟):", 
            "CONTINUOUS_USAGE_ALERT",
            1, 30, 180
        )
        
        # 无活动重置时间
        self._add_number_setting(
            time_tab, 
            "无活动重置时间(分钟):", 
            "INACTIVITY_RESET",
            2, 5, 30
        )
        
        # ==== 通知设置标签页 ====
        # 启用连续通知
        self._add_checkbox_setting(
            notify_tab,
            "启用连续通知提醒",
            "ENABLE_CONTINUOUS_NOTIFICATION"
        )
        
        # 连续通知间隔
        self._add_number_setting(
            notify_tab, 
            "连续通知间隔(分钟):", 
            "CONTINUOUS_NOTIFICATION_INTERVAL",
            1, 1, 15
        )
        
        # 应用名称
        self._add_text_setting(
            notify_tab,
            "应用名称:",
            "APP_NAME"
        )
        
        # 通知标题
        self._add_text_setting(
            notify_tab,
            "通知标题:",
            "NOTIFICATION_TITLE"
        )
        
        # 通知消息
        self._add_text_setting(
            notify_tab,
            "通知消息:",
            "NOTIFICATION_MESSAGE",
            is_multiline=True
        )
        
        # 连续通知标题
        self._add_text_setting(
            notify_tab,
            "连续通知标题:",
            "CONTINUOUS_NOTIFICATION_TITLE"
        )
        
        # 连续通知消息
        self._add_text_setting(
            notify_tab,
            "连续通知消息:",
            "CONTINUOUS_NOTIFICATION_MESSAGE",
            is_multiline=True
        )
        
        # 系统托盘提示
        self._add_text_setting(
            notify_tab,
            "系统托盘提示:",
            "TRAY_TOOLTIP"
        )
        
        # ==== 报告设置标签页 ====
        # 启用自动报告
        self._add_checkbox_setting(
            report_tab,
            "启用自动报告生成",
            "AUTO_REPORT_ENABLED"
        )
        
        # 自动报告间隔
        self._add_number_setting(
            report_tab, 
            "自动报告生成间隔(分钟):", 
            "AUTO_REPORT_INTERVAL",
            1, 15, 240
        )
        
        # 报告显示天数
        self._add_number_setting(
            report_tab, 
            "报告显示天数:", 
            "REPORT_DAYS",
            1, 7, 90
        )
        
        # 报告目录
        self._add_text_setting(
            report_tab,
            "报告输出目录:",
            "REPORTS_DIR"
        )
        
        # ==== 其他设置标签页 ====
        # 数据库文件路径
        self._add_text_setting(
            other_tab,
            "数据库文件路径:",
            "DATABASE_PATH"
        )
        
        # 调试模式
        self._add_checkbox_setting(
            other_tab,
            "启用调试模式",
            "DEBUG"
        )
        
        # 添加重置按钮
        reset_frame = ttk.Frame(main_frame)
        reset_frame.pack(fill=tk.X, pady=10)
        
        reset_btn = ttk.Button(
            reset_frame, 
            text="恢复默认设置", 
            command=self._reset_settings
        )
        reset_btn.pack(side=tk.RIGHT)
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_btn = ttk.Button(
            button_frame, 
            text="保存设置", 
            command=self._save_settings
        )
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ttk.Button(
            button_frame, 
            text="取消", 
            command=self.window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
    def _add_number_setting(self, parent, label_text, variable_name, row, min_val=0, max_val=1000):
        """添加数字设置控件"""
        # 创建一行
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row_frame, text=label_text).pack(side=tk.LEFT, padx=5)
        
        # 获取当前值
        current_value = getattr(config, variable_name)
        
        # 创建变量
        var = tk.IntVar(value=current_value)
        self.settings_vars[variable_name] = var
        
        # 使用tk.Spinbox替代ttk.Spinbox
        spinbox = tk.Spinbox(
            row_frame,
            from_=min_val,
            to=max_val,
            textvariable=var,
            width=10
        )
        
        spinbox.pack(side=tk.RIGHT, padx=5)
        
    def _add_text_setting(self, parent, label_text, config_key, is_multiline=False):
        """添加文本设置控件
        
        参数:
            parent: 父容器
            label_text: 标签文本
            config_key: 配置键名
            is_multiline: 是否多行文本
        """
        # 创建一行
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(row_frame, text=label_text).pack(side=tk.LEFT, padx=5)
        
        # 获取当前值
        current_value = getattr(config, config_key)
        
        # 创建变量
        var = tk.StringVar(value=current_value)
        
        # 创建控件
        if is_multiline:
            # 多行文本框
            input_widget = tk.Text(row_frame, height=3, width=40)
            input_widget.insert("1.0", current_value)
            input_widget.pack(side=tk.RIGHT, padx=5)
            
            # 存储控件引用而非变量
            if not hasattr(self, "text_widgets"):
                self.text_widgets = {}
            self.text_widgets[config_key] = input_widget
        else:
            # 单行文本框
            entry = ttk.Entry(row_frame, textvariable=var, width=30)
            entry.pack(side=tk.RIGHT, padx=5)
            
            # 存储变量引用
            if not hasattr(self, "settings_vars"):
                self.settings_vars = {}
            self.settings_vars[config_key] = var
        
    def _add_checkbox_setting(self, parent, label_text, config_key):
        """添加复选框设置
        
        参数:
            parent: 父容器
            label_text: 标签文本
            config_key: 配置键名
        """
        # 创建一行
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=5)
        
        # 获取当前值
        current_value = getattr(config, config_key)
        
        # 创建变量
        var = tk.BooleanVar(value=current_value)
        
        # 创建复选框
        checkbox = ttk.Checkbutton(
            row_frame, 
            text=label_text,
            variable=var
        )
        checkbox.pack(side=tk.LEFT, padx=5)
        
        # 存储变量引用
        if not hasattr(self, "settings_vars"):
            self.settings_vars = {}
        self.settings_vars[config_key] = var
        
    def _save_settings(self):
        """保存所有设置"""
        try:
            # 保存普通设置变量
            if hasattr(self, "settings_vars"):
                for key, var in self.settings_vars.items():
                    config.save_config(key, var.get())
            
            # 保存多行文本框
            if hasattr(self, "text_widgets"):
                for key, widget in self.text_widgets.items():
                    text_value = widget.get("1.0", "end-1c")  # 获取文本但去掉最后的换行符
                    config.save_config(key, text_value)
            
            messagebox.showinfo("成功", "设置已保存。部分设置可能需要重启程序后生效。")
            self.window.destroy()
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _reset_settings(self):
        """重置所有设置为默认值"""
        if messagebox.askyesno("确认", "确定要恢复所有设置为默认值吗？"):
            # 重置配置
            from config_manager import config_manager, DEFAULT_CONFIG
            config_manager.reset_to_default()
            
            # 重新加载配置
            config.reload_config()
            
            # 关闭设置窗口，需要重新打开才能看到默认值
            messagebox.showinfo("成功", "已恢复默认设置。")
            self.window.destroy()
    
    def run(self):
        """运行设置窗口"""
        # 设置窗口为模态
        self.window.transient(self.window.master)
        self.window.grab_set()
        
        # 运行窗口
        if isinstance(self.window, tk.Tk):
            self.window.mainloop() 