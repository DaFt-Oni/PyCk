import os
import sys
import re
import subprocess
from pathlib import Path
from pym.utils import log_info, log_error, log_warning, Colors, ask_confirm
from pym.venv import get_venv_bin_dir, find_venv_root
from pym.config import load_global_config
from pym.security import analyze_script_risk

def load_dotenv(dotenv_path: Path) -> dict:
    """
    Parse a local .env file securely and return a dictionary of key-value pairs.
    Handles quotes, trailing comments, and spaces.
    """
    env_vars = {}
    if not dotenv_path.is_file():
        return env_vars
        
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Ignore comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Split at first '='
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                
                # Strip quotes if present
                if len(val) >= 2 and (
                    (val.startswith('"') and val.endswith('"')) or 
                    (val.startswith("'") and val.endswith("'"))
                ):
                    val = val[1:-1]
                
                # Remove inline comments if any
                if " #" in val:
                    val = val.split(" #", 1)[0].strip()
                    
                env_vars[key] = val
    except Exception as e:
        log_error(f"Error reading .env file: {e}")
        
    return env_vars

def get_venv_env_vars(venv_path: Path, allow_network=False, allow_fs=False, allow_env=False, no_sandbox=False) -> dict:
    """
    Prepares a simulated virtualenv environment dictionary with sandbox safety constraints applied.
    """
    config = load_global_config()
    sandbox_opt = config.get("sandboxOption", "A")
    strict = config.get("strictMode", False)
    
    # 1. Clean Environment base setup
    if not no_sandbox and (sandbox_opt == "A" or strict) and not allow_env:
        # Strip all sensitive variables. Keep only essential system paths.
        env = {}
        # Essential paths for OS to function
        essentials = [
            "PATH", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "PATHEXT", "WINDIR", 
            "USER", "LOGNAME", "LANG", "LC_ALL", "TERM", "PWD", "SHELL"
        ]
        for k in os.environ.keys():
            if k.upper() in essentials:
                env[k] = os.environ[k]
    else:
        # Balanced or explicitly allowed
        env = os.environ.copy()
        
    env["UV_NATIVE_TLS"] = "true"
    env["PYTHONIOENCODING"] = "utf-8"
    
    if venv_path.exists():
        bin_dir = str(get_venv_bin_dir(venv_path))
        
        # Prepend venv bin folder to PATH
        path_key = "PATH"
        for k in env.keys():
            if k.upper() == "PATH":
                path_key = k
                break
                
        existing_path = env.get(path_key, "")
        env[path_key] = f"{bin_dir}{os.pathsep}{existing_path}"
        env["VIRTUAL_ENV"] = str(venv_path)
        
        # Remove PYTHONHOME to avoid conflicts with global installation
        env.pop("PYTHONHOME", None)
        
    # Read and inject .env variables if env sandboxing is not strictly blocking it
    if no_sandbox or allow_env or sandbox_opt == "B":
        dotenv_path = venv_path.parent / ".env"
        if dotenv_path.is_file():
            dotenv_vars = load_dotenv(dotenv_path)
            env.update(dotenv_vars)
            
    # 2. File System Sandbox Isolation
    if not no_sandbox and not allow_fs:
        # Redirect user home directory to virtual sandbox home inside .venv
        sandbox_home = venv_path / ".sandbox_home"
        try:
            sandbox_home.mkdir(parents=True, exist_ok=True)
            # Create subdirs to mimic Windows AppData layout to prevent crash of tools
            (sandbox_home / "AppData" / "Roaming").mkdir(parents=True, exist_ok=True)
            (sandbox_home / "AppData" / "Local").mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
            
        env["HOME"] = str(sandbox_home)
        env["USERPROFILE"] = str(sandbox_home)
        env["HOMEPATH"] = str(sandbox_home)
        env["APPDATA"] = str(sandbox_home / "AppData" / "Roaming")
        env["LOCALAPPDATA"] = str(sandbox_home / "AppData" / "Local")

    # 3. Network Sandbox Isolation
    if not no_sandbox and not allow_network:
        # Inject blocked localhost proxy addresses.
        # Outward TCP/HTTP connections will respect these and fail safely.
        blocked_proxy = "http://127.0.0.1:99999"
        env["HTTP_PROXY"] = blocked_proxy
        env["HTTPS_PROXY"] = blocked_proxy
        env["ALL_PROXY"] = "socks5://127.0.0.1:99999"
        env["http_proxy"] = blocked_proxy
        env["https_proxy"] = blocked_proxy
        env["all_proxy"] = "socks5://127.0.0.1:99999"
        
    return env

