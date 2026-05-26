import os
import sys
import subprocess
from pathlib import Path

# Force stdout/stderr stream encoding to UTF-8 to prevent Windows CP1252 charmap crashes
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_interactive_installer():
    """
    Runs the custom interactive installation that installs pym via pip
    and registers it in the system environment PATH persistently.
    """
    print("\n\033[1;36m┌────────────────────────────────────────────────────────┐\033[0m")
    print("\033[1;36m│          PyCk Global Setup & PATH Register             │\033[0m")
    print("\033[1;36m└────────────────────────────────────────────────────────┘\033[0m\n")
    
    print("🚀 Installing PyCk globally in development (editable) mode...")
    
    # Run pip install -e .
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode != 0:
            print(f"\033[1;31m✖ Error installing package via pip:\033[0m\n{res.stderr}")
            sys.exit(1)
        print("\033[1;32m✔ Package registered successfully!\033[0m")
    except Exception as e:
        print(f"\033[1;31m✖ Failed to run pip installation: {e}\033[0m")
        sys.exit(1)

    # Resolve scripts directory (where pip places the executable)
    python_dir = Path(sys.executable).parent
    scripts_dir = None
    
    if os.name == "nt":
        scripts_candidate = python_dir / "Scripts"
        if scripts_candidate.exists():
            scripts_dir = scripts_candidate
        else:
            scripts_dir = python_dir
    else:
        scripts_candidate = python_dir
        if (scripts_candidate / "pym").exists():
            scripts_dir = scripts_candidate
        else:
            scripts_dir = python_dir.parent / "bin"
            
    # Try user site-packages bin as fallback
    if not scripts_dir or not scripts_dir.exists():
        try:
            import site
            user_base = Path(site.getuserbase())
            if os.name == "nt":
                scripts_dir = user_base / "Scripts"
            else:
                scripts_dir = user_base / "bin"
        except Exception:
            pass

    if not scripts_dir or not scripts_dir.exists():
        scripts_dir = python_dir
        
    print(f"ℹ Resolved CLI scripts directory: \033[1;35m{scripts_dir}\033[0m")
    
    # Persistent PATH registration depending on operating system
    registered = False
    if os.name == "nt":
        try:
            import winreg
            import ctypes
            
            # Access HKCU Environment variable registry
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                current_path, type_id = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
                type_id = winreg.REG_EXPAND_SZ
                
            path_list = [p.strip() for p in current_path.split(";") if p.strip()]
            target_str = str(scripts_dir.resolve())
            
            if target_str not in path_list:
                path_list.append(target_str)
                new_path = ";".join(path_list)
                winreg.SetValueEx(key, "Path", 0, type_id, new_path)
                registered = True
                print("\033[1;32m✔ PATH updated persistently in Windows Registry!\033[0m")
            else:
                print("ℹ Scripts directory is already registered in your Windows PATH.")
                registered = True
            winreg.CloseKey(key)
            
            # Broadcast environment change to system to update active processes instantly
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_ulong()
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
            )
            print("\033[1;32m✔ Broadcasted PATH changes to Windows system successfully!\033[0m")
        except Exception as e:
            print(f"\033[1;31m✖ Failed to modify Windows Registry PATH: {e}\033[0m")
            print("Please add the scripts folder to your PATH manually.")
    else:
        # Unix Shell profiles registration
        shell_configs = [Path.home() / ".bashrc", Path.home() / ".zshrc", Path.home() / ".profile"]
        export_line = f'\n# PyCk package manager CLI PATH registration\nexport PATH="{scripts_dir.resolve()}:$PATH"\n'
        
        modified_files = []
        for conf in shell_configs:
            if conf.exists():
                try:
                    with open(conf, "r") as f:
                        content = f.read()
                    if str(scripts_dir.resolve()) not in content:
                        with open(conf, "a") as f:
                            f.write(export_line)
                        modified_files.append(conf.name)
                except Exception as e:
                    print(f"⚠️ Failed to update {conf.name}: {e}")
                    
        if modified_files:
            print(f"\033[1;32m✔ PATH export registered in shell profiles: {', '.join(modified_files)}!\033[0m")
            registered = True
        else:
            print("ℹ PATH export already exists or shell configurations were not found.")
            registered = True
            
    print("\n\033[1;32m┌────────────────────────────────────────────────────────┐\033[0m")
    print("\033[1;32m│               🎉 Setup Completed! 🎉                   │\033[0m")
    print("\033[1;32m├────────────────────────────────────────────────────────┤\033[0m")
    print("│  To start managing your Python environments with ease: │")
    print("│                                                        │")
    print("│  1. Open a \033[1;33mNEW\033[0m terminal window to load the path.        │")
    print("│  2. Type \033[1;36mpym --help\033[0m to explore available commands.     │")
    print("│  3. Type \033[1;36mpym init\033[0m in any folder to scaffold a project. │")
    print("\033[1;32m└────────────────────────────────────────────────────────┘\033[0m\n")

if __name__ == "__main__":
    # If run directly without arguments, start interactive environment register
    if len(sys.argv) == 1:
        run_interactive_installer()
    else:
        # Behave as standard setuptools script fallback
        try:
            from setuptools import setup, find_packages
            setup(
                name="pyck",
                version="1.0.0",
                packages=find_packages(),
                entry_points={
                    'console_scripts': [
                        'pym=pym.cli:main',
                    ],
                },
            )
        except ImportError:
            print("Error: setuptools is required to run installation options.")
            sys.exit(1)
