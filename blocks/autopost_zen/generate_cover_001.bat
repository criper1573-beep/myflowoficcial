@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
python docs\scripts\scripts\generate_zen_cover.py --article blocks/autopost_zen/publish/001/article.json
pause
