param(
    [string]$DatabaseUrl = "postgresql://estate:estate@localhost:5432/estate_pulse",
    [string]$TestDatabaseUrl = "postgresql://estate:estate@localhost:5432/estate_pulse_test"
)

$ErrorActionPreference = "Stop"

function Get-PythonExecutable {
    $repoRoot = Split-Path -Parent $PSScriptRoot
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }
    return "python"
}

$pythonExecutable = Get-PythonExecutable

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $env:DATABASE_URL = $DatabaseUrl
    $env:TEST_DATABASE_URL = $TestDatabaseUrl
    $maskedTestDatabaseUrl = $TestDatabaseUrl -replace '://([^:/?#]+):([^@/]+)@', '://$1:****@'
    Write-Host "[info] TEST_DATABASE_URL=$maskedTestDatabaseUrl"

@'
from __future__ import annotations

import os
import socket
import sys
from urllib.parse import urlsplit


database_url = os.environ["DATABASE_URL"]
test_database_url = os.environ["TEST_DATABASE_URL"]

test_database_name = urlsplit(test_database_url).path.lstrip("/")
if test_database_name != "estate_pulse_test":
    raise SystemExit(
        "TEST_DATABASE_URL must point to estate_pulse_test before the PostgreSQL smoke test can run."
    )

try:
    import psycopg  # noqa: F401
except ImportError as exc:  # pragma: no cover - script guard
    raise SystemExit(
        "psycopg is not installed in the selected Python environment. Run .\\.venv\\Scripts\\python -m pip install -r requirements.txt first."
    ) from exc

parts = urlsplit(test_database_url)
host = parts.hostname or "localhost"
port = parts.port or 5432

with socket.socket() as connection:
    connection.settimeout(2)
    try:
        connection.connect((host, port))
    except OSError as exc:  # pragma: no cover - script guard
        raise SystemExit(
            f"PostgreSQL connection failed for {host}:{port}. Start PostgreSQL and run scripts\\init_postgres.ps1 first. Original error: {exc}"
        ) from exc
'@ | & $pythonExecutable -
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL smoke precheck failed. Review the message above, then rerun."
    }

    Write-Host "[step] Running PostgreSQL smoke test"
    & $pythonExecutable -B -m unittest tests.test_postgres_smoke -v
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL smoke test failed. Review the unittest output above."
    }
} finally {
    Pop-Location
}
