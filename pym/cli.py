import os
import sys
import re
import shutil
from pathlib import Path
from pym.utils import (
    print_logo, log_success, log_info, log_warning, log_error, 
    ask_text, ask_confirm, ask_select, Colors, Spinner
)
from pym.venv import (
    find_venv_root, get_venv_python, get_venv_pip, create_venv, get_dir_size_mb
)
from pym.engine import (
    install_packages, uninstall_packages, sync_dependencies, get_or_bootstrap_uv
)
from pym.project import (
    find_pyckage_json, load_pyckage_json, save_pyckage_json, 
    update_pyckage_dependencies, generate_lockfile
)
from pym.runner import run_script, spawn_subshell
from pym.boilerplate import scaffold_project
from pym.config import load_global_config, save_global_config, CONFIG_FILE

def show_help():
    print_logo()
    help_text = f"""
{Colors.BOLD}USAGE:{Colors.RESET}
    pym <command> [options]

{Colors.BOLD}COMMANDS:{Colors.RESET}
    {Colors.CYAN}init{Colors.RESET}          Scaffold a premium project via interactive CLI prompts (Vite-style)
    {Colors.CYAN}install, i{Colors.RESET}    Install dependencies in .venv (syncs everything if no arguments passed)
    {Colors.CYAN}uninstall, remove, un{Colors.RESET}
                  Uninstall packages from .venv and update pyckage.json
    {Colors.CYAN}run, r{Colors.RESET}        Execute a script defined in pyckage.json (with automatic sandboxing)
    {Colors.CYAN}code{Colors.RESET}          Generate boilerplate elements (e.g. pym code api, pym code test)
    {Colors.CYAN}shell{Colors.RESET}         Drop into an active virtual environment shell
    {Colors.CYAN}info{Colors.RESET}          Display a gorgeous dashboard of the current project state
    {Colors.CYAN}list{Colors.RESET}          List all installed dependencies in .venv in a gorgeous premium table
    
    {Colors.CYAN}audit{Colors.RESET}         Perform a deep security and import audit on dependencies
    {Colors.CYAN}outdated{Colors.RESET}      Scan for newer safe releases available on PyPI (>72h old)
    {Colors.CYAN}prune{Colors.RESET}         Prune unneeded or orphaned package debris from .venv
    {Colors.CYAN}clean{Colors.RESET}         Recursively wipe out python caches, ruff caches, and build clutter
    {Colors.CYAN}lock{Colors.RESET}          Verify and regenerate pyckage.lock with cryptographic hashes
    {Colors.CYAN}update, upgrade{Colors.RESET}
                  Safe upgrade of all packages (or specific package) with quarantine checks
    {Colors.CYAN}config{Colors.RESET}          [NEW] View or modify global preferences (e.g. pym config set quarantineHours 48)

{Colors.BOLD}INSTALL OPTIONS:{Colors.RESET}
    {Colors.GRAY}-D, --dev{Colors.RESET}            Save installed packages as devDependencies
    {Colors.GRAY}-g, --global{Colors.RESET}         Install package globally (using system pip)
    {Colors.GRAY}--latest, --force-latest{Colors.RESET}
                        Bypass the 72-hour package quarantine period

{Colors.BOLD}SCRIPT RUN OPTIONS:{Colors.RESET}
    {Colors.GRAY}--allow-network{Colors.RESET}     Allow outgoing network requests from sandbox
    {Colors.GRAY}--allow-fs{Colors.RESET}          Allow unrestricted file system access
    {Colors.GRAY}--allow-env{Colors.RESET}         Allow loading of sensitive system env vars
    {Colors.GRAY}--no-sandbox{Colors.RESET}        Completely disable sandbox isolation
    {Colors.GRAY}-y, --yes{Colors.RESET}            Bypass risk warning confirmation prompts

{Colors.BOLD}EXAMPLES:{Colors.RESET}
    pym init
    pym install requests
    pym run dev --allow-network
    pym config show
    pym config set quarantineHours 48
    pym config wizard
"""
    print(help_text)

