# Simple PowerShell test script to validate MCP server pre-publishing
param(
    [string]$TestApiKey = "test_fake_api_key_12345"
)

# Color definitions
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

# Counters
$script:TestsTotal = 0
$script:TestsPassed = 0
$script:TestsFailed = 0

function Write-TestSection {
    param([string]$SectionName)
    Write-Host ""
    Write-Host "=== $SectionName ===" -ForegroundColor $Yellow
    Write-Host ("-" * 50) -ForegroundColor $Yellow
}

function Write-TestResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details = ""
    )
    $script:TestsTotal++
    if ($Passed) {
        $script:TestsPassed++
        Write-Host "[PASS] $Name" -ForegroundColor $Green
        if ($Details) { Write-Host "   $Details" -ForegroundColor $Green }
    } else {
        $script:TestsFailed++
        Write-Host "[FAIL] $Name" -ForegroundColor $Red
        if ($Details) { Write-Host "   $Details" -ForegroundColor $Red }
    }
}

function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$TestCode
    )
    try {
        $result = & $TestCode
        if ($result -eq $true) {
            Write-TestResult $Name $true
        } else {
            Write-TestResult $Name $false "Test returned: $result"
        }
    } catch {
        Write-TestResult $Name $false $_.Exception.Message
        $script:TestsFailed++
    }
}

Write-Host "Demo MCP Server - Pre-Publishing Tests" -ForegroundColor $Blue
Write-Host "=========================================" -ForegroundColor $Blue

# Set location
Set-Location "C:\Projects\demo-mcp-server"

Write-TestSection "1. Project Structure Validation"

Test-Step "Project directory exists" {
    Test-Path "C:\Projects\demo-mcp-server"
}

Test-Step "Main files exist" {
    (Test-Path "main.py") -and 
    (Test-Path "remote_main.py") -and 
    (Test-Path "models.py") -and
    (Test-Path "pyproject.toml") -and
    (Test-Path "README.md")
}

Write-TestSection "2. Build System Tests"

Test-Step "UV package manager available" {
    try {
        $null = uv --version 2>&1
        $true
    } catch { $false }
}

Test-Step "Project builds successfully" {
    try {
        $output = uv build 2>&1
        $LASTEXITCODE -eq 0
    } catch { $false }
}

Write-TestSection "3. Python Environment Tests"

Test-Step "Python version compatible" {
    try {
        $output = uv run python --version 2>&1
        $pythonVersion = $output -replace "Python ", ""
        $pythonVersion -match "3\.(10|11|12|13)"
    } catch { $false }
}

Test-Step "Main module imports successfully" {
    try {
        $output = uv run python -c "import main; print('OK')" 2>&1
        $output -like "*OK*"
    } catch { $false }
}

Test-Step "Remote main module imports successfully" {
    try {
        $output = uv run python -c "import remote_main; print('OK')" 2>&1
        $output -like "*OK*"
    } catch { $false }
}

Test-Step "Models module imports successfully" {
    try {
        $output = uv run python -c "import models; print('OK')" 2>&1
        $output -like "*OK*"
    } catch { $false }
}

Write-TestSection "4. Function Tests"

Test-Step "Add function works" {
    try {
        # Create temporary Python script file to avoid quote issues
        $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
        @"
from main import add
result = add(5, 3)
print('Result:', result)
assert result == 8
print('OK')
"@ | Out-File -FilePath $tempFile -Encoding utf8
        
        $output = uv run python $tempFile 2>&1
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Write-TestSection "5. Final Results"

$successRate = if ($script:TestsTotal -gt 0) { 
    [math]::Round(($script:TestsPassed / $script:TestsTotal) * 100, 1) 
} else { 0 }

Write-Host ""
Write-Host "Test Summary:" -ForegroundColor $Blue
Write-Host "Total Tests: $($script:TestsTotal)" -ForegroundColor $Blue
Write-Host "Passed: $($script:TestsPassed)" -ForegroundColor $Green
Write-Host "Failed: $($script:TestsFailed)" -ForegroundColor $Red
Write-Host "Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { $Green } else { $Red })

if ($script:TestsFailed -eq 0) {
    Write-Host ""
    Write-Host "All tests passed! Ready for publishing." -ForegroundColor $Green
    exit 0
} else {
    Write-Host ""
    Write-Host "Some tests failed. Please fix issues before publishing." -ForegroundColor $Yellow
    exit 1
}