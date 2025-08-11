@echo off
echo Starting Cognitive Companion Agent...
echo.
echo Opening browser at http://localhost:8501
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
streamlit run app.py

pause