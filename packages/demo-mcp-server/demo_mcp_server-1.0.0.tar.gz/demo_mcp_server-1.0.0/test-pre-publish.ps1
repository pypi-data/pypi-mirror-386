#!/usr/bin/env pwsh
# Pre-Publishing Test Script for Demo MCP Server

param(
    [string]$TestApiKey = "test_key_12345_demo",
    [switch]$SkipBuild = $false,
    [switch]$Verbose = $false
)

# Colors for output
$Green = "Green"
$Red = "Red" 
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-TestResult {
    param($Message, $Success, $Details = "")
    if ($Success) {
        Write-Host "✅ $Message" -ForegroundColor $Green
        if ($Details -and $Verbose) { Write-Host "   $Details" -ForegroundColor Gray }
    } else {
        Write-Host "❌ $Message" -ForegroundColor $Red
        if ($Details) { Write-Host "   $Details" -ForegroundColor $Red }
    }
}

function Write-TestSection {
    param($Title)
    Write-Host "`n🔍 $Title" -ForegroundColor $Blue
    Write-Host ("=" * 50) -ForegroundColor $Blue
}

# Test counter
$TestsPassed = 0
$TestsFailed = 0
$TotalTests = 0

function Test-Step {
    param($Name, $ScriptBlock)
    $script:TotalTests++
    
    try {
        $result = & $ScriptBlock
        if ($result -eq $false) {
            Write-TestResult $Name $false
            $script:TestsFailed++
        } else {
            Write-TestResult $Name $true
            $script:TestsPassed++
        }
    } catch {
        Write-TestResult $Name $false $_.Exception.Message
        $script:TestsFailed++
    }
}

Write-Host "🚀 Demo MCP Server - Pre-Publishing Tests" -ForegroundColor $Blue
Write-Host "=========================================" -ForegroundColor $Blue

# Set location
Set-Location "C:\Projects\mcp-server"

Write-TestSection "1. Project Structure Validation"

Test-Step "Project directory exists" {
    Test-Path "C:\Projects\mcp-server"
}

Test-Step "Main files exist" {
    (Test-Path "main.py") -and 
    (Test-Path "remote_main.py") -and 
    (Test-Path "models.py") -and
    (Test-Path "pyproject.toml") -and
    (Test-Path "README.md")
}

Test-Step "License file exists" {
    Test-Path "LICENSE"
}

Test-Step ".gitignore exists" {
    Test-Path ".gitignore"
}

Write-TestSection "2. Python Environment Tests"

Test-Step "UV is available" {
    try {
        $uvVersion = uv --version 2>$null
        $uvVersion -ne $null
    } catch { $false }
}

Test-Step "Python version compatibility" {
    try {
        $pythonVersion = uv run python --version 2>&1
        if ($pythonVersion -match "3\.10|3\.11|3\.12|3\.13") { $true } else { $false }
    } catch { $false }
}

Test-Step "Dependencies sync" {
    try {
        $output = uv sync 2>&1
        $LASTEXITCODE -eq 0
    } catch { $false }
}

Write-TestSection "3. Import Tests"

