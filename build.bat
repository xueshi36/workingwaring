@echo off
echo 正在打包电脑使用时间监控工具，请稍候...

:: 设置Python 3.6的虚拟环境
echo 检查虚拟环境...
if not exist "venv" (
    echo 创建Python 3.6虚拟环境...
    :: 先检查是否安装了virtualenv
    pip show virtualenv > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo 正在安装virtualenv...
        pip install virtualenv
        if %ERRORLEVEL% NEQ 0 (
            echo virtualenv安装失败，请检查网络连接或手动安装。
            exit /b 1
        )
    )
    
    :: 使用virtualenv创建环境，支持老版本Python
    virtualenv venv
    if %ERRORLEVEL% NEQ 0 (
        echo 创建虚拟环境失败，请确保已安装Python 3.6
        exit /b 1
    )
)

:: 激活虚拟环境
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo 激活虚拟环境失败，请检查venv目录是否正确
    exit /b 1
)

:: 检查Python版本
python --version
echo.

:: 检查是否安装了PyInstaller
pip show pyinstaller > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller==3.6
    if %ERRORLEVEL% NEQ 0 (
        echo PyInstaller安装失败，请检查网络连接或手动安装。
        exit /b 1
    )
)

:: 确保所有依赖已安装
echo 正在检查并安装依赖...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo 依赖安装失败，请检查网络连接或手动安装依赖。
    exit /b 1
)

:: 清理旧的build和dist目录
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 打包程序 - 使用特定的设置以兼容Windows 7
echo 正在打包程序...
pyinstaller --onefile --noconsole ^
--add-data "icon.ico;." ^
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
--icon=icon.ico ^
--name="电脑使用时间监控" ^
main.py

if %ERRORLEVEL% NEQ 0 (
    echo 打包失败，请查看上方错误信息。
    exit /b 1
)

:: 复制示例配置文件到dist目录
echo 正在复制配置文件模板...
if not exist "dist\config.json" (
    copy "config_template.json" "dist\config.json"
)

:: 创建可能需要的目录
echo 正在创建必要目录...
if not exist "dist\reports" mkdir "dist\reports"
if not exist "dist\logs" mkdir "dist\logs"

:: 创建一个简单的运行时检查批处理文件
echo 创建启动脚本...
echo @echo off > "dist\启动程序.bat"
echo echo 正在检查环境... >> "dist\启动程序.bat"
echo if not exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Shared\VC\redist\MSVC\v140\vc_redist.x64.exe" ( >> "dist\启动程序.bat"
echo   echo 提示：您可能需要安装Visual C++运行库，如果程序无法启动，请安装MSVC运行库。 >> "dist\启动程序.bat"
echo   echo 您可以从Microsoft官方网站下载：https://support.microsoft.com/zh-cn/help/2977003/the-latest-supported-visual-c-downloads >> "dist\启动程序.bat"
echo   echo. >> "dist\启动程序.bat"
echo   timeout /t 3 >> "dist\启动程序.bat"
echo ) >> "dist\启动程序.bat"
echo echo 正在启动电脑使用时间监控工具... >> "dist\启动程序.bat"
echo start "" "电脑使用时间监控.exe" >> "dist\启动程序.bat"
echo exit >> "dist\启动程序.bat"

:: 复制运行时依赖说明
echo 创建运行依赖说明文件...
echo 运行环境要求 > "dist\运行环境说明.txt"
echo =============== >> "dist\运行环境说明.txt"
echo Windows 7 SP1 或更高版本 (64位) >> "dist\运行环境说明.txt"
echo Visual C++ Redistributable for Visual Studio 2015-2019 (x64) >> "dist\运行环境说明.txt" 
echo 下载地址: https://aka.ms/vs/16/release/vc_redist.x64.exe >> "dist\运行环境说明.txt"
echo. >> "dist\运行环境说明.txt"
echo 如果程序无法启动，请确保安装了相应版本的VC++运行库 >> "dist\运行环境说明.txt"

:: 停用虚拟环境
call venv\Scripts\deactivate

echo.
echo 打包完成！
echo 可执行文件位于 dist 文件夹中，双击"启动程序.bat"运行程序。
echo.

exit /b 0 