@echo off
echo Installing Poppler for PDF to Image conversion
echo ==============================================
echo.
echo Poppler is required for pdf2image to work.
echo.
echo Please download Poppler for Windows:
echo.
echo 1. Go to: https://github.com/oschwartz10612/poppler-windows/releases/
echo 2. Download the latest Release-xx.xx.x-x.zip
echo 3. Extract the zip file to C:\Program Files\poppler
echo 4. The folder structure should be:
echo    C:\Program Files\poppler\Library\bin\
echo    (containing pdftoppm.exe and other files)
echo.
echo After installation, this script will add it to PATH.
echo.
pause

echo.
echo Adding Poppler to PATH...
set PATH=C:\Program Files\poppler\Library\bin;%PATH%
setx PATH "C:\Program Files\poppler\Library\bin;%PATH%" >nul 2>&1

echo.
echo Testing Poppler installation...
"C:\Program Files\poppler\Library\bin\pdftoppm.exe" -h >nul 2>&1
if %errorLevel% == 0 (
    echo SUCCESS! Poppler is installed and working.
) else (
    echo Poppler not found. Please install it first.
)

pause