@echo off
cd /d "%~dp0"

:: Define the virtual environment folder
set VENV_DIR=.venv

:: Check if the virtual environment exists
if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Creating one...
    python -m venv %VENV_DIR%
    
    :: Activate the virtual environment
    call "%VENV_DIR%\Scripts\activate.bat"
    
    :: Install the required packages
    python -m pip install -r requirements.txt --prefer-binary
) else (
    echo Activating existing virtual environment...
    call "%VENV_DIR%\Scripts\activate.bat"
)

pause