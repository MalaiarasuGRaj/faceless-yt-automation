@echo off
echo ╔══════════════════════════════════════════════════════════╗
echo ║  YouTube Automation - Windows Task Scheduler Setup       ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

echo This will create a Windows scheduled task that runs
echo the YouTube automation every 6 hours automatically.
echo.
echo Current directory: %SCRIPT_DIR%
echo.

choice /C YN /M "Do you want to create the scheduled task"
if errorlevel 2 goto :cancel

echo.
echo [1/3] Creating scheduled task...

schtasks /create /tn "YouTubeShortsAutomation" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_DIR%scheduler.py\" --once" ^
    /sc HOURLY /mo 6 ^
    /st 09:00 ^
    /f

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create task. Try running this as Administrator.
    echo.
    echo Manual alternative - run in PowerShell as Admin:
    echo   schtasks /create /tn "YouTubeShortsAutomation" /tr "python %SCRIPT_DIR%scheduler.py --once" /sc HOURLY /mo 6 /st 09:00 /f
    pause
    exit /b 1
)

echo.
echo [2/3] Task created successfully!
echo.
echo Task details:
echo   Name:      YouTubeShortsAutomation
echo   Schedule:  Every 6 hours
echo   Start:     09:00 AM
echo   Command:   python scheduler.py --once
echo.

echo [3/3] Verifying task...
schtasks /query /tn "YouTubeShortsAutomation" /fo LIST

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  DONE! Automation will run every 6 hours.               ║
echo ║                                                          ║
echo ║  Useful commands:                                        ║
echo ║  View task:    schtasks /query /tn "YouTubeShortsAutomation" ║
echo ║  Delete task:  schtasks /delete /tn "YouTubeShortsAutomation" /f ║
echo ║  Run now:      schtasks /run /tn "YouTubeShortsAutomation"   ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
pause
exit /b 0

:cancel
echo.
echo Cancelled. No task was created.
echo.
echo You can always run manually:
echo   python scheduler.py
echo   python scheduler.py --once
echo.
pause