def run_script(script_name: str, script_cmd: str, venv_path: Path, extra_args: list = None,
               allow_network=False, allow_fs=False, allow_env=False, no_sandbox=False, force_yes=False) -> int:
    """
    Executes a script command under virtualenv context, managing sandbox restrictions and approvals.
    """
    from pym.project import load_pyckage_json, find_pyckage_json
    
    pyckage_path = find_pyckage_json()
    data = load_pyckage_json(pyckage_path)
    
    project_name = data.get("name", "my-project")
    project_ver = data.get("version", "0.1.0")
    
    full_cmd = f"{script_cmd} {' '.join(extra_args)}" if extra_args else script_cmd
    
    # 1. Static Security Risk Assessment
    risk_info = analyze_script_risk(full_cmd)
    risk_level = risk_info["risk_level"]
    warnings = risk_info["warnings"]
    
    # Check if sandbox is active
    config = load_global_config()
    sandbox_opt = config.get("sandboxOption", "A")
    strict = config.get("strictMode", False)
    
    sandbox_active = not no_sandbox
    if sandbox_opt == "B" and not strict:
        # Under Option B, only sandbox if Medium/High risk or requested
        sandbox_active = (risk_level in ["MEDIUM", "HIGH"]) and not no_sandbox
        
    # Determine if we should prompt the user
    should_prompt = (risk_level in ["MEDIUM", "HIGH"] or sandbox_opt == "A") and not force_yes
    
    if should_prompt:
        # Print Gorgeous Security Card
        print(f"\n{Colors.RED}{Colors.BOLD}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}│            PyCk SECURITY GUARD: CONTROL DE RIESGO      │{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}├────────────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"  {Colors.BOLD}Script Name:{Colors.RESET}  {Colors.CYAN}{script_name}{Colors.RESET}")
        print(f"  {Colors.BOLD}Command:{Colors.RESET}      {Colors.GRAY}{full_cmd}{Colors.RESET}")
        
        # Risk level styling
        if risk_level == "HIGH":
            risk_str = f"{Colors.RED}{Colors.BOLD}ALTO ⚠{Colors.RESET}"
        elif risk_level == "MEDIUM":
            risk_str = f"{Colors.YELLOW}{Colors.BOLD}MEDIO ⚠{Colors.RESET}"
        else:
            risk_str = f"{Colors.GREEN}{Colors.BOLD}BAJO ✔{Colors.RESET}"
            
        print(f"  {Colors.BOLD}Risk Level:{Colors.RESET}   {risk_str}")
        print(f"{Colors.RED}{Colors.BOLD}├────────────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"  {Colors.BOLD}ANÁLISIS ESTÁTICO DE AMENAZAS:{Colors.RESET}")
        for w in warnings:
            print(f"   {Colors.YELLOW}• {w}{Colors.RESET}")
            
        print(f"{Colors.RED}{Colors.BOLD}├────────────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"  {Colors.BOLD}AISLAMIENTO DE PROCESO (SANDBOX):{Colors.RESET}")
        print(f"   [{'✔' if sandbox_active and not allow_network else ' '}] Bloqueo de Red Externa (Proxy nulo)")
        print(f"   [{'✔' if sandbox_active and not allow_fs else ' '}] Aislamiento de Directorio Home (Virtualizado)")
        print(f"   [{'✔' if sandbox_active and not allow_env else ' '}] Purgado de Variables de Entorno del Sistema")
        print(f"{Colors.RED}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}")
        
        confirm = ask_confirm("¿Confirmas la ejecución de este script bajo estas condiciones de seguridad?", default=False)
        if not confirm:
            log_error("Ejecución cancelada por el usuario por motivos de seguridad.")
            return 1
            
    else:
        # Sleek low-risk notice
        print(f"\n{Colors.GRAY}> {project_name}@{project_ver} {script_name}: {Colors.RESET}{Colors.BOLD}{Colors.CYAN}{full_cmd}{Colors.RESET}")
        if sandbox_active:
            log_info(f"{Colors.GRAY}Ejecutando en Sandbox Aislado (Seguro por Defecto).{Colors.RESET}")
            
    # 2. Get environment variables
    env_vars = get_venv_env_vars(
        venv_path, 
        allow_network=allow_network, 
        allow_fs=allow_fs, 
        allow_env=allow_env, 
        no_sandbox=not sandbox_active
    )
    
    try:
        # Run inside shell so user can execute complex chains: python main.py && echo Completed
        process = subprocess.run(
            full_cmd,
            shell=True,
            env=env_vars
        )
        return process.returncode
    except KeyboardInterrupt:
        print()
        log_warning("Script interrumpido por el usuario.")
        return 130
    except Exception as e:
        log_error(f"Fallo al ejecutar el script: {e}")
        return 1

def spawn_subshell(venv_path: Path):
    """
    Spawns an interactive terminal subshell pre-loaded with virtual environment paths.
    """
    env_vars = get_venv_env_vars(venv_path, allow_network=True, allow_fs=True, allow_env=True, no_sandbox=True)
    shell_exe = env_vars.get("COMSPEC", "cmd.exe") if os.name == "nt" else env_vars.get("SHELL", "/bin/sh")
    
    log_info(f"Spawning interactive subshell in virtual environment ({Colors.CYAN}{venv_path.name}{Colors.RESET}).")
    log_info(f"Type {Colors.BOLD}exit{Colors.RESET} to close the virtual environment shell.\n")
    
    try:
        subprocess.run(
            [shell_exe],
            env=env_vars
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_error(f"Failed to spawn interactive shell: {e}")
