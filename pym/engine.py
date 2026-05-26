import os
import sys
import shutil
import subprocess
from pathlib import Path
from pym.utils import Spinner, log_info, log_success, log_warning, log_error, Colors
from pym.venv import get_venv_python, get_venv_pip

# Global injection of Native TLS to trust Windows registry system certificates (essential for corporate proxies)
os.environ["UV_NATIVE_TLS"] = "true"

def get_uv_cmd() -> list:
    """
    Detect if 'uv' is available.
    1. Check system path for 'uv'
    2. Check if python can run 'uv' as a module: python -m uv
    Returns the command list prefix if found, or None.
    """
    # 1. Check system PATH
    uv_path = shutil.which("uv")
    if uv_path:
        return [uv_path]
        
    # 2. Check python -m uv
    try:
        res = subprocess.run(
            [sys.executable, "-m", "uv", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            return [sys.executable, "-m", "uv"]
    except Exception:
        pass
        
    return None

def bootstrap_uv() -> list:
    """
    Attempts to bootstrap 'uv' by installing it.
    Shows a beautiful loading spinner and returns the command list.
    """
    spinner = Spinner("PyCk: Self-bootstrapping high-performance 'uv' engine (Rust speed)...")
    spinner.start()
    
    try:
        # Install uv into user site-packages
        cmd = [sys.executable, "-m", "pip", "install", "uv", "--user"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if res.returncode == 0:
            uv_cmd = get_uv_cmd()
            if uv_cmd:
                spinner.stop(success=True, finish_message="Successfully bootstrapped the Rust 'uv' engine!")
                return uv_cmd
                
        spinner.stop(success=False, finish_message="Could not install 'uv'. Falling back to native pip/venv.")
    except Exception as e:
        spinner.stop(success=False, finish_message=f"Failed to bootstrap 'uv': {e}. Using native pip.")
        
    return None

def get_or_bootstrap_uv(silent=False) -> list:
    """
    Finds uv, and if not present, installs it.
    Respects user preference for 'defaultEngine' in global configuration.
    """
    from pym.config import load_global_config
    config = load_global_config()
    if config.get("defaultEngine", "uv") == "pip":
        return None
        
    uv_cmd = get_uv_cmd()
    if uv_cmd:
        return uv_cmd
    if not silent:
        log_info("Rust-powered 'uv' engine not detected. Let's bootstrap it for maximum speed! ⚡")
    return bootstrap_uv()

def caret_to_pep440(pkg: str, ver: str) -> str:
    """
    Converts a caret version specifier (e.g., ^3.0.0 or ^0.3.0) to a PEP 440
    compliant specifier (e.g., >=3.0.0,<4.0.0 or >=0.3.0,<0.4.0).
    """
    if not ver:
        return pkg
    if ver.startswith("^"):
        version_str = ver[1:]
        parts = version_str.split(".")
        if not parts or not parts[0].isdigit():
            return f"{pkg}>={version_str}"
        
        major = int(parts[0])
        if major > 0:
            next_major = major + 1
            return f"{pkg}>={version_str},<{next_major}.0.0"
        else:
            minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            if minor > 0:
                next_minor = minor + 1
                return f"{pkg}>={version_str},<0.{next_minor}.0"
            else:
                patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                next_patch = patch + 1
                return f"{pkg}==0.0.{next_patch}"
    return f"{pkg}{ver}"

def sanitize_version_specifiers(packages: list) -> list:
    """
    Sanitize incoming package arguments to convert any caret version ranges to standard Python PEP 440 constraints.
    """
    sanitized = []
    for pkg_spec in packages:
        if "^" in pkg_spec:
            parts = pkg_spec.split("^", 1)
            pkg_name = parts[0]
            ver_val = "^" + parts[1]
            sanitized.append(caret_to_pep440(pkg_name, ver_val))
        else:
            sanitized.append(pkg_spec)
    return sanitized

def parse_and_print_installation_summary(stdout: str, stderr: str, packages_requested: list = None):
    installed = []
    uninstalled = []
    skipped = []
    
    # Merge process outputs
    full_output = (stdout or "") + "\n" + (stderr or "")
    
    # Normalize names of packages_requested for exact tracking
    req_names = []
    if packages_requested:
        for p in packages_requested:
            name = p.split("=")[0].split(">")[0].split("<")[0].split("^")[0].split("~")[0].strip().lower()
            req_names.append(name)
            
    for line in full_output.splitlines():
        line_strip = line.strip()
        
        # 1. Modern UV stdout/stderr parsing (+ package==version / - package==version)
        if line_strip.startswith("+ "):
            pkg_name = line_strip[2:].strip()
            if pkg_name not in installed:
                installed.append(pkg_name)
        elif line_strip.startswith("- "):
            pkg_name = line_strip[2:].strip()
            if pkg_name not in uninstalled:
                uninstalled.append(pkg_name)
                
        # 2. Legacy UV style parsing (Resolved/Installed colon formats)
        elif "Installed" in line_strip and ":" in line_strip:
            parts = line_strip.split(":", 1)
            pkgs = parts[1].split(",")
            for p in pkgs:
                p_clean = p.strip().split(" (")[0].strip()
                if p_clean and p_clean not in installed:
                    installed.append(p_clean)
        elif "Uninstalled" in line_strip and ":" in line_strip:
            parts = line_strip.split(":", 1)
            pkgs = parts[1].split(",")
            for p in pkgs:
                p_clean = p.strip()
                if p_clean and p_clean not in uninstalled:
                    uninstalled.append(p_clean)
                    
    # 3. Standard pip styles (fallback) if uv parsing yielded nothing
    if not installed and not uninstalled:
        for line in full_output.splitlines():
            line_strip = line.strip()
            if "Successfully installed" in line_strip:
                parts = line_strip.replace("Successfully installed", "").strip().split()
                installed.extend(parts)
            elif "Successfully uninstalled" in line_strip:
                parts = line_strip.replace("Successfully uninstalled", "").strip().split()
                uninstalled.extend(parts)
            elif "Requirement already satisfied:" in line_strip:
                part = line_strip.replace("Requirement already satisfied:", "").strip().split(" in ")[0].split("(")[0].strip()
                if part and part not in skipped:
                    skipped.append(part)
                    
    # Process upgrades (packages that appear in both installed and uninstalled)
    upgrades = {}
    cleaned_installed = []
    cleaned_uninstalled = []
    
    # Index uninstalled by package name for easy mapping
    uninstalled_dict = {}
    for u in uninstalled:
        parts = u.split("==")
        u_name = parts[0].strip().lower()
        u_ver = parts[1].strip() if len(parts) > 1 else ""
        uninstalled_dict[u_name] = (u, u_ver)
        
    for inst in installed:
        parts = inst.split("==")
        inst_name = parts[0].strip().lower()
        inst_ver = parts[1].strip() if len(parts) > 1 else ""
        
        if inst_name in uninstalled_dict:
            orig_str, old_ver = uninstalled_dict[inst_name]
            upgrades[inst_name] = {
                "name": parts[0].strip(),
                "old": old_ver,
                "new": inst_ver
            }
            # Remove from uninstalled dict so we don't treat it as a pure uninstall
            uninstalled_dict.pop(inst_name)
        else:
            cleaned_installed.append(inst)
            
    # Remaining uninstalls are pure uninstalls
    cleaned_uninstalled = [v[0] for v in uninstalled_dict.values()]
    
    # If nothing was parsed but packages were requested, treat them as skipped/already satisfied
    if not installed and not uninstalled and not skipped and packages_requested:
        skipped = [p for p in packages_requested]
        
    # Print the premium visual dashboard!
    print()
    if upgrades:
        print(f" {Colors.GREEN}✔{Colors.RESET} {Colors.BOLD}Upgraded Dependencies:{Colors.RESET}")
        for upg in upgrades.values():
            old_str = f"v{upg['old']} " if upg['old'] else ""
            print(f"   {Colors.GREEN}↑ {upg['name']}{Colors.RESET} ({old_str}→ {Colors.BOLD}v{upg['new']}{Colors.RESET})")
            
    if cleaned_installed:
        print(f" {Colors.GREEN}✔{Colors.RESET} {Colors.BOLD}Newly Installed / Added:{Colors.RESET}")
        for pkg in cleaned_installed:
            print(f"   {Colors.GREEN}+ {pkg}{Colors.RESET}")
            
    if cleaned_uninstalled:
        print(f" {Colors.RED}✖{Colors.RESET} {Colors.BOLD}Removed / Uninstalled:{Colors.RESET}")
        for pkg in cleaned_uninstalled:
            print(f"   {Colors.RED}- {pkg}{Colors.RESET}")
            
    if skipped and not upgrades and not cleaned_installed and not cleaned_uninstalled:
        # Filter skipped list
        clean_skipped = []
        for s in skipped:
            s_clean = s.split("==")[0].split(">=")[0].split("<=")[0].split("-")[0].strip()
            if s_clean.lower() not in clean_skipped:
                clean_skipped.append(s_clean.lower())
                
        # Filter to requested names if provided
        display_skipped = []
        for s in clean_skipped:
            if req_names:
                if s in req_names:
                    display_skipped.append(s)
            else:
                display_skipped.append(s)
                
        if display_skipped:
            print(f" {Colors.BLUE}ℹ{Colors.RESET} {Colors.BOLD}Already Satisfied (Skipped):{Colors.RESET}")
            for pkg in display_skipped[:5]:
                orig_name = pkg
                if packages_requested:
                    for pr in packages_requested:
                        if pr.lower().startswith(pkg):
                            orig_name = pr
                            break
                print(f"   {Colors.GRAY}• {orig_name} (already matching version){Colors.RESET}")
            if len(display_skipped) > 5:
                print(f"   {Colors.GRAY}• ... and {len(display_skipped) - 5} other sub-dependencies.{Colors.RESET}")
    print()

def install_packages(packages: list, venv_path: Path, dev=False, global_install=False, force_latest=False) -> bool:
    """
    Installs packages into `.venv` or globally.
    Verifies quarantine constraints (72 hours default) unless force_latest=True.
    Updates dependencies list in calling modules.
    """
    if not packages and not global_install:
        return False
        
    import re
    from pym.config import load_global_config
    from pym.security import get_quarantine_info, find_latest_safe_version
    from pym.utils import ask_confirm
    
    config = load_global_config()
    quarantine_hours = config.get("quarantineHours", 72)
        
    # Translate and clean caret versions to standard PEP 440 constraints
    packages = sanitize_version_specifiers(packages)
    
    resolved_packages = []
    
    if not global_install:
        for pkg in packages:
            # Check for version specifiers
            parts = re.split(r"(==|>=|<=|>|<|\^)", pkg)
            pkg_name = parts[0].strip()
            
            if len(parts) >= 3 and parts[1] == "==":
                version = parts[2].strip()
                if not force_latest:
                    q_info = get_quarantine_info(pkg_name, version, quarantine_hours)
                    if q_info.get("is_quarantined"):
                        print(f"\n{Colors.YELLOW}⚠ ADVERTENCIA DE SEGURIDAD (CUARENTENA):{Colors.RESET}")
                        print(f"  El paquete {Colors.BOLD}{pkg_name}=={version}{Colors.RESET} fue publicado hace solo {q_info['hours_old']:.1f} horas.")
                        print(f"  El límite de cuarentena configurado es de {quarantine_hours} horas.")
                        confirm = ask_confirm("¿Estás seguro de que deseas forzar la instalación de esta versión potencialmente insegura?", default=False)
                        if not confirm:
                            log_error(f"Instalación cancelada por seguridad: {pkg_name}=={version} está en cuarentena.")
                            return False
                resolved_packages.append(pkg)
            elif len(parts) == 1:
                # No version specified, fetch the latest safe version
                if not force_latest:
                    safe_ver = find_latest_safe_version(pkg_name, quarantine_hours)
                    if safe_ver:
                        log_info(f"Fijando {Colors.BOLD}{pkg_name}=={safe_ver}{Colors.RESET} (Última versión segura >{quarantine_hours}h de antigüedad).")
                        resolved_packages.append(f"{pkg_name}=={safe_ver}")
                    else:
                        resolved_packages.append(pkg)
                else:
                    resolved_packages.append(pkg)
            else:
                resolved_packages.append(pkg)
    else:
        resolved_packages = packages
        
    if global_install:
        spinner = Spinner(f"Installing {', '.join(resolved_packages)} globally...")
        spinner.start()
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + resolved_packages
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                spinner.stop(success=True, finish_message=f"Installed {len(resolved_packages)} packages globally.")
                return True
            spinner.stop(success=False, finish_message=f"Failed to install packages globally: {res.stderr.strip()}")
            return False
        except Exception as e:
            spinner.stop(success=False, finish_message=f"Global install error: {e}")
            return False

    # Venv install
    python_exe = get_venv_python(venv_path)
    pip_exe = get_venv_pip(venv_path)
    
    uv_cmd = get_or_bootstrap_uv()
    
    spinner = Spinner(f"Installing {', '.join(resolved_packages)} in environment...")
    spinner.start()
    
    try:
        if uv_cmd:
            # High-performance uv installation
            cmd = uv_cmd + ["pip", "install", "--python", str(python_exe)] + resolved_packages
        else:
            # Fallback to standard pip
            cmd = [str(pip_exe), "install"] + resolved_packages
            
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if res.returncode == 0:
            spinner.stop(success=True, finish_message="Dependency installation completed successfully.")
            parse_and_print_installation_summary(res.stdout, res.stderr, resolved_packages)
            return True
            
        spinner.stop(success=False, finish_message=f"Installation failed:\n{res.stderr.strip()}")
        return False
    except Exception as e:
        spinner.stop(success=False, finish_message=f"Installation error: {e}")
        return False

def uninstall_packages(packages: list, venv_path: Path) -> bool:
    """
    Uninstalls packages from virtualenv.
    """
    if not packages:
        return False
        
    python_exe = get_venv_python(venv_path)
    pip_exe = get_venv_pip(venv_path)
    
    uv_cmd = get_or_bootstrap_uv()
    
    spinner = Spinner(f"Removing {', '.join(packages)} from environment...")
    spinner.start()
    
    try:
        if uv_cmd:
            cmd = uv_cmd + ["pip", "uninstall", "--python", str(python_exe)] + packages
        else:
            cmd = [str(pip_exe), "uninstall", "-y"] + packages
            
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            spinner.stop(success=True, finish_message="Package removal completed successfully.")
            parse_and_print_installation_summary(res.stdout, res.stderr, packages)
            return True
            
        spinner.stop(success=False, finish_message=f"Failed to remove packages: {res.stderr.strip()}")
        return False
    except Exception as e:
        spinner.stop(success=False, finish_message=f"Removal error: {e}")
        return False

def sync_dependencies(dependencies: dict, dev_dependencies: dict, venv_path: Path, force_latest=False) -> bool:
    """
    Syncs the virtual environment to match the packages in pyckage.json (like npm install).
    """
    # Collect all packages to install
    all_packages = []
    
    import re
    from pym.config import load_global_config
    from pym.security import get_quarantine_info, find_latest_safe_version
    from pym.utils import ask_confirm
    
    config = load_global_config()
    quarantine_hours = config.get("quarantineHours", 72)
    
    # Process standard dependencies
    for pkg, ver in dependencies.items():
        if ver and ver != "*":
            spec = caret_to_pep440(pkg, ver)
        else:
            spec = pkg
            
        parts = re.split(r"(==|>=|<=|>|<|\^)", spec)
        pkg_name = parts[0].strip()
        
        if len(parts) >= 3 and parts[1] == "==":
            version = parts[2].strip()
            if not force_latest:
                q_info = get_quarantine_info(pkg_name, version, quarantine_hours)
                if q_info.get("is_quarantined"):
                    print(f"\n{Colors.YELLOW}⚠ ADVERTENCIA DE SEGURIDAD (SINCRO-CUARENTENA):{Colors.RESET}")
                    print(f"  La dependencia {Colors.BOLD}{pkg_name}=={version}{Colors.RESET} está en cuarentena (publicada hace {q_info['hours_old']:.1f}h).")
                    confirm = ask_confirm("¿Deseas forzar su instalación durante la sincronización?", default=False)
                    if not confirm:
                        log_error(f"Sincronización cancelada por seguridad.")
                        return False
            all_packages.append(spec)
        elif len(parts) == 1:
            if not force_latest:
                safe_ver = find_latest_safe_version(pkg_name, quarantine_hours)
                if safe_ver:
                    all_packages.append(f"{pkg_name}=={safe_ver}")
                else:
                    all_packages.append(pkg)
            else:
                all_packages.append(pkg)
        else:
            all_packages.append(spec)
            
    # Process dev dependencies
    for pkg, ver in dev_dependencies.items():
        if ver and ver != "*":
            spec = caret_to_pep440(pkg, ver)
        else:
            spec = pkg
            
        parts = re.split(r"(==|>=|<=|>|<|\^)", spec)
        pkg_name = parts[0].strip()
        
        if len(parts) >= 3 and parts[1] == "==":
            version = parts[2].strip()
            if not force_latest:
                q_info = get_quarantine_info(pkg_name, version, quarantine_hours)
                if q_info.get("is_quarantined"):
                    print(f"\n{Colors.YELLOW}⚠ ADVERTENCIA DE SEGURIDAD (SINCRO-CUARENTENA-DEV):{Colors.RESET}")
                    print(f"  La dependencia dev {Colors.BOLD}{pkg_name}=={version}{Colors.RESET} está en cuarentena (publicada hace {q_info['hours_old']:.1f}h).")
                    confirm = ask_confirm("¿Deseas forzar su instalación durante la sincronización?", default=False)
                    if not confirm:
                        log_error(f"Sincronización cancelada por seguridad.")
                        return False
            all_packages.append(spec)
        elif len(parts) == 1:
            if not force_latest:
                safe_ver = find_latest_safe_version(pkg_name, quarantine_hours)
                if safe_ver:
                    all_packages.append(f"{pkg_name}=={safe_ver}")
                else:
                    all_packages.append(pkg)
            else:
                all_packages.append(pkg)
        else:
            all_packages.append(spec)
        
    if not all_packages:
        log_success("No dependencies found to install. Environment is clean!")
        return True
        
    python_exe = get_venv_python(venv_path)
    pip_exe = get_venv_pip(venv_path)
    
    uv_cmd = get_or_bootstrap_uv()
    
    spinner = Spinner(f"Syncing environment ({len(all_packages)} packages)...")
    spinner.start()
    
    try:
        if uv_cmd:
            cmd = uv_cmd + ["pip", "install", "--python", str(python_exe)] + all_packages
        else:
            cmd = [str(pip_exe), "install"] + all_packages
            
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if res.returncode == 0:
            spinner.stop(success=True, finish_message="Environment synchronization completed successfully.")
            parse_and_print_installation_summary(res.stdout, res.stderr, all_packages)
            return True
            
        spinner.stop(success=False, finish_message=f"Sync failed:\n{res.stderr.strip()}")
        return False
    except Exception as e:
        spinner.stop(success=False, finish_message=f"Sync error: {e}")
        return False
