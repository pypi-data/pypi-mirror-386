# File: bin/serena.ps1
# Purpose: PowerShell wrapper to invoke Serena CLI via uvx for Codex diagnostics.
# Context: Matches Codex MCP settings so Windows users can call `serena` without manual uvx commands.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgsFromUser
)

$ErrorActionPreference = 'Stop'

function Resolve-UvxPath {
    param()

    if ($env:UVX_BIN) {
        return $env:UVX_BIN
    }

    $defaultPath = Join-Path $env:USERPROFILE 'AppData\Local\Programs\Python\Python313\Scripts\uvx.exe'
    if (Test-Path $defaultPath) {
        return $defaultPath
    }

    try {
        $uvx = (Get-Command uvx.exe -ErrorAction Stop).Source
        return $uvx
    } catch {
        try {
            $uvx = (Get-Command uvx -ErrorAction Stop).Source
            return $uvx
        } catch {
            throw "serena.ps1: uvx executable not found. Set UVX_BIN or install uvx."
        }
    }
}

$uvxPath = Resolve-UvxPath

& $uvxPath --from git+https://github.com/oraios/serena serena @ArgsFromUser
