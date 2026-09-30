@echo off
REM Double-click this file to install (first time) and play Streetball Kingdom.
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py
echo Getting the game ready...
%PY% -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo.
  echo Could not install. Is Python installed with "Add Python to PATH" ticked?
  pause
  exit /b 1
)
echo Starting the game...
%PY% main.py
if errorlevel 1 pause
