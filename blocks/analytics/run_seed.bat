@echo off
cd /d "%~dp0..\.."
python -m blocks.analytics.seed_test_data
pause
