@echo off
REM ===========================================================================
REM  CVmate build script
REM  Double-click this file to produce a standalone Windows executable at:
REM      dist\CVmate.exe
REM  No Python knowledge needed beyond having Python 3.11+ installed.
REM ===========================================================================
setlocal

set PY=py
%PY% --version >nul 2>nul
if errorlevel 1 set PY=python

echo === [1/3] Installing runtime dependencies ===
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo === [2/3] Installing PyInstaller (build tool) ===
%PY% -m pip install pyinstaller
if errorlevel 1 goto :error

echo === [3/3] Building CVmate.exe ===
%PY% -m PyInstaller --clean --noconfirm CVmate.spec
if errorlevel 1 goto :error

echo.
echo ===========================================================================
echo  Build complete.  Your executable is here:
echo      %CD%\dist\CVmate.exe
echo  Share that single file. On first run it asks for a Gemini API key.
echo ===========================================================================
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Scroll up to see the error.
pause
exit /b 1
