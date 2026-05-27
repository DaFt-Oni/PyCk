# PyCk (pym)

```
  _____          _____  _     
 |  __ \        |  __ \| |    
 | |__) | _   _ | |  \/| | __ 
 |  ___/ | | | || | __ | |/ / 
 | |     | |_| || |__\ \   <  
 |_|      \__, | \____/|_|\_\ 
           __/ |                      
          |___/                       
```

**Modern, Ultra-Fast Python Project Manager & Runtime Toolkit (Secure-by-Default & Zero-Trust)**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform Support](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)
[![Dependency Engine](https://img.shields.io/badge/engine-uv-violet.svg)](https://github.com/astral-sh/uv)
[![Standalone Build](https://img.shields.io/badge/bundler-pyinstaller-orange.svg)](#)

---

### Language / Idioma
*   **English**: You are reading the English version.
*   **Español**: Leer la documentación en Español: [README.es.md (Versión en Español)](./README.es.md)

---

## Table of Contents
1. [Overview](#overview)
2. [Secure-by-Default (Zero-Trust) Architecture](#secure-by-default-zero-trust-architecture)
   - [72-Hour Version Quarantine](#1-72-hour-version-quarantine)
   - [Interactive Script Consent & Static Risk Analysis](#2-interactive-script-consent--static-risk-analysis)
   - [Advanced Process Sandboxing](#3-advanced-process-sandboxing)
3. [Key Features](#key-features)
4. [Architecture & Components](#architecture--components)
5. [Installation & Setup](#installation--setup)
   - [Method 1: One-Liner Web Installer (Recommended)](#method-1-one-liner-web-installer-recommended)
   - [Method 2: Interactive Local Setup (From Source)](#method-2-interactive-local-setup-from-source)
   - [Method 3: Standalone Binary Compiler](#method-3-standalone-binary-compiler)
6. [Global First-Run Setup Wizard](#global-first-run-setup-wizard)
7. [CLI Command Reference](#cli-command-reference)
   - [pym init](#1-pym-init)
   - [pym install](#2-pym-install--pym-i)
   - [pym uninstall](#3-pym-uninstall--pym-remove--pym-un)
   - [pym run](#4-pym-run--pym-r)
   - [pym audit](#5-pym-audit)
   - [pym outdated](#6-pym-outdated)
   - [pym prune](#7-pym-prune)
   - [pym clean](#8-pym-clean-new)
   - [pym lock](#9-pym-lock-new)
   - [pym update](#10-pym-update-new)
   - [pym code](#11-pym-code)
   - [pym shell](#12-pym-shell)
   - [pym info](#13-pym-info)
   - [pym list](#14-pym-list)
8. [Configuration Files Specification](#configuration-files-specification)
   - [pyckage.json](#pyckagejson)
   - [pyckage.lock](#pyckagelock)
   - [~/.pyck/config.json](#pyckconfigjson)

---

## Overview

PyCk is an elegant, high-performance overlay on top of standard Python virtual environments and the fast Rust-powered `uv` dependency engine. 

By introducing a familiar, declarative, npm-style project management paradigm directly to Python, it uses a central `pyckage.json` configuration to track metadata, dependencies, devDependencies, and custom scripts under a single executable command: `pym` (Python Manager).

---

## Secure-by-Default (Zero-Trust) Architecture

PyCk is engineered around the **Secure-by-Default** philosophy. Security always takes priority over convenience, minimizing implicit trust and requiring explicit, intentional actions for potentially risky system operations.

### 1. 72-Hour Version Quarantine
To mitigate typosquatting, supply chain attacks, and vulnerability exploits:
*   **Default Restrictive Install**: By default, PyCk **refuses** to automatically install any package version published to PyPI within the last **72 hours**.
*   **Automatic Stable Rollback**: If the latest version is quarantined, PyCk automatically resolves and locks the newest safe version that has successfully passed the 72-hour quarantine threshold.
*   **Bypass Flags**: Advanced users can explicitly force the absolute newest release using the `--latest`, `--force-latest`, or `--bleeding-edge` flags.

### 2. Interactive Script Consent & Static Risk Analysis
PyCk contains a static risk assessment engine that intercepts scripts before execution:
*   **Threat Classification**: Evaluates commands for suspicious behaviors (e.g., shell pipings, raw binary runs, absolute path systems references, path traversals `..`, network utilities like `curl` or `wget`, destructive commands).
*   **Gorgeous Alert Cards**: Displays an information security card listing the script details, threat warnings, risk rating (**LOW**, **MEDIUM**, **HIGH**), and sandbox policies applied.
*   **Explicit Approval**: Prompts for explicit user confirmation `[y/N]`. If not approved, execution is safely cancelled.
*   **Bypass**: Can be bypassed via `-y` / `--yes` / `--force-scripts` flags.

### 3. Advanced Process Sandboxing
Spawned scripts run inside isolated environments:
*   **Environment Scrubbing**: Purges sensitive variables (system tokens, AWS keys, API keys, password caches) from subprocess memory, feeding only baseline OS paths unless `--allow-env` is declared.
*   **Network Isolation**: Injects local blocked proxy variables (`http://127.0.0.1:99999`) to safely cut out-of-bound socket connections, preventing data exfiltration or secondary payload downloads unless `--allow-network` is enabled.
*   **File System Virtualization**: Redirects home paths (`HOME` / `USERPROFILE`) to `.venv/.sandbox_home` to protect SSH keys, AWS credentials, and browser cookies from exfiltration unless `--allow-fs` is configured.

---

## Key Features

*   **Zero-Trust Security Safeguards**: Sandboxing, 72h version quarantine, cryptographic lockfile SHA256 audits, and static risk code verification.
*   **First-Run Interactive Setup Wizard**: Auto-boots to configure sandbox preferences, default developer credentials, preferred engine, and audit autopilot settings.
*   **UV-Powered Speeds**: Synced environments resolving dependencies up to 100x faster than traditional pip.
*   **Unified Declared Dependency Management**: Simple declarative `pyckage.json` and cryptographic `pyckage.lock` configurations.
*   **Sleek Console Dashboards**: Modern colorized receipt dashboards and ASCII data tables.

---

## Architecture & Components

```
   ┌────────────────────────────────────────────────────────┐
   │                       pym CLI                          │
   └────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
   │ Project State  │ │  Sandbox & UI  │ │  Security &    │
   │ ## Installation & Setup Methods

PyCk offers multiple deployment pathways tailored for local developers, DevOps engineers, and system administrators managing secure, isolated production servers.

---

### Method 1: One-Liner Web Installer (Online / Interactive)
*   **Best For**: Quick developer local installations with online connectivity.
*   **Description**: Downloads the latest release, registers `pym` persistently in your user environment variable `PATH`, and triggers the global Setup Wizard automatically.
*   **Windows (PowerShell)**:
    ```powershell
    irm https://raw.githubusercontent.com/DaFt-Oni/PyCk/main/bin/install_cli.ps1 | iex
    ```
*   **Unix / macOS (Shell)**:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/DaFt-Oni/PyCk/main/bin/install_cli.sh | bash
    ```

---

### Method 2: Standalone Local / Offline Installer (Zero-Dependency)
*   **Best For**: Air-gapped corporate servers, headless automated provisioning (Ansible, Chef), and strict security environments where executing compiled binaries directly to perform system changes is restricted.
*   **Step 1**: Compile the standalone executable using the packaging suite:
    ```bash
    python build_exe.py --include-installer
    ```
    *(This compiles a self-contained `pym` binary and generates a plain-text, zero-dependency helper installer script named `install.py` next to it under `bin/v[timestamp]/`)*.
*   **Step 2**: Choose one of the deployment models:
    *   **Method 2.1: Scripted / Auditable Installer (`install.py`)**:
        Copy the generated folder `bin/v[timestamp]/` to the target server and execute the installer:
        ```bash
        python install.py
        ```
        *(This plain-text script cleanly handles directory pre-provisioning, copies the binary, registers user PATH variables persistently, and initializes your preferences. Security compliance teams can fully inspect and audit `install.py` before execution)*.
    *   **Method 2.2: Direct Executable Self-Setup**:
        Simply copy only the compiled binary (`pym.exe` or `pym`) and execute it directly in your terminal. Since no configuration is detected, it automatically launches the Setup Wizard on its very first run!

---

### Method 3: Source-Code Developer Installation (From Source)
*   **Best For**: Contributors and developers working directly on PyCk's source code.
*   **Action**: Clone the repository and run the native installer at the root:
    *   **Option A: Universal Python Setup**: `python setup.py`
    *   **Option B: Windows Setup**: `setup.bat`
    *   **Option C: Unix Setup**: `sh setup.sh`

---

### Method 4: Standalone Compilation Suite (`build_exe.py`)
To compile PyCk into a single standalone binary yourself:
```bash
python build_exe.py [options]
```
**Compiler Arguments & Options**:
*   `--include-installer`: Generates the optional standalone `install.py` wizard next to the binary in the version folder.
*   `--target {windows,linux}`: Forces OS compilation format. If targeting Linux from a Windows machine, the compiler automatically detects WSL or launches a lightweight `python:3.11-slim` Docker container to bundle a native Linux ELF binary on the fly!

---

## Global Setup & Reconfiguration Wizard

The first time you execute any command in PyCk, if the configuration file `~/.pyck/config.json` does not exist, the console will clear, and launch a gorgeous Vite-like **Setup Wizard**:
1. **Physical Installation Directory** (Only when running the standalone binary): Select a permanent folder to install the executable `pym.exe` (defaults to `~/.pyck/bin`). The wizard will automatically copy the running binary to this location, preventing your temporary folders (like `Downloads`) from being registered in system variables.
2. **Choose Sandbox Policy**:
   *   **Option A (Strict - Recommended)**: Strict sandboxing active on ALL scripts by default. Outward network, environment variables, and file systems are virtualized/restricted.
   *   **Option B (Balanced)**: Sandbox active only on dependencies installation or scripts with MEDIUM/HIGH risk flags.
3. **Quarantine hours**: Set default package quarantine time in hours (defaults to `72` hours).
4. **Developer Author Name**: Input your global author name (e.g. Jane Doe) to pre-fill all `pym init` scaffolds.
5. **Default License**: Select your default project license (`MIT`, `Apache-2.0`, `GPL-3.0`, `Proprietary`).
6. **Preferred Engine**: Pick your default package resolver engine (`uv` for ultra-fast Rust speed vs `pip` standard native fallback).
7. **Auto-Audit Autopilot**: Enable or disable automated security audits (`pym audit`) after every package installation process.
8. **PATH Env Registration**: Offers to register `pym` persistently in your operating system's global environment `PATH` pointing to the permanent installation folder (`~/.pyck/bin`), broadcasting changes instantly across active shell sessions.

### Dynamic Reconfiguration
If you migrate your folder (e.g., moving `pym.exe` to a new directory) or want to change your settings, you can re-launch the Setup Wizard anytime:
*   **Direct Command**: `pym setup`
*   **Config Subcommand**: `pym config wizard` or `pym config setup`

> [!NOTE]
> During a reconfigure setup, PyCk **automatically loads your existing configuration** as default answers. You can simply press **Enter (empty value)** on any question (including the physical installation directory) to keep your current setting without modifying it.

---

## CLI Command Reference

### 1. `pym init`
Scaffolds a premium new Python project. Running the command without arguments launches the interactive, user-friendly setup wizard which pre-fills fields based on your global settings.

*   **Syntax**: `pym init [options]`
*   **Example**: `pym init`

---

### 2. `pym install` | `pym i`
Synchronizes the environment with declaring package specifications or installs new packages. Running this command will also launch a silent `pym audit` immediately afterward if the Auto-Audit autopilot is active in your global settings.

*   **Syntax**: `pym install [packages...] [options]`
*   **Options**:
    | Option / Flag | Type | Description |
    | :--- | :--- | :--- |
    | `-D`, `--dev` | Flag | Registers package under `devDependencies` in `pyckage.json`. |
    | `-g`, `--global` | Flag | Installs designated packages globally in system-wide Python. |
    | `--latest`, `--force-latest` | Flag | Bypasses the 72-hour package quarantine period. |
*   **Example**: `pym install requests --dev`

---

### 3. `pym uninstall` | `pym remove` | `pym un`
Removes installed packages from `.venv` and declarations in `pyckage.json`.

*   **Syntax**: `pym uninstall <packages...>`
*   **Example**: `pym uninstall requests`

---

### 4. `pym run` | `pym r`
Runs scripts defined in `pyckage.json` `"scripts"` block with automatic sandboxing and environment injection.

*   **Syntax**: `pym run <script_name> [options]`
*   **Options**:
    | Option / Flag | Type | Description |
    | :--- | :--- | :--- |
    | `--allow-network` | Flag | Grants outbound network connections in sandbox. |
    | `--allow-fs` | Flag | Grants unrestricted file system accesses. |
    | `--allow-env` | Flag | Injects all system-level environment variables. |
    | `--no-sandbox` | Flag | Disables sandboxing isolation completely. |
    | `-y`, `--yes` | Flag | Disables risk alert consent prompts. |
*   **Example**: `pym run dev --allow-network`

---

### 5. `pym audit`
Performs a deep cryptographic and programmatic audit on project dependencies:
1.  **Vulnerability Scanner**: Scans all packages against official PyPI CVE records.
2.  **Unmaintained Scanner**: Flags deprecated or abandoned packages (>2 years since last release).
3.  **Orphaned Dependency Finder**: Recursively scans your python codebase files for `import` statements and reports declared packages in `pyckage.json` that are completely unused.

*   **Syntax**: `pym audit`

---

### 6. `pym outdated`
Scans installed virtual environment packages and queries PyPI to identify newer versions available that are older than the 72-hour quarantine threshold.

*   **Syntax**: `pym outdated`

---

### 7. `pym prune`
Recursively maps direct declared dependencies and transitive requirements to wipe out any orphaned packages or debris inside `.venv`.

*   **Syntax**: `pym prune`

---

### 8. `pym clean`
Recursively cleans the project workspace directory of Python caching clutter, Pytest cache registries, Ruff lint caches, and PyInstaller build directories (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `build/`, `dist/`, `.pyc`, `.pyo`, `.pyd`). Prints a visual dashboard showing deleted files and total MBs freed up.

*   **Syntax**: `pym clean`

---

### 9. `pym lock`
Verifies dependencies requirements and manually regenerates the `pyckage.lock` file, calculating and locking down all secure SHA256 PyPI package hashes.

*   **Syntax**: `pym lock`

---

### 10. `pym update` | `pym upgrade`
Performs quarantine-safe upgrades of either all dependencies or a specific package. Resolves and locks versions that exceed the configured quarantine window (72 hours), updating both `pyckage.json` and `pyckage.lock`.

*   **Syntax**: `pym update [package_name] [options]`
*   **Options**:
    | Option / Flag | Type | Description |
    | :--- | :--- | :--- |
    | `--latest`, `--force-latest` | Flag | Forces upgrading to the absolute latest version on PyPI, bypassing quarantine. |
*   **Example**: `pym update fastapi --force-latest`

---

### 11. `pym code`
Generates boilerplate code templates for API endpoints (`api`), pytest files (`test`), or python classes (`class <Name>`).

*   **Syntax**: `pym code <type>`

---

### 12. `pym shell`
Drops you into an active, isolated terminal session initialized within the local virtual environment.

---

### 13. `pym info`
Displays a gorgeous dashboard panel showing your current project environment health.

---

### 14. `pym list`
Displays an elegant, visual ASCII table listing all packages currently active inside `.venv` along with their category (Core, Dev, Transitive).

---

### 15. `pym config`
Allows viewing, retrieving, or setting global user configuration keys dynamically from the command line interface.

*   **Syntax**: `pym config <action> [key] [value]`
*   **Subcommands**:
    *   `pym config show` / `pym config list`: Displays a visual ASCII card listing all current global configurations.
    *   `pym config get <key>`: Prints the raw value of a designated configuration key.
    *   `pym config set <key> <value>`: Updates a global preference and saves it dynamically to `~/.pyck/config.json`.
*   **Example**: `pym config set quarantineHours 48`

---

### 16. `pym setup`
Re-boots the interactive global Setup Wizard, allowing you to completely re-configure Sandbox options, quarantine times, default author details, default engines, and persistently re-register or update your system environment `PATH` pointing to the physical install directory.

*   **Syntax**: `pym setup`
*   **Behavior**: Deletes the active global configuration and triggers a fresh `ensure_global_setup()` process inside the current terminal session.

---

## Configuration Files Specification

### `pyckage.json`
The central project configuration file. Written in standard JSON.
```json
{
  "name": "my-pyck-app",
  "version": "1.0.0",
  "description": "A premium Python application managed by PyCk",
  "author": "Developer Name",
  "license": "MIT",
  "python": "^3.13",
  "engines": {
    "python": "^3.13"
  },
  "scripts": {
    "dev": "python main.py",
    "test": "pytest"
  },
  "dependencies": {
    "fastapi": "^0.110.0"
  },
  "devDependencies": {
    "pytest": "^8.1.0"
  }
}
```

### `pyckage.lock`
Autogenerated lockfile. Tracks resolved precise pinned versions of packages along with their SHA256 integrity digests. Do not modify manually.

### `~/.pyck/config.json`
Global user configuration file.
```json
{
  "quarantineHours": 72,
  "sandboxOption": "A",
  "strictMode": true,
  "defaultAuthor": "Jane Doe",
  "defaultLicense": "MIT",
  "defaultEngine": "uv",
  "autoAudit": true
}
```

---

## License & Contributions

Developed as a modern package manager paradigm for premium Python applications. Contributions, bug reports, and features are welcome.

All intellectual property rights regarding the ultra-fast **uv** packaging engine belong to and are exclusively reserved by its original creators and maintainers at [Astral](https://astral.sh/).
