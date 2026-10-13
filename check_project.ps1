$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

Write-Host 'Running Python regression tests...'
py -m unittest discover -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'Checking browser scripts...'
node --check teacher_copilot\review_static\app.js
node --check teacher_copilot\review_static\bank.js
node --check teacher_copilot\review_static\curriculum.js
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$required = @(
    'teacher_copilot\review_app.py',
    'teacher_copilot\review_static\index.html',
    'teacher_copilot\review_static\bank.html',
    'teacher_copilot\review_static\app.js',
    'teacher_copilot\review_static\style.css',
    'start_teacher_copilot.bat'
)
foreach ($path in $required) {
    if (-not (Test-Path $path)) { throw "Missing required file: $path" }
}
Write-Host 'Teacher Copilot checks passed.' -ForegroundColor Green
