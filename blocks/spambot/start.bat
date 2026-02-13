@echo off
chcp 65001 > nul
REM Usage: start.bat [project_id] e.g. start.bat flowcabinet

pushd "%~dp0"
cd ..
cd ..
if errorlevel 1 goto err_cd

if not exist .env goto err_env
for /f "usebackq tokens=1,* delims==" %%a in (.env) do set "%%a=%%b"

if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

if not "%~1"=="" (
    python -m blocks.spambot --project %~1
) else (
    if defined PROJECT_ID (
        python -m blocks.spambot --project %PROJECT_ID%
    ) else (
        python -m blocks.spambot
    )
)

if errorlevel 1 goto err_run
goto done

:err_cd
echo Error: cannot change to project root.
pause
exit 1

:err_env
echo ERROR: .env not found in project root.
echo Create .env and set TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID or PROJECT_ID.
pause
exit 1

:err_run
echo Bot exited with error.
pause
exit 1

:done
echo.
pause
popd
