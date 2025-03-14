# 电脑使用时间监控工具

一个帮助用户监控电脑使用时间，预防久坐的工具。通过监测鼠标和键盘活动判断您是否正在使用电脑，并在连续使用过长时间后提醒您休息。

## 功能特点

- 自动监控电脑使用时间
- 检测鼠标和键盘活动判断使用状态
- 连续使用60分钟自动提醒休息
- 10分钟无活动自动重置计时
- 统计每日使用总时间
- 记录活动数据到SQLite数据库
- 生成多种类型的数据可视化报表
- 系统托盘图标便于查看和控制

## 安装方法

1. 确保已安装Python 3.6+
2. 克隆或下载此仓库
3. 安装所需依赖：
   ```
   pip install -r requirements.txt
   ```

## 使用说明

### 基本使用

1. 运行程序：
   ```
   python main.py
   ```

2. 程序启动后会自动在后台运行，并在系统托盘显示图标
3. 通过托盘图标可以：
   - 查看当前使用时间统计
   - 查看使用统计报告
   - 手动重置计时器
   - 退出程序

4. 连续使用60分钟会弹出提醒通知
5. 10分钟无活动后计时自动重置

### 查看统计报告

1. 点击系统托盘图标中的"显示使用统计报告"选项
2. 浏览器将自动打开HTML格式的统计报告
3. 报告包含：
   - 每日使用情况折线图
   - 一周使用热力图
   - 月度使用统计图表

### 数据存储位置

- 使用数据存储在程序目录下的`usage_data.db`文件中
- 生成的报表存储在`reports`文件夹中

## 命令行选项

```
python main.py --debug  # 启用调试模式，显示详细日志
```

## 配置选项

您可以在`config.py`文件中修改以下配置：

- `CONTINUOUS_USAGE_ALERT`: 连续使用提醒时间（分钟）
- `INACTIVITY_RESET`: 无活动重置时间（分钟）
- `NOTIFICATION_MESSAGE`: 提醒消息内容

## 技术架构

- 活动监控：使用pynput库监测鼠标和键盘活动
- 时间追踪：记录和计算连续使用时间
- 通知系统：使用plyer库实现跨平台桌面通知
- 系统托盘：使用pystray库实现系统托盘图标和菜单

## 系统要求

- Windows 7+, macOS 10.12+, 或 Linux
- Python 3.6 或更高版本
- 支持显示桌面通知的系统

## 隐私说明

本程序仅在本地运行，所有使用数据均保存在本地，不会向任何远程服务器发送信息。程序监控鼠标移动和键盘按键次数，但不会记录具体的鼠标位置或按键内容。

## 许可协议

MIT License 