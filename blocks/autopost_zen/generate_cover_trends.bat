@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd ..\..
python docs\scripts\scripts\generate_zen_cover.py "Тренды офисных пространств 2026" -o blocks\autopost_zen\articles\trends_office_2026_cover.png
