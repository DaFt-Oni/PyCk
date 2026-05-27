# PyCk Windows CLI Installer (PowerShell)
# Recommended remote invocation: 
#   irm https://raw.githubusercontent.com/usuario/PyCk/main/bin/install_cli.ps1 | iex

$ErrorActionPreference = "Stop"
Write-Host "[INIT] Iniciando Instalador Web de PyCk (CLI) para Windows..." -ForegroundColor Cyan

# 1. Setup system directories
$PyCkDir = Join-Path $HOME ".pyck"
$BinDir = Join-Path $PyCkDir "bin"

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
}

# 2. Locate or simulate downloading the compiled executable pym.exe
# In production, this would download from a GitHub release:
# Invoke-WebRequest -Uri "https://github.com/usuario/PyCk/releases/latest/download/pym.exe" -OutFile "$BinDir\pym.exe"
$LatestDir = Get-ChildItem -Path "$PSScriptRoot" -Directory -Filter "v*" | Sort-Object Name -Descending | Select-Object -First 1
if ($LatestDir) {
    $SourceExe = Join-Path $LatestDir.FullName "pym.exe"
} else {
    $SourceExe = ""
}
if (-not (Test-Path $SourceExe)) {
    # Fallback if executed standalone: scan subdirectories for any compiled pym.exe
    $FoundExes = Get-ChildItem -Path "$PSScriptRoot" -Filter "pym.exe" -Recurse
    if ($FoundExes.Count -gt 0) {
        $SourceExe = $FoundExes[0].FullName
    }
}

if (Test-Path $SourceExe) {
    Write-Host "[SUCCESS] Copiando ejecutable pym.exe compilado hacia $BinDir..." -ForegroundColor Green
    Copy-Item -Path $SourceExe -Destination "$BinDir\pym.exe" -Force
} else {
    Write-Host "[WARN] No se encontro un ejecutable pre-compilado en local. Creando lanzador de script Python..." -ForegroundColor Yellow
    # If no exe, we create a batch file pym.bat in PATH pointing to python -m pym.cli
    $BatContent = "@echo off`r`npython -m pym.cli %*"
    Set-Content -Path "$BinDir\pym.bat" -Value $BatContent -Force
}

# 3. Persistent user PATH registration (Windows Registry)
Write-Host "[INFO] Registrando PyCk de forma persistente en tu PATH de usuario..." -ForegroundColor Green
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    $NewPath = "$UserPath;$BinDir"
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    $env:PATH = "$env:PATH;$BinDir"
    Write-Host "[SUCCESS] PATH de usuario actualizado en el Registro con exito." -ForegroundColor Green
} else {
    Write-Host "[INFO] PyCk ya se encuentra registrado en tu PATH de usuario." -ForegroundColor Gray
}

# Broadcast environment changes to system without rebooting
$Signature = '[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);'
$SendNotifyMessage = Add-Type -MemberDefinition $Signature -Name "Win32SendMessage" -Namespace "Win32" -PassThru
$Result = [IntPtr]::Zero
$SendNotifyMessage::SendMessageTimeout([IntPtr]0xffff, 0x001a, [IntPtr]::Zero, "Environment", 2, 5000, [ref]$Result) | Out-Null

Write-Host "[SUCCESS] Cambios de variables de entorno notificados al sistema." -ForegroundColor Green

# 4. Trigger Configuration Wizard
Write-Host "`n[INIT] Lanzando asistente de configuracion inicial interactivo..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

if (Test-Path "$BinDir\pym.exe") {
    & "$BinDir\pym.exe" info
} else {
    python -m pym.cli info
}
