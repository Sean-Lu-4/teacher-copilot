$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 8765
$url = "http://127.0.0.1:$port/"
Set-Location $projectDir

# Enable real-time generation when an API key is already configured in the environment.
if ($env:OPENAI_API_KEY) { $env:TEACHER_COPILOT_ENABLE_AI = '1' }

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    Write-Host 'Starting Teacher Copilot local service...'
    & py -m teacher_copilot.review_app --port $port
    exit $LASTEXITCODE
}

try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3
    if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode)" }
    Write-Host "Teacher Copilot is already running: $url"
    Start-Process $url
} catch {
    Write-Host "Port $port is occupied, but the page did not respond. Close the process using this port and try again."
    exit 1
}
