@echo off
REM File: bin/serena.cmd
REM Purpose: Windows wrapper for launching Serena CLI through uvx.
REM Context: Mirrors Codex MCP configuration so repository diagnostics can call `serena` directly.

setlocal enabledelayedexpansion

REM Allow overriding uvx location via UVX_BIN. Fallback to common install path or PATH lookup.
if not defined UVX_BIN (
    set "UVX_BIN=%USERPROFILE%\AppData\Local\Programs\Python\Python313\Scripts\uvx.exe"
    if not exist "!UVX_BIN!" (
        for %%I in (uvx.exe uvx) do (
            for %%J in (%%~$PATH:I) do if not defined UVX_BIN set "UVX_BIN=%%~fJ"
        )
    )
)

if not exist "!UVX_BIN!" (
    echo serena.cmd: uvx executable not found. Set UVX_BIN or install uvx.>&2
    exit /b 1
)

"!UVX_BIN!" --from git+https://github.com/oraios/serena serena %*
