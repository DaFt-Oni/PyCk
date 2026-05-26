# PyCk Premium Windows CLI Installer (PowerShell)
# Invocación remota recomendada: 
#   irm https://raw.githubusercontent.com/usuario/PyCk/main/bin/install_cli.ps1 | iex

$ErrorActionPreference = "Stop"
Write-Host "⚡ Iniciando Instalador Web de PyCk (CLI) para Windows..." -ForegroundColor Cyan

# 1. Configurar directorios del sistema
$PyCkDir = Join-Path $HOME ".pyck"
$BinDir = Join-Path $PyCkDir "bin"

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
}

# 2. Localizar o simular descarga del ejecutable compilado pym.exe
# En un entorno de producción, esto descargaríade una release de GitHub:
# Invoke-WebRequest -Uri "https://github.com/usuario/PyCk/releases/latest/download/pym.exe" -OutFile "$BinDir\pym.exe"
$SourceExe = "$PSScriptRoot\v20260518_151858\pym.exe"
if (-not (Test-Path $SourceExe)) {
    # Fallback si se ejecuta de forma aislada: busca cualquier ejecutable compilado en subcarpetas
    $FoundExes = Get-ChildItem -Path "$PSScriptRoot" -Filter "pym.exe" -Recurse
    if ($FoundExes.Count -gt 0) {
        $SourceExe = $FoundExes[0].FullName
    }
}

if (Test-Path $SourceExe) {
    Write-Host "✔ Copiando ejecutable pym.exe compilado hacia $BinDir..." -ForegroundColor Green
    Copy-Item -Path $SourceExe -Destination "$BinDir\pym.exe" -Force
} else {
    Write-Host "⚠ No se encontró un ejecutable pre-compilado en local. Creando lanzador de script Python..." -ForegroundColor Yellow
    # Si no hay exe, creamos un archivo batch pym.bat en el PATH que lanza python -m pym.cli
    $BatContent = "@echo off`r`npython -m pym.cli %*"
    Set-Content -Path "$BinDir\pym.bat" -Value $BatContent -Force
}

# 3. Registro persistente en el PATH del usuario (Registro de Windows)
Write-Host "✔ Registrando PyCk de forma persistente en tu PATH de usuario..." -ForegroundColor Green
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    $NewPath = "$UserPath;$BinDir"
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    $env:PATH = "$env:PATH;$BinDir"
    Write-Host "✔ PATH de usuario actualizado en el Registro con éxito." -ForegroundColor Green
} else {
    Write-Host "ℹ PyCk ya se encuentra registrado en tu PATH de usuario." -ForegroundColor Gray
}

# Broadcast del cambio de entorno para que las terminales lo capten sin reiniciar
$Signature = '[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);'
$SendNotifyMessage = Add-Type -MemberDefinition $Signature -Name "Win32SendMessage" -Namespace "Win32" -PassThru
$Result = [IntPtr]::Zero
$SendNotifyMessage::SendMessageTimeout([IntPtr]0xffff, 0x001a, [IntPtr]::Zero, "Environment", 2, 5000, [ref]$Result) | Out-Null

Write-Host "✔ Cambios de variables de entorno notificados al sistema." -ForegroundColor Green

# 4. Iniciar automáticamente el Asistente de Configuración Global Interactiva (Vite-style)
Write-Host "`n⚡ Lanzando asistente de configuración inicial interactivo..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

if (Test-Path "$BinDir\pym.exe") {
    & "$BinDir\pym.exe" info
} else {
    python -m pym.cli info
}