def handle_init(args=[]):
    print_logo()
    
    # Load global setup preferences
    config = load_global_config()
    
    # Defaults
    default_name = Path(os.getcwd()).name
    project_name = default_name
    version = "0.1.0"
    description = "A Python project powered by PyCk"
    private = True
    
    author = config.get("defaultAuthor", "Developer")
    framework = "None"
    use_ruff = True
    use_pytest = True
    use_docker = False
    init_git = True
    use_gitignore = True
    
    # If any CLI argument is supplied, bypass interactive prompts
    interactive = len(args) == 0
    
    if not interactive:
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-n", "--name") and i + 1 < len(args):
                project_name = args[i+1]
                i += 2
            elif arg in ("-v", "--version") and i + 1 < len(args):
                version = args[i+1]
                i += 2
            elif arg in ("-d", "--desc", "--description") and i + 1 < len(args):
                description = args[i+1]
                i += 2
            elif arg in ("-a", "--author") and i + 1 < len(args):
                author = args[i+1]
                i += 2
            elif arg == "--private":
                private = True
                i += 1
            elif arg == "--public":
                private = False
                i += 1
            elif arg in ("-f", "--framework") and i + 1 < len(args):
                val = args[i+1].lower()
                if val == "fastapi":
                    framework = "FastAPI"
                elif val == "flask":
                    framework = "Flask"
                elif val == "django":
                    framework = "Django"
                else:
                    framework = "None"
                i += 2
            elif arg == "--pytest":
                use_pytest = True
                i += 1
            elif arg == "--no-pytest":
                use_pytest = False
                i += 1
            elif arg == "--ruff":
                use_ruff = True
                i += 1
            elif arg == "--no-ruff":
                use_ruff = False
                i += 1
            elif arg == "--docker":
                use_docker = True
                i += 1
            elif arg == "--no-docker":
                use_docker = False
                i += 1
            elif arg == "--git":
                init_git = True
                i += 1
            elif arg == "--no-git":
                init_git = False
                use_gitignore = False
                i += 1
            elif arg == "--gitignore":
                use_gitignore = True
                i += 1
            elif arg == "--no-gitignore":
                use_gitignore = False
                i += 1
            else:
                i += 1
    else:
        print(f"{Colors.BOLD}{Colors.CYAN}--- PyCk Project Setup Wizard ---{Colors.RESET}\n")
        
        # Interactive prompts
        project_name = ask_text("Project Name", default=default_name)
        version = ask_text("Version", default="0.1.0")
        description = ask_text("Description", default="A Python project powered by PyCk")
        private = ask_confirm("Private project?", default=True)
        author = ask_text("Author", default=author)
        
        # Selection menus
        framework = ask_select("Choose Web Framework:", ["None", "FastAPI", "Flask", "Django"], default_idx=0)
        use_ruff = ask_confirm("Enable Ruff for linting & formatting?", default=True)
        use_pytest = ask_confirm("Enable pytest for testing?", default=True)
        use_docker = ask_confirm("Add production-ready Dockerfile?", default=False)
        
        # Git & Gitignore logic (Conditional prompt!)
        init_git = ask_confirm("Initialize Git repository?", default=True)
        if init_git:
            use_gitignore = ask_confirm("Generate .gitignore file?", default=True)
        else:
            use_gitignore = False
    
    print(f"\n{Colors.CYAN}⚡ Initializing project '{project_name}'...{Colors.RESET}")
    
    # 2. Setup pyckage.json structure
    pyckage_data = {
        "name": project_name,
        "version": version,
        "description": description,
        "private": private,
        "author": author,
        "license": config.get("defaultLicense", "MIT"),
        "python": f"^{sys.version_info.major}.{sys.version_info.minor}",
        "engines": {
            "python": f"^{sys.version_info.major}.{sys.version_info.minor}"
        },
        "scripts": {
            "dev": "python main.py"
        },
        "dependencies": {},
        "devDependencies": {}
    }
    
    # Append scripts and framework dependencies
    if framework == "FastAPI":
        pyckage_data["dependencies"]["fastapi"] = "^0.110.0"
        pyckage_data["dependencies"]["uvicorn"] = "^0.28.0"
        pyckage_data["scripts"]["dev"] = "python main.py"
    elif framework == "Flask":
        pyckage_data["dependencies"]["flask"] = "^3.0.0"
        pyckage_data["scripts"]["dev"] = "python main.py"
    elif framework == "Django":
        pyckage_data["dependencies"]["django"] = "^5.0.0"
        pyckage_data["scripts"]["dev"] = "python main.py runserver"
    else:
        pyckage_data["scripts"]["dev"] = "python main.py"
        
    if use_pytest:
        pyckage_data["devDependencies"]["pytest"] = "^8.1.0"
        pyckage_data["scripts"]["test"] = "pytest"
        
    if use_ruff:
        pyckage_data["devDependencies"]["ruff"] = "^0.3.0"
        pyckage_data["scripts"]["lint"] = "ruff check"
        pyckage_data["scripts"]["format"] = "ruff format"

    # Save initial pyckage.json
    pyckage_path = Path("pyckage.json").resolve()
    save_pyckage_json(pyckage_data, pyckage_path)
    
    # 3. Create virtual environment
    venv_path = Path(".venv").resolve()
    uv_cmd = get_or_bootstrap_uv(silent=True)
    uv_path = uv_cmd[0] if uv_cmd and len(uv_cmd) == 1 else None
    
    spinner = Spinner("Creating isolated virtual environment (.venv)...")
    spinner.start()
    success = create_venv(venv_path, uv_path)
    if success:
        spinner.stop(success=True, finish_message="Isolated environment (.venv) successfully created.")
    else:
        spinner.stop(success=False, finish_message="Failed to create virtual environment.")
        sys.exit(1)
        
    # 4. Scaffold Files (main.py, test, readme, gitignore, Dockerfile)
    scaffold_project(
        root_path=Path(".").resolve(),
        name=project_name,
        description=description,
        framework=framework,
        use_docker=use_docker,
        use_ruff=use_ruff,
        use_pytest=use_pytest,
        use_gitignore=use_gitignore
    )
    
    # 4.5 Initialize Git if requested
    if init_git:
        import subprocess
        try:
            res = subprocess.run(["git", "init"], capture_output=True, text=True)
            if res.returncode == 0:
                log_success("Git repository successfully initialized.")
            else:
                log_info("Git is installed but 'git init' failed.")
        except Exception:
            log_info("Git is not found or not installed on this system. Skipping Git initialization.")
    
    # 5. Sync dependencies automatically inside newly created .venv!
    log_info("Installing standard project dependencies...")
    sync_success = sync_dependencies(
        dependencies=pyckage_data["dependencies"],
        dev_dependencies=pyckage_data["devDependencies"],
        venv_path=venv_path
    )
    
    if sync_success:
        generate_lockfile(venv_path)
        log_success("All packages successfully installed and locked!")
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 PyCk Project Successfully Scaffolded!{Colors.RESET}")
        print(f"To run your app in development mode, enter:")
        print(f"   {Colors.CYAN}pym run dev{Colors.RESET}\n")
    else:
        log_warning("Project was created, but dependency installation failed. Try running 'pym install' manually.")

