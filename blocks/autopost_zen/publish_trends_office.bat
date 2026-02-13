@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..
python docs\scripts\scripts\run_zen_publish.py -f blocks\autopost_zen\articles\article_trends_office_2026.json -p
