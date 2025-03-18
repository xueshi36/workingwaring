# 电脑使用时间监控工具 - 设计文档

## 1. 设计思路与架构

### 1.1 核心设计理念

本项目旨在创建一个既易用又强大的电脑使用时间监控工具，通过以下设计理念指导实现：

- **用户友好**：简洁的界面和便捷的操作方式
- **非侵入性**：在后台运行，不干扰用户正常工作
- **准确监测**：精确判断电脑实际使用状态
- **数据可视化**：通过图表直观展示使用模式
- **模块化设计**：各功能模块相对独立，便于维护和扩展
- **配置灵活性**：支持多种方式修改设置

### 1.2 系统架构

系统采用分层架构设计，主要包括以下几层：

1. **数据采集层**：监控鼠标和键盘活动
2. **数据处理层**：分析活动数据，判断使用状态
3. **数据存储层**：保存使用记录到数据库
4. **业务逻辑层**：实现提醒、统计等核心功能
5. **表示层**：提供用户界面和可视化展示
6. **配置管理层**：处理程序设置的读取和保存

### 1.3 模块组织

- **主程序模块** (main.py)：整合各模块，提供系统托盘功能
- **活动监控模块** (activity_monitor.py)：监控鼠标和键盘活动
- **时间跟踪模块** (time_tracker.py)：计算使用时间，触发提醒
- **数据库管理模块** (db_manager.py)：处理数据存储和检索
- **通知系统模块** (notification.py)：显示桌面通知
- **数据可视化模块** (visualization.py)：生成统计图表
- **监控界面模块** (ui_monitor.py)：实时显示使用状态
- **配置管理模块** (config_manager.py)：管理程序配置
- **设置界面模块** (settings_ui.py)：提供配置的图形界面

## 2. 核心功能模块详解

### 2.1 活动监控模块 (activity_monitor.py)

此模块负责检测用户的鼠标和键盘活动，是判断电脑是否被使用的基础。

```python
class ActivityMonitor:
    def __init__(self):
        """初始化活动监控器"""
        self.mouse_position = None
        self.last_mouse_position = None
        self.key_press_count = 0
        self.mouse_move_count = 0  # 鼠标移动计数
        self.last_activity_time = time.time()
        self.is_active_minute = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False
        self.lock = threading.Lock()
```

**关键技术点**：
- 使用pynput库监听鼠标和键盘事件
- 使用线程锁(threading.Lock)确保线程安全
- 每分钟检查一次活动状态，记录鼠标移动次数和按键次数
- 通过对比鼠标位置变化和按键次数来判断活动状态

### 2.2 时间跟踪模块 (time_tracker.py)

此模块负责跟踪和计算连续使用时间，决定何时触发休息提醒。

```python
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
        self.today = datetime.now().strftime("%Y-%m-%d")
```

**核心逻辑**：
1. 通过后台线程每分钟检查一次活动状态
2. 如果检测到活动，增加连续使用时间计数
3. 连续使用达到阈值(默认60分钟)时触发提醒
4. 连续无活动达到阈值(默认10分钟)时重置计时器
5. 记录每日总使用时间和使用模式

### 2.3 数据库管理模块 (db_manager.py)

此模块处理所有与数据库相关的操作，包括保存活动记录和查询统计数据。

```python
class DatabaseManager:
    def __init__(self, db_path="usage_data.db"):
        """初始化数据库管理器"""
        self.db_path = db_path
        self.local = threading.local()  # 创建线程局部存储对象
        
        # 初始化主线程的连接
        self._initialize_db()
```

**设计要点**：
- 使用SQLite作为数据存储引擎，轻量级且无需额外服务
- 采用线程局部存储(threading.local)解决SQLite多线程访问问题
- 表设计：
  - minute_activity表：记录每分钟的详细活动数据
  - daily_summary表：存储每日汇总使用统计
- 提供各种查询方法，支持不同时间维度的数据统计

### 2.4 数据可视化模块 (visualization.py)

此模块负责生成各种可视化报表，直观展示用户的电脑使用情况。

```python
class UsageVisualizer:
    def __init__(self, db_manager, output_dir="reports"):
        """初始化可视化器"""
        self.db_manager = db_manager
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 设置中文字体支持
        self._setup_fonts()
```

**可视化方案**：
1. **每日使用报告**：柱状图显示每小时使用情况
2. **周活动热力图**：热力图展示一周内的使用模式
3. **月度使用摘要**：折线图跟踪使用趋势
4. **HTML综合报告**：将所有图表整合到单个HTML页面

### 2.5 UI监视器模块 (ui_monitor.py)

此模块提供了图形用户界面，实时显示使用状态和各项统计数据。

```python
class MonitorWindow:
    def __init__(self, time_tracker, visualizer):
        """初始化监视器窗口"""
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
```

