# Virtual Environment Setup Guide

## Overview

This project uses **uv** for fast, reliable virtual environment management. The `.venv` directory contains a platform-appropriate Python environment.

- **Windows**: `.venv/Scripts/python.exe` (PE32+ executable)
- **WSL/Linux**: `.venv/bin/python` (ELF executable)

## Quick Start

### Windows (PowerShell/CMD)

```powershell
# Install uv (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create venv and install dependencies
uv venv .venv --python 3.13
uv pip install -e .

# Activate
.\.venv\Scripts\Activate.ps1

# Verify
python --version
python -c "import noveler; print(noveler.__version__)"
```

### WSL/Linux

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create venv and install dependencies
uv venv .venv --python 3.13
uv pip install -e .

# Activate
source .venv/bin/activate

# Verify
python --version
python -c "import noveler; print(noveler.__version__)"
```

### Automated Setup (WSL/Linux)

Use the provided script for a complete automated setup:

```bash
cd /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド
bash scripts/setup/rebuild_wsl_venv.sh
```

This script will:
1. Check you're in a true WSL environment
2. Install uv if needed
3. Remove broken `.venv` if exists
4. Create a fresh Linux Python 3.13 venv
5. Install all dependencies including dev tools

## Important: WSL Environment Notes

### Run in True WSL, Not Git Bash

❌ **Wrong** (Git Bash):
```bash
# Git Bash creates Windows Python venv
$ uname -a
MINGW64_NT-10.0-26100 ...  # ← Not WSL!
```

✅ **Correct** (WSL Ubuntu):
```bash
# WSL creates Linux Python venv
$ uname -a
Linux ... Microsoft ...  # ← True WSL
```

### Why This Matters

When Claude Code runs MCP servers via WSL, it expects:
- **Linux ELF executables** (not Windows PE .exe)
- **Unix-style paths** (`/mnt/c/...`)
- **Native Linux performance**

Using Windows Python from WSL adds overhead and can cause issues.

## Troubleshooting

### Broken .venv Symlink

If you see `broken symbolic link` errors:

```bash
# Check symlink status
file .venv/bin/python
# Output: broken symbolic link to /home/user/.local/share/uv/python/...

# Solution: Rebuild venv in WSL Ubuntu
bash scripts/setup/rebuild_wsl_venv.sh
```

### Permission Denied (Windows)

```powershell
# Enable script execution
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### uv Not Found

```bash
# WSL/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Import Error After Install

```bash
# Reinstall in editable mode
uv pip install -e .

# Or force reinstall
uv pip install -e . --force-reinstall
```

## Platform Detection

The `.venv` structure differs by platform:

| Platform | Python Path | Type | MCP Compatible |
|----------|-------------|------|----------------|
| **Windows** | `.venv/Scripts/python.exe` | PE32+ | Via WSL wrapper |
| **WSL** | `.venv/bin/python` | ELF64 | ✅ Native |
| **Linux** | `.venv/bin/python` | ELF64 | ✅ Native |

## Dependencies

All dependencies are managed in `pyproject.toml`:

```toml
[project]
dependencies = [
    "PyYAML>=6.0",
    "rich>=13.0.0",
    "mcp>=1.13.0",
    "janome>=0.5.0",
    # ... more
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.0.290",
    # ... more
]
```

### Installation Modes

```bash
# Production (runtime only)
uv pip install .

# Development (with test tools)
uv pip install -e .[dev]
```

## Verification Checklist

After setup, verify:

```bash
# 1. Python version
python --version  # Should be 3.13.x

# 2. Noveler package
python -c "import noveler; print(noveler.__version__)"

# 3. MCP dependencies
python -c "import mcp; print('MCP OK')"

# 4. File type (WSL only)
file .venv/bin/python  # Should show "ELF 64-bit"
```

## Migration from Old Setup

### From scripts/setup_venv.py

The old `setup_venv.py` created `.venv.win` and `.venv.wsl`. This is no longer used.

```bash
# Remove old venvs
rm -rf .venv.win .venv.wsl

# Create new uv-managed venv
uv venv .venv --python 3.13
uv pip install -e .[dev]
```

### From Manual venv

```bash
# Remove old venv
rm -rf .venv

# Create with uv
uv venv .venv --python 3.13
uv pip install -e .[dev]
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Setup Python environment
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    uv venv .venv --python 3.13
    uv pip install -e .[dev]

- name: Run tests
  run: |
    source .venv/bin/activate
    pytest tests/
```

## FAQ

### Q: Why uv instead of venv or virtualenv?

**A**: uv is significantly faster (10-100x) and provides:
- Unified dependency resolution
- Cross-platform compatibility
- Built-in lockfile support
- Better reproducibility

### Q: Can I use conda or poetry instead?

**A**: Yes, but ensure:
1. Python 3.13+ compatibility
2. Editable install: `pip install -e .[dev]`
3. Correct platform (Linux ELF for WSL)

### Q: What if I need both Windows and WSL venvs?

**A**: Create separate venvs:

```bash
# Windows (in PowerShell)
uv venv .venv.win --python 3.13

# WSL (in Ubuntu terminal)
uv venv .venv --python 3.13
```

Then use appropriate paths in your configs.

### Q: How do I update dependencies?

```bash
# Activate venv
source .venv/bin/activate

# Update all
uv pip install -e .[dev] --upgrade

# Update specific package
uv pip install --upgrade <package-name>
```

## Related Documentation

- [pyproject.toml](../../pyproject.toml) - Dependency specifications
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines
- [docs/mcp/config_management.md](../mcp/config_management.md) - MCP configuration
- [scripts/setup/rebuild_wsl_venv.sh](../../scripts/setup/rebuild_wsl_venv.sh) - Automated setup script
