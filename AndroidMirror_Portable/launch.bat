@echo off
title Android Mirror
echo ========================================
echo   Android Mirror - Portable Version
echo ========================================
echo.
echo Starting Android Mirror...
start "" "%~dp0AndroidMirror.exe"
echo.
echo Application started!
echo You can close this window now.
timeout /t 2 >nul
exit
