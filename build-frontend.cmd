@echo off
cd /d "%~dp0tools\个人工具中心新版\frontend"
call npm ci
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
cd /d "%~dp0tools\宝可梦小镇新版\frontend"
call npm ci
if errorlevel 1 exit /b 1
call npm run build
exit /b %errorlevel%
