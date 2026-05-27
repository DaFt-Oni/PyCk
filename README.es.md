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

**Gestor de Proyectos y Entornos de Ejecución de Python Moderno y Ultra Rápido (Seguro por Defecto y Zero-Trust)**

[![Versión de Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Soporte de Plataformas](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#)
[![Motor de Dependencias](https://img.shields.io/badge/engine-uv-violet.svg)](https://github.com/astral-sh/uv)
[![Compilación Standalone](https://img.shields.io/badge/bundler-pyinstaller-orange.svg)](#)

---

### Idioma / Language
*   **Español**: Estás leyendo la versión en español.
*   **English**: Read the documentation in English: [README.md (English Version)](./README.md)

---

## Tabla de Contenidos
1. [Descripción General](#descripción-general)
2. [Arquitectura de Seguridad "Secure-by-Default" (Zero-Trust)](#arquitectura-de-seguridad-secure-by-default-zero-trust)
   - [Cuarentena de 72 Horas para Versiones](#1-cuarentena-de-72-horas-para-versiones)
   - [Consentimiento de Scripts y Análisis de Riesgo Estático](#2-consentimiento-de-scripts-y-análisis-de-riesgo-estático)
   - [Sandbox Avanzado de Procesos](#3-sandbox-avanzado-de-procesos)
3. [Características Principales](#características-principales)
4. [Arquitectura y Componentes](#arquitectura-y-componentes)
5. [Instalación y Configuración](#instalación-y-configuración)
   - [Método 1: Instalador de una Línea desde Web (Recomendado)](#método-1-instalador-de-una-línea-desde-web-recomendado)
   - [Método 2: Instalación Local Interactiva (Desde el Código)](#método-2-instalación-local-interactiva-desde-el-código)
   - [Método 3: Compilación con Ejecutable Standalone](#método-3-compilación-con-ejecutable-standalone)
6. [Asistente de Configuración Global de Primera Ejecución](#asistente-de-configuración-global-de-primera-ejecución)
7. [Referencia de Comandos CLI](#referencia-de-comandos-cli)
   - [pym init](#1-pym-init)
   - [pym install](#2-pym-install--pym-i)
   - [pym uninstall](#3-pym-uninstall--pym-remove--pym-un)
   - [pym run](#4-pym-run--pym-r)
   - [pym audit](#5-pym-audit)
   - [pym outdated](#6-pym-outdated)
   - [pym prune](#7-pym-prune)
   - [pym clean](#8-pym-clean-nuevo)
   - [pym lock](#9-pym-lock-new)
   - [pym update](#10-pym-update-new)
   - [pym code](#11-pym-code)
   - [pym shell](#12-pym-shell)
   - [pym info](#13-pym-info)
   - [pym list](#14-pym-list)
8. [Especificación de Archivos de Configuración](#especificación-de-archivos-de-configuración)
   - [pyckage.json](#pyckagejson)
   - [pyckage.lock](#pyckagelock)
   - [~/.pyck/config.json](#pyckconfigjson)

---

## Descripción General

PyCk es una capa elegante y de alto rendimiento construida sobre los entornos virtuales estándar de Python y el motor de dependencias ultra rápido uv basado en Rust.

Al introducir un paradigma de gestión declarativo al estilo de npm en Python, utiliza un archivo de configuración central `pyckage.json` para gestionar metadatos, dependencias, dependencias de desarrollo (`devDependencies`) y scripts personalizados bajo un único comando ejecutable global: `pym` (Python Manager).

---

## Arquitectura de Seguridad "Secure-by-Default" (Zero-Trust)

PyCk está diseñado bajo la filosofía **Secure-by-Default (Seguro por Defecto)**. La seguridad siempre tiene prioridad sobre la conveniencia, minimizando la confianza implícita y requiriendo acciones explícitas para cualquier operación de sistema potencialmente peligrosa.

### 1. Cuarentena de 72 Horas para Versiones
Para mitigar typosquatting, secuestro de cuentas, malware de día cero y supply chain attacks:
*   **Instalación Restrictiva por Defecto**: Por defecto, PyCk **se negará** a instalar automáticamente cualquier versión de paquete publicada en PyPI en las últimas **72 horas**.
*   **Rollback Estable Automático**: Si la última versión está en cuarentena, PyCk resuelve y congela de manera automática la última versión segura que haya superado el límite de 72 horas.
*   **Banderas de Salto (Bypass)**: Los usuarios avanzados pueden forzar la instalación de la versión más reciente usando los flags `--latest`, `--force-latest` o `--bleeding-edge`.

### 2. Consentimiento de Scripts y Análisis de Riesgo Estático
PyCk posee un motor de evaluación estática que intercepta los scripts antes de ejecutarse:
*   **Clasificación de Amenazas**: Evalúa los comandos buscando comportamientos sospechosos (ej. tuberías/pipes, llamadas directas a binarios, rutas absolutas del sistema operativo, saltos de ruta `..`, herramientas de red como `curl`/`wget` o comandos de borrado destructivo).
*   **Hermosas Tarjetas de Alerta**: Muestra una ficha de seguridad detallando el script, advertencias encontradas, nivel de riesgo (**BAJO**, **MEDIO**, **ALTO**) y la política de sandbox activa.
*   **Aprobación Explícita**: Solicita confirmación explícita mediante `[y/N]` antes de ejecutar.
*   **Bypass**: Se puede saltar la confirmación con los flags `-y` / `--yes` / `--force-scripts`.

### 3. Sandbox Avanzado de Procesos
Los scripts se ejecutan dentro de subprocesos con aislamiento lógico:
*   **Limpieza de Entorno (Environment Scrubbing)**: Purga variables del sistema, tokens, llaves de AWS, claves de bases de datos y contraseñas de la memoria del subproceso, alimentando solo rutas esenciales a menos que se declare `--allow-env`.
*   **Aislamiento de Red**: Inyecta variables de proxy local nulas (`http://127.0.0.1:99999`) para desactivar de forma segura sockets salientes estándar, evitando fuga de datos o descargas maliciosas a menos que se use `--allow-network`.
*   **Virtualización de Archivos**: Redirecciona el directorio raíz de usuario (`HOME` / `USERPROFILE`) a `.venv/.sandbox_home` protegiendo llaves SSH, claves de AWS y cookies de navegación a menos que se especifique `--allow-fs`.

---

## Características Principales

*   **Salvaguardas de Seguridad Zero-Trust**: Aislamiento por Sandbox, cuarentena de 72h, validaciones hash SHA256 criptográficas en lockfile y auditoría estática.
*   **Asistente Global Interactivo Inicial**: Configura tus preferencias de Sandbox, datos predeterminados de autor, licencias predilectas, motores uv/pip y piloto automático de auditoría de forma guiada en tu primera ejecución.
*   **Rendimiento Rápido con UV**: Sincronizaciones veloces hasta 100 veces más rápidas que pip clásico.
*   **Gestión Unificada Declarativa**: Archivo simple `pyckage.json` y lockfile determinista criptográfico `pyckage.lock`.
*   **Tableros Modernos en Consola**: Hermosas pantallas de resumen con colores de consola y tablas ASCII limpias.

---

## Arquitectura y Componentes

```
   ┌────────────────────────────────────────────────────────┐
   │                       pym CLI                          │
   └────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
   │Estado Proyecto │ │  Sandbox e IU  │ │ Seguridad y    │
   │ pyckage.json   │ │ Entorno Aislado│ │ Cuarentena     │
   └────────────────┘ └────────────────┘ └────────────────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │           Entorno Virtual Local Activo (.venv)         │
   └────────────────────────────────────────────────────────┘
```

---

## Métodos de Instalación y Configuración

PyCk ofrece múltiples rutas de despliegue diseñadas para desarrolladores locales, ingenieros de DevOps y administradores de sistemas que gestionan servidores de producción seguros y aislados.

---

### Método 1: Instalador de una Línea desde Web (En Línea / Interactivo)
*   **Ideal para**: Instalaciones locales rápidas con conectividad a Internet.
*   **Descripción**: Descarga la última versión, registra `pym` de forma persistente en tu `PATH` de variables de entorno de usuario, e inicia el Asistente de Configuración (Setup Wizard) automáticamente.
*   **Windows (PowerShell)**:
    ```powershell
    irm https://raw.githubusercontent.com/DaFt-Oni/PyCk/main/bin/install_cli.ps1 | iex
    ```
*   **Unix / macOS (Shell)**:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/DaFt-Oni/PyCk/main/bin/install_cli.sh | bash
    ```

---

### Método 2: Instalador Local / Fuera de Línea Standalone (Cero Dependencias)
*   **Ideal para**: Servidores corporativos aislados (air-gapped), aprovisionamientos automáticos headless (Ansible, Chef) y entornos de alta seguridad donde la ejecución directa de binarios compilados para escribir en el sistema está restringida.
*   **Paso 1**: Compila el ejecutable standalone usando la suite de empaquetado:
    ```bash
    python build_exe.py --include-installer
    ```
    *(Esto compila un binario autoinstalable `pym` y genera un script asistente de instalación en texto plano con cero dependencias llamado `install.py` justo al lado en la carpeta `bin/v[timestamp]/`)*.
*   **Paso 2**: Elige uno de los modelos de despliegue:
    *   **Método 2.1: Instalador Standalone Automatizable (`install.py`)**:
        Copia la carpeta generada `bin/v[timestamp]/` a tu servidor objetivo y ejecuta el instalador:
        ```bash
        python install.py
        ```
        *(Este script de Python en texto plano realiza el pre-aprovisionamiento de carpetas de manera limpia, copia el binario de forma permanente, registra las variables de PATH del usuario de forma persistente y guarda tus preferencias globales. Los equipos de auditoría de seguridad corporativos pueden inspeccionar visualmente `install.py` antes de correrlo)*.
    *   **Método 2.2: Autoinstalación Directa de Ejecutable**:
        Simplemente copia el ejecutable compilado (`pym.exe` o `pym`) a tu máquina y ejecútalo directamente en la terminal. Como no existe archivo de configuración previa, ¡limpiará la pantalla y lanzará el asistente interactivo en su primera corrida!

---

### Método 3: Instalación de Desarrollo (Desde el Código Fuente)
*   **Ideal para**: Colaboradores y programadores trabajando directamente en el código de PyCk.
*   **Acción**: Clona el repositorio y ejecuta los instaladores nativos en la raíz:
    *   **Opción A: Instalación Universal Python**: `python setup.py`
    *   **Opción B: Instalador de Windows**: `setup.bat`
    *   **Opción C: Script de Unix Shell**: `sh setup.sh`

---

### Método 4: Compilador Standalone Automático (`build_exe.py`)
Para empaquetar tú mismo PyCk en un binario ejecutable único de grado empresarial:
```bash
python build_exe.py [opciones]
```
**Opciones y Argumentos del Compilador**:
*   `--include-installer`: Genera el instalador interactivo offline `install.py` al lado del binario en la carpeta de versión.
*   `--target {windows,linux}`: Fuerza la compilación del OS objetivo. Si compilas para Linux en Windows, busca WSL o levanta un contenedor ligero Docker de `python:3.11-slim` para compilar un binario Linux nativo al vuelo de manera transparente.

---

## Asistente de Configuración y Reconfiguración Global

La primera vez que corras cualquier comando de PyCk, si el archivo de configuración `~/.pyck/config.json` no existe, se limpiará la pantalla de la consola y arrancará un **Asistente Interactivo** (Vite-style):
1. **Directorio de Instalación Física** (Solo al ejecutar el binario standalone): Selecciona un directorio permanente para instalar `pym.exe` (por defecto `~/.pyck/bin`). El asistente copiará automáticamente el ejecutable en ejecución a esta ubicación, evitando que tu carpeta de descargas temporales contamine el PATH del sistema.
2. **Política de Sandbox**:
   *   **Opción A (Estricta - Recomendada)**: Sandbox activo para TODOS los scripts por defecto (Red, archivos y entorno virtualizados/restringidos).
   *   **Opción B (Balanceada)**: Sandbox activo solo en instalaciones y scripts con riesgos MEDIOS/ALTOS detectados.
3. **Horas de Cuarentena**: Configura el límite de horas deseadas para cuarentena (72 horas por defecto).
4. **Nombre del Autor**: Configura tu firma global como desarrollador (ej. Jane Doe) para auto-rellenar en todos tus nuevos proyectos.
5. **Licencia por Defecto**: Elige el tipo de licenciamiento predilecto (`MIT`, `Apache-2.0`, `GPL-3.0`, `Proprietary`).
6. **Motor Preferido**: Elige si prefieres usar Rust `uv` a máxima velocidad o fallback nativo `pip`.
7. **Piloto Automático de Auditorías**: Activa o desactiva la ejecución automática de auditorías (`pym audit`) después de cada instalación de paquetes exitosa.
8. **Registro en el PATH**: Te pregunta si deseas registrar de forma persistente `pym` en tu variable de entorno PATH apuntando al directorio permanente (`~/.pyck/bin`), notificando instantáneamente al sistema operativo.

### Reconfiguración Dinámica
Si mueves tu ejecutable de ubicación (ej., cambiar `pym.exe` a otra carpeta permanente) o deseas cambiar cualquiera de tus preferencias globales, puedes re-lanzar el asistente en cualquier momento:
*   **Comando Directo**: `pym setup`
*   **Subcomando de Configuración**: `pym config wizard` o `pym config setup`

> [!NOTE]
> Al correr el asistente de reconfiguración, PyCk **cargará automáticamente tu configuración actual** como valores por defecto en cada pregunta. Puedes presionar simplemente **Enter (vacío)** en cualquier pregunta (incluyendo la carpeta de instalación física) para mantener tu ajuste existente sin modificarlo.

---

## Referencia de Comandos CLI

### 1. `pym init`
Crea la estructura base de un nuevo proyecto Python. Ejecutar el comando sin argumentos inicia el asistente de configuración interactivo guiado por prompts de terminal (UI interactiva) pre-cargando tus preferencias de desarrollador.

*   **Sintaxis**: `pym init [opciones]`
*   **Ejemplo**: `pym init`

---

### 2. `pym install` | `pym i`
Sincroniza el entorno con las declaraciones o instala nuevos paquetes. Si el Piloto Automático de Auditorías está activo, ejecutará una auditoría de seguridad silenciosa al final.

*   **Sintaxis**: `pym install [paquetes...] [opciones]`
*   **Opciones**:
    | Opción / Flag | Type | Descripción |
    | :--- | :--- | :--- |
    | `-D`, `--dev` | Flag | Guarda los paquetes instalados como dependencias de desarrollo (`devDependencies`). |
    | `-g`, `--global` | Flag | Instala paquetes a nivel global en tu Python del sistema. |
    | `--latest`, `--force-latest` | Flag | Salta el filtro de cuarentena de 72 horas e instala la versión más reciente. |
*   **Ejemplo**: `pym install requests --dev`

---

### 3. `pym uninstall` | `pym remove` | `pym un`
Desinstala paquetes del entorno virtual y los remueve de las declaraciones de `pyckage.json`.

*   **Sintaxis**: `pym uninstall <paquetes...>`
*   **Ejemplo**: `pym uninstall requests`

---

### 4. `pym run` | `pym r`
Ejecuta scripts configurados en el bloque `"scripts"` de `pyckage.json` con sandbox y carga automática de `.env`.

*   **Sintaxis**: `pym run <nombre_script> [opciones]`
*   **Opciones**:
    | Opción / Flag | Tipo | Descripción |
    | :--- | :--- | :--- |
    | `--allow-network` | Flag | Permite conexiones de red salientes en el sandbox. |
    | `--allow-fs` | Flag | Permite acceso total al sistema de archivos del usuario. |
    | `--allow-env` | Flag | Permite cargar y leer todas las variables de entorno reales del sistema. |
    | `--no-sandbox` | Flag | Desactiva por completo el aislamiento del sandbox. |
    | `-y`, `--yes` | Flag | Ignora las advertencias de seguridad y bypassa la confirmación. |
*   **Ejemplo**: `pym run dev --allow-network`

---

### 5. `pym audit`
Realiza un escaneo profundo de seguridad y código en tus dependencias:
1.  **Vulnerabilidades**: Consulta registros oficiales de CVEs en PyPI buscando brechas de seguridad.
2.  **Mantenimiento**: Advierte sobre paquetes obsoletos o sin mantenimiento (>2 años sin releases).
3.  **Huérfanos**: Escanea archivos `.py` del proyecto y reporta paquetes listados en `pyckage.json` que no se estén importando en ninguna parte.

*   **Sintaxis**: `pym audit`

---

### 6. `pym outdated`
Compara las versiones de paquetes instalados contra la base de datos de PyPI para sugerir actualizaciones seguras que ya superaron el límite de cuarentena.

*   **Sintaxis**: `pym outdated`

---

### 7. `pym prune`
Mapea tus dependencias declaradas y sus dependencias transitivas para desinstalar de forma limpia cualquier paquete huérfano sobrante en tu `.venv`.

*   **Sintaxis**: `pym prune`

---

### 8. `pym clean` 
Limpia recursivamente el área de trabajo de archivos de cache y residuos de Python, Pytest, Ruff y compiladores (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `build/`, `dist/`, `.pyc`, `.pyo`, `.pyd`). Presenta una ficha detallando directorios borrados, archivos purgados y megabytes liberados.

*   **Sintaxis**: `pym clean`

---

### 9. `pym lock` 
Verifica los requerimientos y regenera manualmente el archivo `pyckage.lock`, calculando y bloqueando las firmas hash de seguridad SHA256 correspondientes a PyPI de cada paquete.

*   **Sintaxis**: `pym lock`

---

### 10. `pym update` | `pym upgrade` 
Realiza actualizaciones seguras (respetando la cuarentena de 72h) de todas tus dependencias o de un paquete específico, actualizando automáticamente el archivo `pyckage.json` y `pyckage.lock`.

*   **Sintaxis**: `pym update [nombre_paquete] [opciones]`
*   **Opciones**:
    | Opción / Flag | Tipo | Descripción |
    | :--- | :--- | :--- |
    | `--latest`, `--force-latest` | Flag | Fuerza la actualización a la versión más reciente en PyPI ignorando la cuarentena. |
*   **Ejemplo**: `pym update fastapi --force-latest`

---

### 11. `pym code`
Genera plantillas rápidas de código para endpoints FastAPI (`api`), archivos pytest (`test`) o clases Python (`class <Nombre>`).

*   **Sintaxis**: `pym code <tipo>`

---

### 12. `pym shell`
Abre una terminal interactiva pre-cargada con el entorno virtual activo.

---

### 13. `pym info`
Muestra un tablero visual con estadísticas de salud de tu proyecto actual.

---

### 14. `pym list`
Muestra una elegante tabla ASCII listando todos los paquetes activos instalados en tu `.venv` con sus respectivas clasificaciones.

---

### 15. `pym config`
Permite consultar, listar o modificar las claves de configuración global interactiva de tu usuario directamente desde la CLI.

*   **Sintaxis**: `pym config <acción> [clave] [valor]`
*   **Subcomandos**:
    *   `pym config show` / `pym config list`: Muestra una tarjeta visual de consola con todas tus preferencias actuales y sus valores.
    *   `pym config get <clave>`: Imprime el valor plano de una preferencia específica.
    *   `pym config set <clave> <valor>`: Modifica y persiste dinámicamente un valor de configuración global en `~/.pyck/config.json`.
*   **Ejemplo**: `pym config set quarantineHours 48`

---

### 16. `pym setup`
Vuelve a lanzar el Asistente de Configuración Global interactivo, permitiéndote reconfigurar las directivas de Sandbox, tiempos de cuarentena, firma de autor, licencias predilectas, motores de empaquetado, y **registrar o actualizar de forma persistente tu PATH** apuntando al directorio de instalación física del ejecutable de PyCk.

*   **Sintaxis**: `pym setup`
*   **Comportamiento**: Limpia el archivo de configuración global actual y ejecuta la inicialización completa `ensure_global_setup()` en la sesión de terminal activa.

---

## Especificación de Archivos de Configuración

### `pyckage.json`
El archivo central de configuración de tu proyecto en formato JSON.
```json
{
  "name": "mi-pyck-app",
  "version": "1.0.0",
  "description": "Una aplicación premium de Python administrada por PyCk",
  "author": "Nombre Desarrollador",
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
Archivo lock autogenerado de versiones y firmas hash SHA256 criptográficas de integridad de cada paquete. No modificar manualmente.

### `~/.pyck/config.json`
Configuración global del usuario.
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

## Licencia y Agradecimientos

Desarrollado como un paradigma moderno para aplicaciones premium de Python. Reportes de fallos y contribuciones son bienvenidos.

Todos los derechos del rápido motor de paquetes **uv** corresponden de forma exclusiva a sus creadores originales en [Astral](https://astral.sh/). Agradecemos enormemente sus excepcionales aportes open-source al ecosistema Python.