# Navigate to script directory (works for anyone)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Set execution policy for this session
Set-ExecutionPolicy -Scope Process Bypass

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the app
streamlit run app.py