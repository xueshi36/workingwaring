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
7. **日志管理层**：记录程序运行状态和用户行为

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
- **日志管理模块** (log_manager.py)：提供全局日志记录功能
- **日志配置模块** (logger_config.py)：配置日志系统并提供logger实例

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

### 2.8 日志管理系统 (log_manager.py & logger_config.py)

日志管理系统由两个密切相关的模块组成，提供全面的日志记录功能。

#### 2.8.1 日志配置模块 (logger_config.py)

此模块负责配置日志系统并提供统一的日志实例获取方法。

```python
def setup_logging(debug_mode=False):
    """设置日志系统，创建日志目录并配置格式"""
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 获取当前日期作为日志文件名一部分
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join('logs', f'usage_monitor_{current_date}.log')
    
    # 设置日志级别
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    """获取指定名称的日志记录器"""
    # 如果根记录器没有处理程序，先进行配置
    if not logging.getLogger().handlers:
        setup_logging()
    
    # 返回带有名称的日志记录器
    return logging.getLogger(name)
```

**设计要点**：
- 日志文件按日期分割，便于管理和查询
- 同时输出到文件和控制台，方便开发和调试
- 支持调试模式，可详细记录程序运行状态
- 提供统一的logger获取方法，确保命名一致性

#### 2.8.2 日志管理模块 (log_manager.py)

此模块提供高级日志记录功能，封装常用的日志记录场景。

```python
# 全局日志记录器
logger = None

def setup_logger(debug_mode=False):
    """设置日志记录器"""
    global logger
    # 使用logger_config模块获取logger
    from logger_config import get_logger
    logger = get_logger('monitor')
    
    # 日志路径
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 添加分隔线，标识新的日志会话
    logger.info('=' * 42)
    logger.info('电脑使用时间监控程序启动')
    logger.info('日志级别: ' + ('调试模式' if debug_mode else '正常模式'))
    
    # 获取当前日期作为日志文件名的一部分
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f'usage_monitor_{current_date}.log')
    logger.info(f'日志文件: {os.path.abspath(log_path)}')
    logger.info('=' * 42)
```

**功能特点**：
- 提供应用程序生命周期事件的专用日志方法
- 记录系统信息，便于问题排查
- 跟踪关键用户操作和程序状态变化
- 使用分隔符和格式化输出增强日志可读性

**核心日志事件**：
- 应用启动和退出
- 系统信息记录
- 配置加载和保存
- 通知发送
- 报告生成
- 错误和异常
- 用户操作

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

### 3.4 系统托盘集成

程序通过系统托盘图标实现后台运行功能，为用户提供便捷的访问方式。

```python
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
```

**实现特点**：
1. **轻量级菜单**：系统托盘菜单提供两个基本选项 - "显示窗口"和"退出"
2. **跨平台兼容**：使用pystray库实现，保证跨平台兼容性
3. **独立线程运行**：托盘图标在独立线程中运行，避免阻塞主线程
4. **容错设计**：对图标加载失败等异常情况进行处理，确保程序稳定运行
5. **优雅退出**：通过托盘菜单退出时，会调用cleanup方法释放资源

**窗口-托盘协作机制**：
1. 当用户关闭主窗口时，程序不会直接退出，而是隐藏到系统托盘
2. 用户可以通过点击托盘图标的"显示窗口"选项重新显示主界面
3. 只有通过托盘菜单中的"退出"选项，程序才会完全退出

这种设计保证了程序可以在后台持续监控用户活动，同时为用户提供了方便的访问入口，非常适合需要长时间运行的监控工具。

### 3.5 跨Windows版本兼容性

为确保在不同版本的Windows上正常运行：
1. 使用Python 3.8作为基础环境
2. 使用兼容不同版本的库版本
3. 确保正确处理路径和文件访问权限
4. 添加必要的Visual C++运行库依赖说明

### 3.6 资源处理

程序运行时会动态生成或访问以下资源：
1. 数据库文件：存储使用记录
2. 配置文件：存储用户设置
3. 报告文件夹：存储生成的报表
4. 日志文件：记录程序运行状态

### 3.7 配置外部化

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

### 4.1 打包策略

使用PyInstaller打包为可执行文件，主要配置如下：

```
pyinstaller -D ^
--add-data "icon.ico;." ^
--add-data "config.json;." ^
--hidden-import plyer.platforms ^
--hidden-import logger_config ^
--hidden-import log_manager ^
--hidden-import matplotlib ^
--hidden-import seaborn ^
--collect-all pystray ^
--collect-data PIL ^
--icon="icon.ico" ^
--name="电脑使用时间监控" ^
--windowed ^
main.py
```

**打包注意事项**：
1. 使用--windowed参数避免控制台窗口
2. 确保所有必要资源文件打包进发布版本
3. 使用--hidden-import添加隐式导入模块
4. 使用--collect-all确保第三方库完整打包

### 4.2 目录结构规划

打包后的目录结构：

```
电脑使用时间监控/
|-- 电脑使用时间监控.exe   # 主程序
|-- icon.ico              # 图标文件
|-- config.json           # 配置文件
|-- python3x.dll          # Python运行库
|-- data/                 # 数据目录
|   `-- usage_data.db     # 数据库文件
|-- logs/                 # 日志目录
|   `-- usage_monitor_*.log  # 日志文件
|-- reports/              # 报告目录
|   `-- *.html, *.png     # 生成的报告和图表
`-- _internal/            # 打包库文件
```

### 4.3 版本管理

程序采用语义化版本号，格式为X.Y.Z：
- X：主版本号，不兼容的API变更
- Y：次版本号，向下兼容的功能性新增
- Z：修订号，向下兼容的问题修正

当前版本：1.1.0

## 5. 未来发展计划

### 5.1 功能增强

1. **多屏幕支持**：监控多显示器使用情况
2. **任务时间分配**：根据不同程序分析使用时间
3. **自定义提醒计划**：允许设置不同时段的提醒策略
4. **数据导出功能**：支持导出为CSV或Excel格式
5. **多用户支持**：为不同用户提供独立的配置和记录

### 5.2 技术改进

1. **性能优化**：减少资源占用
2. **同步备份**：支持配置和数据的云端备份
3. **插件系统**：提供API允许开发者扩展功能
4. **多语言支持**：添加英语等其他语言界面

## 6. 总结

电脑使用时间监控工具通过模块化设计、多线程处理和灵活配置实现了高效、低干扰的使用监控功能。系统通过精确的活动检测算法和人性化的提醒机制，帮助用户养成健康的电脑使用习惯，预防久坐带来的健康问题。 