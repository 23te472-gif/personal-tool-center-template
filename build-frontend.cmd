@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
pushd "tools\个人工具中心新版\frontend"
call npm ci
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
popd
pushd "tools\宝可梦小镇新版\frontend"
call npm ci
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
popd
