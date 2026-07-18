# VedyaAI — Windows one-shot launcher
# Checks deps, installs packages, starts Postgres + FastAPI backend + Next.js frontend.
# Usage:  .\start.ps1
# Optional: .\start.ps1 -SkipDataLoad -LlmEnabled $true

[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$SkipDataLoad,
    [Nullable[bool]]$LlmEnabled = $null
)

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root

$PidDir = Join-Path $Root ".run"
$LogDir = Join-Path $PidDir "logs"
New-Item -ItemType Directory -Force -Path $PidDir, $LogDir | Out-Null

function Write-Info  { param([string]$Message) Write-Host "[VedyaAI] $Message" -ForegroundColor Cyan }
function Write-Ok    { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warn  { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Fail  { param([string]$Message) Write-Host "[FAIL] $Message" -ForegroundColor Red; exit 1 }

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-CommandVersionLine {
    param([string]$Name)
    try {
        $out = & $Name --version 2>&1 | Select-Object -First 1
        return "$out"
    } catch {
        return "(unknown version)"
    }
}

function Require-Command {
    param([string]$Name, [string]$Hint = "")
    if (Test-CommandExists $Name) {
        Write-Ok "$Name found: $(Get-CommandVersionLine $Name)"
    } else {
        $msg = "Missing required command: $Name"
        if ($Hint) { $msg += " - $Hint" }
        Write-Fail $msg
    }
}

function Stop-TrackedProcess {
    param([string]$PidFile)
    if (Test-Path $PidFile) {
        $procId = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($procId) {
            try {
                $p = Get-Process -Id ([int]$procId) -ErrorAction SilentlyContinue
                if ($p) {
                    Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
                    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                        Where-Object { $_.ParentProcessId -eq [int]$procId } |
                        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
                }
            } catch { }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-Cleanup {
    Write-Info "Stopping backend and frontend..."
    Stop-TrackedProcess (Join-Path $PidDir "backend.pid")
    Stop-TrackedProcess (Join-Path $PidDir "frontend.pid")
}

Write-Host ""
Write-Host "========================================"
Write-Host "  VedyaAI - Local Dev Launcher (Windows)"
Write-Host "========================================"
Write-Host ""

# -- 1. Prerequisite checks ---------------------------
Write-Info "Cross-verifying system dependencies..."
Require-Command "python" "Install Python 3.11+ from python.org (enable Add to PATH)"
Require-Command "node" "Install Node.js 20+ from nodejs.org"
Require-Command "npm" "Install npm (bundled with Node.js)"
Require-Command "docker" "Install Docker Desktop for Windows"

$script:ComposeIsPlugin = $false
try {
    docker compose version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $script:ComposeIsPlugin = $true
        Write-Ok "docker compose found"
    }
} catch { }

if (-not $script:ComposeIsPlugin) {
    if (Test-CommandExists "docker-compose") {
        Write-Ok "docker-compose found"
    } else {
        Write-Fail "Neither 'docker compose' nor 'docker-compose' is available"
    }
}

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($script:ComposeIsPlugin) {
            & docker compose @ComposeArgs 2>&1 | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    Write-Host $_.ToString()
                } else {
                    Write-Host $_
                }
            }
        } else {
            & docker-compose @ComposeArgs 2>&1 | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    Write-Host $_.ToString()
                } else {
                    Write-Host $_
                }
            }
        }
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
}

$pyVer = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$pyParts = $pyVer.Split(".")
if ([int]$pyParts[0] -lt 3 -or ([int]$pyParts[0] -eq 3 -and [int]$pyParts[1] -lt 10)) {
    Write-Fail "Python 3.10+ required (found $pyVer)"
}
Write-Ok "Python version OK ($pyVer)"

$nodeMajor = & node -p "process.versions.node.split('.')[0]"
if ([int]$nodeMajor -lt 18) {
    Write-Fail "Node.js 18+ required (found $(node -v))"
}
Write-Ok "Node.js version OK ($(node -v))"

