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
        print(f"🚀 {Colors.YELLOW}PyInstaller no está instalado en el entorno activo.{Colors.RESET}")
        print(" Instalando PyInstaller automáticamente mediante pip...")
        try:
            # Try standard install first
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            print(f" {Colors.GREEN}✔ PyInstaller instalado correctamente!{Colors.RESET}")
            return True
        except Exception:
            try:
                # Try with --break-system-packages for modern Unix systems
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--break-system-packages", "pyinstaller"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                print(f" {Colors.GREEN}✔ PyInstaller instalado correctamente (usando --break-system-packages)!{Colors.RESET}")
                return True
            except Exception as e:
                print(f" {Colors.RED}✖ Error al instalar PyInstaller automáticamente: {e}{Colors.RESET}")
                print("Por favor, ejecuta 'pip install pyinstaller' manualmente dentro de tu entorno y vuelve a intentarlo.")
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
    import argparse
    parser = argparse.ArgumentParser(
        description=(
            "======================================================================\n"
            "          PyCk Standalone Compiler & Packager Production Suite        \n"
            "======================================================================\n"
            "This enterprise-grade compiler engine bundles the entire PyCk package \n"
            "manager (pym) into a single standalone binary. It supports automatic  \n"
            "dependency resolution, cross-compilation target routing, and optional \n"
            "auditable shell-integrated installation orchestrators.\n\n"
            "Key Features:\n"
            " 1. Zero Dependencies: Intended for isolated corporate environments.\n"
            " 2. Smart Cross-Compilation: Easily compile Linux ELFs on Windows via WSL/Docker.\n"
            " 3. Dynamic Self-Deployment: Generate interactive setup wrappers alongside binary.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--include-installer",
        action="store_true",
        help=(
            "Generate an optional standalone 'install.py' script next to the compiled "
            "binary. Highly recommended for DevOps automation (Ansible, SSH provisioning) "
            "and corporate IT security auditing before binary execution."
        )
    )
    parser.add_argument(
        "--target",
        choices=["windows", "linux"],
        default=None,
        help=(
            "Force the target compilation Operating System format. By default, PyInstaller "
            "targets the active host OS. Specifying '--target linux' on a Windows machine "
            "will automatically try to locate WSL or Docker Desktop and launch a virtualized "
            "Linux slim container to build a native Linux ELF binary seamlessly."
        )
    )
    args = parser.parse_args()

    root_dir = Path(__file__).parent.resolve()

    # Handle cross-compilation target request
    if args.target:
        target_os = args.target.lower()
        host_os = "windows" if os.name == "nt" else "linux"
        
        if target_os != host_os:
            if host_os == "windows" and target_os == "linux":
                print(f"\n{Colors.CYAN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
                print(f"{Colors.CYAN}│             PyCk Standalone Compiler & Packager Engine │{Colors.RESET}")
                print(f"{Colors.CYAN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
                print(f"⚡ {Colors.YELLOW}Detectado target forzado para Linux en Host Windows.{Colors.RESET}")
                print(f"ℹ️  {Colors.GRAY}PyInstaller no realiza compilación cruzada directa.")
                print(f"    Intentando invocar WSL (Windows Subsystem for Linux) de forma recursiva...{Colors.RESET}\n")
                
                try:
                    # Run the script inside WSL
                    wsl_cmd = ["wsl", "python3", "build_exe.py"] + (["--include-installer"] if args.include_installer else [])
                    subprocess.run(wsl_cmd, check=True)
                    print(f"\n{Colors.GREEN}✔ ¡Compilación para Linux en WSL completada con éxito!{Colors.RESET}")
                    sys.exit(0)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print(f"⚠️  {Colors.YELLOW}WSL no está disponible o ha fallado. Intentando compilar usando Docker...{Colors.RESET}")
                    try:
                        # Docker compilation command
                        docker_cmd = [
                            "docker", "run", "--rm",
                            "-v", f"{root_dir}:/app",
                            "-w", "/app",
                            "python:3.11-slim",
                            "sh", "-c", "pip install pyinstaller && python build_exe.py" + (" --include-installer" if args.include_installer else "")
                        ]
                        subprocess.run(docker_cmd, check=True)
                        print(f"\n{Colors.GREEN}✔ ¡Compilación para Linux en Docker completada con éxito!{Colors.RESET}")
                        sys.exit(0)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print(f"\n{Colors.RED}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
                        print(f"{Colors.RED}│ ✖ Error: No se pudo compilar para Linux desde Windows  │{Colors.RESET}")
                        print(f"{Colors.RED}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
                        print("Para compilar para Linux en una máquina Windows, debes:")
                        print("  1. Tener instalado WSL (ejecuta 'wsl --install' en tu terminal y reinicia).")
                        print("  2. O tener Docker Desktop corriendo en tu sistema.")
                        print("\nDe lo contrario, por favor copia este repositorio y ejecuta 'python build_exe.py' directamente en tu máquina virtual o servidor Linux.\n")
                        sys.exit(1)
            elif host_os == "linux" and target_os == "windows":
                # Compiling for Windows on Linux
                print(f"\n{Colors.RED}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
                print(f"{Colors.RED}│ ✖ Error: No se admite compilar para Windows en Linux │{Colors.RESET}")
                print(f"{Colors.RED}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
                print("PyInstaller no admite compilar ejecutables de Windows (.exe) desde máquinas Linux.")
                print("Por favor, ejecuta este compilador directamente en una máquina Windows.\n")
                sys.exit(1)

    print(f"\n{Colors.CYAN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│             PyCk Standalone Compiler & Packager Engine │{Colors.RESET}")
    print(f"{Colors.CYAN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")

    # Detect current OS
    current_os = "Windows (Nativo)" if os.name == "nt" else "Linux/macOS (Nativo)"
    binary_ext = "pym.exe (Windows PE)" if os.name == "nt" else "pym (Linux ELF)"
    
    print(f"🖥️  {Colors.BOLD}Sistema Operativo Detectado:{Colors.RESET} {Colors.MAGENTA}{current_os}{Colors.RESET}")
    print(f"📦 {Colors.BOLD}Formato de Salida Compilado:{Colors.RESET} {Colors.YELLOW}{binary_ext}{Colors.RESET}")
    print(f"ℹ️  {Colors.GRAY}Información Técnica sobre Distribución Cruzada:{Colors.RESET}")
    print(f"    PyInstaller empaqueta el intérprete de Python y librerías dinámicas del sistema host.")
    print(f"    Por ello, no admite compilación cruzada directa (ej. generar binario de Linux desde Windows).")
    print(f"    {Colors.BOLD}{Colors.GREEN}¡Buenas noticias!{Colors.RESET} {Colors.GRAY}Este script ya es 100% multiplataforma. Para obtener el binario")
    print(f"    nativo de Linux, simplemente corre este mismo script en Linux, WSL o un contenedor Docker!{Colors.RESET}\n")

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
    
    # Clean previous build artifacts
    clean_paths([entry_file, spec_file, build_dir, dist_dir])
    
    # 2. Create entry point
    print(f"📂 {Colors.GRAY}Creando punto de entrada temporal de la CLI...{Colors.RESET}")
    try:
        with open(entry_file, "w", encoding="utf-8") as f:
            f.write(
                "import sys\n"
                "from pym.cli import main\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )
    except Exception as e:
        print(f" {Colors.RED}✖ Error al escribir el punto de entrada temporal: {e}{Colors.RESET}")
        sys.exit(1)
        
    # 3. Trigger compilation
    print(f"⚡ {Colors.CYAN}Compilando ejecutable standalone (este proceso puede tardar unos segundos)...{Colors.RESET}")
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
            print(f" {Colors.RED}✖ La compilación de PyInstaller ha fallado:{Colors.RESET}\n{res.stderr}")
            clean_paths([entry_file, spec_file, build_dir, dist_dir])
            sys.exit(1)
    except Exception as e:
        print(f" {Colors.RED}✖ Error al invocar el subproceso de PyInstaller: {e}{Colors.RESET}")
        clean_paths([entry_file, spec_file, build_dir, dist_dir])
        sys.exit(1)
        
    # Determine output
    exe_filename = "pym.exe" if os.name == "nt" else "pym"
    compiled_exe = dist_dir / exe_filename
    
    if not compiled_exe.exists():
        print(f" {Colors.RED}✖ Error: No se encontró el ejecutable compilado en: {compiled_exe}{Colors.RESET}")
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
        print(f" {Colors.RED}✖ Error al mover el ejecutable compilado a la carpeta bin: {e}{Colors.RESET}")
        clean_paths([entry_file, spec_file, build_dir, dist_dir])
        sys.exit(1)
        
    # 5. Standalone installer next to the binary if requested
    if args.include_installer:
        print(f"📄 {Colors.GRAY}Creando instalador standalone interactivo para distribución...{Colors.RESET}")
        installer_code = """import os
import sys
import json
from pathlib import Path

# Force UTF-8 encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

class Colors:
    CYAN = "\\033[1;36m"
    GREEN = "\\033[1;32m"
    YELLOW = "\\033[1;33m"
    MAGENTA = "\\033[1;35m"
    RED = "\\033[1;31m"
    GRAY = "\\033[90m"
    BOLD = "\\033[1m"
    RESET = "\\033[0m"

def ask_text(prompt_text, default=""):
    if not sys.stdin.isatty():
        return default
    try:
        suffix = f" {Colors.GRAY}({default}){Colors.RESET}" if default else ""
        sys.stdout.write(f"{Colors.BOLD}?{Colors.RESET} {prompt_text}{suffix}: ")
        sys.stdout.flush()
        user_val = input().strip()
        return user_val if user_val else default
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)

def ask_confirm(prompt_text, default=True):
    if not sys.stdin.isatty():
        return default
    try:
        opts = " [Y/n] " if default else " [y/N] "
        sys.stdout.write(f"{Colors.BOLD}?{Colors.RESET} {prompt_text}{Colors.CYAN}{opts}{Colors.RESET}")
        sys.stdout.flush()
        user_val = input().strip().lower()
        if not user_val:
            return default
        return user_val.startswith("y")
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)

def ask_select(prompt_text, options, default_idx=0):
    if not sys.stdin.isatty():
        fallback_opt = options[default_idx]
        print(f"{Colors.GREEN}✔{Colors.RESET} {Colors.BOLD}{prompt_text}{Colors.RESET} {Colors.CYAN}❯ {fallback_opt} (auto){Colors.RESET}")
        return fallback_opt
    print(f"\\n{Colors.CYAN}?{Colors.RESET} {Colors.BOLD}{prompt_text}{Colors.RESET}")
    for idx, opt in enumerate(options):
        print(f"  [{idx + 1}] {opt}")
    while True:
        try:
            sys.stdout.write(f"👉 Selecciona opción [1-{len(options)}] (Por defecto {default_idx+1}): ")
            sys.stdout.flush()
            val = input().strip()
            if not val:
                return options[default_idx]
            idx = int(val) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, KeyboardInterrupt, EOFError):
            pass

def main():
    print(f"\\n{Colors.CYAN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│          PyCk Standalone Package Installer             │{Colors.RESET}")
    print(f"{Colors.CYAN}└────────────────────────────────────────────────────────┘{Colors.RESET}\\n")

    current_dir = Path(__file__).parent.resolve()
    exe_name = "pym.exe" if os.name == "nt" else "pym"
    exe_file = current_dir / exe_name

    if not exe_file.is_file():
        print(f"{Colors.RED}✖ Error: No se encontró el ejecutable '{exe_name}' en: {current_dir}{Colors.RESET}")
        sys.exit(1)

    # Load existing config for defaults if present
    config_dir = Path.home() / ".pyck"
    config_file = config_dir / "config.json"
    existing_config = {}
    is_reconfigured = config_file.is_file()
    if is_reconfigured:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except Exception:
            pass

    # Global interactive Setup Wizard config keys
    if is_reconfigured:
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 Iniciando Asistente de Reconfiguración de PyCk...{Colors.RESET}\\n")
        print(f"   {Colors.GRAY}(Presiona Enter en cada pregunta para mantener tu configuración actual.){Colors.RESET}\\n")
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 Iniciando Asistente de Configuración Inicial de PyCk...{Colors.RESET}\\n")
    
    # 0. Target Physical Installation Directory (Symmetric to first-run setup)
    default_install_dir = existing_config.get("installDir")
    if not default_install_dir:
        default_install_dir = str(Path.home() / ".pyck" / "bin")
    
    install_dir = Path(default_install_dir).resolve()
    print(f"📁 {Colors.BOLD}Selecciona el directorio para instalar permanentemente 'pym.exe':{Colors.RESET}")
    print(f"   {Colors.GRAY}(Presiona Enter para mantener por defecto: {install_dir}){Colors.RESET}")
    user_install_dir = ask_text("Ruta del directorio de instalación", default=str(install_dir))
    install_dir = Path(user_install_dir).resolve()
    print()

    # 1. Sandbox Policy
    sandbox_opts = [
        "Opción A (Zero-Trust Absoluto): Sandbox estricto activo en TODOS los scripts.",
        "Opción B (Balanceado): Sandbox activo solo en instalaciones o scripts de riesgo."
    ]
    curr_sandbox = existing_config.get("sandboxOption", "A")
    default_sandbox_idx = 0 if curr_sandbox == "A" else 1
    selected_sandbox = ask_select("Elige la política de seguridad del Sandbox:", sandbox_opts, default_idx=default_sandbox_idx)
    sandbox_val = "A" if "Opción A" in selected_sandbox else "B"

    # 2. Quarantine Hours
    curr_quarantine = str(existing_config.get("quarantineHours", "72"))
    quarantine_hours_str = ask_text("Horas de cuarentena para nuevos paquetes en PyPI", default=curr_quarantine)
    try:
        quarantine_hours = int(quarantine_hours_str)
    except ValueError:
        quarantine_hours = 72

    # 3. Default Author
    if "defaultAuthor" in existing_config:
        default_name = existing_config["defaultAuthor"]
    else:
        try:
            default_name = os.getlogin()
        except Exception:
            default_name = "Developer"
    author_val = ask_text("Nombre por defecto del desarrollador (autor)", default=default_name)

    # 4. Default License
    license_opts = ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]
    curr_license = existing_config.get("defaultLicense", "MIT")
    try:
        default_license_idx = license_opts.index(curr_license)
    except ValueError:
        default_license_idx = 0
    license_val = ask_select("Elige la licencia por defecto para tus proyectos:", license_opts, default_idx=default_license_idx)

    # 5. Preferred Packaging Engine
    engine_opts = [
        "uv (Rust speed) ⚡ - Máxima velocidad",
        "pip (Python standard) - Fallback nativo"
    ]
    curr_engine = existing_config.get("defaultEngine", "uv")
    default_engine_idx = 0 if curr_engine == "uv" else 1
    selected_engine = ask_select("Elige tu motor de empaquetado favorito:", engine_opts, default_idx=default_engine_idx)
    engine_val = "uv" if "uv" in selected_engine else "pip"

    # 6. Auto Audit
    curr_audit = existing_config.get("autoAudit", True)
    auto_audit_val = ask_confirm("¿Activar Piloto Automático de Auditorías tras instalar?", default=curr_audit)

    # Save to global config directory
    config_dir = Path.home() / ".pyck"
    config_file = config_dir / "config.json"
    
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        config_data = {
            "quarantineHours": quarantine_hours,
            "sandboxOption": sandbox_val,
            "strictMode": True if sandbox_val == "A" else False,
            "defaultAuthor": author_val,
            "defaultLicense": license_val,
            "defaultEngine": engine_val,
            "autoAudit": auto_audit_val,
            "installDir": str(install_dir)
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            f.write("\\n")
        print(f"\\n {Colors.GREEN}✔ Configuración global guardada con éxito en: {config_file}{Colors.RESET}")
    except Exception as e:
        print(f" {Colors.RED}✖ Error al guardar archivo de configuración global: {e}{Colors.RESET}")
        sys.exit(1)

    # Perform physical self-copying install
    copied_successfully = False
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        target_exe_path = install_dir / exe_name
        
        # Prevent copying onto itself
        if exe_file.resolve() != target_exe_path.resolve():
            import shutil
            shutil.copy2(exe_file, target_exe_path)
            print(f" {Colors.GREEN}✔ Ejecutable '{exe_name}' copiado de forma permanente en: {target_exe_path}{Colors.RESET}")
        else:
            print(f"ℹ {Colors.YELLOW}El ejecutable ya se encuentra en el directorio permanente.{Colors.RESET}")
        copied_successfully = True
    except Exception as e:
        print(f" {Colors.RED}✖ Error al copiar el ejecutable al directorio permanente: {e}{Colors.RESET}")
        sys.exit(1)

    # Register target folder in system PATH
    registered = False
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
            target_str = str(install_dir.resolve())
            
            if target_str not in path_list:
                path_list.append(target_str)
                new_path = ";".join(path_list)
                winreg.SetValueEx(key, "Path", 0, type_id, new_path)
                registered = True
                print(f" {Colors.GREEN}✔ PATH registrado persistentemente en el Registro de Windows!{Colors.RESET}")
            else:
                print(f"ℹ {Colors.YELLOW}Este directorio de ejecutables ya se encuentra en tu PATH de Windows.{Colors.RESET}")
                registered = True
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
            print(f" {Colors.GREEN}✔ Cambios en el entorno notificados al sistema operativo!{Colors.RESET}")
        except Exception as e:
            print(f" {Colors.RED}✖ Error al modificar el registro de PATH: {e}{Colors.RESET}")
            print("Por favor, agrega la carpeta de ejecutables a tu PATH de Windows de manera manual.")
    else:
        # Unix Shell profiles registration
        shell_configs = [Path.home() / ".bashrc", Path.home() / ".zshrc", Path.home() / ".profile"]
        export_line = f'\\n# PyCk package manager CLI PATH registration\\nexport PATH="{install_dir.resolve()}:$PATH"\\n'
        
        modified_files = []
        for conf in shell_configs:
            if conf.exists():
                try:
                    with open(conf, "r") as f:
                        content = f.read()
                    if str(install_dir.resolve()) not in content:
                        with open(conf, "a") as f:
                            f.write(export_line)
                        modified_files.append(conf.name)
                except Exception as e:
                    print(f"⚠️ Error al actualizar {conf.name}: {e}")
                    
        if modified_files:
            print(f" {Colors.GREEN}✔ Exportación de PATH registrada en archivos de perfil: {', '.join(modified_files)}!{Colors.RESET}")
            registered = True
        else:
            print(f"ℹ {Colors.YELLOW}La exportación de PATH ya existía o no se encontraron configuraciones de shell.{Colors.RESET}")
            registered = True
            
    print(f"\\n{Colors.GREEN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GREEN}│               🎉 Instalación Finalizada! 🎉             │{Colors.RESET}")
    print(f"{Colors.GREEN}├────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"│  {Colors.BOLD}Ubicación Exe:{Colors.RESET} {Colors.YELLOW}{str(install_dir):<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Estatus PATH:{Colors.RESET}  {Colors.CYAN}{'Registrado con éxito':<42}{Colors.RESET} │")
    print(f"{Colors.GREEN}└────────────────────────────────────────────────────────┘{Colors.RESET}\\n")
    print(f"🚀 Para comenzar a utilizar PyCk:")
    print(f"   1. Abre una {Colors.BOLD}{Colors.YELLOW}NUEVA{Colors.RESET} pestaña de terminal para cargar el PATH.")
    print(f"   2. Ejecuta {Colors.BOLD}{Colors.CYAN}pym --help{Colors.RESET} para explorar los comandos.")
    print(f"   3. Escribe {Colors.BOLD}{Colors.CYAN}pym info{Colors.RESET} para ver el estatus de tu entorno.\\n")
    if copied_successfully:
        print(f"💡 {Colors.YELLOW}{Colors.BOLD}Nota:{Colors.RESET} Ya puedes borrar de forma segura el archivo temporal descargas.")

if __name__ == '__main__':
    main()
"""
        try:
            with open(target_bin_dir / "install.py", "w", encoding="utf-8") as f:
                f.write(installer_code)
        except Exception as e:
            print(f" {Colors.RED}✖ Error al escribir el archivo de instalación standalone: {e}{Colors.RESET}")
            clean_paths([entry_file, spec_file, build_dir, dist_dir])
            sys.exit(1)
    else:
        print(f"ℹ️ {Colors.GRAY}Omitiendo la generación del instalador install.py (se compilará solo el ejecutable autocontenido).{Colors.RESET}")

    # 6. Clean up intermediate build directories
    print(f"🧹 {Colors.GRAY}Limpiando directorios de compilación temporales...{Colors.RESET}")
    clean_paths([entry_file, spec_file, build_dir, dist_dir])
    
    # 7. Print compilation receipt
    elapsed_time = round(time.time() - start_time, 2)
    file_size_mb = round(os.path.getsize(final_exe_path) / (1024 * 1024), 2)
    
    print(f"\n{Colors.GREEN}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"│               🎉 Compilación Finalizada! 🎉             │{Colors.RESET}")
    print(f"├────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"│  {Colors.BOLD}Versión Bin:{Colors.RESET}   {Colors.YELLOW}{version_str:<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Ejecutable:{Colors.RESET}    {Colors.GRAY}{str(final_exe_path.relative_to(root_dir)):<42}{Colors.RESET} │")
    if args.include_installer:
        print(f"│  {Colors.BOLD}Instalador:{Colors.RESET}    {Colors.GRAY}{f'bin/{version_str}/install.py':<42}{Colors.RESET} │")
    else:
        print(f"│  {Colors.BOLD}Instalador:{Colors.RESET}    {Colors.GRAY}{'Omitido (No generado)':<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Tamaño Exe:{Colors.RESET}    {Colors.GREEN}{f'{file_size_mb} MB':<42}{Colors.RESET} │")
    print(f"│  {Colors.BOLD}Duración:{Colors.RESET}      {Colors.CYAN}{f'{elapsed_time} segundos':<42}{Colors.RESET} │")
    print(f"{Colors.GREEN}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
    print(f"📦 Paquete Standalone generado en: {Colors.BOLD}{Colors.YELLOW}bin/{version_str}/{Colors.RESET}")
    
    if args.include_installer:
        print(f"   Este paquete incluye 'install.py' para automatizaciones (Ansible) y auditorías corporativas.")
        print(f"   Para instalarlo en cualquier servidor, ejecuta:")
        print(f"   {Colors.BOLD}{Colors.CYAN}python bin/{version_str}/install.py{Colors.RESET}\n")
    else:
        print(f"   El ejecutable es 100% autoinstalable y autocontenido en su primera ejecución.")
        print(f"   (Puedes reconfigurarlo o actualizar su PATH en cualquier momento usando el comando '{Colors.BOLD}pym config wizard{Colors.RESET}').")
        print(f"   Si necesitas generar el instalador 'install.py' para aprovisionamientos programados (Ansible) o auditorías de seguridad, compila usando:")
        print(f"   {Colors.BOLD}{Colors.CYAN}python build_exe.py --include-installer{Colors.RESET}\n")

if __name__ == "__main__":
    main()
