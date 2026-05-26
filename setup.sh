#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo -e "\033[1;36m┌────────────────────────────────────────────────────────┐\033[0m"
echo -e "\033[1;36m│          PyCk Shell Onboarding & Installer             │\033[0m"
echo -e "\033[1;36m└────────────────────────────────────────────────────────┘\033[0m"

# Find Python executable
if command -v python3 &>/dev/null; then
    PYTHON_EXE="python3"
elif command -v python &>/dev/null; then
    PYTHON_EXE="python"
else
    echo -e "\033[1;31m✖ Error: Python is not installed on this system. Please install Python 3.8+ first.\033[0m"
    exit 1
fi

# Run the python setup script
$PYTHON_EXE setup.py
