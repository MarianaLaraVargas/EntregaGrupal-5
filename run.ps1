# ---- run.ps1 (Windows, v3) ----
$ErrorActionPreference = "Stop"

# Ir a la raíz del repo
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

# 0) Si no hay .env, crearlo con valores por defecto
$envPath = Join-Path $ROOT ".env"
if (-not (Test-Path $envPath)) {
@"
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=Mariana1.
DB_NAME=gym_inventory
DB_PORT=3306

HOST=127.0.0.1
PORT=8000
"@ | Out-File -FilePath $envPath -Encoding UTF8 -Force
  Write-Host "Creado .env con valores por defecto."
}

# 1) Cargar variables desde .env
Write-Host "Cargando variables desde .env..."
Get-Content $envPath | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $parts = $_ -split '=', 2
  if ($parts.Count -ge 2) {
    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"')) { $value = $value.Trim('"') }
    [Environment]::SetEnvironmentVariable($name, $value, 'Process')
  }
}

# Defaults si faltan
if (-not $env:DB_HOST) { $env:DB_HOST = "localhost" }
if (-not $env:DB_USER) { $env:DB_USER = "root" }
if (-not $env:DB_PASSWORD) { $env:DB_PASSWORD = "" }
if (-not $env:DB_NAME) { $env:DB_NAME = "gym_inventory" }
if (-not $env:DB_PORT) { $env:DB_PORT = "3306" }
if (-not $env:HOST) { $env:HOST = "127.0.0.1" }
if (-not $env:PORT) { $env:PORT = "8000" }

# 2) Verificar Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: Python no está instalado o no está en PATH. Instálalo desde https://www.python.org/downloads/"
  Read-Host "Presiona Enter para salir"
  exit 1
}

# 3) Preparar entorno virtual
Write-Host "Preparando entorno virtual..."
if (-not (Test-Path "venv")) { python -m venv venv }
. .\venv\Scripts\Activate.ps1

# 4) Instalar dependencias
Write-Host "Instalando dependencias..."
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt

# 5) Intentar localizar mysql.exe (cliente de MySQL)
function Find-MySQL {
  if (Get-Command mysql -ErrorAction SilentlyContinue) { return "mysql" }
  $candidates = @(
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Workbench 8.0\mysql.exe"
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
  return $null
}

$mysqlExe   = Find-MySQL
$schemaPath = Join-Path $ROOT "sql\schema.sql"

if ($mysqlExe) {
  Write-Host "Asegurando base de datos y schema..."
  try {
    # Construir argumentos (usar --password=... para evitar prompt)
    $mysqlArgs = @("-h", $env:DB_HOST, "-P", $env:DB_PORT, "-u", $env:DB_USER)
    if ($env:DB_PASSWORD -ne "") { $mysqlArgs += "--password=$($env:DB_PASSWORD)" }

    # Log sin exponer contraseña
    $mysqlArgsLog = $mysqlArgs | ForEach-Object { if ($_ -like "--password=*") { "--password=****" } else { $_ } }
    Write-Host ("MySQL CLI: " + $mysqlExe + " " + ($mysqlArgsLog -join " "))

    # Crear DB si no existe (sin backticks)
    & $mysqlExe @mysqlArgs -e "CREATE DATABASE IF NOT EXISTS $($env:DB_NAME);"

    # Importar schema.sql desde stdin (si existe)
    if (Test-Path $schemaPath) {
      Get-Content -Raw $schemaPath | & $mysqlExe @mysqlArgs $env:DB_NAME
    } else {
      Write-Host "Aviso: no se encontró sql\schema.sql, se omite importación."
    }
  } catch {
    Write-Host "Aviso: no se pudo importar schema.sql automáticamente. Puedes importarlo con MySQL Workbench."
  }
} else {
  Write-Host "Aviso: no se encontró mysql.exe. Omitiendo creación/importación de DB."
  Write-Host "       Importa 'sql\schema.sql' con MySQL Workbench o instala el cliente CLI."
}

# 6) Abrir navegador (no bloqueante)
$launchUrl = "http://$($env:HOST):$($env:PORT)/"
Start-Process $launchUrl | Out-Null

# 7) Iniciar Uvicorn
Write-Host "Iniciando Uvicorn en $launchUrl"
python -m uvicorn backend.main:app --host $env:HOST --port $env:PORT
