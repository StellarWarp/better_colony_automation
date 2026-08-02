@echo off
setlocal
title Check Colony Automation Patch Status
echo Stellaris may remain open. This check does not modify game files.
echo.
"%~dp0ColonyAutomationParallelizePatch.exe" --prompt --status --output "%~dp0patch_status.json"
set "exit_code=%ERRORLEVEL%"
echo.
if not "%exit_code%"=="0" (
    echo Patch status could not be inspected. No game file was changed.
) else (
    echo Status written to patch_status.json.
)
echo.
pause
exit /b %exit_code%
