import os
import sys
import subprocess
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw

def create_icon():
    os.makedirs("assets", exist_ok=True)
    icon_path = os.path.join("assets", "icon.ico")
    
    if not os.path.exists(icon_path):
        print("Generating default icon...")
        # Create a simple 256x256 image with a blue background and 'A'
        img = Image.new('RGB', (256, 256), color='#3498db')
        d = ImageDraw.Draw(img)
        # We don't have a guaranteed font, so we'll just draw a simple shape
        d.rectangle([64, 64, 192, 192], fill="white")
        d.ellipse([96, 96, 160, 160], fill="#3498db")
        img.save(icon_path, format='ICO', sizes=[(256, 256)])
        print(f"Icon created at {icon_path}")
    return icon_path

def create_version_file():
    version_content = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(3, 0, 0, 0),
    prodvers=(3, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'AutoImageFlow'),
        StringStruct('FileDescription', 'Auto Bulk Image Generator V3'),
        StringStruct('FileVersion', '3.0.0'),
        StringStruct('InternalName', 'AutoImageFlow'),
        StringStruct('LegalCopyright', 'Copyright (c) 2026'),
        StringStruct('OriginalFilename', 'AutoImageFlow.exe'),
        StringStruct('ProductName', 'AutoImageFlow V3'),
        StringStruct('ProductVersion', '3.0.0')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_content)
    return "version_info.txt"

def build():
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    icon_path = create_icon()
    version_file = create_version_file()
    
    try:
        import customtkinter
    except ImportError:
        print("Dependencies missing. Installing customtkinter...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter
        
    try:
        import playwright
    except ImportError:
        print("Dependencies missing. Installing playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        import playwright
        
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--name", "AutoImageFlow",
        "--icon", icon_path,
        "--version-file", version_file,
        "--add-data", f"config{os.pathsep}config",
        "--add-data", f"{ctk_path}{os.pathsep}customtkinter",
        "--collect-all", "playwright",
        "--noconfirm",
        "main.py"
    ]
    
    # Optional files
    if os.path.exists("workflow_api.json"):
        cmd.extend(["--add-data", f"workflow_api.json{os.pathsep}."])
        
    print(f"Running build command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("Build complete! Check the dist/ folder.")

if __name__ == "__main__":
    build()
