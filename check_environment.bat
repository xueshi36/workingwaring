@echo off
echo 正在检查系统环境...
echo ============================

:: 检查操作系统版本
echo 检查操作系统...
ver | findstr /i "6\.1\." > nul
if %ERRORLEVEL% EQU 0 (
    echo [√] Windows 7 已检测到
) else (
    ver | findstr /i "6\.[2-3]\." > nul
    if %ERRORLEVEL% EQU 0 (
        echo [√] Windows 8/8.1 已检测到
    ) else (
        ver | findstr /i "10\.0\." > nul
        if %ERRORLEVEL% EQU 0 (
            echo [√] Windows 10/11 已检测到
        ) else (
            echo [!] 警告: 无法确认Windows版本，程序可能无法正常运行
        )
    )
)

:: 检查是否64位系统
echo 检查系统架构...
if defined ProgramFiles(x86) (
    echo [√] 64位系统已检测到
) else (
    echo [×] 错误: 需要64位系统
    echo     程序需要在64位Windows系统上运行
)

:: 检查VC++运行库
echo 检查Visual C++运行库...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [√] Visual C++ 2015-2019 Redistributable (x64) 已安装
) else (
    echo [×] 警告: 未检测到Visual C++ 2015-2019 Redistributable (x64)
    echo     程序需要此运行库才能正常运行
    echo     请从以下地址下载并安装: https://aka.ms/vs/16/release/vc_redist.x64.exe
)

echo.
echo 环境检查完成。
echo 如有标记为[×]的项目，请先解决后再运行程序。
echo.

pause 