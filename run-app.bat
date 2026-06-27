@echo off
REM AI-IDE Application Launcher
REM Sets up Qt environment and runs the app

setlocal enabledelayedexpansion

set QT_PATH=C:\Qt\6.11.1\llvm-mingw_64
set BUILD_DIR=D:\Desktop\Aide\ai-ide\build\src

REM Add Qt bin to PATH so DLLs are found
set PATH=!QT_PATH!\bin;!BUILD_DIR!;!PATH!
set QT_PLUGIN_PATH=!QT_PATH!\plugins

REM Run the executable
echo Launching AI-IDE...
"!BUILD_DIR!\ai-ide.exe"

if errorlevel 1 (
    echo.
    echo Error: Failed to run ai-ide.exe
    pause
)