Test-Step "Main module imports" {
    try {
        $output = uv run python -c "import main; print('OK')" 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "Remote main module imports" {
    try {
        $output = uv run python -c "import remote_main; print('OK')" 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "Models module imports" {
    try {
        $output = uv run python -c "import models; print('OK')" 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "All dependencies importable" {
    try {
        $output = uv run python -c "import sys; import os; import httpx; import json; sys.path.append('.'); import main; import remote_main; import models; print('OK')" 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Write-TestSection "4. Code Structure Tests"

Test-Step "FastMCP server creation" {
    try {
        $tempScript = "from main import mcp`nprint(f'Server name: {mcp.name}')`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "FastMCP tools discoverable" {
    try {
        $tempScript = "from main import mcp`ntools = [f for f in dir(mcp) if not f.startswith('_')]`nprint(f'Tools found: {len(tools)}')`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "Models dataclass structure" {
    try {
        $output = uv run python -c "from models import BookingForm, Location; booking = BookingForm('Test', 'test@example.com'); location = Location('virtual', 'google_meet'); print('Models OK')" 2>&1
        if ($output -match "Models OK") { $true } else { $false }
    } catch { $false }
}

Write-TestSection "5. Function Tests (No API Key Required)"

Test-Step "Add function works" {
    try {
        $tempScript = "from main import add`nresult = add(5, 3)`nprint(f'Result: {result}')`nassert result == 8`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "Environment variable handling" {
    try {
        $env:ONCEHUB_API_KEY = $TestApiKey
        $tempScript = "from main import get_api_key`nkey = get_api_key()`nprint(f'API key found: {key[:8]}...')`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        Remove-Item Env:ONCEHUB_API_KEY -ErrorAction SilentlyContinue
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Write-TestSection "6. API Integration Tests (Mock)"

Test-Step "Booking function handles missing API key" {
    try {
        Remove-Item Env:ONCEHUB_API_KEY -ErrorAction SilentlyContinue
        $tempScript = "from main import get_booking_time_slots`nresult = get_booking_time_slots('test_cal')`nprint('Success:', result.get('success'))`nassert result.get('success') == False`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Test-Step "Schedule function handles missing API key" {
    try {
        Remove-Item Env:ONCEHUB_API_KEY -ErrorAction SilentlyContinue
        $tempScript = "from main import schedule_meeting`nresult = schedule_meeting(calendar_id='test_cal', start_time='2024-01-15T14:30:00', guest_time_zone='America/New_York', guest_name='Test User', guest_email='test@example.com')`nprint('Success:', result.get('success'))`nassert result.get('success') == False`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

Write-TestSection "7. MCP Server Tests"

Test-Step "Remote server can initialize" {
    try {
        $tempScript = "from remote_main import server, convert_timestamp_if_needed`nprint('Server created:', server.name)`niso_time = convert_timestamp_if_needed('2024-01-15T14:30:00')`nprint('ISO conversion OK:', iso_time)`ntimestamp_time = convert_timestamp_if_needed(1705327800000)`nprint('Timestamp conversion OK:', timestamp_time)`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

if (-not $SkipBuild) {
    Write-TestSection "8. Build Tests"

    Test-Step "Package builds successfully" {
        try {
            $output = uv build 2>&1
            $success = $LASTEXITCODE -eq 0
            if ($success) {
                $distFiles = Get-ChildItem "dist\" -ErrorAction SilentlyContinue
                $success = $distFiles.Count -gt 0
            }
            $success
        } catch { $false }
    }

    Test-Step "Built package can be installed" {
        try {
            # Get the wheel file
            $wheelFile = Get-ChildItem "dist\*.whl" | Select-Object -First 1
            if ($wheelFile) {
                $output = uv pip install $wheelFile.FullName --force-reinstall 2>&1
                $LASTEXITCODE -eq 0
            } else { $false }
        } catch { $false }
    }

    Test-Step "CLI command is available" {
        try {
            # Test if the command exists (will start server, so timeout quickly)
            $job = Start-Job -ScriptBlock { 
                try {
                    demo-mcp-server 2>&1
                } catch {
                    "Command not found"
                }
            }
            Start-Sleep 2
            Stop-Job $job -ErrorAction SilentlyContinue
            $output = Receive-Job $job
            Remove-Job $job -ErrorAction SilentlyContinue
            
            # If it started without "Command not found", it exists
            $output -notmatch "Command not found"
        } catch { $false }
    }
}

Write-TestSection "9. Configuration Tests"

Test-Step "pyproject.toml is valid" {
    try {
        $content = Get-Content "pyproject.toml" -Raw
        $content -match 'name = "demo-mcp-server"' -and
        $content -match 'version = "1.0.0"' -and
        $content -match '\[project\.scripts\]' -and
        $content -match 'demo-mcp-server = "remote_main:run_server"'
    } catch { $false }
}

Test-Step "README.md has required sections" {
    try {
        $content = Get-Content "README.md" -Raw
        $content -match "# Demo MCP Server" -and
        $content -match "## Installation" -and
        $content -match "## Configuration" -and
        $content -match "ONCEHUB_API_KEY"
    } catch { $false }
}

Write-TestSection "10. Final Integration Test"

Test-Step "Complete workflow with test API key" {
    try {
        $env:ONCEHUB_API_KEY = $TestApiKey
        $tempScript = "from main import add, get_booking_time_slots, schedule_meeting`nmath_result = add(10, 5)`nprint('Math result:', math_result)`nbooking_result = get_booking_time_slots('test_cal')`nprint('Booking handled:', 'success' in booking_result)`nschedule_result = schedule_meeting(calendar_id='test_cal', start_time='2024-01-15T14:30:00', guest_time_zone='America/New_York', guest_name='Test User', guest_email='test@example.com')`nprint('Schedule handled:', 'success' in schedule_result)`nprint('OK')"
        $output = uv run python -c $tempScript 2>&1
        Remove-Item Env:ONCEHUB_API_KEY -ErrorAction SilentlyContinue
        if ($output -match "OK") { $true } else { $false }
    } catch { $false }
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "📊 TEST SUMMARY" -ForegroundColor $Blue
Write-Host "===============" -ForegroundColor $Blue

$PassRate = if ($TotalTests -gt 0) { [math]::Round(($TestsPassed / $TotalTests) * 100, 1) } else { 0 }

Write-Host "Total Tests: $TotalTests" -ForegroundColor White
Write-Host "Passed: $TestsPassed" -ForegroundColor $Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $(if ($TestsFailed -gt 0) { $Red } else { $Green })
Write-Host "Pass Rate: $PassRate%" -ForegroundColor $(if ($PassRate -ge 90) { $Green } elseif ($PassRate -ge 70) { $Yellow } else { $Red })

if ($TestsFailed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED! Ready for publishing! 🚀" -ForegroundColor $Green
    exit 0
} else {
    Write-Host "`n⚠️  Some tests failed. Please fix issues before publishing." -ForegroundColor $Yellow
    exit 1
}