@echo off
echo ========================================
echo 电脑使用时间监控工具打包脚本
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

echo [提示] 开始打包应用程序...
echo [提示] 这可能需要几分钟时间，请耐心等待...

REM 执行PyInstaller打包命令
pyinstaller -D ^
--add-data "D:\工作文件\usage_data.db;data"  ^
--add-data "D:\工作文件\icon.ico;." ^
--add-data "D:\工作文件\config.json;." ^
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
--hidden-import PIL ^
--hidden-import PIL._tkinter_finder ^
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
--distpath %DIST_PATH% ^
--icon="D:\工作文件\icon.ico" ^
--name="电脑使用时间监控" ^
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
)
if not exist "%DIST_PATH%电脑使用时间监控\logs" (
    mkdir "%DIST_PATH%电脑使用时间监控\logs"
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