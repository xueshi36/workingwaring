@echo off
echo ========================================
echo 电脑使用时间监控工具打包脚本 (简化版)
echo ========================================
echo.

REM 安装必要的依赖
pip install plyer pystray pillow matplotlib seaborn pandas pynput

REM 执行PyInstaller打包命令
python -m PyInstaller -D ^
--add-data "usage_data.db;data" ^
--add-data "icon.ico;." ^
--add-data "config.json;." ^
--hidden-import logger_config ^
--hidden-import log_manager ^
--hidden-import matplotlib ^
--hidden-import seaborn ^
--collect-all pystray ^
--collect-data PIL ^
--distpath "dist" ^
--icon="icon.ico" ^
--name="电脑使用时间监控" ^
--windowed ^
main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败，请查看上方错误信息。
    exit /b 1
)

REM 复制必要的目录和文件
if not exist "dist\电脑使用时间监控\logs" (
    mkdir "dist\电脑使用时间监控\logs"
    echo [提示] 已创建日志目录
)

if not exist "dist\电脑使用时间监控\reports" (
    mkdir "dist\电脑使用时间监控\reports"
    echo [提示] 已创建报告目录
)

echo.
echo [成功] 打包完成！
echo.
pause 