@echo off
setlocal
if not exist "%~dp0runtime\python.exe" (
  echo Portable Python is missing. Extract the complete Windows portable ZIP. 1>&2
  exit /b 1
)
"%~dp0runtime\python.exe" -I -B -X utf8 "%~dp0scripts\boss.py" %*
exit /b %errorlevel%
