@echo off
echo ========================================
echo 电脑使用时间监控工具打包脚本 v1.3.0
echo 修复了系统托盘功能和报告显示问题
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请确保已安装Python并添加到PATH中。
    exit /b 1
)

REM 检查PyInstaller是否安装
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未安装PyInstaller，正在安装...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] PyInstaller安装失败，请手动安装后重试。
        exit /b 1
    )
)

REM 检查必要的库是否安装
echo [提示] 检查必要的库...
python -c "import pystray" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未安装pystray库，正在安装...
    pip install pystray
    if %errorlevel% neq 0 (
        echo [警告] pystray安装失败，系统托盘功能可能不可用。
    )
)

python -c "from PIL import Image" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未安装Pillow库，正在安装...
    pip install pillow
    if %errorlevel% neq 0 (
        echo [警告] Pillow安装失败，系统托盘图标可能不可用。
    )
)

REM 创建输出目录
set DIST_PATH=D:\共享\workingwaring\
if not exist "%DIST_PATH%" (
    mkdir "%DIST_PATH%"
    echo [提示] 已创建输出目录：%DIST_PATH%
)

REM 清理旧文件
echo [提示] 清理旧的构建文件...
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1

REM 确保reports目录存在
if not exist "reports" (
    mkdir "reports"
    echo [提示] 已创建reports目录
)

REM 确保logs目录存在
if not exist "logs" (
    mkdir "logs"
    echo [提示] 已创建logs目录
)

REM 确保图标文件存在
if not exist "icon.ico" (
    echo [警告] 图标文件不存在，系统托盘图标可能无法显示
)

echo [提示] 开始打包应用程序...
echo [提示] 这可能需要几分钟时间，请耐心等待...

REM 执行PyInstaller打包命令
pyinstaller -D ^
--add-data "icon.ico;." ^
--add-data "config.json;." ^
--hidden-import pystray ^
--hidden-import PIL ^
--hidden-import PIL.Image ^
--hidden-import PIL.ImageDraw ^
--hidden-import PIL._tkinter_finder ^
--hidden-import plyer.platforms ^
--hidden-import plyer.platforms.win.notification ^
--hidden-import matplotlib ^
--hidden-import seaborn ^
--hidden-import numpy ^
--hidden-import pandas ^
--hidden-import pynput ^
--hidden-import pymsgbox ^
--hidden-import config_manager ^
--hidden-import settings_ui ^
--hidden-import tkinter ^
--hidden-import tkinter.ttk ^
--hidden-import sqlite3 ^
--hidden-import six ^
--hidden-import packaging ^
--hidden-import packaging.version ^
--hidden-import packaging.specifiers ^
--hidden-import tempfile ^
--hidden-import subprocess ^
--hidden-import webbrowser ^
--hidden-import threading ^
--hidden-import datetime ^
--hidden-import ctypes ^
--hidden-import sys ^
--hidden-import os ^
--collect-data pystray ^
--collect-all PIL ^
--distpath %DIST_PATH% ^
--icon="icon.ico" ^
--name="电脑使用时间监控" ^
--noconsole ^
main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败，请查看上方错误信息。
    exit /b 1
)

echo.
echo [成功] 打包完成！
echo [提示] 可执行文件位于: %DIST_PATH%电脑使用时间监控\电脑使用时间监控.exe
echo.

REM 确保必要的目录存在
echo [提示] 创建必要的目录结构...
if not exist "%DIST_PATH%电脑使用时间监控\reports" (
    mkdir "%DIST_PATH%电脑使用时间监控\reports"
    echo [提示] 已创建报告目录
)
if not exist "%DIST_PATH%电脑使用时间监控\logs" (
    mkdir "%DIST_PATH%电脑使用时间监控\logs"
    echo [提示] 已创建日志目录
)

REM 复制当前目录中的reports文件夹内容到打包目录
echo [提示] 复制示例报告...
if exist "reports" (
    xcopy /s /y /i "reports\*" "%DIST_PATH%电脑使用时间监控\reports\" >nul 2>&1
    echo [提示] 已复制reports文件夹中的内容
)

REM 复制图标文件到打包目录(再次确认)
echo [提示] 确保图标文件已复制...
if exist "icon.ico" (
    copy /y "icon.ico" "%DIST_PATH%电脑使用时间监控\" >nul 2>&1
    echo [提示] 已复制图标文件
)

REM 创建其他必要目录
if not exist "%DIST_PATH%电脑使用时间监控\data" (
    mkdir "%DIST_PATH%电脑使用时间监控\data"
    echo [提示] 已创建数据目录
)

REM 验证目录权限
echo [提示] 验证目录权限...
echo 测试文件 > "%DIST_PATH%电脑使用时间监控\reports\test.txt" 2>nul
if %errorlevel% neq 0 (
    echo [警告] 可能没有对报告目录的写入权限，请确保程序有足够权限
) else (
    del "%DIST_PATH%电脑使用时间监控\reports\test.txt" >nul 2>&1
    echo [提示] 报告目录权限正常
)

REM 创建启动快捷方式
echo [提示] 正在创建快捷方式...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DIST_PATH%电脑使用时间监控工具.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%DIST_PATH%电脑使用时间监控\电脑使用时间监控.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%DIST_PATH%电脑使用时间监控" >> CreateShortcut.vbs
echo oLink.Description = "电脑使用时间监控工具" >> CreateShortcut.vbs
echo oLink.IconLocation = "%DIST_PATH%电脑使用时间监控\icon.ico" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo [提示] 快捷方式已创建: %DIST_PATH%电脑使用时间监控工具.lnk
echo.
echo ========================================
echo 打包过程已完成，按任意键退出...
echo ========================================
pause > nul 