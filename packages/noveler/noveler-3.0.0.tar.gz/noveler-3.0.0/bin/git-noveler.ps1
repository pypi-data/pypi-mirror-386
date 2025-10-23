#!/usr/bin/env pwsh
# File: bin/git-noveler.ps1
# Purpose: Provide a PowerShell wrapper that pins Git operations to the Noveler bare repository.
# Context: Helps Windows users interact with the shared OneDrive worktree without manually exporting GIT_DIR / GIT_WORK_TREE.

param(
    [string]$GitDir = $(if ($env:NOVELER_GIT_DIR) { $env:NOVELER_GIT_DIR } else { Join-Path $HOME '.git-noveler' }),
    [string]$WorkTree = $(if ($env:NOVELER_WORK_TREE) { $env:NOVELER_WORK_TREE } else { (Resolve-Path -Path (Join-Path $PSScriptRoot '..')).Path }),
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GitArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-NormPath {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Value
    }

    $expanded = [Environment]::ExpandEnvironmentVariables($Value)
    if ($expanded.StartsWith('~')) {
        $expanded = $expanded -replace '^~', $HOME
    }
    try {
        return (Resolve-Path -LiteralPath $expanded -ErrorAction Stop).ProviderPath
    }
    catch {
        return [System.IO.Path]::GetFullPath($expanded)
    }
}

$resolvedGitDir = Resolve-NormPath $GitDir
$resolvedWorkTree = Resolve-NormPath $WorkTree

if (-not (Test-Path -LiteralPath $resolvedGitDir)) {
    throw "git-noveler.ps1: Git directory not found: $resolvedGitDir"
}

if (-not (Test-Path -LiteralPath $resolvedWorkTree)) {
    throw "git-noveler.ps1: Work tree directory not found: $resolvedWorkTree"
}

if (-not $GitArgs -or $GitArgs.Count -eq 0) {
    $GitArgs = @('status', '--short')
}

$arguments = @("--git-dir=$resolvedGitDir", "--work-tree=$resolvedWorkTree") + $GitArgs
Write-Verbose ("[git-noveler] git {0}" -f ($arguments -join ' '))

& git @arguments
exit $LASTEXITCODE
