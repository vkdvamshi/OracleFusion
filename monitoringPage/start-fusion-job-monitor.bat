@echo off
rem Double-click me: starts the local proxy and opens the monitor page.
cd /d "%~dp0"
echo Starting Fusion Job Monitor... (close this window or press Ctrl+C to stop)

rem Prefer the Windows Python launcher, fall back to python on PATH.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 cors-proxy.py
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python cors-proxy.py
    ) else (
        echo.
        echo Python 3 was not found. Install it from https://www.python.org/downloads/
        echo ^(check "Add python.exe to PATH" during install^), then run this again.
    )
)
pause
