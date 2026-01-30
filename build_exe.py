import os
import subprocess
import sys

def check_pyinstaller():
    try:
        subprocess.run(["pyinstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[INFO] PyInstaller is already installed.")
        return True
    except FileNotFoundError:
        print("[INFO] PyInstaller not found. Installing...")
        return False

def install_pyinstaller():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[INFO] PyInstaller installed successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to install PyInstaller: {e}")
        sys.exit(1)

def build_executable():
    print("[INFO] Starting build process...")
    
    # Define separator based on OS (Windows uses ';', Linux ':')
    if os.name == 'nt':
        sep = ';'
    else:
        sep = ':'
        
    cmd = [
        "pyinstaller",
        "--name", "AsunaVPet",
        "--noconsole",
        "--onefile",
        # Bundle assets
        "--add-data", f"assets{sep}assets",
        # We don't bundle 'data' because it's for saves, which are generated
        "main.py"
    ]
    
    print(f"[INFO] Running command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\n[SUCCESS] Build complete! Check the 'dist' folder for AsunaVPet.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with exit code {e.returncode}")

if __name__ == "__main__":
    if not check_pyinstaller():
        install_pyinstaller()
    
    # Ensure Assets exist
    if not os.path.exists("assets"):
        print("[ERROR] 'assets' folder not found! Make sure you are in the project root.")
        sys.exit(1)
        
    build_executable()
