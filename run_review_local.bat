@echo off
@rem SPDX-FileCopyrightText: 2026 Peter Bezemek <peter.bezemek@gmail.com>
@rem SPDX-License-Identifier: Apache-2.0 OR MIT
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

set "REVIEW_HOME=%LOCALAPPDATA%\slabika-review"
if not defined LOCALAPPDATA set "REVIEW_HOME=%USERPROFILE%\slabika-review"
if not exist "%REVIEW_HOME%" mkdir "%REVIEW_HOME%"
if errorlevel 1 (
    echo Nepodarilo sa vytvorit pracovny priecinok: %REVIEW_HOME%
    pause
    exit /b 1
)
set "DECISIONS=%REVIEW_HOME%\review_decisions.sqlite"

echo Rozhodnutia sa ukladaju oddelene do:
echo   %DECISIONS%
echo Navrhy pre autora stiahnete tlacidlom "Stiahnut opravy" v rozhrani.
echo.

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor in range(10))" >nul 2>nul
    if not errorlevel 1 goto run_py
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor in range(10))" >nul 2>nul
    if not errorlevel 1 goto run_python
)

echo Chyba: treba nainstalovat Python 3.10 alebo novsi.
pause
exit /b 1

:run_py
py -3 -m slabika.review --decisions "%DECISIONS%" %*
goto finished

:run_python
python -m slabika.review --decisions "%DECISIONS%" %*

:finished
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
