@echo off
echo Starting Cognitive Companion Agent...
echo.
echo Opening your browser to http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the Streamlit app
streamlit run app.py

echo.
echo Application stopped.
pause