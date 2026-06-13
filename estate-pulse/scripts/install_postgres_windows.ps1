param()

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ExpectedPsqlPath {
    $candidatePaths = @(
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe"
    )

    foreach ($path in $candidatePaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    return $candidatePaths[0]
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget was not found. Install Microsoft's App Installer first, then rerun this script."
}

if (-not (Test-IsAdministrator)) {
    throw "PostgreSQL 16 installation may require Administrator privileges. Open PowerShell as Administrator and rerun this script."
}

Write-Host "[step] Installing PostgreSQL 16 with winget"
& winget install --id PostgreSQL.PostgreSQL.16 --exact --accept-package-agreements --accept-source-agreements
if ($LASTEXITCODE -ne 0) {
    throw "winget failed to install PostgreSQL 16. Review the installer output above and rerun after fixing the issue."
}

$psqlCommand = Get-Command psql -ErrorAction SilentlyContinue
$psqlPath = if ($psqlCommand) { $psqlCommand.Source } else { Get-ExpectedPsqlPath }

Write-Host "[done] PostgreSQL 16 installation command completed."
Write-Host "[info] If psql is not on PATH yet, use this expected path:"
Write-Host "       $psqlPath"
Write-Host "[info] You may need to open a new PowerShell window before psql is available on PATH."
Write-Host "[next] After installation, run:"
Write-Host "       powershell -ExecutionPolicy Bypass -File .\scripts\init_postgres.ps1"
