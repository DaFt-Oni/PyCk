import os
import json
import subprocess
from pathlib import Path
from pym.utils import log_error, log_info
from pym.venv import get_venv_python

DEFAULT_PYCKAGE = {
    "name": "my-project",
    "version": "0.1.0",
    "description": "A Python project managed by PyCk",
    "private": True,
    "author": "",
    "python": "^3.13",
    "scripts": {
        "dev": "python main.py"
    },
    "dependencies": {},
    "devDependencies": {}
}

def find_pyckage_json(start_path=None) -> Path:
    """
    Search recursively upwards for a pyckage.json file.
    Returns the Path to pyckage.json or the current directory candidate.
    """
    curr = Path(start_path or os.getcwd()).resolve()
    while True:
        candidate = curr / "pyckage.json"
        if candidate.is_file():
            return candidate
            
        if curr.parent == curr:
            break
        curr = curr.parent
        
    return Path(os.getcwd()).resolve() / "pyckage.json"

def load_pyckage_json(path: Path = None) -> dict:
    """
    Load pyckage.json file. Returns default dict if not found.
    """
    if not path:
        path = find_pyckage_json()
        
    if not path.is_file():
        return DEFAULT_PYCKAGE.copy()
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Error reading {path.name}: {e}")
        return DEFAULT_PYCKAGE.copy()

def save_pyckage_json(data: dict, path: Path = None):
    """
    Format and save pyckage.json file with 2 space indentation.
    """
    if not path:
        path = find_pyckage_json()
        
    # Order key sections nicely
    key_order = ["name", "version", "description", "private", "author", "python", "scripts", "dependencies", "devDependencies"]
    ordered_data = {}
    for key in key_order:
        if key in data:
            ordered_data[key] = data[key]
    for key in data:
        if key not in ordered_data:
            ordered_data[key] = data[key]
            
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ordered_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        log_error(f"Failed to save pyckage.json: {e}")

def get_installed_version(package_name: str, venv_path: Path) -> str:
    """
    Query the exact version of the package installed inside .venv
    using importlib.metadata in a clean subprocess.
    """
    python_exe = get_venv_python(venv_path)
    if not python_exe.exists():
        return "*"
        
    # Standardize package name for lookup (dashes to underscores, lowercase)
    norm_pkg = package_name.replace("-", "_").lower()
    
    code = f"""
import importlib.metadata
try:
    print(importlib.metadata.version('{package_name}'))
except Exception:
    try:
        print(importlib.metadata.version('{norm_pkg}'))
    except Exception:
        print("*")
"""
    try:
        res = subprocess.run(
            [str(python_exe), "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        ver = res.stdout.strip()
        return ver if ver and ver != "*" else "*"
    except Exception:
        return "*"

def update_pyckage_dependencies(packages: list, venv_path: Path, dev=False, remove=False):
    """
    Updates dependencies listed in pyckage.json based on installation / removal.
    """
    pyckage_path = find_pyckage_json()
    data = load_pyckage_json(pyckage_path)
    
    dep_key = "devDependencies" if dev else "dependencies"
    other_key = "dependencies" if dev else "devDependencies"
    
    if dep_key not in data:
        data[dep_key] = {}
    if other_key not in data:
        data[other_key] = {}
        
    for pkg in packages:
        # Extract pure package name (in case it contains version markers)
        # e.g., requests>=2.31.0 -> requests
        pkg_name = pkg
        for char in [">", "=", "<", "!", "~", "@"]:
            if char in pkg_name:
                pkg_name = pkg_name.split(char)[0]
        
        pkg_name = pkg_name.strip()
        
        if remove:
            # Delete from both lists to be sure
            if pkg_name in data[dep_key]:
                del data[dep_key][pkg_name]
            if pkg_name in data[other_key]:
                del data[other_key][pkg_name]
        else:
            # Add package
            installed_ver = get_installed_version(pkg_name, venv_path)
            # NPM-like caret behavior
            version_str = f"^{installed_ver}" if installed_ver != "*" else "*"
            
            # Remove from the other group in case it's moving
            if pkg_name in data[other_key]:
                del data[other_key][pkg_name]
                
            data[dep_key][pkg_name] = version_str
            
    # Alphabetize dependencies
    data[dep_key] = {k: data[dep_key][k] for k in sorted(data[dep_key].keys())}
    if data[other_key]:
        data[other_key] = {k: data[other_key][k] for k in sorted(data[other_key].keys())}
        
    save_pyckage_json(data, pyckage_path)

def generate_lockfile(venv_path: Path):
    """
    Generates a locked snapshot file 'pyckage.lock' in the root directory.
    Stores flat dictionary of all installed packages, their exact versions in .venv,
    and their cryptographic integrity hashes (SHA256).
    """
    python_exe = get_venv_python(venv_path)
    if not python_exe.exists():
        return
        
    pyckage_path = find_pyckage_json()
    lock_path = pyckage_path.parent / "pyckage.lock"
    
    # Python code to get all installed distributions in .venv
    code = """
import importlib.metadata
dists = importlib.metadata.distributions()
locked = {d.metadata['Name'].lower(): d.version for d in dists if d.metadata.get('Name')}
import json
print(json.dumps(locked))
"""
    try:
        res = subprocess.run(
            [str(python_exe), "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            locked_data = json.loads(res.stdout.strip())
            
            # Fetch hashes from PyPI in a lightweight way
            from pym.security import fetch_pypi_metadata
            packages_locked = {}
            
            for pkg, ver in sorted(locked_data.items()):
                sha = "sha256:unknown"
                metadata = fetch_pypi_metadata(pkg, ver)
                if metadata:
                    # Retrieve the sha256 of the sdist or wheel packages
                    urls = metadata.get("urls", [])
                    for u in urls:
                        digests = u.get("digests", {})
                        if "sha256" in digests:
                            sha = f"sha256:{digests['sha256']}"
                            break
                packages_locked[pkg] = {
                    "version": ver,
                    "resolved": f"https://pypi.org/project/{pkg}/{ver}/",
                    "integrity": sha
                }
            
            # Format and save lockfile
            lock_content = {
                "lockfileVersion": 1,
                "packages": packages_locked
            }
            with open(lock_path, "w", encoding="utf-8") as f:
                json.dump(lock_content, f, indent=2, ensure_ascii=False)
                f.write("\n")
    except Exception:
        pass
