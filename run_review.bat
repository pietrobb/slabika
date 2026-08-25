@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

where py >nul 2>nul
if errorlevel 1 (
    python -m slabika.review --db "%~dp0tests\data\translatemaster_hyphenation_working.sqlite" --decisions "%~dp0tests\data\review_decisions.sqlite" %*
) else (
    py -3 -m slabika.review --db "%~dp0tests\data\translatemaster_hyphenation_working.sqlite" --decisions "%~dp0tests\data\review_decisions.sqlite" %*
)

if errorlevel 1 pause