def run_auto_audit_if_enabled():
    config = load_global_config()
    if config.get("autoAudit", True):
        log_info("Iniciando Piloto Automático de Auditoría...")
        try:
            handle_audit()
        except Exception:
            pass

def handle_install(args):
    # Parse options
    dev = False
    global_install = False
    force_latest = False
    packages = []
    
    for arg in args:
        if arg in ("-D", "--dev"):
            dev = True
        elif arg in ("-g", "--global"):
            global_install = True
        elif arg in ("--latest", "--force-latest", "--bleeding-edge"):
            force_latest = True
        else:
            packages.append(arg)
            
    venv_path = find_venv_root()
    
    if global_install:
        if not packages:
            log_error("Please specify packages to install globally. Example: pym install requests -g")
            sys.exit(1)
        success = install_packages(packages, venv_path, dev=False, global_install=True, force_latest=force_latest)
        sys.exit(0 if success else 1)
        
    # Standard venv install
    pyckage_path = find_pyckage_json()
    
    if not packages:
        # NPM Install equivalent: sync all packages listed in pyckage.json
        if not pyckage_path.is_file():
            log_error("pyckage.json not found in this folder or parents. Run 'pym init' first.")
            sys.exit(1)
            
        data = load_pyckage_json(pyckage_path)
        
        # Ensure .venv exists
        if not venv_path.exists():
            log_info(".venv not found. Creating it first...")
            create_venv(venv_path)
            
        success = sync_dependencies(
            dependencies=data.get("dependencies", {}),
            dev_dependencies=data.get("devDependencies", {}),
            venv_path=venv_path,
            force_latest=force_latest
        )
        if success:
            generate_lockfile(venv_path)
            run_auto_audit_if_enabled()
        sys.exit(0 if success else 1)
        
    else:
        # Install explicit packages
        if not pyckage_path.is_file():
            log_warning("pyckage.json not found. Creating a default configuration...")
            save_pyckage_json({}, pyckage_path)
            
        if not venv_path.exists():
            log_info(".venv not found. Creating it first...")
            create_venv(venv_path)
            
        success = install_packages(packages, venv_path, dev=dev, force_latest=force_latest)
        if success:
            update_pyckage_dependencies(packages, venv_path, dev=dev)
            generate_lockfile(venv_path)
            log_success(f"Added {', '.join(packages)} to {'devDependencies' if dev else 'dependencies'} in pyckage.json.")
            run_auto_audit_if_enabled()
            
        sys.exit(0 if success else 1)

def handle_uninstall(args):
    if not args:
        log_error("Please specify packages to uninstall. Example: pym uninstall requests")
        sys.exit(1)
        
    venv_path = find_venv_root()
    pyckage_path = find_pyckage_json()
    
    success = uninstall_packages(args, venv_path)
    if success:
        if pyckage_path.is_file():
            update_pyckage_dependencies(args, venv_path, remove=True)
            generate_lockfile(venv_path)
            log_success(f"Removed {', '.join(args)} from pyckage.json.")
            
    sys.exit(0 if success else 1)

def handle_run(args):
    if not args:
        log_error("Please specify a script to run. Examples: pym run dev, pym run test")
        sys.exit(1)
        
    # Extract security flags
    allow_network = "--allow-network" in args
    allow_fs = "--allow-fs" in args
    allow_env = "--allow-env" in args
    no_sandbox = "--no-sandbox" in args
    force_yes = ("-y" in args) or ("--yes" in args)
    
    clean_args = [a for a in args if a not in [
        "--allow-network", "--allow-fs", "--allow-env", "--no-sandbox", "-y", "--yes"
    ]]
    
    script_name = clean_args[0]
    extra_args = clean_args[1:]
    
    pyckage_path = find_pyckage_json()
    if not pyckage_path.is_file():
        log_error("pyckage.json not found. Run 'pym init' first.")
        sys.exit(1)
        
    data = load_pyckage_json(pyckage_path)
    scripts = data.get("scripts", {})
    
    if script_name not in scripts:
        log_error(f"Script '{script_name}' not defined in pyckage.json.")
        if scripts:
            print(f"\n{Colors.BOLD}Available scripts:{Colors.RESET}")
            for k, v in scripts.items():
                print(f"  {Colors.CYAN}{k}{Colors.RESET} : {v}")
        sys.exit(1)
        
    script_cmd = scripts[script_name]
    venv_path = find_venv_root()
    
    # Check if venv exists, otherwise warn
    if not venv_path.exists():
        log_warning(f"Virtual environment (.venv) not found at {venv_path.name}. Command may execute globally.")
        
    exit_code = run_script(
        script_name, script_cmd, venv_path, extra_args,
        allow_network=allow_network,
        allow_fs=allow_fs,
        allow_env=allow_env,
        no_sandbox=no_sandbox,
        force_yes=force_yes
    )
    sys.exit(exit_code)

