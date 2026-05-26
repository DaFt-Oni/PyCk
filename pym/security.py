import os
import re
import sys
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from pym.utils import Colors, Spinner, log_info, log_warning, log_error

PYPI_URL_PATTERN = "https://pypi.org/pypi/{package}/json"
PYPI_VER_URL_PATTERN = "https://pypi.org/pypi/{package}/{version}/json"

def fetch_pypi_metadata(package_name: str, version: str = None) -> dict:
    """
    Fetches package metadata from PyPI JSON API.
    Handles network errors, offline states, and timeouts gracefully.
    """
    clean_name = package_name.strip().lower()
    if version:
        url = PYPI_VER_URL_PATTERN.format(package=clean_name, version=version)
    else:
        url = PYPI_URL_PATTERN.format(package=clean_name)

    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "PyCk-PackageManager/1.0.0"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        # Graceful network fallback
        pass
    return None

def parse_pypi_date(date_str: str) -> datetime:
    """
    Parses date strings returned by PyPI releases (e.g. 2024-03-20T12:00:00Z).
    Returns timezone-aware datetime in UTC.
    """
    clean_str = date_str.replace("Z", "+00:00")
    # Truncate fractional seconds if present
    if "." in clean_str:
        base, tz = clean_str.split("+") if "+" in clean_str else (clean_str, "00:00")
        base = base.split(".")[0]
        clean_str = f"{base}+{tz}"
    return datetime.fromisoformat(clean_str)

def get_quarantine_info(package_name: str, version: str, quarantine_hours: int) -> dict:
    """
    Validates if a specific package version is in the quarantine period.
    Returns a dict with: is_quarantined, upload_time, hours_old, latest_safe_ver.
    """
    metadata = fetch_pypi_metadata(package_name)
    if not metadata:
        # Offline or not found, assume not quarantined to allow offline installations, but warn
        return {"is_quarantined": False, "upload_time": None, "hours_old": 9999, "offline": True}

    releases = metadata.get("releases", {})
    if version not in releases or not releases[version]:
        return {"is_quarantined": False, "upload_time": None, "hours_old": 9999, "offline": False}

    # Find the upload time of this version
    files = releases[version]
    upload_time_str = None
    for f in files:
        if "upload_time_iso_8601" in f:
            upload_time_str = f["upload_time_iso_8601"]
            break
        elif "upload_time" in f:
            upload_time_str = f["upload_time"]
            break

    if not upload_time_str:
        return {"is_quarantined": False, "upload_time": None, "hours_old": 9999, "offline": False}

    upload_dt = parse_pypi_date(upload_time_str)
    now = datetime.now(timezone.utc)
    age_seconds = (now - upload_dt).total_seconds()
    hours_old = age_seconds / 3600.0

    is_quarantined = hours_old < quarantine_hours

    return {
        "is_quarantined": is_quarantined,
        "upload_time": upload_time_str,
        "hours_old": hours_old,
        "offline": False
    }

def find_latest_safe_version(package_name: str, quarantine_hours: int) -> str:
    """
    Searches PyPI for the newest stable release that is older than quarantine_hours.
    Returns the version string, or None if none fit the criteria.
    """
    metadata = fetch_pypi_metadata(package_name)
    if not metadata:
        return None

    releases = metadata.get("releases", {})
    if not releases:
        return None

    # Map versions to their oldest file upload time
    version_ages = []
    for ver, files in releases.items():
        if not files:
            continue
        # Skip pre-releases (alpha, beta, rc, dev, post) unless there are no other versions
        if any(x in ver.lower() for x in ["a", "b", "rc", "dev", "post"]):
            continue

        upload_time_str = None
        for f in files:
            if "upload_time_iso_8601" in f:
                upload_time_str = f["upload_time_iso_8601"]
                break
        
        if upload_time_str:
            try:
                dt = parse_pypi_date(upload_time_str)
                version_ages.append((ver, dt))
            except Exception:
                pass

    if not version_ages:
        # Fallback to absolute latest if no clean versions parsed
        return metadata.get("info", {}).get("version")

    # Sort versions by upload time descending (newest first)
    version_ages.sort(key=lambda x: x[1], reverse=True)
    now = datetime.now(timezone.utc)

    for ver, dt in version_ages:
        hours_old = (now - dt).total_seconds() / 3600.0
        if hours_old >= quarantine_hours:
            return ver

    # If all versions are in quarantine, return the oldest one found
    return version_ages[-1][0] if version_ages else None

