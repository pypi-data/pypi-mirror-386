# File: scripts/diagnostics/setup_git_worktree.ps1
# Purpose: Configure bare Git repository + working tree mapping for Windows/WSL split setups.
# Context: Automates core.worktree and Git environment variables so developers can switch between hosts safely.

param(
    [string]$GitDir = "$HOME/.git-noveler",
    [string]$WorkTree = "C:/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド",
    [switch]$DryRun,
    [switch]$PersistEnv
)

function Write-SetupMessage {
    param([string]$Message)
    Write-Host "[setup-git] $Message"
}

function Resolve-CustomPath {
    param([string]$PathValue)

    $expanded = [Environment]::ExpandEnvironmentVariables($PathValue)
    if ($expanded.StartsWith("~")) {
        $expanded = $expanded -replace "^~", $HOME
    }
    try {
        $resolved = Resolve-Path -LiteralPath $expanded -ErrorAction Stop
        return $resolved.ProviderPath
    }
    catch {
        return $expanded
    }
}

function Invoke-GitCommand {
    param(
        [string]$GitDirPath,
        [string]$WorkTreePath,
        [string[]]$Arguments,
        [switch]$Preview
    )

    $args = @("--git-dir=$GitDirPath", "--work-tree=$WorkTreePath") + $Arguments
    if ($Preview) {
        Write-SetupMessage "Preview: git $($args -join ' ')"
        return
    }

    $process = Start-Process -FilePath git -ArgumentList $args -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $($process.ExitCode)."
    }
}

function Ensure-GitAvailable {
    try {
        $null = Get-Command git -ErrorAction Stop
    }
    catch {
        throw "git command not found. Install Git for Windows or ensure it is on PATH."
    }
}

Ensure-GitAvailable

$resolvedGitDir = Resolve-CustomPath -PathValue $GitDir
$resolvedWorkTree = Resolve-CustomPath -PathValue $WorkTree

Write-SetupMessage "Git directory : $resolvedGitDir"
Write-SetupMessage "Work tree     : $resolvedWorkTree"

if (-not (Test-Path -LiteralPath $resolvedGitDir)) {
    throw "Git directory not found: $resolvedGitDir"
}
if (-not (Test-Path -LiteralPath $resolvedWorkTree)) {
    throw "Work tree directory not found: $resolvedWorkTree"
}

try {
    Invoke-GitCommand -GitDirPath $resolvedGitDir -WorkTreePath $resolvedWorkTree -Arguments @("config", "--local", "core.worktree", $resolvedWorkTree) -Preview:$DryRun
    Write-SetupMessage "core.worktree updated."

    if (-not $DryRun) {
        $current = & git --git-dir=$resolvedGitDir config --local --get core.worktree 2>$null
        Write-SetupMessage "Current core.worktree: $current"
    }

    if (-not $DryRun) {
        $originalGitDir = $env:GIT_DIR
        $originalGitWorkTree = $env:GIT_WORK_TREE

        $env:GIT_DIR = $resolvedGitDir
        $env:GIT_WORK_TREE = $resolvedWorkTree

        try {
            Write-SetupMessage "Running git status to verify configuration..."
            & git status --short | Out-Default
        }
        finally {
            if (-not $PersistEnv) {
                $env:GIT_DIR = $originalGitDir
                $env:GIT_WORK_TREE = $originalGitWorkTree
            }
        }

        if ($PersistEnv) {
            $aliasLine = "function Set-NovelerGitContext {\n    Set-Item Env:GIT_DIR '$resolvedGitDir'\n    Set-Item Env:GIT_WORK_TREE '$resolvedWorkTree'\n    Write-Host '[setup-git] Git context persisted for current session.'\n}\nSet-Alias Use-NovelerGit Set-NovelerGitContext\n"
            $profilePath = $PROFILE
            Write-SetupMessage "Persisting helper alias to $profilePath"
            Add-Content -Path $profilePath -Value $aliasLine
        }
    }
}
catch {
    throw $_
}
