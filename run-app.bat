@echo off
REM AI-IDE Application Launcher
REM Sets up Qt environment and runs the app

set QT_PATH=C:\Qt\6.11.1\llvm-mingw_64
set BUILD_DIR=D:\Desktop\Aide\ai-ide\build\src

REM Add Qt bin to PATH so DLLs are found
set PATH=%QT_PATH%\bin;%BUILD_DIR%;%PATH%
set QT_PLUGIN_PATH=%QT_PATH%\plugins

echo.
echo ===================================================
echo Launching AI-IDE...
echo Qt Bin Path: %QT_PATH%\bin
echo Executable:  %BUILD_DIR%\ai-ide.exe
echo ===================================================
echo.

"%BUILD_DIR%\ai-ide.exe"

if errorlevel 1 (
    echo.
    echo Error: Failed to run ai-ide.exe
    pause
)
