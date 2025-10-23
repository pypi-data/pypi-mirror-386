# File: scripts/diagnostics/fix_git_path_windows.ps1
# Purpose: Convert WSL Git directory path to Windows-accessible UNC path in .git file
# Context: Enables Windows Git clients to recognize WSL-hosted bare repositories

param(
    [string]$WorkTree = "$PSScriptRoot\..\..",
    [string]$WslDistro = "Ubuntu-22.04",
    [string]$WslGitDir = "/home/bamboocity/.git-noveler",
    [switch]$DryRun
)

function Write-FixMessage {
    param([string]$Message, [string]$Level = "INFO")
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

$gitFilePath = Join-Path $WorkTree ".git"

# Check if .git file exists
if (-not (Test-Path $gitFilePath -PathType Leaf)) {
    Write-FixMessage ".git file not found at: $gitFilePath" "ERROR"
    exit 1
}

# Read current content
$currentContent = Get-Content $gitFilePath -Raw
Write-FixMessage "Current .git content: $currentContent" "INFO"

# Detect if it's already a WSL path
if ($currentContent -notmatch "^gitdir:\s*/home/") {
    Write-FixMessage "Not a WSL path format. No changes needed." "WARN"
    exit 0
}

# Convert WSL path to UNC format
$uncPath = "gitdir: \\wsl.localhost\$WslDistro$WslGitDir"
Write-FixMessage "Converting to UNC path: $uncPath" "INFO"

if ($DryRun) {
    Write-FixMessage "[DRY-RUN] Would update .git file with: $uncPath" "WARN"
    exit 0
}

# Backup original file
$backupPath = "$gitFilePath.bak"
Copy-Item $gitFilePath $backupPath -Force
Write-FixMessage "Backup created at: $backupPath" "SUCCESS"

# Update .git file
Set-Content $gitFilePath -Value $uncPath -NoNewline
Write-FixMessage "Updated .git file successfully" "SUCCESS"

# Verify Git can access the repository
try {
    $status = & git status --short 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-FixMessage "Git status verification: OK" "SUCCESS"
        Write-Output $status
    } else {
        throw "Git command failed"
    }
} catch {
    Write-FixMessage "Git verification failed. Restoring backup..." "ERROR"
    Copy-Item $backupPath $gitFilePath -Force
    throw $_
}

Write-FixMessage @"

✅ Configuration complete!

To use Git on Windows:
  git status
  git add .
  git commit -m "message"

Original .git file backed up to: $backupPath
"@ "SUCCESS"