def analyze_script_risk(command: str) -> dict:
    """
    Statically analyzes a script command string for security risks.
    Returns a dictionary indicating the risk level and warning explanations.
    """
    cmd_lower = command.lower()
    warnings = []
    risk_level = "LOW"

    # 1. High Risk Indicators (Execution of dangerous system commands, shells, and network tools)
    high_keywords = [
        "curl", "wget", "powershell", "cmd.exe", "bash", "sh ", "zsh", "netcat", "nc ", 
        "rm -rf", "del /s", "rmdir /s", "format ", "mkfs", "chmod +x", "chown"
    ]
    for kw in high_keywords:
        if kw in cmd_lower:
            risk_level = "HIGH"
            warnings.append(f"Uso detectado de herramienta del sistema o comando destructivo: '{kw}'")

    # Redirection and piping to executables
    if "|" in cmd_lower and any(sh in cmd_lower for sh in ["python", "bash", "sh", "cmd", "powershell"]):
        risk_level = "HIGH"
        warnings.append("Llamada por tubería (pipe) detectada hacia un intérprete ejecutable.")

    # Execution of uncompiled binary payloads or unknown binary downloads
    if any(ext in cmd_lower for ext in [".exe", ".sh", ".bin", ".bat", ".ps1"]):
        risk_level = "HIGH"
        warnings.append("Ejecución directa de scripts de terminal compilados o binarios (.exe, .sh, .bat).")

    # File system climbing checks (escaping project workspace directory)
    if ".." in cmd_lower:
        risk_level = "HIGH"
        warnings.append("Intento de salida de directorio mediante salto de ruta ('..').")
    
    if os.name == "nt":
        # Absolute path references in Windows
        if re.search(r"[a-zA-Z]:\\(?!.*?\.venv)", cmd_lower):
            risk_level = "HIGH"
            warnings.append("Referencia absoluta al sistema de archivos de Windows (fuera del workspace).")
    else:
        # Absolute path references in Unix
        if re.search(r"/(etc|var|usr|bin|home|opt)(/|$)", cmd_lower):
            risk_level = "HIGH"
            warnings.append("Referencia absoluta a directorios sensibles del sistema Unix (/etc, /usr, /var).")

    # 2. Medium Risk Indicators (Environment injection and minor shell chains)
    if risk_level != "HIGH":
        medium_keywords = ["export ", "set ", "env ", "&&", ";", ">>", ">"]
        for kw in medium_keywords:
            if kw in cmd_lower:
                risk_level = "MEDIUM"
                warnings.append(f"Modificación del entorno u operación encadenada de comandos: '{kw}'")

    if not warnings:
        warnings.append("El comando ejecuta scripts de python locales estándar o llamadas básicas.")

    return {
        "risk_level": risk_level,
        "warnings": warnings
    }

def scan_project_imports() -> set:
    """
    Recursively scans the current directory for all python files (.py) and extracts
    all imported package names using regex (ignoring standard library or local modules).
    """
    imported_modules = set()
    cwd = Path(".").resolve()
    
    # Simple list of common stdlib modules to filter them out
    stdlib = {
        "os", "sys", "time", "json", "urllib", "subprocess", "shutil", "pathlib", "datetime",
        "math", "random", "re", "collections", "itertools", "functools", "hashlib", "io",
        "threading", "csv", "argparse", "logging", "socket", "struct", "tempfile", "uuid"
    }

    # Python module import regex
    import_re = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)")

    for root, dirs, files in os.walk(cwd):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in [".venv", "build", "dist", "pyck.egg-info", "tests", "__pycache__"]]
        
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            match = import_re.match(line)
                            if match:
                                mod = match.group(1).split(".")[0].strip().lower()
                                if mod and mod not in stdlib:
                                    imported_modules.add(mod)
                except Exception:
                    pass
    return imported_modules

