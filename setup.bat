@echo off
setlocal enabledelayedexpansion

:menu
cls
echo TextCompare
echo ==========
echo.
echo 1. Install Requirements
echo 2. Run Application
echo 3. Install Requirements and Run
echo 4. Check Python Installation
echo 5. Check Ollama Installation
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto run
if "%choice%"=="3" goto install_and_run
if "%choice%"=="4" goto check_python
if "%choice%"=="5" goto check_ollama
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:install
echo.
echo Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing requirements.
    pause
    goto menu
)
echo Requirements installed successfully!
pause
goto menu

:run
echo.
echo Starting TextCompare...
python app.py
if errorlevel 1 (
    echo Error running the application.
    pause
    goto menu
)
goto menu

:install_and_run
echo.
echo Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing requirements.
    pause
    goto menu
)
echo Requirements installed successfully!
echo.
echo Starting TextCompare...
python app.py
if errorlevel 1 (
    echo Error running the application.
    pause
    goto menu
)
goto menu

:check_python
echo.
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher from https://www.python.org/downloads/
) else (
    echo Python is installed correctly.
)
pause
goto menu

:check_ollama
echo.
echo Checking Ollama installation...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Ollama is not running or not installed.
    echo Please install Ollama from https://ollama.com
    echo and make sure it's running.
) else (
    echo Ollama is running correctly.
)
pause
goto menu

:end
echo.
echo Thank you for using TextCompare!
timeout /t 2 >nul
exit 