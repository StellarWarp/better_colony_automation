@echo off
setlocal
title Restore Original Stellaris Executable
echo Stellaris must be closed before restoring the original executable.
echo.
"%~dp0ColonyAutomationParallelizePatch.exe" --prompt --restore-auto-backup --output "%~dp0patch_restore_receipt.json"
set "exit_code=%ERRORLEVEL%"
echo.
if not "%exit_code%"=="0" (
    echo Restore was refused because no exact matching backup was found.
) else (
    echo Original executable restored. The receipt is patch_restore_receipt.json.
)
echo.
pause
exit /b %exit_code%
