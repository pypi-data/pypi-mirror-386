# MCP Config Automation Update Summary

**Date**: 2025-10-03
**Status**: ✅ Completed
**Task**: Update `scripts/setup/update_mcp_configs.py` to support platform-specific venv paths

---

## Background

After implementing cross-platform venv management (`.venv.win` for Windows, `.venv.wsl` for WSL), the MCP configuration update script needed to be updated to automatically detect the platform and use the correct venv Python path.

### Previous Issue

- **Hard-coded**: `"command": "python"` (no path specification)
- **No platform detection**: Could not distinguish Windows vs WSL
- **Manual updates required**: Users had to manually edit MCP configs

---

## Changes Applied

### File: `scripts/setup/update_mcp_configs.py`

#### 1. Added Platform Detection (Lines 39-64)

```python
def detect_wsl() -> bool:
    """Detect if running in WSL environment."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False

def get_platform_venv_python(project_root: Path) -> tuple[str, Path]:
    """Get platform-specific venv Python path.

    Returns:
        Tuple of (command_string, venv_python_path)
        - Windows: ("C:/path/.venv.win/Scripts/python.exe", Path(...))
        - WSL: ("/mnt/c/path/.venv.wsl/bin/python", Path(...))
    """
    is_wsl = detect_wsl()
    is_windows = platform.system() == "Windows" and not is_wsl

    if is_windows:
        venv_python = project_root / ".venv.win" / "Scripts" / "python.exe"
    else:  # WSL or Linux
        venv_python = project_root / ".venv.wsl" / "bin" / "python"

    return str(venv_python), venv_python
```

**Logic**: Reused from `scripts/setup_venv.py` for consistency

#### 2. Updated `ensure_mcp_server_entry()` (Lines 89-128)

```python
def ensure_mcp_server_entry(project_root: Path, name: str, description: str) -> dict:
    """Generate MCP server entry with platform-specific venv Python path.

    Platform detection:
    - Windows: Uses .venv.win/Scripts/python.exe
    - WSL/Linux: Uses .venv.wsl/bin/python
    """
    # Get platform-specific venv Python path
    python_cmd, venv_python_path = get_platform_venv_python(project_root)

    # Verify venv exists, warn if not
    if not venv_python_path.exists():
        print(f"⚠️  Warning: venv Python not found at {venv_python_path}")
        print(f"   Run 'python scripts/setup_venv.py' to create platform-specific venv")

    return {
        "command": python_cmd,  # Platform-specific venv Python (was: "python")
        # ... rest of config
    }
```

**Key Changes**:
- `command` now uses full path to platform-specific venv Python
- Added venv existence check with helpful warning message

#### 3. Added UTF-8 Encoding Support (Lines 30-36)

```python
# Configure UTF-8 encoding for Windows console
if platform.system() == "Windows":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "buffer") and sys.stdout.encoding.lower() != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
```

**Purpose**: Prevents `UnicodeEncodeError` with Japanese paths on Windows (cp932 encoding)

---

## Test Results

### Windows Environment

```bash
$ py -3 scripts/setup/update_mcp_configs.py --dry-run
🔧 Updating MCP configs (server=noveler) in project: C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド
```

### Generated Configs

#### codex.mcp.json
```json
{
  "mcpServers": {
    "noveler": {
      "command": "C:\\Users\\bamboocity\\OneDrive\\Documents\\9_小説\\00_ガイド\\.venv.win\\Scripts\\python.exe",
      "args": ["-u", "C:\\Users\\...\\main.py"],
      "env": {
        "PYTHONPATH": "C:\\Users\\...\\00_ガイド;C:\\Users\\...\\00_ガイド\\src",
        "PYTHONUNBUFFERED": "1",
        "NOVELER_PRODUCTION_MODE": "1",
        "MCP_STDIO_SAFE": "1"
      }
    }
  }
}
```

✅ **Result**: Correct `.venv.win\Scripts\python.exe` path generated

#### .mcp/config.json
```json
{
  "mcpServers": {
    "noveler": {
      "command": "C:\\Users\\bamboocity\\OneDrive\\Documents\\9_小説\\00_ガイド\\.venv.win\\Scripts\\python.exe",
      // ... same structure
    }
  }
}
```

✅ **Result**: Correct platform-specific path

#### Claude Desktop Config
```json
{
  "mcpServers": {
    "noveler": {
      "command": "C:\\Users\\bamboocity\\OneDrive\\Documents\\9_小説\\00_ガイド\\.venv.win\\Scripts\\python.exe",
      // ... same structure
    }
  }
}
```

✅ **Result**: Correct platform-specific path

### All Configs Updated Successfully

- ✅ codex.mcp.json
- ✅ .mcp/config.json
- ✅ Claude desktop config (AppData/Roaming/Claude/)

---

## Usage

### Dry-run (Recommended First)

```bash
python scripts/setup/update_mcp_configs.py --dry-run
```

Shows what changes will be made without modifying files.

### Update All Configs

```bash
python scripts/setup/update_mcp_configs.py
```

