import os
import sys
import subprocess
import shutil
from pathlib import Path
from pym.utils import log_info, log_success, log_error

def find_venv_root(start_path=None) -> Path:
    """
    Traverse parent directories to find a folder containing a '.venv' directory.
    Defaults to starting from current working directory.
    """
    curr = Path(start_path or os.getcwd()).resolve()
    while True:
        candidate = curr / ".venv"
        if candidate.is_dir() and (candidate / "pyvenv.cfg").is_file():
            return candidate
        
        # Check parents
        if curr.parent == curr:
            break
        curr = curr.parent
        
    # Return local Candidate if none found, as default destination
    return Path(start_path or os.getcwd()).resolve() / ".venv"

def get_venv_bin_dir(venv_path: Path) -> Path:
    """
    Get the directory containing executables inside the virtual environment
    which depends on the operating system.
    """
    if os.name == "nt":
        return venv_path / "Scripts"
    return venv_path / "bin"

def get_venv_python(venv_path: Path = None) -> Path:
    """
    Get path to the python executable within the virtualenv.
    """
    if not venv_path:
        venv_path = find_venv_root()
    
    bin_dir = get_venv_bin_dir(venv_path)
    exe_name = "python.exe" if os.name == "nt" else "python"
    return bin_dir / exe_name

def get_venv_pip(venv_path: Path = None) -> Path:
    """
    Get path to the pip executable within the virtualenv.
    """
    if not venv_path:
        venv_path = find_venv_root()
        
    bin_dir = get_venv_bin_dir(venv_path)
    exe_name = "pip.exe" if os.name == "nt" else "pip"
    return bin_dir / exe_name

def is_venv_active() -> bool:
    """
    Check if the script is currently running inside a virtual environment.
    """
    return hasattr(sys, "real_prefix") or (sys.base_prefix != sys.prefix)

def get_dir_size_mb(path: Path) -> float:
    """
    Compute directory size in megabytes.
    """
    total = 0
    if not path.exists():
        return 0.0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += int(get_dir_size_mb(Path(entry.path)) * 1024 * 1024)
    except Exception:
        pass
    return round(total / (1024 * 1024), 2)

def create_venv(venv_path: Path, uv_path: str = None) -> bool:
    """
    Create a new virtual environment at venv_path.
    Uses 'uv venv' if uv_path is provided, otherwise standard 'venv' module.
    """
    if venv_path.exists():
        log_info(f"Existing virtual environment detected at {venv_path}.")
        return True
        
    if uv_path:
        try:
            # Run high-speed uv virtualenv engine
            cmd = [uv_path, "venv", str(venv_path)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
            
    # Fallback to standard Python venv
    import venv
    try:
        venv.create(str(venv_path), with_pip=True)
        return True
    except Exception as e:
        log_error(f"Failed to create virtual environment: {e}")
        return False
