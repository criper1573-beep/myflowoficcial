@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..
python -m blocks.autopost_zen --file blocks/autopost_zen/publish/008/article.json
