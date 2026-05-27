#!/usr/bin/env bash

# PyCk Premium Unix/macOS CLI Installer
# Remote invocation recommendation:
#   curl -fsSL https://raw.githubusercontent.com/user/PyCk/main/bin/install_cli.sh | bash

set -e

echo -e "\033[96m⚡ Iniciando Instalador Web de PyCk (CLI) para Unix/macOS...\033[0m"

PYCK_DIR="$HOME/.pyck"
BIN_DIR="$PYCK_DIR/bin"

# 1. Create directory structure
mkdir -p "$BIN_DIR"

# 2. Setup symlink or runner script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LATEST_DIR=$(ls -d "$SCRIPT_DIR"/v* 2>/dev/null | sort -r | head -n 1 || true)

BINARY_COPIED=false
if [ -n "$LATEST_DIR" ] && [ -f "$LATEST_DIR/pym" ]; then
    echo -e "\033[92m✔ Copiando binario compilado pym desde $LATEST_DIR...\033[0m"
    cp "$LATEST_DIR/pym" "$BIN_DIR/pym"
    chmod +x "$BIN_DIR/pym"
    BINARY_COPIED=true
fi

if [ "$BINARY_COPIED" = false ]; then
    # Fallback si se ejecuta de forma aislada: busca cualquier ejecutable compilado en subcarpetas
    FOUND_EXE=$(find "$SCRIPT_DIR" -type f -name "pym" | grep -v "/bin/pym" | head -n 1 || true)
    if [ -n "$FOUND_EXE" ] && [ -f "$FOUND_EXE" ]; then
        echo -e "\033[92m✔ Copiando binario compilado pym encontrado en $FOUND_EXE...\033[0m"
        cp "$FOUND_EXE" "$BIN_DIR/pym"
        chmod +x "$BIN_DIR/pym"
        BINARY_COPIED=true
    fi
fi

if [ "$BINARY_COPIED" = false ]; then
    echo -e "\033[93m⚠ No se encontró un binario compilado pym. Creando lanzador de script Python...\033[0m"
    cat << 'EOF' > "$BIN_DIR/pym"
#!/usr/bin/env bash
python3 -m pym.cli "$@"
EOF
    chmod +x "$BIN_DIR/pym"
fi

echo -e "\033[92m✔ Lanzador ejecutable pym instalado en $BIN_DIR/pym.\033[0m"

# 3. Add to shell configuration persistently
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_CONFIG="$HOME/.profile"
fi

if [ -n "$SHELL_CONFIG" ]; then
    if ! grep -q "$BIN_DIR" "$SHELL_CONFIG"; then
        echo -e "\n# PyCk Package Manager PATH Registration" >> "$SHELL_CONFIG"
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$SHELL_CONFIG"
        echo -e "\033[92m✔ PATH agregado de forma persistente a $SHELL_CONFIG.\033[0m"
    else
        echo -e "\033[90mℹ PyCk ya se encuentra registrado en tu PATH en $SHELL_CONFIG.\033[0m"
    fi
else
    echo -e "\033[93m⚠ No se pudo detectar un archivo de configuración de terminal compatible (.bashrc/.zshrc). Agrega $BIN_DIR a tu PATH manualmente.\033[0m"
fi

# 4. Trigger Configuration Wizard
echo -e "\033[96m⚡ Lanzando el asistente de configuración interactivo...\033[0m"
sleep 1

export PATH="$PATH:$BIN_DIR"
if [ -x "$BIN_DIR/pym" ]; then
    "$BIN_DIR/pym" info || true
else
    python3 -m pym.cli info || true
fi
