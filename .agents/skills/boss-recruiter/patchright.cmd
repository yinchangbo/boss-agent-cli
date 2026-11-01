@echo off
setlocal
if not exist "%~dp0runtime\python.exe" (
  echo Portable Python is missing. Extract the complete Windows portable ZIP. 1>&2
  exit /b 1
)
if not defined PLAYWRIGHT_BROWSERS_PATH set "PLAYWRIGHT_BROWSERS_PATH=%~dp0ms-playwright"
"%~dp0runtime\python.exe" -I -B -X utf8 -m patchright %*
exit /b %errorlevel%