def handle_code(args):
    if not args:
        log_error("Please specify a generator type. Examples:\n  pym code api\n  pym code class User\n  pym code test")
        sys.exit(1)
        
    gen_type = args[0].lower()
    
    if gen_type == "api":
        target = Path("api.py")
        if target.is_file():
            log_warning("api.py already exists. Generator cancelled to prevent overwrite.")
            sys.exit(1)
        api_code = """from fastapi import APIRouter
 
router = APIRouter(
    prefix="/api/v1",
    tags=["endpoints"]
)
 
@router.get("/users")
async def get_users():
    return [{"id": 1, "username": "pyck_user"}]
"""
        with open(target, "w", encoding="utf-8") as f:
            f.write(api_code)
        log_success("Generated FastAPI endpoint blueprint in 'api.py'.")
        
    elif gen_type == "class":
        if len(args) < 2:
            log_error("Please specify a class name. Example: pym code class User")
            sys.exit(1)
        class_name = args[1]
        filename = f"{class_name.lower()}.py"
        target = Path(filename)
        
        if target.is_file():
            log_warning(f"{filename} already exists. Action cancelled.")
            sys.exit(1)
            
        class_code = f"""class {class_name}:
    def __init__(self):
        pass
 
    def __repr__(self) -> str:
        return f"<{class_name}>"
"""
        with open(target, "w", encoding="utf-8") as f:
            f.write(class_code)
        log_success(f"Generated class blueprint {class_name} in '{filename}'.")
        
    elif gen_type == "test":
        target = Path("test_main.py")
        if target.is_file():
            log_warning("test_main.py already exists. Action cancelled.")
            sys.exit(1)
            
        test_code = """def test_app_logic():
    # Write your pytest assert scripts here
    assert True
"""
        with open(target, "w", encoding="utf-8") as f:
            f.write(test_code)
        log_success("Generated mock pytest file in 'test_main.py'.")
        
    else:
        log_error(f"Unknown generator type '{gen_type}'. Supported: api, class, test.")
        sys.exit(1)

def handle_info():
    pyckage_path = find_pyckage_json()
    data = load_pyckage_json(pyckage_path)
    venv_path = find_venv_root()
    
    project_name = data.get("name", "Unknown Project")
    project_ver = data.get("version", "0.0.0")
    project_desc = data.get("description", "No description provided.")
    
    # Calculate environment size
    venv_size = get_dir_size_mb(venv_path) if venv_path.exists() else 0.0
    venv_status = f"{Colors.GREEN}Active{Colors.RESET} ({venv_size} MB)" if venv_path.exists() else f"{Colors.RED}Missing{Colors.RESET}"
    
    # Detect engine
    uv_cmd = get_or_bootstrap_uv(silent=True)
    engine_name = f"{Colors.GREEN}uv (Rust speed) ⚡{Colors.RESET}" if uv_cmd else f"{Colors.YELLOW}pip (native fallback){Colors.RESET}"
    
    # Render dashboard box
    print(f"\n{Colors.CYAN}{Colors.BOLD}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│                   PyCk Project Info                    │{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}")
    print(f"  {Colors.BOLD}Project Name:{Colors.RESET}   {Colors.CYAN}{Colors.BOLD}{project_name}{Colors.RESET}")
    print(f"  {Colors.BOLD}Version:{Colors.RESET}        {Colors.GRAY}{project_ver}{Colors.RESET}")
    print(f"  {Colors.BOLD}Description:{Colors.RESET}    {project_desc}")
    print(f"  {Colors.BOLD}Author:{Colors.RESET}         {data.get('author', 'Anonymous')}")
    print(f"  {Colors.BOLD}Environment:{Colors.RESET}    {venv_status}")
    print(f"  {Colors.BOLD}Python Targets:{Colors.RESET} {data.get('python', 'Any')}")
    print(f"  {Colors.BOLD}Core Engine:{Colors.RESET}    {engine_name}")
    print(f"  {Colors.BOLD}Path:{Colors.RESET}           {pyckage_path.parent}")
    
    scripts = data.get("scripts", {})
    if scripts:
        print(f"\n  {Colors.BOLD}{Colors.UNDERLINE}Defined Scripts:{Colors.RESET}")
        for k, v in scripts.items():
            print(f"    {Colors.CYAN}{k:<10}{Colors.RESET} : {Colors.GRAY}{v}{Colors.RESET}")
            
    deps = data.get("dependencies", {})
    if deps:
        print(f"\n  {Colors.BOLD}{Colors.UNDERLINE}Dependencies ({len(deps)}):{Colors.RESET}")
        for k, v in deps.items():
            print(f"    {Colors.GREEN}✔ {k:<20}{Colors.RESET} {v}")
            
    dev_deps = data.get("devDependencies", {})
    if dev_deps:
        print(f"\n  {Colors.BOLD}{Colors.UNDERLINE}Development Dependencies ({len(dev_deps)}):{Colors.RESET}")
        for k, v in dev_deps.items():
            print(f"    {Colors.BLUE}🛠 {k:<20}{Colors.RESET} {v}")
    print()

def get_installed_packages(venv_path: Path) -> list:
    """
    Queries the virtual environment to list all currently installed packages.
    """
    import subprocess
    import json
    
    python_exe = get_venv_python(venv_path)
    uv_cmd = get_or_bootstrap_uv(silent=True)
    
    try:
        if uv_cmd:
            cmd = uv_cmd + ["pip", "list", "--format=json", "--python", str(python_exe)]
        else:
            pip_exe = get_venv_pip(venv_path)
            cmd = [str(pip_exe), "list", "--format=json"]
            
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception:
        pass
        
    return []

