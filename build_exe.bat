@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing build dependencies...
python -m pip install -e ".[dev]" pyinstaller -q
if errorlevel 1 goto :error

echo [2/3] Building xLizard.exe (onedir)...
python -m PyInstaller --noconfirm xlizard.spec
if errorlevel 1 goto :error

echo [3/3] Ensuring xlizard.json next to the exe...
copy /Y "xlizard.json" "dist\xLizard\xlizard.json" >nul
if errorlevel 1 goto :error

echo.
echo Done.
echo Run:  dist\xLizard\xLizard.exe
echo Edit: dist\xLizard\xlizard.json
echo.
goto :eof

:error
echo BUILD FAILED
exit /b 1
