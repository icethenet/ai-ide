import os
import subprocess
import shutil
import sys

LLVM_PATH = r"C:\Qt\Tools\llvm-mingw_64\bin"
QT_PATH = r"C:\Qt\6.11.1\llvm-mingw_64"
BUILD_DIR = r"D:\Desktop\Aide\ai-ide\build"
SOURCE_DIR = r"D:\Desktop\Aide\ai-ide"

# Ensure tools and Qt are in the environment PATH for this process
qt_bin = os.path.join(QT_PATH, "bin")
os.environ["PATH"] = LLVM_PATH + os.pathsep + qt_bin + os.pathsep + os.environ.get("PATH", "")

def check_tool(tool):
    path = shutil.which(tool)
    if path:
        print(f"FOUND: {tool} -> {path}")
        return True
    else:
        print(f"MISSING: {tool}")
        return False

def run_init_scripts():
    print("\n=== CLEANING LEGACY SOURCE FILES ===\n")
    # List of legacy files to remove from the src root that conflict with src/ui/
    legacy_files = [
        "CustomEditor.h", "CustomEditor.cpp",
        "DiffView.h", "DiffView.cpp",
        "EditorWindow.h", "EditorWindow.cpp",
        "GitClient.h", "GitClient.cpp",
        "main.cpp"
    ]
    for f in legacy_files:
        path = os.path.join(SOURCE_DIR, "src", f)
        if os.path.exists(path):
            print(f"Removing legacy file: {path}")
            os.remove(path)

    print("\n=== INITIALIZING SOURCE FILES ===\n")
    # Consolidated all generation into features script
    scripts = ["add_custom_editor_and_features.py"]
    for script in scripts:
        if os.path.exists(script):
            print(f"Running {script}...")
            subprocess.run([sys.executable, script], check=True)

# Ensure source is initialized
run_init_scripts()

print("\n=== VERIFYING LLVM-MINGW TOOLCHAIN ===\n")

tools_ok = all([
    check_tool("clang"),
    check_tool("clang++"),
    check_tool("ninja"),
])

if not tools_ok:
    print("\nERROR: Toolchain not visible in PATH.")
    print("Add this to SYSTEM PATH and restart:")
    print(LLVM_PATH)
    exit(1)

print("\n=== CONFIGURING PROJECT WITH CMAKE + NINJA ===\n")

os.makedirs(BUILD_DIR, exist_ok=True)
os.chdir(BUILD_DIR)

config = [
    "cmake",
    "-G", "Ninja",
    "-DCMAKE_C_COMPILER=clang",
    "-DCMAKE_CXX_COMPILER=clang++",
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    f"-DCMAKE_PREFIX_PATH={QT_PATH}",
    SOURCE_DIR
]

if subprocess.call(config) != 0:
    print("\nCONFIGURATION FAILED.")
    exit(1)

print("\n=== BUILDING PROJECT ===\n")

if subprocess.call(["cmake", "--build", "."]) == 0:
    print("\n=== BUILD SUCCESSFUL ===")
    
    # Optional: Run the app immediately
    exe_path = os.path.join(BUILD_DIR, "src", "ai-ide.exe")
    if "--run" in sys.argv and os.path.exists(exe_path):
        print(f"\n=== STARTING {exe_path} ===\n")
        subprocess.run([exe_path])
else:
    print("\n=== BUILD FAILED ===")
