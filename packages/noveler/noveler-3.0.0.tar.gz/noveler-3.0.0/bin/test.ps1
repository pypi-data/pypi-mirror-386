#!/usr/bin/env pwsh
# File: bin/test.ps1
# Purpose: PowerShell wrapper to execute the unified pytest runner on Windows.
# Context: Provides parity with the Bash-based bin/test script for native shells.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Arguments = @($args)

function Resolve-PythonCommand {
    if ($env:PYTHON -and $env:PYTHON.Trim()) {
        return ,$env:PYTHON.Trim()
    }

    foreach ($candidate in @('python', 'python3')) {
        try {
            $command = (Get-Command $candidate -ErrorAction Stop).Path
            if ($command) {
                return ,$command
            }
        } catch {
        }
    }

    try {
        $pyCommand = (Get-Command 'py' -ErrorAction Stop).Path
        if ($pyCommand) {
            return @($pyCommand, '-3')
        }
    } catch {
    }

    throw "bin/test.ps1: Python executable was not found. Install Python 3.8+ or set `$env:PYTHON."
}

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent -LiteralPath $MyInvocation.MyCommand.Path }
$rootDir = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..')).Path
$runner = Join-Path $rootDir 'scripts/run_pytest.py'

if (-not (Test-Path -LiteralPath $runner)) {
    throw "bin/test.ps1: Expected runner script at $runner"
}

$pythonParts = @(Resolve-PythonCommand)
$exe = $pythonParts[0]
$exeArgs = @()
if ($pythonParts.Count -gt 1) {
    $exeArgs = $pythonParts[1..($pythonParts.Count - 1)]
}

$invokeArgs = @()
$invokeArgs += $exeArgs
$invokeArgs += @($runner)
$invokeArgs += $Arguments

& $exe @invokeArgs
exit $LASTEXITCODE
