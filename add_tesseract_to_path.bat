@echo off
echo Adding Tesseract-OCR to PATH...
echo ================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo WARNING: Not running as administrator. 
    echo You may need to run this script as administrator.
    echo Right-click and select "Run as administrator"
    echo.
)

:: Add to current session PATH
set PATH=C:\Program Files\Tesseract-OCR;%PATH%

:: Add to user PATH permanently
setx PATH "C:\Program Files\Tesseract-OCR;%PATH%" >nul 2>&1

:: Test if tesseract works
echo.
echo Testing Tesseract installation...
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version 2>NUL
if %errorLevel% == 0 (
    echo.
    echo SUCCESS! Tesseract is installed and working.
    echo.
    echo IMPORTANT: You need to:
    echo 1. Close and restart any open Command Prompts
    echo 2. Restart your Streamlit app
    echo 3. If using an IDE like VS Code, restart it
    echo.
) else (
    echo.
    echo ERROR: Could not run Tesseract. Please check installation.
)

pause