# -- 2. Environment file ------------------------------
$envFile = Join-Path $Root ".env"
$envExample = Join-Path $Root ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Warn "Created .env from .env.example - edit OPENAI_API_KEY if you want LLM explanations"
    } else {
        Write-Fail ".env.example missing"
    }
} else {
    Write-Ok ".env present"
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length - 2) }
    if ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Substring(1, $val.Length - 2) }
    [Environment]::SetEnvironmentVariable($key, $val, "Process")
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://vedya:vedyapass@localhost:5433/vedyaai"
}
if ($null -ne $LlmEnabled) {
    $env:LLM_ENABLED = if ($LlmEnabled) { "true" } else { "false" }
} elseif (-not $env:LLM_ENABLED) {
    $env:LLM_ENABLED = "false"
}
if (-not $env:NEXT_PUBLIC_API_URL) {
    $env:NEXT_PUBLIC_API_URL = "http://localhost:$BackendPort"
}
if (-not $env:CORPUS_VERSION) {
    $env:CORPUS_VERSION = "1.0.0"
}

# -- 3. Postgres via Docker ---------------------------
Write-Info "Starting PostgreSQL (pgvector)..."
# Pass args as an array so PowerShell does not swallow -d as a switch
$composeExit = Invoke-Compose -ComposeArgs @("up", "-d", "postgres")
if ($composeExit -ne 0) { Write-Fail "Failed to start postgres container" }

Write-Info "Waiting for Postgres to become healthy..."
$ready = $false
for ($i = 1; $i -le 60; $i++) {
    $readyExit = Invoke-Compose -ComposeArgs @("exec", "-T", "postgres", "pg_isready", "-U", "vedya", "-d", "vedyaai")
    if ($readyExit -eq 0) {
        Write-Ok "Postgres is ready"
        $ready = $true
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $ready) { Write-Fail "Postgres did not become ready in time" }

# -- 4. Python virtualenv + backend deps --------------
Write-Info "Setting up Python backend environment..."
$venvPath = Join-Path $Root "backend\.venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv $venvPath
    Write-Ok "Created virtualenv at backend\.venv"
}

& $venvPython -m pip install --upgrade pip | Out-Null
Write-Info "Installing / verifying backend requirements..."
& $venvPip install -r (Join-Path $Root "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed" }

Write-Info "Cross-verifying Python packages..."
$verifyPy = Join-Path $LogDir "verify_backend.py"
@'
import importlib
import sys

required = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("psycopg2", "psycopg2"),
    ("pydantic", "pydantic"),
    ("dotenv", "python-dotenv"),
    ("yaml", "PyYAML"),
    ("httpx", "httpx"),
    ("openai", "openai"),
]
missing = []
for mod, pkg in required:
    try:
        importlib.import_module(mod)
        print("  OK " + pkg)
    except ImportError:
        missing.append(pkg)
        print("  MISSING " + pkg)
if missing:
    print("Missing: " + ", ".join(missing), file=sys.stderr)
    sys.exit(1)
print("All backend packages verified.")
'@ | Set-Content -Path $verifyPy -Encoding UTF8

& $venvPython $verifyPy
if ($LASTEXITCODE -ne 0) { Write-Fail "Backend dependency verification failed" }
Write-Ok "Backend dependencies verified"

# -- 5. Frontend deps ---------------------------------
Write-Info "Installing / verifying frontend packages..."
Push-Location (Join-Path $Root "frontend")
try {
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Fail "npm install failed" }

    Write-Info "Cross-verifying Node packages..."
    $verifyJs = Join-Path $LogDir "verify_frontend.js"
    @'
const required = ["next", "react", "react-dom", "framer-motion", "lucide-react"];
let ok = true;
for (const name of required) {
  try {
    require.resolve(name);
    console.log("  OK " + name);
  } catch {
    console.log("  MISSING " + name);
    ok = false;
  }
}
if (!ok) process.exit(1);
console.log("All frontend packages verified.");
'@ | Set-Content -Path $verifyJs -Encoding UTF8
    node $verifyJs
    if ($LASTEXITCODE -ne 0) { Write-Fail "Frontend dependency verification failed" }
    Write-Ok "Frontend dependencies verified"
} finally {
    Pop-Location
}

