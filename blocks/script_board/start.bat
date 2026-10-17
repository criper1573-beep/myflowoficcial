@echo off
chcp 65001 >nul
REM Доска скриптов диалогов — запуск веб-приложения

pushd "%~dp0"
cd ..\..
if errorlevel 1 (
    echo Ошибка: не удалось перейти в корень проекта.
    pause
    exit /b 1
)

if not exist blocks\script_board\dist\index.html (
    echo Сборка фронта (dist отсутствует)...
    pushd blocks\script_board\frontend
    call npm run build
    popd
)

if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

python -m blocks.script_board

popd
pause
