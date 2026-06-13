param(
    [string]$AdminUser = "postgres",
    [string]$AdminPassword = $env:POSTGRES_ADMIN_PASSWORD,
    [string]$DbHost = "localhost",
    [int]$Port = 5432,
    [string]$RoleName = "estate",
    [string]$RolePassword = "estate",
    [string]$DatabaseName = "estate_pulse",
    [string]$TestDatabaseName = "estate_pulse_test"
)

$ErrorActionPreference = "Stop"

function Assert-Identifier {
    param(
        [string]$Value,
        [string]$Label
    )

    if ($Value -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
        throw "$Label '$Value' contains unsupported characters. Use letters, numbers, and underscores only."
    }
}

function Get-PsqlPath {
    $command = Get-Command psql -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $expectedPaths = @(
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe"
    )

    foreach ($path in $expectedPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    throw "psql.exe was not found. Install PostgreSQL 16 first with .\scripts\install_postgres_windows.ps1, then open a new PowerShell window."
}

function Invoke-PsqlScript {
    param(
        [string]$PsqlPath,
        [string]$Database,
        [string]$ScriptContent,
        [string]$StepName
    )

    $tempFile = Join-Path $env:TEMP ("estate-pulse-postgres-" + [System.Guid]::NewGuid().ToString() + ".sql")
    try {
        [System.IO.File]::WriteAllText(
            $tempFile,
            $ScriptContent,
            (New-Object System.Text.UTF8Encoding($false))
        )
        & $PsqlPath -h $DbHost -p $Port -U $AdminUser -d $Database -v ON_ERROR_STOP=1 -f $tempFile
        if ($LASTEXITCODE -ne 0) {
            throw "psql exited with code $LASTEXITCODE during '$StepName'."
        }
    } catch {
        throw "PostgreSQL step failed: $StepName`n$($_.Exception.Message)"
    } finally {
        Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue
    }
}

Assert-Identifier -Value $AdminUser -Label "Admin user"
Assert-Identifier -Value $RoleName -Label "Role name"
Assert-Identifier -Value $DatabaseName -Label "Database name"
Assert-Identifier -Value $TestDatabaseName -Label "Test database name"

if (-not $AdminPassword) {
    throw "POSTGRES_ADMIN_PASSWORD is required for PostgreSQL initialization. Set `$env:POSTGRES_ADMIN_PASSWORD first."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $repoRoot "migrations\postgres\0001_initial_schema.sql"
if (-not (Test-Path $schemaPath)) {
    throw "Schema file not found: $schemaPath"
}

$psqlPath = Get-PsqlPath
Write-Host "[info] Using psql: $psqlPath"
Write-Host "[info] Target server: $DbHost`:$Port"

$escapedRolePassword = $RolePassword.Replace("'", "''")
$adminScript = @"
DO $`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$RoleName') THEN
        CREATE ROLE $RoleName LOGIN PASSWORD '$escapedRolePassword';
    ELSE
        ALTER ROLE $RoleName WITH LOGIN PASSWORD '$escapedRolePassword';
    END IF;
END
$`$;

SELECT format('CREATE DATABASE %I OWNER %I', '$DatabaseName', '$RoleName')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$DatabaseName')
\gexec

SELECT format('CREATE DATABASE %I OWNER %I', '$TestDatabaseName', '$RoleName')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$TestDatabaseName')
\gexec
"@

$appSchemaScript = Get-Content -LiteralPath $schemaPath -Raw
$ownershipScript = @"
ALTER SCHEMA public OWNER TO $RoleName;
GRANT USAGE, CREATE ON SCHEMA public TO $RoleName;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO $RoleName;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO $RoleName;
ALTER DEFAULT PRIVILEGES FOR ROLE $AdminUser IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES TO $RoleName;
ALTER DEFAULT PRIVILEGES FOR ROLE $AdminUser IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO $RoleName;
ALTER DEFAULT PRIVILEGES FOR ROLE $RoleName IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES TO $RoleName;
ALTER DEFAULT PRIVILEGES FOR ROLE $RoleName IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO $RoleName;

DO $`$
DECLARE
    item record;
BEGIN
    FOR item IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I OWNER TO %I',
            item.schemaname,
            item.tablename,
            '$RoleName'
        );
    END LOOP;

    FOR item IN
        SELECT sequence_schema, sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE %I.%I OWNER TO %I',
            item.sequence_schema,
            item.sequence_name,
            '$RoleName'
        );
    END LOOP;
END
$`$;
"@

$previousPgPasswordExists = Test-Path Env:PGPASSWORD
$previousPgPassword = $env:PGPASSWORD

try {
    $env:PGPASSWORD = $AdminPassword

    Write-Host "[step] Ensuring role and databases exist"
    Invoke-PsqlScript `
        -PsqlPath $psqlPath `
        -Database "postgres" `
        -ScriptContent $adminScript `
        -StepName "create role and databases"

    Write-Host "[step] Applying schema to $DatabaseName"
    Invoke-PsqlScript `
        -PsqlPath $psqlPath `
        -Database $DatabaseName `
        -ScriptContent $appSchemaScript `
        -StepName "apply schema to $DatabaseName"

    Write-Host "[step] Synchronizing ownership and grants in $DatabaseName"
    Invoke-PsqlScript `
        -PsqlPath $psqlPath `
        -Database $DatabaseName `
        -ScriptContent $ownershipScript `
        -StepName "synchronize ownership and grants in $DatabaseName"

    Write-Host "[step] Applying schema to $TestDatabaseName"
    Invoke-PsqlScript `
        -PsqlPath $psqlPath `
        -Database $TestDatabaseName `
        -ScriptContent $appSchemaScript `
        -StepName "apply schema to $TestDatabaseName"

    Write-Host "[step] Synchronizing ownership and grants in $TestDatabaseName"
    Invoke-PsqlScript `
        -PsqlPath $psqlPath `
        -Database $TestDatabaseName `
        -ScriptContent $ownershipScript `
        -StepName "synchronize ownership and grants in $TestDatabaseName"

    Write-Host "[done] PostgreSQL role/database/schema initialization completed."
    Write-Host "[done] DATABASE_URL=postgresql://${RoleName}:${RolePassword}@$DbHost`:$Port/$DatabaseName"
    Write-Host "[done] TEST_DATABASE_URL=postgresql://${RoleName}:${RolePassword}@$DbHost`:$Port/$TestDatabaseName"
} finally {
    if ($previousPgPasswordExists) {
        $env:PGPASSWORD = $previousPgPassword
    } else {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}
