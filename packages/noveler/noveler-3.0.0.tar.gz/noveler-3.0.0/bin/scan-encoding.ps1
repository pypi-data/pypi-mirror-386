# File: bin/scan-encoding.ps1
# Purpose: Wrapper to run warn-only encoding scan across docs/src (Windows).
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsRest
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path "$PSScriptRoot\..\").Path
& python "$Root\scripts\scan_encoding.py" @ArgsRest

