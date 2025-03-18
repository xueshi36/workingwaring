# 电脑使用时间监控工具

一款帮助用户监控电脑使用时间，预防久坐危害的健康管理软件。通过监测鼠标和键盘活动来智能判断使用状态，及时提醒休息，同时提供详细的使用数据统计和可视化报表。

## 功能特点

- **智能活动监测**：自动监控鼠标和键盘活动，判断电脑是否在被使用
- **定时休息提醒**：连续使用60分钟自动提醒休息
- **智能连续提醒**：超过设定时间后，系统将定期发送连续通知，直到休息足够时间
- **数据统计与分析**：记录详细使用数据，提供每日/周/月使用情况统计
- **可视化报表**：多种形式的图表直观展示使用习惯
- **自动生成报告**：每小时自动生成使用报告
- **实时状态监控**：实时显示当前连续使用时间
- **系统托盘集成**：方便访问各项功能
- **灵活配置选项**：支持图形界面和配置文件两种方式修改设置

## 安装方法

### 从源码安装

1. 确保已安装Python 3.8或更高版本
2. 克隆或下载此仓库
3. 安装所需依赖：
   ```
   pip install -r requirements.txt
   ```
4. 运行程序：
   ```
   python main.py
   ```

### 使用可执行文件

1. 下载最新的发布版本
2. 解压缩到任意位置
3. 运行`电脑使用时间监控.exe`

## 使用说明

### 基本使用

1. 启动程序后，监控窗口会自动打开，系统托盘显示图标
2. 系统会自动跟踪鼠标和键盘活动，判断电脑是否被使用
3. 监控窗口显示当前连续使用时间、今日总使用时间等信息
4. 连续使用60分钟会弹出提醒通知
5. 达到连续使用时间阈值后，每隔设定的时间（默认3分钟）会继续发送提醒，直到休息足够时间
6. 10分钟无活动会自动重置计时器

### 查看统计报告

有多种方式查看使用统计报告：

- **从监控窗口**：点击"查看报告"按钮
- **从系统托盘**：右键点击托盘图标，选择"查看统计报告"
- **自动生成报告**：系统每小时自动生成一次报告

报告内容包括：
- 每日使用情况折线图
- 周使用情况热力图
- 月度使用趋势图

### 修改设置

有两种方式修改程序设置：

1. **图形界面**：
   - 在监控窗口点击"设置"按钮
   - 或从系统托盘菜单选择"设置"

2. **配置文件**：
   - 编辑程序目录下的`config.json`文件
   - 修改后重启程序生效

可配置项包括：
- 连续使用提醒时间
- 无活动重置时间
- 连续通知功能（开启/关闭）
- 连续通知间隔时间
- 连续通知提示信息
- 自动报告设置
- 数据存储位置
- 等等

## 数据存储

- 使用数据存储在程序目录下的`usage_data.db`文件中(SQLite数据库)
- 生成的报表存储在`reports`文件夹中
- 配置信息存储在`config.json`文件中

## 系统要求

- Windows 7/10/11
- 需要安装Visual C++ Redistributable for Visual Studio 2015-2019
- 推荐屏幕分辨率：1280x720或更高

## 开发者信息

- 本程序使用Python编写
- 使用PyInstaller打包成独立执行文件
- 主要依赖：pynput, matplotlib, sqlite3, tkinter, win10toast

## 隐私说明

本程序仅在本地记录电脑使用时间相关的数据，不会收集任何个人信息或将数据上传到互联网。监控仅限于记录鼠标移动和键盘按键次数，不会记录具体的键盘输入内容。

## 许可协议

MIT License 

pyinstaller -D  --add-data "D:\工作文件\usage_data.db;data"  --hidden-import plyer.platforms --hidden-import plyer.platforms.win.notification --hidden-import matplotlib --hidden-import seaborn --hidden-import numpy --hidden-import pandas --hidden-import pynput --hidden-import pymsgbox --hidden-import config_manager --hidden-import settings_ui --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import sqlite3 --hidden-import PIL --hidden-import PIL._tkinter_finder --hidden-import six --hidden-import packaging --hidden-import packaging.version --hidden-import packaging.specifiers  --hidden-import plyer.platforms --hidden-import plyer.platforms.win.notification  --distpath D:\共享\workingwaring\ D:\工作文件\main.py
