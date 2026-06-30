@echo off
setlocal

set "SELECTED_PYTHON="

if defined ROMAICPU_PY if exist "%ROMAICPU_PY%" set "SELECTED_PYTHON=%ROMAICPU_PY%"
if not defined SELECTED_PYTHON if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "SELECTED_PYTHON=%PYTHON_EXE%"
if not defined SELECTED_PYTHON if exist "C:\Users\Jian\.conda\envs\romaicpu\python.exe" set "SELECTED_PYTHON=C:\Users\Jian\.conda\envs\romaicpu\python.exe"
if not defined SELECTED_PYTHON if exist "C:\Users\admin\.conda\envs\romaicpu\python.exe" set "SELECTED_PYTHON=C:\Users\admin\.conda\envs\romaicpu\python.exe"

if not defined SELECTED_PYTHON (
    echo [ERROR] No usable Python interpreter found.
    echo [ERROR] Checked ROMAICPU_PY, PYTHON_EXE, and common romaicpu env paths.
    exit /b 1
)

"%SELECTED_PYTHON%" %*
exit /b %ERRORLEVEL%
