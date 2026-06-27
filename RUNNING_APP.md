# Running AI-IDE Application

## Problem
The compiled `ai-ide.exe` couldn't find Qt6 runtime DLLs when running:
- `Qt6Widgets.dll`
- `Qt6Core.dll`
- `Qt6Gui.dll`
- `Qt6Network.dll`
- `qwindows.dll` (platform plugin)

## Solution Implemented

### ✅ Option 1: Use the Run Script (Easiest)
Double-click or run from PowerShell:
```
d:\Desktop\Aide\run-app.bat
```

This automatically sets up the Qt environment and launches the app.

### ✅ Option 2: Run from PowerShell with Environment Setup
```powershell
$env:QT_PATH = "C:\Qt\6.11.1\llvm-mingw_64"
$env:PATH = "$env:QT_PATH\bin;d:\Desktop\Aide\ai-ide\build\src;$env:PATH"
& "d:\Desktop\Aide\ai-ide\build\src\ai-ide.exe"
```

### ✅ Option 3: Run from Command Prompt
```cmd
set QT_PATH=C:\Qt\6.11.1\llvm-mingw_64
set PATH=%QT_PATH%\bin;d:\Desktop\Aide\ai-ide\build\src;%PATH%
d:\Desktop\Aide\ai-ide\build\src\ai-ide.exe
```

---

## What Was Done

1. ✅ **Copied Qt DLLs** to `ai-ide\build\src\`:
   - Qt6Core.dll
   - Qt6Gui.dll
   - Qt6Widgets.dll
   - Qt6Network.dll
   - platforms/qwindows.dll

2. ✅ **Created** `run-app.bat` launch script that:
   - Sets Qt binary directory in PATH
   - Automatically finds all DLL dependencies
   - Launches the executable

---

## Files Created
- `d:\Desktop\Aide\run-app.bat` - Application launcher script

## Files Modified
- Qt DLLs copied to `d:\Desktop\Aide\ai-ide\build\src\`

---

## Application Architecture
```
d:\Desktop\Aide\
├── ai-ide\
│   ├── src\
│   │   ├── ai-ide.exe          (Main executable)
│   │   ├── Qt6Core.dll         (Core Qt library)
│   │   ├── Qt6Gui.dll          (GUI library)
│   │   ├── Qt6Widgets.dll      (Widgets library)
│   │   ├── Qt6Network.dll      (Network library)
│   │   └── platforms\
│   │       └── qwindows.dll    (Windows platform plugin)
│   └── build\                   (CMake build output)
├── run-app.bat                  (Launch script)
└── build.py                     (Build automation)
```

---

## Troubleshooting

### If app still won't run:
1. Ensure Qt6 is installed at `C:\Qt\6.11.1\llvm-mingw_64`
2. Verify DLLs were copied successfully to `ai-ide\build\src\`
3. Check that `platforms\qwindows.dll` exists in the src directory
4. Set `QT_DEBUG_PLUGINS=1` environment variable to see what plugins are being loaded

### If you see "Missing platform plugin":
This means the `platforms\qwindows.dll` wasn't found. Ensure the plugins directory structure is correct:
```
ai-ide/build/src/
├── ai-ide.exe
├── platforms/
│   └── qwindows.dll
└── (other Qt DLLs)
```
