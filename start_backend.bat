@echo off
chcp 65001 >nul
cd /d "%~dp0"

runtime\python.exe backend\run.py

pause