import sys
import os

# --- CONFIGURATION (Change for future projects) ---
PROJECT_NAME = "Auto Image Flow"
REQUIRED_PYTHON_VERSION = "3.10"
EXPECTED_VENV_PATH = r"E:\Open-Generative-AI-main\AutoImageFlow\venv"
# --------------------------------------------------

def get_detected_venv():
    # sys.prefix returns the venv path if activated, otherwise the global python path
    return sys.prefix

def run_guard():
    # If running as a PyInstaller executable, skip the guard
    if getattr(sys, 'frozen', False):
        return

    detected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    interpreter_path = sys.executable
    detected_venv = get_detected_venv()
    
    # Check if python version matches the required major.minor (e.g. 3.10)
    version_mismatch = not detected_version.startswith(REQUIRED_PYTHON_VERSION)
    
    # Check if running in the expected venv path (case insensitive for Windows)
    expected_venv_norm = os.path.normpath(EXPECTED_VENV_PATH).lower()
    detected_venv_norm = os.path.normpath(detected_venv).lower()
    
    venv_mismatch = expected_venv_norm != detected_venv_norm
    
    mismatch = version_mismatch or venv_mismatch
    expected_interpreter = os.path.join(EXPECTED_VENV_PATH, "Scripts", "python.exe")
    
    if mismatch:
        # Check if the expected python interpreter exists
        if os.path.exists(expected_interpreter):
            print("========================")
            print("Python Guard:")
            print("Mismatch detected. Auto-relaunching with project venv...")
            print(f"Switching to: {expected_interpreter}")
            print("========================")
            
            # Relaunch the current process with the correct interpreter
            os.execv(expected_interpreter, [expected_interpreter] + sys.argv)
            return  # Should never reach here due to os.execv
        
        # If expected interpreter doesn't exist, show warning and halt
        print("========================")
        print("")
        print("PROJECT:")
        print(PROJECT_NAME)
        print("")
        print("Required Python:")
        print(f"{REQUIRED_PYTHON_VERSION}.x")
        print("")
        print("Detected Python:")
        print(detected_version)
        print("")
        print("Interpreter:")
        print(interpreter_path)
        print("")
        print("Expected Venv:")
        print(EXPECTED_VENV_PATH)
        print("")
        print("Detected Venv:")
        print(detected_venv)
        print("")
        print("STATUS:")
        print("MISMATCH")
        print("")
        print("Fix:")
        print("")
        print("Activate:")
        print(EXPECTED_VENV_PATH)
        print("")
        print("or select:")
        print(expected_interpreter)
        print("")
        print("========================")
        input("Press Enter to exit...")
        sys.exit(1)
    else:
        print("========================")
        print("")
        print("PROJECT:")
        print(PROJECT_NAME)
        print("")
        print("Required Python:")
        print(f"{REQUIRED_PYTHON_VERSION}.x")
        print("")
        print("Detected Python:")
        print(detected_version)
        print("")
        print("Interpreter:")
        print(interpreter_path)
        print("")
        print("Expected Venv:")
        print(EXPECTED_VENV_PATH)
        print("")
        print("Detected Venv:")
        print(detected_venv)
        print("")
        print("STATUS:")
        print("OK")
        print("")
        print("========================")
        print("Launching Application...")
        print("")

if __name__ == "__main__":
    run_guard()