def handle_list(args=None):
    venv_path = find_venv_root()
    if not venv_path.exists():
        log_error(f"Isolated environment (.venv) not found.")
        log_info("Please run 'pym install' first to initialize the environment and install dependencies.")
        sys.exit(1)
        
    spinner = Spinner("Reading installed environment packages...")
    spinner.start()
    packages = get_installed_packages(venv_path)
    spinner.stop()
    
    if not packages:
        log_warning("No packages are currently installed in the virtual environment.")
        sys.exit(0)
        
    pyckage_path = find_pyckage_json()
    data = load_pyckage_json(pyckage_path) if pyckage_path.is_file() else {}
    
    core_deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    
    # Lowercase mappings for robust identification
    core_keys = {k.lower(): v for k, v in core_deps.items()}
    dev_keys = {k.lower(): v for k, v in dev_deps.items()}
    
    # Alphabetical sort
    packages = sorted(packages, key=lambda x: x["name"].lower())
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}┌───────────────────────────────────┬───────────────────┬────────────────┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│ Package Name                      │ Installed Version │ Type           │{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}├───────────────────────────────────┼───────────────────┼────────────────┤{Colors.RESET}")
    
    for pkg in packages:
        name = pkg["name"]
        ver = pkg["version"]
        name_lower = name.lower()
        
        # Categorize type
        if name_lower in core_keys:
            dep_type = f"{Colors.GREEN}[Core]{Colors.RESET}"
            type_name = "Core"
        elif name_lower in dev_keys:
            dep_type = f"{Colors.MAGENTA}[Dev]{Colors.RESET}"
            type_name = "Dev"
        else:
            dep_type = f"{Colors.GRAY}[Transitive]{Colors.RESET}"
            type_name = "Transitive"
            
        name_pad = name.ljust(33)
        ver_pad = ver.ljust(17)
        type_pad = dep_type + "".ljust(14 - len(type_name))
        
        print(f"│ {Colors.BOLD}{Colors.CYAN}{name_pad}{Colors.RESET} │ {Colors.GREEN}{ver_pad}{Colors.RESET} │ {type_pad} │")
        
    print(f"{Colors.BOLD}{Colors.CYAN}└───────────────────────────────────┴───────────────────┴────────────────┘{Colors.RESET}")
    print(f"  {Colors.BOLD}Total packages installed:{Colors.RESET} {Colors.GREEN}{len(packages)}{Colors.RESET}\n")

def handle_audit():
    pyckage_path = find_pyckage_json()
    if not pyckage_path.is_file():
        log_error("pyckage.json not found. Run 'pym init' first.")
        sys.exit(1)
        
    data = load_pyckage_json(pyckage_path)
    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    
    # Load lockfile packages
    lock_path = pyckage_path.parent / "pyckage.lock"
    locked_packages = {}
    if lock_path.is_file():
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
                locked_packages = lock_data.get("packages", {})
        except Exception:
            pass
            
    from pym.security import run_security_audit
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}⚡ INICIANDO AUDITORÍA DE SEGURIDAD ZERO-TRUST...{Colors.RESET}")
    res = run_security_audit(deps, dev_deps, locked_packages)
    
    # Render Audit findings dashboard
    print(f"\n{Colors.CYAN}{Colors.BOLD}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│                PyCk INFORME DE SEGURIDAD               │{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}")
    
    # A. Active Vulnerabilities
    print(f"  {Colors.BOLD}{Colors.UNDERLINE}Vulnerabilidades Activas ({len(res['vulnerabilities'])}):{Colors.RESET}")
    if res["vulnerabilities"]:
        for v in res["vulnerabilities"]:
            print(f"    {Colors.RED}✖ {v['package']} v{v['version']} - CVE: {v['id']}{Colors.RESET}")
            print(f"      {Colors.GRAY}{v['details'][:80]}...{Colors.RESET}")
            print(f"      Referencia: {Colors.CYAN}{v['link']}{Colors.RESET}")
    else:
        print(f"    {Colors.GREEN}✔ No se detectaron vulnerabilidades activas en PyPI.{Colors.RESET}")
        
    # B. Abandoned Packages
    print(f"\n  {Colors.BOLD}{Colors.UNDERLINE}Paquetes sin mantenimiento / Obsoletos ({len(res['abandoned'])}):{Colors.RESET}")
    if res["abandoned"]:
        for a in res["abandoned"]:
            years = a["days"] / 365.0
            print(f"    {Colors.YELLOW}⚠ {a['package']} v{a['version']}{Colors.RESET} - Último release hace {years:.1f} años.")
            print(f"      {Colors.GRAY}Última versión en PyPI: v{a['latest_version']}{Colors.RESET}")
    else:
        print(f"    {Colors.GREEN}✔ Todos los paquetes instalados están mantenidos activamente.{Colors.RESET}")
        
    # C. Orphaned (Unused) Dependencies
    print(f"\n  {Colors.BOLD}{Colors.UNDERLINE}Dependencias Huérfanas (Sin importar en código) ({len(res['orphaned'])}):{Colors.RESET}")
    if res["orphaned"]:
        for o in res["orphaned"]:
            print(f"    {Colors.YELLOW}⚠ {o}{Colors.RESET} (No se detectó ninguna sentencia 'import {o.replace('-','_')}' en el proyecto).")
            print(f"      {Colors.GRAY}Recomendación: Ejecuta 'pym prune' para depurar tu espacio.{Colors.RESET}")
    else:
        print(f"    {Colors.GREEN}✔ Todas las dependencias declaradas están activas en tu código.{Colors.RESET}")
        
    # Print Summary Box
    print(f"\n{Colors.CYAN}{Colors.BOLD}├────────────────────────────────────────────────────────┤{Colors.RESET}")
    sum_color = Colors.RED if res["vulnerabilities"] else (Colors.YELLOW if res["orphaned"] or res["abandoned"] else Colors.GREEN)
    print(f"  {Colors.BOLD}Estado general:{Colors.RESET} {sum_color}{Colors.BOLD}{'CRÍTICO' if res['vulnerabilities'] else ('ADVERTENCIAS' if res['orphaned'] or res['abandoned'] else 'SEGURO')}{Colors.RESET}")
    print(f"  - Vulnerabilidades:  {Colors.RED}{len(res['vulnerabilities'])}{Colors.RESET}")
    print(f"  - Sin Mantenimiento: {Colors.YELLOW}{len(res['abandoned'])}{Colors.RESET}")
    print(f"  - Sin Uso en Código: {Colors.YELLOW}{len(res['orphaned'])}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")

