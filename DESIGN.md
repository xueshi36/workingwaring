# 电脑使用时间监控系统设计文档

## 1. 系统概述

### 1.1 项目目标
开发一个轻量级的电脑使用时间监控系统，用于：
- 实时监控用户电脑使用情况
- 记录每日使用时间统计
- 生成月度使用报告
- 提供数据可视化展示

### 1.2 核心功能
- 实时活动监控
- 使用时间统计
- 数据持久化存储
- 月度报告生成
- 数据可视化展示

## 2. 系统架构

### 2.1 模块划分
```
project/
├── main.py              # 主程序入口
├── ui_monitor.py        # 主界面和监控逻辑
├── time_tracker.py      # 时间追踪核心
├── database.py          # 数据库操作
├── report_generator.py  # 报告生成
├── utils/
│   ├── __init__.py
│   ├── logger.py        # 日志工具
│   └── config.py        # 配置管理
└── logs/               # 日志目录
```

### 2.2 核心类设计

#### 2.2.1 TimeTracker 类
负责时间追踪的核心类，主要功能：
- 活动状态检测
- 使用时间计算
- 会话管理

核心代码：
```python
class TimeTracker:
    def __init__(self):
        self.last_active_time = datetime.now()
        self.current_session_start = datetime.now()
        self.total_active_time = timedelta()
        self.is_active = False
        self.sessions = []
        
    def check_activity_minute(self):
        """检查当前分钟是否有活动"""
        current_time = datetime.now()
        if current_time - self.last_active_time < timedelta(minutes=1):
            return True
        return False
        
    def update_activity(self):
        """更新活动状态"""
        current_time = datetime.now()
        if self.check_activity_minute():
            if not self.is_active:
                self.start_session()
            self.total_active_time += timedelta(minutes=1)
        else:
            if self.is_active:
                self.end_session()
        self.last_active_time = current_time
```

#### 2.2.2 DatabaseManager 类
负责数据库操作，主要功能：
- 数据库连接管理
- 数据记录和查询
- 数据统计

核心代码：
```python
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
        
    def _create_tables(self):
        """创建必要的数据表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS minute_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                is_active BOOLEAN NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_minutes INTEGER NOT NULL,
                longest_session INTEGER NOT NULL,
                session_count INTEGER NOT NULL
            )
        ''')
        self.conn.commit()
```

#### 2.2.3 ReportGenerator 类
负责报告生成，主要功能：
- 月度数据统计
- 图表生成
- 报告格式化

核心代码：
```python
class ReportGenerator:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def generate_monthly_report(self):
        """生成月度报告"""
        # 获取月度数据
        monthly_data = self.db_manager.get_monthly_summary()
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        plt.plot(monthly_data['date'], monthly_data['total_minutes'])
        plt.title('月度使用时间趋势')
        plt.xlabel('日期')
        plt.ylabel('使用时间(分钟)')
        
        # 保存报告
        report_path = f'reports/monthly_report_{datetime.now().strftime("%Y%m")}.pdf'
        plt.savefig(report_path)
        plt.close()
```

## 3. 关键功能实现

### 3.1 活动监控机制
```python
def check_activity(self):
    """检查用户活动状态"""
    try:
        # 获取当前活动窗口
        active_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        
        # 检查鼠标和键盘状态
        mouse_x, mouse_y = win32api.GetCursorPos()
        keyboard_state = win32api.GetKeyState(0x10)  # Shift键状态
        
        # 判断活动状态
        if active_window and (mouse_x != self.last_mouse_x or 
                            mouse_y != self.last_mouse_y or 
                            keyboard_state != self.last_keyboard_state):
            self.last_active_time = datetime.now()
            self.last_mouse_x, self.last_mouse_y = mouse_x, mouse_y
            self.last_keyboard_state = keyboard_state
            return True
            
        return False
    except Exception as e:
        logger.error(f"活动检测错误: {str(e)}")
        return False
```

### 3.2 数据持久化
```python
def record_activity(self, is_active):
    """记录活动状态"""
    try:
        current_time = datetime.now()
        self.cursor.execute('''
            INSERT INTO minute_activity (timestamp, is_active)
            VALUES (?, ?)
        ''', (current_time, is_active))
        self.conn.commit()
    except Exception as e:
        logger.error(f"记录活动状态错误: {str(e)}")
```

