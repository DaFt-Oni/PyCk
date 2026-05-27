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

def ensure_global_setup(force_wizard=False) -> dict:
    """
    Verifies if the global configuration exists.
    If it is missing or force_wizard is True, triggers the interactive Setup Wizard to configure PyCk preferences.
    """
    if CONFIG_FILE.is_file() and not force_wizard:
        return load_global_config()

    # Clear terminal if possible for a clean wizard experience
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    # Load existing config for defaults if present
    existing_config = {}
    is_reconfigured = CONFIG_FILE.is_file()
    if is_reconfigured:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except Exception:
            pass

    print_logo()
    if is_reconfigured:
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 ¡Bienvenido de nuevo a PyCk! Asistente de Reconfiguración{Colors.RESET}")
        print(f"{Colors.GRAY}Presiona Enter en cada pregunta para mantener tu configuración actual.{Colors.RESET}\n")
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 ¡Bienvenido a PyCk! Asistente de Configuración Inicial{Colors.RESET}")
        print(f"{Colors.GRAY}Detectamos que es tu primera vez ejecutando PyCk. Vamos a configurar tus preferencias.{Colors.RESET}\n")

    # Question 1: Physical Installation Directory (Only if frozen to avoid Downloads folder pollution)
    default_install_dir = existing_config.get("installDir")
    if not default_install_dir:
        default_install_dir = str(Path.home() / ".pyck" / "bin")
    
    is_frozen = getattr(sys, 'frozen', False)
    install_dir = Path(default_install_dir).resolve()
    
    if is_frozen:
        print(f"📁 {Colors.BOLD}Selecciona el directorio para instalar el ejecutable de PyCk (pym.exe):{Colors.RESET}")
        print(f"   {Colors.GRAY}(Presiona Enter para mantener por defecto: {install_dir}){Colors.RESET}")
        user_install_dir = ask_text("Ruta del directorio de instalación", default=str(install_dir))
        install_dir = Path(user_install_dir).resolve()
        print()

    # Question 2: Sandbox Policy
    sandbox_opts = [
        "Opción A (Zero-Trust Absoluto): Sandbox estricto activo en TODOS los scripts por defecto.",
        "Opción B (Balanceado): Sandbox activo en instalaciones y scripts con riesgo detectado."
    ]
    curr_sandbox = existing_config.get("sandboxOption", "A")
    default_sandbox_idx = 0 if curr_sandbox == "A" else 1
    selected_sandbox = ask_select("Elige la política de seguridad del Sandbox para tus scripts:", sandbox_opts, default_idx=default_sandbox_idx)
    sandbox_val = "A" if "Opción A" in selected_sandbox else "B"

    # Question 3: Quarantine Hours
    curr_quarantine = str(existing_config.get("quarantineHours", "72"))
    quarantine_hours_str = ask_text("Horas de cuarentena para nuevos paquetes en PyPI", default=curr_quarantine)
    try:
        quarantine_hours = int(quarantine_hours_str)
    except ValueError:
        quarantine_hours = 72
        log_info("Valor no válido, usando 72 horas por defecto.")

    # Question 4: Default Author Name
    if "defaultAuthor" in existing_config:
        default_name = existing_config["defaultAuthor"]
    else:
        try:
            default_name = os.getlogin()
        except Exception:
            default_name = "Developer"
    author_val = ask_text("Nombre por defecto del desarrollador (autor)", default=default_name)

    # Question 5: Default License
    license_opts = ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]
    curr_license = existing_config.get("defaultLicense", "MIT")
    try:
        default_license_idx = license_opts.index(curr_license)
    except ValueError:
        default_license_idx = 0
    license_val = ask_select("Elige la licencia por defecto para tus proyectos:", license_opts, default_idx=default_license_idx)

    # Question 6: Preferred packaging engine
    engine_opts = [
        "uv (Rust speed) ⚡ - Máxima velocidad",
        "pip (Python standard) - Fallback nativo"
    ]
    curr_engine = existing_config.get("defaultEngine", "uv")
    default_engine_idx = 0 if curr_engine == "uv" else 1
    selected_engine = ask_select("Elige tu motor de empaquetado favorito:", engine_opts, default_idx=default_engine_idx)
    engine_val = "uv" if "uv" in selected_engine else "pip"

    # Question 7: Auto Audit
    curr_audit = existing_config.get("autoAudit", True)
    auto_audit_val = ask_confirm("¿Activar Piloto Automático de Auditorías (pym audit automático tras instalar)?", default=curr_audit)

    # Build config dict
    config = {
        "quarantineHours": quarantine_hours,
        "sandboxOption": sandbox_val,
        "strictMode": True if sandbox_val == "A" else False,
        "defaultAuthor": author_val,
        "defaultLicense": license_val,
        "defaultEngine": engine_val,
        "autoAudit": auto_audit_val,
        "installDir": str(install_dir)
    }

    # Save to file
    save_global_config(config)
    print()
    log_success("¡Configuración global inicial guardada con éxito!")
    log_info(f"Guardado en: {CONFIG_FILE}")

    # Perform physical self-copying install if frozen
    copied_successfully = False
    if is_frozen:
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
            target_exe_path = install_dir / Path(sys.executable).name
            
            # Prevent copying onto itself
            if Path(sys.executable).resolve() != target_exe_path.resolve():
                import shutil
                shutil.copy2(sys.executable, target_exe_path)
                log_success(f"¡Ejecutable 'pym.exe' copiado de forma permanente en: {target_exe_path}!")
            else:
                log_info("El ejecutable ya se encuentra ejecutándose desde el directorio permanente.")
            copied_successfully = True
        except Exception as e:
            sys.stderr.write(f"{Colors.RED}✖ Error al copiar el ejecutable al directorio de destino: {e}{Colors.RESET}\n")

    # Question 8: Persistent PATH Registration (Self-Installable like bgm!)
    print(f"\n⚙️ {Colors.BOLD}¿Deseas registrar/actualizar 'pym' en tu PATH del sistema de forma persistente?{Colors.RESET}")
    print(f"   {Colors.GRAY}(Te permitirá ejecutar 'pym' desde cualquier terminal sin especificar su ruta){Colors.RESET}")
    
    path_registered = False
    if ask_confirm("¿Registrar en PATH?", default=True):
        active_binary_dir = install_dir

        if os.name == "nt":
            try:
                import winreg
                import ctypes
                
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                try:
                    current_path, type_id = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    current_path = ""
                    type_id = winreg.REG_EXPAND_SZ
                    
                path_list = [p.strip() for p in current_path.split(";") if p.strip()]
                target_str = str(active_binary_dir)
                
                if target_str not in path_list:
                    path_list.append(target_str)
                    new_path = ";".join(path_list)
                    winreg.SetValueEx(key, "Path", 0, type_id, new_path)
                    log_success("¡PATH registrado persistentemente en el Registro de Windows!")
                else:
                    log_info("Este directorio ya se encuentra registrado en tu PATH de Windows.")
                winreg.CloseKey(key)
                
                # Broadcast environment changes to system to update terminal sessions instantly
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                result = ctypes.c_ulong()
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                    SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
                )
                log_success("¡Cambios en el entorno notificados al sistema operativo!")
                path_registered = True
            except Exception as e:
                from pym.utils import log_error
                log_error(f"Error al registrar PATH en Windows Registry: {e}")
        else:
            # Unix shell profiles
            shell_configs = [Path.home() / ".bashrc", Path.home() / ".zshrc", Path.home() / ".profile"]
            export_line = f'\n# PyCk package manager CLI PATH registration\nexport PATH="{active_binary_dir}:$PATH"\n'
            
            modified_files = []
            for conf in shell_configs:
                if conf.exists():
                    try:
                        with open(conf, "r") as f:
                            content = f.read()
                        if str(active_binary_dir) not in content:
                            with open(conf, "a") as f:
                                f.write(export_line)
                            modified_files.append(conf.name)
                    except Exception:
                        pass
            if modified_files:
                log_success(f"¡Exportación de PATH registrada en archivos de perfil: {', '.join(modified_files)}!")
                path_registered = True
            else:
                log_info("La exportación de PATH ya existía o no se encontraron configuraciones de shell.")
                path_registered = True
    else:
        log_info("Registro de PATH omitido.")

    # Premium Receipt Panel
    status_path = "Registrado con éxito" if path_registered else "Omitido"
    print(f"\n{Colors.GREEN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GREEN}│          🎉 Configuración Completada con Éxito! 🎉     │{Colors.RESET}")
    print(f"{Colors.GREEN}├────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"│  {Colors.BOLD}Modo Sandbox:{Colors.RESET}  {Colors.CYAN}{f'Opción {sandbox_val}':<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Cuarentena:{Colors.RESET}    {Colors.YELLOW}{f'{quarantine_hours} horas':<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Instalación:{Colors.RESET}   {Colors.MAGENTA}{str(install_dir):<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Estatus PATH:{Colors.RESET}  {Colors.GREEN if path_registered else Colors.GRAY}{status_path:<42}{Colors.RESET} │")
    print(f"{Colors.GREEN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
    print(f"🚀 Para comenzar a utilizar PyCk:")
    print(f"   1. Abre una {Colors.BOLD}{Colors.YELLOW}NUEVA{Colors.RESET} pestaña de terminal para cargar las variables.")
    print(f"   2. Ejecuta {Colors.BOLD}{Colors.CYAN}pym --help{Colors.RESET} para explorar los comandos.")
    print(f"   3. Escribe {Colors.BOLD}{Colors.CYAN}pym info{Colors.RESET} para ver el estatus de tu entorno.\n")
    if is_frozen and copied_successfully:
        print(f"💡 {Colors.YELLOW}{Colors.BOLD}Nota:{Colors.RESET} Ya puedes cerrar esta consola y borrar el archivo temporal descargas.")
        print(f"      La copia permanente ya reside en: {Colors.BOLD}{install_dir}{Colors.RESET}\n")
    print(f"{Colors.GRAY}{'─'*60}{Colors.RESET}\n")

    # Brief sleep for user reading setup summary if frozen
    if is_frozen:
        import time
        time.sleep(3.0)
    
    return config
