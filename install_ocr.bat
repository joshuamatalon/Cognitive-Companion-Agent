@echo off
echo Installing OCR Support for Cognitive Companion App
echo ==================================================
echo.

echo Step 1: Installing Python packages...
pip install pytesseract pdf2image pillow

echo.
echo Step 2: Tesseract-OCR Installation
echo -----------------------------------
echo.
echo You need to install Tesseract-OCR manually:
echo.
echo 1. Download the installer from:
echo    https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo 2. Run the installer (tesseract-ocr-w64-setup-5.x.x.exe)
echo.
echo 3. During installation, make note of the installation path
echo    (typically C:\Program Files\Tesseract-OCR)
echo.
echo 4. Add Tesseract to your PATH:
echo    - Right-click "This PC" and select "Properties"
echo    - Click "Advanced system settings"
echo    - Click "Environment Variables"
echo    - Under "System variables", find and select "Path", then click "Edit"
echo    - Click "New" and add: C:\Program Files\Tesseract-OCR
echo    - Click "OK" to save
echo.
echo 5. Restart your command prompt or IDE after installation
echo.

pause