### 3.3 后台更新机制
```python
def _keep_alive_tick(self):
    """保持程序活跃的后台更新"""
    try:
        # 检查活动状态
        is_active = self.activity_monitor.check_activity_minute()
        
        # 更新使用时间
        self.activity_monitor.update_activity()
        
        # 记录到数据库
        self.db_manager.record_activity(is_active)
        
        # 更新界面
        self.update_display()
        
        # 设置下一次更新
        self.keep_alive_timer = self.root.after(5000, self._keep_alive_tick)
    except Exception as e:
        logger.error(f"后台更新错误: {str(e)}")
```

## 4. 数据存储设计

### 4.1 数据库表结构
1. minute_activity 表
   - id: 主键
   - timestamp: 时间戳
   - is_active: 活动状态

2. daily_summary 表
   - id: 主键
   - date: 日期
   - total_minutes: 总使用时间
   - longest_session: 最长会话时间
   - session_count: 会话次数

### 4.2 数据统计逻辑
```python
def update_daily_summary(self):
    """更新每日统计"""
    try:
        today = datetime.now().date()
        
        # 获取今日活动记录
        self.cursor.execute('''
            SELECT COUNT(*) as total_minutes,
                   MAX(session_duration) as longest_session,
                   COUNT(DISTINCT session_id) as session_count
            FROM minute_activity
            WHERE DATE(timestamp) = ?
            AND is_active = 1
        ''', (today,))
        
        result = self.cursor.fetchone()
        
        # 更新或插入统计记录
        self.cursor.execute('''
            INSERT OR REPLACE INTO daily_summary 
            (date, total_minutes, longest_session, session_count)
            VALUES (?, ?, ?, ?)
        ''', (today, result[0], result[1], result[2]))
        
        self.conn.commit()
    except Exception as e:
        logger.error(f"更新每日统计错误: {str(e)}")
```

## 5. 用户界面设计

### 5.1 主界面布局
```python
def create_widgets(self):
    """创建界面组件"""
    # 状态标签
    self.status_label = ttk.Label(
        self.root,
        text="监控状态: 运行中",
        font=("Arial", 12)
    )
    self.status_label.pack(pady=10)
    
    # 使用时间显示
    self.time_label = ttk.Label(
        self.root,
        text="今日使用时间: 0分钟",
        font=("Arial", 14)
    )
    self.time_label.pack(pady=10)
    
    # 控制按钮
    self.button_frame = ttk.Frame(self.root)
    self.button_frame.pack(pady=10)
    
    self.start_button = ttk.Button(
        self.button_frame,
        text="开始监控",
        command=self.start_monitoring
    )
    self.start_button.pack(side=tk.LEFT, padx=5)
    
    self.stop_button = ttk.Button(
        self.button_frame,
        text="停止监控",
        command=self.stop_monitoring
    )
    self.stop_button.pack(side=tk.LEFT, padx=5)
```

### 5.2 界面更新机制
```python
def update_display(self):
    """更新界面显示"""
    try:
        # 更新使用时间显示
        total_minutes = self.activity_monitor.total_active_time.total_seconds() / 60
        self.time_label.config(
            text=f"今日使用时间: {int(total_minutes)}分钟"
        )
        
        # 更新状态显示
        status = "运行中" if self.is_monitoring else "已停止"
        self.status_label.config(text=f"监控状态: {status}")
        
        # 更新按钮状态
        self.start_button.config(state=tk.DISABLED if self.is_monitoring else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if self.is_monitoring else tk.DISABLED)
    except Exception as e:
        logger.error(f"更新界面显示错误: {str(e)}")
```

## 6. 错误处理机制

### 6.1 异常捕获
```python
def safe_execute(self, func, *args, **kwargs):
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"执行错误: {str(e)}")
        return None
```

### 6.2 日志记录
```python
def setup_logger():
    """配置日志系统"""
    logger = logging.getLogger('usage_monitor')
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    log_file = f'logs/usage_monitor_{datetime.now().strftime("%Y-%m-%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

## 7. 性能优化

### 7.1 数据库优化
- 使用索引优化查询性能
- 定期清理历史数据
- 使用事务提高写入效率

### 7.2 内存管理
- 及时释放不需要的资源
- 控制日志文件大小
- 优化数据结构使用

## 8. 安全性考虑

### 8.1 数据安全
- 数据库文件加密
- 敏感信息保护
- 定期数据备份

### 8.2 程序安全
- 异常处理机制
- 资源释放保证
- 权限控制

## 9. 后续优化方向

### 9.1 功能扩展
- 添加更多统计维度
- 支持自定义报告模板
- 增加数据导出功能

### 9.2 性能提升
- 优化数据库操作
- 改进活动检测算法
- 减少资源占用

### 9.3 用户体验
- 优化界面设计
- 添加配置界面
- 提供更多可视化选项 