# -- 6. Seed data if empty ----------------------------
if (-not $SkipDataLoad) {
    Write-Info "Checking whether knowledge base is loaded..."
    $countPy = Join-Path $LogDir "count_yogas.py"
    @'
import os
import psycopg2

try:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM yogas")
    print(cur.fetchone()[0])
    conn.close()
except Exception:
    print(-1)
'@ | Set-Content -Path $countPy -Encoding UTF8

    $yogaCount = (& $venvPython $countPy | Select-Object -Last 1).ToString().Trim()
    if ($yogaCount -eq "-1") {
        Write-Warn "Could not query yogas table yet - retrying..."
        Start-Sleep -Seconds 3
        $yogaCount = (& $venvPython $countPy | Select-Object -Last 1).ToString().Trim()
    }

    if ([int]$yogaCount -lt 1) {
        Write-Info "Database empty - running data loaders (this may take a few minutes)..."
        Push-Location (Join-Path $Root "scripts")
        try {
            & $venvPython enrich_formulations.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "enrich_formulations.py failed" }
            & $venvPython load_synonyms.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_synonyms.py failed" }
            & $venvPython load_herbs.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_herbs.py failed" }
            & $venvPython load_formulations.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_formulations.py failed" }
            & $venvPython load_constraints.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_constraints.py failed" }
            & $venvPython load_sense_rules.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_sense_rules.py failed" }
            & $venvPython load_charaka.py
            if ($LASTEXITCODE -ne 0) { Write-Fail "load_charaka.py failed" }
        } finally {
            Pop-Location
        }
        Write-Ok "Data load complete"
    } else {
        Write-Ok "Knowledge base already loaded ($yogaCount yogas)"
    }
} else {
    Write-Warn "Skipping data load (-SkipDataLoad)"
}

# Ensure Next.js can read API URL at startup
$frontendEnvLocal = Join-Path $Root "frontend\.env.local"
"NEXT_PUBLIC_API_URL=$($env:NEXT_PUBLIC_API_URL)" | Set-Content -Path $frontendEnvLocal -Encoding UTF8

# -- 7. Start backend ---------------------------------
Write-Info "Starting FastAPI backend on :$BackendPort ..."
$backendLog = Join-Path $LogDir "backend.log"
$backendPidFile = Join-Path $PidDir "backend.pid"
$uvicorn = Join-Path $venvPath "Scripts\uvicorn.exe"

$backendProc = Start-Process -FilePath $uvicorn `
    -ArgumentList @("main:app", "--reload", "--host", "0.0.0.0", "--port", "$BackendPort") `
    -WorkingDirectory (Join-Path $Root "backend") `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError (Join-Path $LogDir "backend.err.log") `
    -PassThru `
    -WindowStyle Hidden
Set-Content -Path $backendPidFile -Value $backendProc.Id

# -- 8. Start frontend --------------------------------
Write-Info "Starting Next.js frontend on :$FrontendPort ..."
$frontendLog = Join-Path $LogDir "frontend.log"
$frontendPidFile = Join-Path $PidDir "frontend.pid"

$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList @("/c", "npm run dev -- --port $FrontendPort") `
    -WorkingDirectory (Join-Path $Root "frontend") `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError (Join-Path $LogDir "frontend.err.log") `
    -PassThru `
    -WindowStyle Hidden
Set-Content -Path $frontendPidFile -Value $frontendProc.Id

# -- 9. Wait for health -------------------------------
Write-Info "Waiting for backend health..."
$backendOk = $false
for ($i = 1; $i -le 45; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            Write-Ok "Backend healthy"
            $backendOk = $true
            break
        }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $backendOk) {
    Write-Warn "Backend health check timed out - see $LogDir\backend.log / backend.err.log"
}

Write-Info "Waiting for frontend..."
$frontendOk = $false
for ($i = 1; $i -le 90; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            Write-Ok "Frontend responding"
            $frontendOk = $true
            break
        }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $frontendOk) {
    Write-Warn "Frontend not responding yet - see $LogDir\frontend.log / frontend.err.log"
}

Write-Host ""
Write-Host "========================================"
Write-Host "  VedyaAI is running"
Write-Host "========================================"
Write-Host "  App:      http://localhost:$FrontendPort"
Write-Host "  API:      http://localhost:$BackendPort"
Write-Host "  API docs: http://localhost:$BackendPort/docs"
Write-Host "  Logs:     $LogDir\"
Write-Host ""
Write-Host "  Press Ctrl+C to stop backend + frontend"
Write-Host "  (Postgres stays up - stop with: docker compose stop postgres)"
Write-Host "========================================"
Write-Host ""

try {
    while ($true) {
        if (-not (Get-Process -Id $backendProc.Id -ErrorAction SilentlyContinue)) {
            Write-Warn "Backend process exited unexpectedly - check logs"
            break
        }
        if (-not (Get-Process -Id $frontendProc.Id -ErrorAction SilentlyContinue)) {
            Write-Warn "Frontend process exited unexpectedly - check logs"
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Invoke-Cleanup
}
