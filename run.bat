@echo off
REM QuickBooks Desktop Test Tool - Launch Script
REM Uses 32-bit Python (required for QBFC COM component)

set PYTHON32=C:\Users\Nick Chamberlain\AppData\Local\Programs\Python\Python313-32\python.exe

echo Starting QBD Test Tool...
echo.
echo Make sure QuickBooks Desktop is running with a company file open!
echo.

REM Check if 32-bit Python is available
"%PYTHON32%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: 32-bit Python not found at %PYTHON32%
    echo.
    echo QBFC requires 32-bit Python. Please install it from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
"%PYTHON32%" -c "import win32com.client" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required dependencies not installed
    echo.
    echo Run this command first:
    echo %PYTHON32% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Launch the application with 32-bit Python
"%PYTHON32%" src\app.py

REM If the script exits with an error, pause so user can see it
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
