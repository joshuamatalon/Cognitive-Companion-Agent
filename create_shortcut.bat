@echo off
echo Creating desktop shortcut for Cognitive Companion Agent...

REM Get the current directory
set "CURRENT_DIR=%~dp0"

REM Create VBScript to create shortcut
echo Set WshShell = WScript.CreateObject("WScript.Shell") > temp_shortcut.vbs
echo Set oShellLink = WshShell.CreateShortcut("%USERPROFILE%\Desktop\Cognitive Companion Agent.lnk") >> temp_shortcut.vbs
echo oShellLink.TargetPath = "%CURRENT_DIR%run_app.bat" >> temp_shortcut.vbs
echo oShellLink.WorkingDirectory = "%CURRENT_DIR%" >> temp_shortcut.vbs
echo oShellLink.Description = "Launch Cognitive Companion Agent" >> temp_shortcut.vbs
echo oShellLink.IconLocation = "%CURRENT_DIR%run_app.bat,0" >> temp_shortcut.vbs
echo oShellLink.Save >> temp_shortcut.vbs

REM Execute the VBScript
cscript temp_shortcut.vbs >nul

REM Clean up
del temp_shortcut.vbs

echo ✅ Desktop shortcut created successfully!
echo 🖥️  You can now double-click "Cognitive Companion Agent" on your desktop to run the app
echo.
pause