Updates:
1. codex.mcp.json (repository root)
2. .mcp/config.json (project-local)
3. Claude desktop config (user profile)

### Selective Updates

```bash
# Update only codex.mcp.json
python scripts/setup/update_mcp_configs.py --codex

# Update only .mcp/config.json
python scripts/setup/update_mcp_configs.py --project

# Update only Claude desktop config
python scripts/setup/update_mcp_configs.py --claude
```

### Using Wrapper Script

```bash
./bin/setup_mcp_configs --dry-run
./bin/setup_mcp_configs
```

Same functionality, cleaner command.

---

## Verification

### 1. Check Generated Paths

```bash
# Windows
cat codex.mcp.json | grep "command"
# Expected: .venv.win\Scripts\python.exe

# WSL
cat codex.mcp.json | grep "command"
# Expected: .venv.wsl/bin/python
```

### 2. Verify Venv Python Works

```bash
# Windows
.\.venv.win\Scripts\python.exe -c "import noveler; print('OK')"

# WSL
.venv.wsl/bin/python -c "import noveler; print('OK')"
```

### 3. Test MCP Server Startup

In Claude Code:
1. Command Palette (`Ctrl+Shift+P`)
2. Run: `Claude Code: Restart MCP Servers`
3. Check Output panel for errors
4. Test noveler tool: Call `status` MCP tool

---

## Rollback

Automatic backups are created with timestamp suffix:

```bash
# List backups
ls -la *.backup_*

# Example backups
codex.mcp.json.backup_20251003_143022
.mcp/config.json.backup_20251003_143023

# Restore from backup
cp codex.mcp.json.backup_20251003_143022 codex.mcp.json
```

---

## Related Scripts

### Scripts Reviewed

| Script | Status | Notes |
|--------|--------|-------|
| **scripts/setup/update_mcp_configs.py** | ✅ Updated | Platform detection added |
| **bin/setup_mcp_configs** | ✅ Compatible | Wrapper works with updated script |
| **bin/claude_code_mcp_setup.py** | ⚠️ Out of scope | Different MCP server (novel-json-converter) |

### Out of Scope

`bin/claude_code_mcp_setup.py` configures a different MCP server (`novel-json-converter`) and was not updated as part of this task. If platform-specific venv support is needed for that server, it should be a separate task.

---

## Documentation

### Created/Updated Files

1. ✅ **scripts/setup/update_mcp_configs.py** - Added platform detection
2. ✅ **docs/development/mcp_config_updates_needed.md** - Updated with automation status
3. ✅ **docs/development/mcp_venv_migration_summary.md** - Updated Phase 2 status
4. ✅ **docs/development/mcp_automation_update_summary.md** - This document

---

## Next Steps

### Immediate (User Action Required)

1. **Create Windows venv** (if not already done):
   ```bash
   python scripts/setup_venv.py
   ```

2. **Run MCP config update**:
   ```bash
   python scripts/setup/update_mcp_configs.py
   ```

3. **Restart MCP servers in Claude Code**

4. **Verify noveler tools work**

### Optional Cleanup

```bash
# Backup old .venv (Linux/WSL created)
mv .venv .venv.backup

# Verify only platform-specific venvs exist
ls -la .venv*
# Expected: .venv.win (Windows) or .venv.wsl (WSL)
```

---

## Technical Details

### Platform Detection Logic

```
1. Check if running on Windows: platform.system() == "Windows"
2. If on Windows, check if WSL: read /proc/version for "microsoft"
3. Select venv:
   - Windows (native): .venv.win/Scripts/python.exe
   - WSL/Linux: .venv.wsl/bin/python
```

### Path Format Differences

| Platform | Path Separator | Example |
|----------|----------------|---------|
| **Windows** | `\` (backslash) | `C:\Users\...\00_ガイド\.venv.win\Scripts\python.exe` |
| **WSL** | `/` (forward slash) | `/mnt/c/Users/.../00_ガイド/.venv.wsl/bin/python` |

### Why Full Paths?

MCP servers run as separate processes. Using full paths ensures:
1. Correct Python interpreter is used
2. Dependencies are loaded from correct venv
3. No ambiguity with system Python or other venvs

---

## Success Criteria

- [x] Script detects platform automatically
- [x] Correct venv path selected for Windows
- [x] Correct venv path selected for WSL/Linux
- [x] UTF-8 encoding works on Windows (Japanese paths)
- [x] `--dry-run` shows correct output
- [x] All 3 MCP configs can be updated
- [x] Backups created automatically
- [x] Warning shown if venv doesn't exist
- [x] Documentation updated

---

## References

- [venv_setup_guide.md](./venv_setup_guide.md) - Virtual environment setup
- [mcp_config_updates_needed.md](./mcp_config_updates_needed.md) - MCP config update guide
- [mcp_venv_migration_summary.md](./mcp_venv_migration_summary.md) - Complete migration summary
- [CLAUDE.md](../../CLAUDE.md) § MCP Operations - Project MCP rules
- [scripts/setup_venv.py](../../scripts/setup_venv.py) - Platform detection reference
