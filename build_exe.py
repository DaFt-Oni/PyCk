import os
import sys
import shutil
import time
import subprocess
from datetime import datetime
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

# Theme colors
class Colors:
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    MAGENTA = "\033[1;35m"
    RED = "\033[1;31m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def bootstrap_pyinstaller():
    """
    Checks if PyInstaller is available; installs it on the fly if missing.
    """
    try:
        import PyInstaller
        return True
    except ImportError:
        print(f"🚀 {Colors.YELLOW}PyInstaller is not installed in the active environment.{Colors.RESET}")
        print(" Installing PyInstaller automatically via pip...")
        try:
            # Run pip install pyinstaller
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            print(f" {Colors.GREEN}✔ PyInstaller installed successfully!{Colors.RESET}")
            return True
        except Exception as e:
            print(f" {Colors.RED}✖ Failed to install PyInstaller automatically: {e}{Colors.RESET}")
            print("Please run 'pip install pyinstaller' manually and retry.")
            return False

def clean_paths(paths):
    """
    Safely removes specified folders or files.
    """
    for p in paths:
        path_obj = Path(p)
        if path_obj.exists():
            try:
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
            except Exception:
                pass

def main():
    print(f"\n{Colors.CYAN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│             PyCk Standalone Compiler Engine            │{Colors.RESET}")
    print(f"{Colors.CYAN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")

    start_time = time.time()
    
    # 1. Ensure PyInstaller is installed
    if not bootstrap_pyinstaller():
        sys.exit(1)
        
    root_dir = Path(__file__).parent.resolve()
    
    # Paths definition
    entry_file = root_dir / "pym_entry.py"
    spec_file = root_dir / "pym.spec"
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    
    # Clean previous build artifacts just in case
    clean_paths([entry_file, spec_file, build_dir, dist_dir])
    
    # 2. Create a clean entry-point script for PyInstaller tracing
    print(f"📂 {Colors.GRAY}Creating temporary entry point script...{Colors.RESET}")
    try:
        with open(entry_file, "w") as f:
            f.write(
                "import sys\n"
                "from pym.cli import main\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
    except Exception as e:
        print(f" {Colors.RED}✖ Failed to write temporary entry point: {e}{Colors.RESET}")
        sys.exit(1)
        
    # 3. Trigger compilation
    print(f"⚡ {Colors.CYAN}Compiling standalone package (this may take a few seconds)...{Colors.RESET}")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "pym",
        "--clean",
        "--log-level", "WARN",
        str(entry_file)
    ]
    
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f" {Colors.RED}✖ PyInstaller Compilation Failed:{Colors.RESET}\n{res.stderr}")
            clean_paths([entry_file, spec_file, build_dir, dist_dir])
            sys.exit(1)
    except Exception as e:
        print(f" {Colors.RED}✖ Failed to invoke PyInstaller subprocess: {e}{Colors.RESET}")
        clean_paths([entry_file, spec_file, build_dir, dist_dir])
        sys.exit(1)
        
    # Determine the compiled binary output name
    exe_filename = "pym.exe" if os.name == "nt" else "pym"
    compiled_exe = dist_dir / exe_filename
    
    if not compiled_exe.exists():
        print(f" {Colors.RED}✖ Error: Compiled executable not found at expected path: {compiled_exe}{Colors.RESET}")
        clean_paths([entry_file, spec_file, build_dir, dist_dir])
        sys.exit(1)
        
    # 4. Move to versioned bin folder
    version_str = datetime.now().strftime("v%Y%m%d_%H%M%S")
    target_bin_dir = root_dir / "bin" / version_str
    target_bin_dir.mkdir(parents=True, exist_ok=True)
    
    final_exe_path = target_bin_dir / exe_filename
    try:
        shutil.move(str(compiled_exe), str(final_exe_path))
    except Exception as e:
        print(f" {Colors.RED}✖ Failed to move executable to bin folder: {e}{Colors.RESET}")
        clean_paths([entry_file, spec_file, build_dir, dist_dir])
        sys.exit(1)
        
    # 5. Clean up build clutter
    print(f"🧹 {Colors.GRAY}Cleaning intermediate build directories and temporary files...{Colors.RESET}")
    clean_paths([entry_file, spec_file, build_dir, dist_dir])
    
    # 6. Print compilation receipt
    elapsed_time = round(time.time() - start_time, 2)
    file_size_mb = round(os.path.getsize(final_exe_path) / (1024 * 1024), 2)
    
    print(f"\n{Colors.GREEN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GREEN}│               🎉 Compilation Complete! 🎉              │{Colors.RESET}")
    print(f"{Colors.GREEN}├────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"│  {Colors.BOLD}Version:{Colors.RESET}   {Colors.YELLOW}{version_str:<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Location:{Colors.RESET}  {Colors.GRAY}{str(final_exe_path.relative_to(root_dir)):<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}File Size:{Colors.RESET} {Colors.GREEN}{f'{file_size_mb} MB':<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Duration:{Colors.RESET}  {Colors.CYAN}{f'{elapsed_time} seconds':<42}{Colors.RESET} │")
    print(f"{Colors.GREEN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
    print(f"🚀 To run this executable directly, execute:")
    print(f"   {Colors.BOLD}{Colors.YELLOW}./bin/{version_str}/{exe_filename} --help{Colors.RESET}\n")

if __name__ == "__main__":
    main()
