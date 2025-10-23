@echo off
REM File: bin/invoke.cmd
REM Purpose: Windows native wrapper for invoke.py
REM Context: Cross-platform compatibility for Windows users without Git Bash

setlocal enabledelayedexpansion

REM Determine project root (one level up from bin/)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

REM Find Python executable
set "PYTHON_BIN="
if not "%PYTHON%"=="" (
    set "PYTHON_BIN=%PYTHON%"
) else (
    where py >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_BIN=py -3"
    ) else (
        where python3 >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_BIN=python3"
        ) else (
            where python >nul 2>&1
            if !errorlevel! equ 0 (
                set "PYTHON_BIN=python"
            ) else (
                echo bin/invoke.cmd: Python executable not found. Install Python 3.8+ or set %%PYTHON%%. >&2
                exit /b 1
            )
        )
    )
)

REM Execute invoke.py with all arguments
%PYTHON_BIN% "%ROOT_DIR%\scripts\tooling\invoke.py" %*