def handle_outdated():
    pyckage_path = find_pyckage_json()
    if not pyckage_path.is_file():
        log_error("pyckage.json no encontrado.")
        sys.exit(1)
        
    venv_path = find_venv_root()
    packages = get_installed_packages(venv_path)
    
    if not packages:
        log_warning("No hay paquetes instalados en tu .venv.")
        sys.exit(0)
        
    from pym.config import load_global_config
    from pym.security import fetch_pypi_metadata, parse_pypi_date
    from datetime import datetime, timezone
    
    config = load_global_config()
    quarantine_hours = config.get("quarantineHours", 72)
    
    spinner = Spinner("Escaneando actualizaciones disponibles y cuarentenas...")
    spinner.start()
    
    outdated = []
    now = datetime.now(timezone.utc)
    
    for pkg in packages:
        name = pkg["name"]
        curr_ver = pkg["version"]
        
        metadata = fetch_pypi_metadata(name)
        if not metadata:
            continue
            
        latest_ver = metadata.get("info", {}).get("version")
        if not latest_ver or latest_ver == curr_ver:
            continue
            
        # Check upload time of the latest release to see if it's quarantined
        releases = metadata.get("releases", {})
        if latest_ver in releases and releases[latest_ver]:
            files = releases[latest_ver]
            upload_time_str = None
            for f in files:
                if "upload_time_iso_8601" in f:
                    upload_time_str = f["upload_time_iso_8601"]
                    break
            
            if upload_time_str:
                try:
                    dt = parse_pypi_date(upload_time_str)
                    age_h = (now - dt).total_seconds() / 3600.0
                    
                    is_quarantined = age_h < quarantine_hours
                    
                    # Find safe newest
                    safe_ver = curr_ver
                    version_ages = []
                    for v, fls in releases.items():
                        if not fls or any(x in v.lower() for x in ["a", "b", "rc", "dev"]):
                            continue
                        up_str = None
                        for fl in fls:
                            if "upload_time_iso_8601" in fl:
                                up_str = fl["upload_time_iso_8601"]
                                break
                        if up_str:
                            try:
                                v_dt = parse_pypi_date(up_str)
                                v_age_h = (now - v_dt).total_seconds() / 3600.0
                                if v_age_h >= quarantine_hours:
                                    version_ages.append((v, v_dt))
                            except Exception:
                                pass
                    if version_ages:
                        version_ages.sort(key=lambda x: x[1], reverse=True)
                        safe_ver = version_ages[0][0]
                        
                    if safe_ver != curr_ver or is_quarantined:
                        outdated.append({
                            "name": name,
                            "installed": curr_ver,
                            "safe": safe_ver,
                            "latest": latest_ver,
                            "quarantined": is_quarantined,
                            "age": age_h
                        })
                except Exception:
                    pass
                    
    spinner.stop(success=True, finish_message="Escaneo de versiones completado.")
    
    if not outdated:
        log_success("¡Todos tus paquetes instalados están en la versión segura más reciente!")
        sys.exit(0)
        
    print(f"\n{Colors.BOLD}{Colors.CYAN}┌──────────────────────┬─────────────┬─────────────┬──────────────────────────┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│ Paquete              │ Instalado   │ Seguro (Sú) │ Última PyPI (Cuarentena) │{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}├──────────────────────┼─────────────┼─────────────┼──────────────────────────┤{Colors.RESET}")
    
    for o in outdated:
        name_p = o["name"].ljust(20)
        inst_p = o["installed"].ljust(11)
        safe_p = o["safe"].ljust(11)
        
        if o["quarantined"]:
            latest_str = f"{o['latest']} ({Colors.YELLOW}CUARENTENA - {o['age']:.1f}h{Colors.RESET})"
        else:
            latest_str = f"{o['latest']} (Bypass)"
            
        latest_p = latest_str.ljust(35) # Adjusted for ANSI color offset
        
        print(f"│ {Colors.BOLD}{Colors.CYAN}{name_p}{Colors.RESET} │ {Colors.GREEN}{inst_p}{Colors.RESET} │ {Colors.GREEN}{safe_p}{Colors.RESET} │ {latest_p} │")
        
    print(f"{Colors.BOLD}{Colors.CYAN}└──────────────────────┴─────────────┴─────────────┴──────────────────────────┘{Colors.RESET}")
    print(f"  {Colors.BOLD}Total actualizaciones disponibles:{Colors.RESET} {Colors.GREEN}{len(outdated)}{Colors.RESET}\n")

