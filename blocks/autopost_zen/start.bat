@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..
python -m blocks.autopost_zen --file blocks/autopost_zen/articles/article_trends_office_2026.json %*
pause
