@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM По умолчанию Chromium (Playwright) — форма входа открывается, Касперский не мешает
python docs/scripts/scripts/capture_cookies.py --browser chromium
pause
