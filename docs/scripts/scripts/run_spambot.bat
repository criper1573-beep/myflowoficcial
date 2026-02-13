@echo off
chcp 65001 > nul
echo ========================================
echo Spambot / NewsBot - RSS to Telegram
echo ========================================
echo.

REM Go to project root: from Doc/Scripts/scripts up three levels
pushd "%~dp0"
cd ..\..\..
if errorlevel 1 goto err_cd

REM Check .env exists
if not exist .env goto err_noenv

REM Load .env
echo Loading .env...
for /f "usebackq tokens=1,* delims==" %%a in (.env) do set "%%a=%%b"

REM Check project or TELEGRAM vars
if not "%~1"=="" goto have_arg
if defined PROJECT_ID goto have_project
if not defined TELEGRAM_BOT_TOKEN goto err_no_token
if not defined TELEGRAM_CHANNEL_ID goto err_no_channel
echo Using .env tokens
goto check_deps

:have_project
echo Default project: %PROJECT_ID%
goto check_deps

:have_arg
echo Project: %~1
goto check_deps

:check_deps
echo.

REM Activate venv if exists
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

REM Check dependencies
echo Checking dependencies...
python -c "import telegram" 2>nul
if errorlevel 1 goto err_deps
echo.

REM Run bot
echo ========================================
echo Starting Spambot... Stop: Ctrl+C
echo ========================================
echo.

if not "%~1"=="" goto run_with_project
if defined PROJECT_ID goto run_with_env_project
python -m blocks.spambot
goto after_run

:run_with_env_project
python -m blocks.spambot --project %PROJECT_ID%
goto after_run

:run_with_project
python -m blocks.spambot --project %~1
goto after_run

:after_run
if errorlevel 1 goto err_run
echo.
echo Bot stopped. To run again: start.bat flowcabinet
echo.
goto done

:err_cd
echo Error: cannot change to project root.
pause
popd
exit 1

:err_noenv
echo ERROR: File .env not found!
echo Create: copy "docs\config\.env.example" .env
echo Then set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID
echo.
pause
popd
exit 1

:err_no_token
echo ERROR: No project and no TELEGRAM_BOT_TOKEN!
echo Use: start.bat flowcabinet
echo Or set PROJECT_ID=flowcabinet in .env
echo Or set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in .env
echo List projects: python -m blocks.spambot --list-projects
echo.
pause
popd
exit 1

:err_no_channel
echo ERROR: TELEGRAM_CHANNEL_ID not set!
echo Add to .env or run: start.bat flowcabinet
echo.
pause
popd
exit 1

:err_deps
echo.
echo WARNING: Dependencies not installed!
echo Run: pip install -r "docs\config\requirements.txt"
echo Or: pip install python-telegram-bot feedparser googletrans==4.0.0-rc1
echo.
set /p install="Install now? y/n: "
if /i not "%install%"=="y" goto err_exit
pip install -r "docs\config\requirements.txt"
if errorlevel 1 goto err_install
goto check_deps

:err_install
echo Install failed.
pause
popd
exit 1

:err_run
echo.
echo ERROR: Bot exited with error.
echo Check: .env tokens, bot is admin in channel, network.
echo.
pause
popd
exit 1

:err_exit
pause
popd
exit 1

:done
popd
pause
