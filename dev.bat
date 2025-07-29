cd /d %~dp0

@echo off
setlocal

REM Set your virtual environment directory name
set VENV_DIR=.mathoku-dev-console-venv

REM Check if venv already exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM Activate the virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Install dependencies
if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt | findstr /V "Requirement already satisfied"
) else (
    echo No requirements.txt found.
)

echo Starting mathoku-dev-console...
python mathoku-dev-console.py

endlocal