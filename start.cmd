@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "tools\个人工具中心新版\app.py"
) else (
  echo Please run setup.cmd first to create the supported local Python environment.
  pause
  exit /b 1
)
if errorlevel 1 pause
