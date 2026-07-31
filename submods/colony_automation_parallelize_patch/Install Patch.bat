@echo off
setlocal
title Colony Automation Parallel Construction Patch
echo Stellaris must be closed before installing this patch.
echo.
"%~dp0ColonyAutomationParallelizePatch.exe" --prompt --apply --output "%~dp0patch_apply_receipt.json"
set "exit_code=%ERRORLEVEL%"
echo.
if not "%exit_code%"=="0" (
    echo Patch installation was refused. No game file was changed.
) else (
    echo Patch installed. The verified receipt is patch_apply_receipt.json.
)
echo.
pause
exit /b %exit_code%
