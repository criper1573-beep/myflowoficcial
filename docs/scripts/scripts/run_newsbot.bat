@echo off
chcp 65001 > nul
echo ========================================
echo NewsBot - RSS to Telegram
echo ========================================
echo.

REM Go to project root: from Doc/Scripts/scripts up three levels
pushd "%~dp0"
cd ..\..\..
if errorlevel 1 goto err_cd

REM Check .env exists
if not exist .env goto err_noenv

REM Load .env
for /f "usebackq tokens=1,* delims==" %%a in (.env) do set "%%a=%%b"

REM Check env vars
if not defined TELEGRAM_BOT_TOKEN goto err_token
if not defined TELEGRAM_CHANNEL_ID goto err_channel

echo Config: TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID set
echo.

REM Activate venv if exists
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

:run_bot
REM Check dependencies
python -c "import telegram" 2>nul
if errorlevel 1 goto err_deps

echo.
echo Starting bot... Stop with Ctrl+C
echo ========================================
echo.

python -m blocks.spambot
if errorlevel 1 goto err_run

echo.
echo Bot stopped.
goto end

:err_cd
echo Error: cannot change to project root.
pause
exit 1

:err_noenv
echo ERROR: .env not found.
echo Create .env in project root from .env.example
echo Example: copy "docs\config\.env.example" .env
echo Then set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID
echo.
pause
exit 1

:err_token
echo ERROR: TELEGRAM_BOT_TOKEN not set. Set it in .env
echo.
pause
exit 1

:err_channel
echo ERROR: TELEGRAM_CHANNEL_ID not set. Set it in .env
echo.
pause
exit 1

:err_deps
echo.
echo WARNING: Dependencies not installed.
echo Run: pip install -r "docs\config\requirements.txt"
echo Or: pip install python-telegram-bot feedparser googletrans==4.0.0-rc1
echo.
set /p install="Install now? y/n: "
if /i not "%install%"=="y" goto end
pip install -r "docs\config\requirements.txt"
if errorlevel 1 goto err_install_failed
goto run_bot

:err_install_failed
echo Install failed.
pause
exit 1

:err_run
echo.
echo ERROR: Bot exited with error.
echo.
pause
exit 1

:end
popd
pause
