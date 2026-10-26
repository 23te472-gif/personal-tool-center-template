@echo off
chcp 65001 >nul
where cl >nul 2>nul
if errorlevel 1 (echo Please open an x64 Native Tools Command Prompt for Visual Studio first. & exit /b 1)
cd /d "%~dp0"
if errorlevel 1 exit /b 1
cl /nologo /EHsc /std:c++17 /utf-8 /O2 /MT test_metrics.cpp /Fe:metrics_tests.exe
if errorlevel 1 exit /b 1
metrics_tests.exe
if errorlevel 1 exit /b 1
rc /nologo /fo app.res app.rc
if errorlevel 1 exit /b 1
cl /nologo /EHsc /std:c++17 /utf-8 /O2 /MT /DUNICODE /D_UNICODE app.cpp app.res /Fe:DesktopStatusCard.exe /link /SUBSYSTEM:WINDOWS /MANIFEST:NO gdiplus.lib iphlpapi.lib psapi.lib shell32.lib user32.lib gdi32.lib dwmapi.lib
if errorlevel 1 exit /b 1
if "%~1"=="card-only" exit /b 0
cl /nologo /EHsc /std:c++17 /utf-8 /O2 /MT hotkey.cpp app.res /Fe:HotkeyLauncher.exe /link /SUBSYSTEM:WINDOWS /MANIFEST:NO shell32.lib user32.lib
exit /b %errorlevel%