def handle_prune():
    pyckage_path = find_pyckage_json()
    if not pyckage_path.is_file():
        log_error("pyckage.json no encontrado.")
        sys.exit(1)
        
    data = load_pyckage_json(pyckage_path)
    core = data.get("dependencies", {}).keys()
    dev = data.get("devDependencies", {}).keys()
    
    direct_deps = set(k.lower() for k in core) | set(k.lower() for k in dev)
    
    venv_path = find_venv_root()
    installed = get_installed_packages(venv_path)
    
    if not installed:
        log_warning("No hay paquetes en el entorno .venv.")
        sys.exit(0)
        
    # Recursive calculation of transitive dependencies
    import importlib.metadata
    required_set = set(direct_deps)
    
    def add_requirements(pkg_name):
        try:
            reqs = importlib.metadata.requires(pkg_name)
            if reqs:
                for r in reqs:
                    match = re.match(r"^([a-zA-Z0-9_\-]+)", r)
                    if match:
                        sub_pkg = match.group(1).lower()
                        if sub_pkg not in required_set:
                            required_set.add(sub_pkg)
                            add_requirements(sub_pkg)
        except Exception:
            pass
            
    for d in list(required_set):
        add_requirements(d)
        
    # Identify packages to prune
    to_prune = []
    for pkg in installed:
        name_lower = pkg["name"].lower()
        if name_lower not in required_set:
            to_prune.append(pkg["name"])
            
    if not to_prune:
        log_success("El entorno virtual (.venv) está perfectamente limpio. Sin residuos huérfanos.")
        sys.exit(0)
        
    print(f"\n{Colors.YELLOW}⚠ RESIDUOS Y PAQUETES HUÉRFANOS DETECTADOS EN .venv:{Colors.RESET}")
    for p in to_prune:
        print(f"  {Colors.RED}- {p}{Colors.RESET}")
        
    print()
    confirm = ask_confirm("¿Estás seguro de que deseas purgar y desinstalar estos paquetes huérfanos?", default=False)
    if confirm:
        success = uninstall_packages(to_prune, venv_path)
        if success:
            generate_lockfile(venv_path)
            log_success("¡Limpieza y purgado del entorno completados con éxito!")
    else:
        log_info("Pruning cancelado.")