def run_security_audit(dependencies: dict, dev_dependencies: dict, locked_packages: dict) -> dict:
    """
    Audits the project state:
    1. Scan imports to detect unused dependencies (orphaned dependencies).
    2. Query PyPI JSON API to identify vulnerabilities inside packages.
    3. Check for abandoned packages (no releases in 2 years).
    4. Detect duplicates.
    """
    audit_results = {
        "orphaned": [],
        "vulnerabilities": [],
        "abandoned": [],
        "duplicates": []
    }

    # 1. Orphaned package check
    log_info("Escaneando código fuente en busca de paquetes no utilizados...")
    used_imports = scan_project_imports()
    
    # Map typical package name differences (e.g. PyYAML -> yaml, fastapi -> fastapi)
    # This maps package installations to their importable names
    import_mappings = {
        "pyyaml": "yaml",
        "pydantic-settings": "pydantic_settings",
        "python-dotenv": "dotenv",
        "pyjwt": "jwt",
        "scikit-learn": "sklearn",
        "pillow": "pil",
        "beautifulsoup4": "bs4",
        "pypdf2": "pypdf"
    }

    for dep_name in dependencies.keys():
        norm_name = dep_name.lower().replace("-", "_")
        mapped_name = import_mappings.get(norm_name, norm_name)
        
        if mapped_name not in used_imports and norm_name not in used_imports:
            audit_results["orphaned"].append(dep_name)

    # 2. Vulnerability & Abandoned Check
    if locked_packages:
        log_info(f"Consultando base de datos PyPI para {len(locked_packages)} paquetes instalados...")
        
        spinner = Spinner("Analizando vulnerabilidades y mantenimiento de paquetes...")
        spinner.start()
        
        now = datetime.now(timezone.utc)
        
        for pkg_name, pkg_info in locked_packages.items():
            version = pkg_info.get("version")
            metadata = fetch_pypi_metadata(pkg_name, version)
            
            if not metadata:
                continue
                
            # A. Vulnerabilities (PyPI JSON standardized field)
            vulns = metadata.get("vulnerabilities", [])
            if vulns:
                for v in vulns:
                    audit_results["vulnerabilities"].append({
                        "package": pkg_name,
                        "version": version,
                        "id": v.get("id", "N/A"),
                        "details": v.get("details", "Sin detalles adicionales."),
                        "link": v.get("link", "https://osv.dev/")
                    })
            
            # B. Abandoned/Maintenance Check
            # Check latest release date
            releases = metadata.get("releases", {})
            latest_version = metadata.get("info", {}).get("version")
            if latest_version and latest_version in releases and releases[latest_version]:
                files = releases[latest_version]
                upload_time_str = None
                for f in files:
                    if "upload_time_iso_8601" in f:
                        upload_time_str = f["upload_time_iso_8601"]
                        break
                
                if upload_time_str:
                    try:
                        dt = parse_pypi_date(upload_time_str)
                        days_since_release = (now - dt).days
                        if days_since_release > 730:  # 2 years
                            audit_results["abandoned"].append({
                                "package": pkg_name,
                                "version": version,
                                "days": days_since_release,
                                "latest_version": latest_version
                            })
                    except Exception:
                        pass
        
        spinner.stop(success=True, finish_message="Análisis de vulnerabilidades completado.")
    else:
        log_warning("No se detectó un archivo pyckage.lock activo. Ejecuta 'pym install' primero para habilitar escaneos de vulnerabilidades.")

    return audit_results
