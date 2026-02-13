@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..
python -m blocks.autopost_zen --file blocks/autopost_zen/articles/office_remont_expanded.json --publish
