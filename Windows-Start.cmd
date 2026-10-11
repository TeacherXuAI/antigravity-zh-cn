@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
if exist "%~dp0runtime\python.exe" (
  "%~dp0runtime\python.exe" -I -X utf8 "%~dp0tools\windows_patcher.py" menu %*
) else (
  py -3 -X utf8 "%~dp0tools\windows_patcher.py" menu %*
)
set "AGZH_EXIT=%ERRORLEVEL%"
echo.
if not "%AGZH_EXIT%"=="0" echo The tool stopped. See the message above and README.md.
pause
exit /b %AGZH_EXIT%
