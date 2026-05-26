import os
import json
import sys
from pathlib import Path
from pym.utils import ask_select, ask_text, ask_confirm, Colors, print_logo, log_success, log_info

CONFIG_DIR = Path.home() / ".pyck"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "quarantineHours": 72,
    "sandboxOption": "A",
    "strictMode": False,
    "defaultAuthor": "Developer",
    "defaultLicense": "MIT",
    "defaultEngine": "uv",
    "autoAudit": True
}

def load_global_config() -> dict:
    """
    Loads the global configuration JSON file from user home directory (~/.pyck/config.json).
    Returns DEFAULT_CONFIG if file is not found or corrupted.
    """
    if not CONFIG_FILE.is_file():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_global_config(config: dict):
    """
    Saves the configuration dictionary to ~/.pyck/config.json.
    Creates directories if needed.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        sys.stderr.write(f"{Colors.RED}✖ Failed to save global config: {e}{Colors.RESET}\n")

def ensure_global_setup() -> dict:
    """
    Verifies if the global configuration exists.
    If it is missing, triggers the interactive first-run Setup Wizard to configure PyCk preferences.
    """
    if CONFIG_FILE.is_file():
        return load_global_config()

    # Clear terminal if possible for a clean wizard experience
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    print_logo()
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 ¡Bienvenido a PyCk! Asistente de Configuración Inicial{Colors.RESET}")
    print(f"{Colors.GRAY}Detectamos que es tu primera vez ejecutando PyCk. Vamos a configurar tus preferencias.{Colors.RESET}\n")

    # Question 1: Sandbox Policy
    sandbox_opts = [
        "Opción A (Zero-Trust Absoluto): Sandbox estricto activo en TODOS los scripts por defecto.",
        "Opción B (Balanceado): Sandbox activo en instalaciones y scripts con riesgo detectado."
    ]
    selected_sandbox = ask_select("Elige la política de seguridad del Sandbox para tus scripts:", sandbox_opts, default_idx=0)
    sandbox_val = "A" if "Opción A" in selected_sandbox else "B"

    # Question 2: Quarantine Hours
    quarantine_hours_str = ask_text("Horas de cuarentena para nuevos paquetes en PyPI (por defecto 72 horas)", default="72")
    try:
        quarantine_hours = int(quarantine_hours_str)
    except ValueError:
        quarantine_hours = 72
        log_info("Valor no válido, usando 72 horas por defecto.")

    # Question 3: Default Author Name
    try:
        default_name = os.getlogin()
    except Exception:
        default_name = "Developer"
    author_val = ask_text("Nombre por defecto del desarrollador (autor)", default=default_name)

    # Question 4: Default License
    license_opts = ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]
    license_val = ask_select("Elige la licencia por defecto para tus proyectos:", license_opts, default_idx=0)

    # Question 5: Preferred packaging engine
    engine_opts = [
        "uv (Rust speed) ⚡ - Máxima velocidad",
        "pip (Python standard) - Fallback nativo"
    ]
    selected_engine = ask_select("Elige tu motor de empaquetado favorito:", engine_opts, default_idx=0)
    engine_val = "uv" if "uv" in selected_engine else "pip"

    # Question 6: Auto Audit
    auto_audit_val = ask_confirm("¿Activar Piloto Automático de Auditorías (pym audit automático tras instalar)?", default=True)

    # Build config dict
    config = {
        "quarantineHours": quarantine_hours,
        "sandboxOption": sandbox_val,
        "strictMode": True if sandbox_val == "A" else False,
        "defaultAuthor": author_val,
        "defaultLicense": license_val,
        "defaultEngine": engine_val,
        "autoAudit": auto_audit_val
    }

    # Save to file
    save_global_config(config)
    print()
    log_success("¡Configuración global inicial guardada con éxito!")
    log_info(f"Guardado en: {CONFIG_FILE}")
    print(f"\n{Colors.GREEN}{Colors.BOLD}✔ PyCk inicializado con éxito. Continuando con la ejecución...{Colors.RESET}\n")
    print(f"{Colors.GRAY}{'─'*60}{Colors.RESET}\n")
    
    return config
