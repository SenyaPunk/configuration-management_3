@echo off
setlocal
pushd "%~dp0" || exit /b 1
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m src %*
) else (
    python -m src %*
)
set "exit_code=%errorlevel%"
popd
exit /b %exit_code%
