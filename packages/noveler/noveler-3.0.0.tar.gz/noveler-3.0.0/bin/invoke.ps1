#!/usr/bin/env pwsh
# File: bin/invoke.ps1
# Purpose: PowerShell wrapper delegating to the Python invoke hub.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ForwardArgs = $args

function Resolve-PythonCommand {
    if ($env:PYTHON -and $env:PYTHON.Trim()) {
        return ,$env:PYTHON.Trim()
    }

    foreach ($candidate in @('py', 'python', 'python3')) {
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

    throw "bin/invoke.ps1: Python executable was not found. Install Python 3.8+ or set `$env:PYTHON."
}

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$rootDir = (Resolve-Path -Path (Join-Path $scriptDir '..')).Path
$cli = Join-Path $rootDir 'scripts/tooling/invoke.py'

if (-not (Test-Path -LiteralPath $cli)) {
    throw "bin/invoke.ps1: Expected CLI script at $cli"
}

$pythonParts = @(Resolve-PythonCommand)
$exe = $pythonParts[0]
$exeArgs = @()
if ($pythonParts.Count -gt 1) {
    $exeArgs = $pythonParts[1..($pythonParts.Count - 1)]
}

& $exe @exeArgs $cli @ForwardArgs
exit $LASTEXITCODE
