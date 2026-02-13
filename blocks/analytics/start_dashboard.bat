@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..\
python -m blocks.analytics
