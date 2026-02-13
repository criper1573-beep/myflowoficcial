@echo off
chcp 65001 > nul
REM Post FLOW: one run = one post to channel. Run from project root.
pushd "%~dp0"
cd ..
cd ..
if errorlevel 1 goto err
python -m blocks.post_flow.bot
goto done
:err
echo Error: cannot change to project root.
pause
exit 1
:done
pause
popd
