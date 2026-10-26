@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run setup.cmd first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -B "tools\个人工具中心新版\app.py" %*
set "APP_EXIT=%errorlevel%"
if not "%APP_EXIT%"=="0" pause
exit /b %APP_EXIT%