def handle_clean():
    """
    Cleans Python caches, ruff caches, pytest caches, build debris.
    Prints MBs saved and count of files deleted.
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}⚡ INICIANDO RECOLECCIÓN DE BASURA Y LIMPIEZA...{Colors.RESET}")
    cwd = Path(".").resolve()
    
    targets = [
        "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist", "*.egg-info"
    ]
    
    file_extensions = [
        "*.pyc", "*.pyo", "*.pyd"
    ]
    
    deleted_dirs = 0
    deleted_files = 0
    freed_bytes = 0
    
    # 1. Clean folders
    for target in targets:
        for p in list(cwd.rglob(target)):
            if ".venv" in p.parts:
                continue
            try:
                if p.is_dir():
                    for root, _, files in os.walk(p):
                        for f in files:
                            fp = Path(root) / f
                            if fp.is_file():
                                freed_bytes += fp.stat().st_size
                    shutil.rmtree(p)
                    deleted_dirs += 1
                else:
                    freed_bytes += p.stat().st_size
                    p.unlink()
                    deleted_files += 1
            except Exception:
                pass
                
    # 2. Clean explicit file wildcards
    for ext in file_extensions:
        for p in list(cwd.rglob(ext)):
            if ".venv" in p.parts:
                continue
            try:
                freed_bytes += p.stat().st_size
                p.unlink()
                deleted_files += 1
            except Exception:
                pass
                
    freed_mb = round(freed_bytes / (1024 * 1024), 2)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}│                PyCk INFORME DE LIMPIEZA                │{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}├────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"  {Colors.BOLD}Directorios eliminados:{Colors.RESET}  {Colors.CYAN}{deleted_dirs}{Colors.RESET}")
    print(f"  {Colors.BOLD}Archivos purgados:{Colors.RESET}       {Colors.CYAN}{deleted_files}{Colors.RESET}")
    print(f"  {Colors.BOLD}Espacio total liberado:{Colors.RESET}  {Colors.GREEN}{freed_mb} MB{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")

def handle_lock():
    """
    Manually regenerates pyckage.lock with PyPI digests validation.
    """
    venv_path = find_venv_root()
    if not venv_path.exists():
        log_error(".venv no detectado. Corre 'pym install' para inicializar tu espacio primero.")
        sys.exit(1)
        
    spinner = Spinner("Regenerando y recalculando firmas del lockfile (pyckage.lock)...")
    spinner.start()
    try:
        generate_lockfile(venv_path)
        spinner.stop(success=True, finish_message="Archivo pyckage.lock recalculado y firmado criptográficamente.")
    except Exception as e:
        spinner.stop(success=False, finish_message=f"Fallo al firmar lockfile: {e}")
        sys.exit(1)

def handle_update(args):
    """
    Performs quarantine-safe upgrades of all packages or a designated package.
    """
    venv_path = find_venv_root()
    if not venv_path.exists():
        log_error(".venv no detectado.")
        sys.exit(1)
        
    pyckage_path = find_pyckage_json()
    if not pyckage_path.is_file():
        log_error("pyckage.json no encontrado.")
        sys.exit(1)
        
    config = load_global_config()
    quarantine_hours = config.get("quarantineHours", 72)
    
    from pym.security import find_latest_safe_version
    
    data = load_pyckage_json(pyckage_path)
    core = data.get("dependencies", {})
    dev = data.get("devDependencies", {})
    
    force_latest = "--force-latest" in args or "--latest" in args
    clean_args = [a for a in args if a not in ["--force-latest", "--latest"]]
    
    packages_to_upgrade = []
    if clean_args:
        packages_to_upgrade = [clean_args[0]]
    else:
        packages_to_upgrade = list(core.keys()) + list(dev.keys())
        
    if not packages_to_upgrade:
        log_info("No hay dependencias configuradas para actualizar.")
        sys.exit(0)
        
    log_info(f"Escaneando actualizaciones seguras para: {', '.join(packages_to_upgrade)}...")
    
    upgraded_packages = []
    for pkg in packages_to_upgrade:
        safe_ver = find_latest_safe_version(pkg, quarantine_hours) if not force_latest else None
        if safe_ver:
            upgraded_packages.append(f"{pkg}=={safe_ver}")
        else:
            upgraded_packages.append(pkg)
            
    is_dev = False
    if clean_args and clean_args[0] in dev:
        is_dev = True
        
    success = install_packages(upgraded_packages, venv_path, dev=is_dev, force_latest=force_latest)
    if success:
        update_pyckage_dependencies(upgraded_packages, venv_path, dev=is_dev)
        generate_lockfile(venv_path)
        log_success("¡Actualización de dependencias completada de forma segura!")
        run_auto_audit_if_enabled()
    else:
        log_error("Fallo al procesar actualizaciones.")
        sys.exit(1)

def handle_config(args):
    """
    Interactive and CLI global configuration controller.
    """
    if not args:
        log_error("Por favor especifica una operación de configuración. Ejemplos:")
        print(f"  {Colors.CYAN}pym config show{Colors.RESET}           : Muestra la configuración actual")
        print(f"  {Colors.CYAN}pym config set <key> <val>{Colors.RESET} : Modifica una preferencia")
        print(f"  {Colors.CYAN}pym config get <key>{Colors.RESET}       : Lee una preferencia")
        print(f"  {Colors.CYAN}pym config wizard{Colors.RESET}         : Re-lanza el asistente interactivo")
        sys.exit(1)
        
    sub = args[0].lower()
    
    if sub in ("show", "list"):
        config = load_global_config()
        print(f"\n{Colors.CYAN}{Colors.BOLD}┌────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}│             PyCk CONFIGURACIÓN GLOBAL                  │{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}")
        for k, v in config.items():
            print(f"  {Colors.BOLD}{k:<18}:{Colors.RESET} {Colors.GREEN}{v}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}└────────────────────────────────────────────────────────┘{Colors.RESET}\n")
        
    elif sub == "get":
        if len(args) < 2:
            log_error("Por favor especifica la clave a consultar. Ejemplo: pym config get quarantineHours")
            sys.exit(1)
        key = args[1]
        config = load_global_config()
        if key in config:
            print(config[key])
        else:
            log_error(f"Clave de configuración desconocida: '{key}'")
            sys.exit(1)
            
    elif sub == "set":
        if len(args) < 3:
            log_error("Uso: pym config set <key> <value>")
            sys.exit(1)
        key = args[1]
        val_str = args[2]
        
        config = load_global_config()
        if key not in config:
            log_error(f"Clave de configuración desconocida: '{key}'")
            print(f"\nClaves válidas: {', '.join(config.keys())}")
            sys.exit(1)
            
        orig_val = config[key]
        if isinstance(orig_val, bool):
            val = val_str.lower() in ("true", "1", "yes", "y", "on")
        elif isinstance(orig_val, int):
            try:
                val = int(val_str)
            except ValueError:
                log_error(f"Valor no válido para {key}. Debe ser un entero.")
                sys.exit(1)
        else:
            val = val_str
            
        config[key] = val
        if key == "sandboxOption":
            config["strictMode"] = (val == "A")
            
        save_global_config(config)
        log_success(f"Configuración actualizada: {Colors.BOLD}{key}{Colors.RESET} = {Colors.GREEN}{val}{Colors.RESET}")
        
    elif sub in ("wizard", "setup"):
        if CONFIG_FILE.is_file():
            try:
                CONFIG_FILE.unlink()
            except Exception:
                pass
        from pym.config import ensure_global_setup
        ensure_global_setup()
        
    else:
        log_error(f"Subcomando de configuración desconocido: '{sub}'.")
        sys.exit(1)

def main():
    try:
        # Iniciar validador y Setup Wizard inicial si no existe configuración global
        from pym.config import ensure_global_setup
        ensure_global_setup()
        
        if len(sys.argv) < 2:
            show_help()
            sys.exit(0)
            
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]
        
        if cmd == "init":
            handle_init(args)
        elif cmd in ("install", "i"):
            handle_install(args)
        elif cmd in ("uninstall", "remove", "un"):
            handle_uninstall(args)
        elif cmd in ("run", "r"):
            handle_run(args)
        elif cmd == "code":
            handle_code(args)
        elif cmd == "shell":
            venv_path = find_venv_root()
            spawn_subshell(venv_path)
        elif cmd == "info":
            handle_info()
        elif cmd == "list":
            handle_list(args)
        elif cmd == "audit":
            handle_audit()
        elif cmd == "outdated":
            handle_outdated()
        elif cmd == "prune":
            handle_prune()
        elif cmd == "clean":
            handle_clean()
        elif cmd == "lock":
            handle_lock()
        elif cmd in ("update", "upgrade"):
            handle_update(args)
        elif cmd == "config":
            handle_config(args)
        elif cmd in ("help", "--help", "-h"):
            show_help()
        else:
            log_error(f"Unknown command: '{cmd}'. Enter 'pym --help' to see available operations.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print()
        log_error("Operación abortada por el usuario.")
        sys.exit(130)
    except Exception as e:
        verbose = "--verbose" in sys.argv or "--debug" in sys.argv or "-v" in sys.argv
        print(f"\n{Colors.RED}{Colors.BOLD}✖ ERROR INESPERADO DE SISTEMA{Colors.RESET}")
        print(f"  Detalle: {Colors.YELLOW}{e}{Colors.RESET}")
        if verbose:
            import traceback
            print(f"\n{Colors.GRAY}{'-'*60}")
            traceback.print_exc()
            print(f"{'-'*60}{Colors.RESET}")
        else:
            print(f"\n  {Colors.GRAY}Para ver el traceback completo del error, ejecuta tu comando con la bandera {Colors.RESET}{Colors.BOLD}--verbose{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