**界面功能**：
- 显示当前连续使用时间
- 显示今日总使用时间
- 显示最近活动时间
- 提供报告生成和查看功能
- 提供设置访问入口
- 自动更新UI信息

### 2.6 配置管理模块 (config_manager.py)

此模块处理程序配置的加载和保存，支持从外部JSON文件读取设置。

```python
class ConfigManager:
    def __init__(self):
        """初始化配置管理器"""
        self.config = {}
        self.config_file = self._get_config_file_path()
        self.load_config()
```

**配置管理策略**：
- 使用JSON格式存储配置，易于人工编辑
- 提供默认配置，确保程序正常运行
- 支持配置的动态加载和保存
- 在启动时自动检测配置文件，不存在则创建默认配置

### 2.7 设置界面模块 (settings_ui.py)

此模块提供了图形化的设置界面，让用户可以方便地修改程序配置。

```python
class SettingsWindow:
    def __init__(self, parent=None):
        """初始化设置窗口"""
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("设置")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
```

**设置界面特点**：
- 分类标签页展示不同类型的设置
- 支持数值、文本、复选框等多种设置类型
- 提供重置为默认设置功能
- 设置实时保存到配置文件

## 3. 关键技术实现

### 3.1 多线程实现

程序中使用多线程处理不同的任务，主要包括：
- 主界面线程：处理UI交互
- 活动监控线程：监听鼠标键盘事件
- 时间跟踪线程：定时检查活动状态
- 托盘图标线程：处理系统托盘相关操作

线程同步通过锁(threading.Lock)和事件(threading.Event)实现，确保数据一致性和线程安全。

### 3.2 数据库架构

数据库采用SQLite，包含两个主要表：

1. **minute_activity表**：
   - id：主键
   - timestamp：记录时间
   - date：日期部分
   - time：时间部分
   - is_active：是否活跃
   - mouse_moves：鼠标移动次数
   - key_presses：按键次数

2. **daily_summary表**：
   - date：日期(主键)
   - total_active_minutes：总活跃分钟数
   - longest_session：最长连续会话
   - last_updated：最后更新时间

### 3.3 可视化实现

可视化使用matplotlib和seaborn库实现，主要图表类型：

1. **柱状图**：使用plt.bar()显示每小时使用情况
2. **热力图**：使用ax.imshow()展示一周使用模式
3. **折线图**：使用plt.plot()展示长期使用趋势

为确保中文显示正常，设置了中文字体支持：
```python
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
```

### 3.4 配置外部化

配置外部化通过JSON文件实现，主要优势：

1. **易读性**：JSON格式人类可读，便于直接编辑
2. **持久性**：配置保存在独立文件，程序更新不会丢失设置
3. **灵活性**：支持运行时修改，不需重新编译程序

配置加载过程：
1. 检查配置文件是否存在
2. 如果存在，加载并与默认配置合并
3. 如果不存在，创建默认配置文件
4. 暴露配置项给程序其他部分使用

## 4. 打包与部署

### 4.1 PyInstaller打包

使用PyInstaller将Python程序打包成独立可执行文件：

```
pyinstaller --onefile --noconsole ^
--add-data "icon.ico;." ^
--hidden-import plyer.platforms ^
--hidden-import plyer.platforms.win.notification ^
--hidden-import matplotlib ^
--hidden-import seaborn ^
--hidden-import numpy ^
--hidden-import config_manager ^
--hidden-import settings_ui ^
--icon=icon.ico ^
--name="电脑使用时间监控" ^
main.py
```

### 4.2 针对Windows 7的兼容性处理

为确保在Windows 7上正常运行：
1. 使用Python 3.8作为基础环境
2. 使用兼容Windows 7的库版本
3. 确保正确处理路径和文件访问权限
4. 添加必要的Visual C++运行库依赖说明

### 4.3 资源处理

程序运行时会动态生成或访问以下资源：
1. 数据库文件：存储使用记录
2. 配置文件：存储用户设置
3. 报告文件夹：存储生成的报表
4. 日志文件：记录程序运行状态

## 5. 未来扩展方向

1. **数据分析增强**：添加更多统计分析功能，如工作效率评估
2. **休息建议**：提供针对性的休息建议和简单的放松运动指导
3. **多设备同步**：支持多台电脑数据同步和汇总
4. **定制化提醒规则**：允许用户设置更复杂的提醒规则
5. **导出功能**：支持导出数据到Excel或CSV格式
6. **更丰富的可视化**：添加更多类型的图表和交互式可视化

## 6. 结语

电脑使用时间监控工具采用模块化设计，将不同功能明确分离，使得代码结构清晰，便于维护和扩展。通过精确的活动监测、数据存储、统计分析和可视化展示，帮助用户了解自己的电脑使用习惯，预防久坐带来的健康问题。灵活的配置选项和友好的用户界面使其既适合普通用户使用，也能满足高级用户的定制需求。 