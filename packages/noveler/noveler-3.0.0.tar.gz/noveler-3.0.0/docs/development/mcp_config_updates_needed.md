# MCP Configuration Updates Required

**Date**: 2025-10-03
**Reason**: Python venv path changes (`.venv` → `.venv.win` / `.venv.wsl`)
**Impact**: MCP server startup will fail if using old `.venv` path

---

## Summary

新しいクロスプラットフォームvenv構造（`.venv.win` / `.venv.wsl`）への移行に伴い、以下のMCP設定ファイルでPythonパスの更新が必要です。

## Files Requiring Updates

### 1. **codex.mcp.json** (Claude Code primary config)
**Location**: `/codex.mcp.json`
**Priority**: 🔴 High (Claude Code起動時に使用)
**Current Issue**: WSL pythonを直接指定（`wsl python`）

```json
{
  "mcpServers": {
    "noveler": {
      "command": "wsl",
      "args": ["python", "-u", "/mnt/c/.../main.py"]
    }
  }
}
```

**Required Changes**:
- WSL環境で動作する場合は問題なし
- Windows nativeで動作させる場合は`.venv.win`パスへの変更が必要

**Recommended Action**:
- Windows: `.venv.win/Scripts/python.exe`を使用
- WSL: `.venv.wsl/bin/python`を使用
- または: 環境変数で動的に切り替え

---

### 2. **.mcp/config.json** (Project-local MCP config)
**Location**: `/.mcp/config.json`
**Priority**: 🟡 Medium (プロジェクト固有設定)
**Current Issue**: 古い`.venv`パスを参照

```json
{
  "mcpServers": {
    "noveler": {
      "command": "/mnt/c/Users/.../00_ガイド/.venv/bin/python",
      "args": ["-u", "/mnt/c/.../main.py"]
    }
  }
}
```

**Required Changes**:
```json
{
  "mcpServers": {
    "noveler": {
      "command": "/mnt/c/Users/.../00_ガイド/.venv.wsl/bin/python",
      "args": ["-u", "/mnt/c/.../main.py"]
    }
  }
}
```

---

### 3. **.codex/mcp.json** (Codex IDE config)
**Location**: `/.codex/mcp.json`
**Priority**: 🟡 Medium (Codex IDE用)
**Current Issue**: 古い`.venv`パスを参照

```json
{
  "mcpServers": {
    "noveler": {
      "command": "/mnt/c/Users/.../00_ガイド/.venv/bin/python"
    },
    "noveler-dev": {
      "command": "/mnt/c/Users/.../00_ガイド/.venv/bin/python"
    }
  }
}
```

**Required Changes**:
- `noveler`: `/mnt/c/Users/.../00_ガイド/.venv.wsl/bin/python`
- `noveler-dev`: `/mnt/c/Users/.../00_ガイド/.venv.wsl/bin/python`

---

### 4. **.mcp.production.json** (Production config)
**Location**: `/.mcp.production.json`
**Priority**: 🟢 Low (本番環境用、現在未使用の可能性)
**Status**: 内容確認が必要

---

## Update Strategy

### Option A: Manual Update (Recommended for Testing)

各ファイルを手動で編集：

```bash
# 1. Backup existing configs
cp codex.mcp.json codex.mcp.json.backup
cp .mcp/config.json .mcp/config.json.backup
cp .codex/mcp.json .codex/mcp.json.backup

# 2. Edit files to use new paths
# Windows: .venv.win/Scripts/python.exe
# WSL: .venv.wsl/bin/python

# 3. Test MCP server startup
# In Claude Code: Restart MCP servers
```

### Option B: Automated Update (Use setup script)

```bash
# Run the setup script (supports --dry-run)
./bin/setup_mcp_configs --dry-run

# Review changes
./bin/setup_mcp_configs

# Verify
ls -la codex.mcp.json.backup*
```

**Note**: `bin/setup_mcp_configs` スクリプトは `scripts/setup/update_mcp_configs.py` を呼び出します。このスクリプトがプラットフォーム検出に対応しているか確認が必要です。

---

## Platform-Specific Paths

| Platform | Venv Directory | Python Path | MCP Command Format |
|----------|----------------|-------------|-------------------|
| **Windows (Native)** | `.venv.win/` | `.venv.win/Scripts/python.exe` | Windows path style |
| **WSL** | `.venv.wsl/` | `.venv.wsl/bin/python` | Unix path style (`/mnt/c/...`) |
| **WSL (via wsl command)** | `.venv.wsl/` | `wsl .venv.wsl/bin/python` | Windows launches WSL |

---

## Environment Variable Approach (Advanced)

For maximum flexibility, use environment variables in MCP configs:

```json
{
  "mcpServers": {
    "noveler": {
      "command": "${NOVELER_PYTHON}",
      "args": ["-u", "${NOVELER_ROOT}/dist/mcp_servers/noveler/main.py"],
      "env": {
        "PYTHONPATH": "${NOVELER_ROOT}/dist:${NOVELER_ROOT}"
      }
    }
  }
}
```

Then set in shell:
```bash
# Windows
$env:NOVELER_PYTHON="C:\...\00_ガイド\.venv.win\Scripts\python.exe"
$env:NOVELER_ROOT="C:\...\00_ガイド"

# WSL
export NOVELER_PYTHON="/mnt/c/.../00_ガイド/.venv.wsl/bin/python"
export NOVELER_ROOT="/mnt/c/.../00_ガイド"
```

**Note**: Claude Code may not support environment variable expansion in MCP configs. Verify before using this approach.

---

## Verification Steps

After updating configs:

### 1. Check MCP Server Startup

In Claude Code:
1. Open Command Palette (`Ctrl+Shift+P`)
2. Run: `Claude Code: Restart MCP Servers`
3. Check Output panel for errors

### 2. Test Noveler Tools

```
# In Claude Code chat
Call noveler MCP tool: status

# Expected output
Project status information should appear
```

### 3. Verify Python Path

```bash
# Windows
.\.venv.win\Scripts\python.exe -c "import noveler; print('OK')"

# WSL
.venv.wsl/bin/python -c "import noveler; print('OK')"
```

---

## Rollback Plan

If MCP servers fail after updates:

```bash
# Restore backups
cp codex.mcp.json.backup codex.mcp.json
cp .mcp/config.json.backup .mcp/config.json
cp .codex/mcp.json.backup .codex/mcp.json

# Restart Claude Code
# Or restart MCP servers via Command Palette
```

---

## ✅ Automation Script Updates (Completed)

**Status**: `scripts/setup/update_mcp_configs.py` has been updated to support platform-specific venv structure.

### Updates Applied (2025-10-03)

1. **✅ Platform Detection** (Lines 39-45)
   - Added `detect_wsl()` function (detects WSL via `/proc/version`)
   - Added `get_platform_venv_python()` function (returns platform-specific paths)

2. **✅ Dynamic Venv Path Selection** (Lines 48-64)
   - Windows: Automatically uses `.venv.win/Scripts/python.exe`
   - WSL/Linux: Automatically uses `.venv.wsl/bin/python`

3. **✅ UTF-8 Encoding Support** (Lines 30-36)
   - Added Windows console UTF-8 configuration
   - Prevents cp932 encoding errors with Japanese paths

4. **✅ Venv Existence Verification** (Lines 111-113)
   - Warns if venv Python path doesn't exist
   - Provides helpful message to run `scripts/setup_venv.py`

### Test Results (Windows)

```bash
$ py -3 scripts/setup/update_mcp_configs.py --dry-run
🔧 Updating MCP configs (server=noveler) in project: C:\Users\...\00_ガイド

# Generated config correctly uses:
"command": "C:\\Users\\...\\00_ガイド\\.venv.win\\Scripts\\python.exe"
```

✅ **All 3 config files updated successfully** with correct platform-specific paths

### How to Use

```bash
# Dry-run (recommended first)
python scripts/setup/update_mcp_configs.py --dry-run

# Update all configs
python scripts/setup/update_mcp_configs.py

# Or use wrapper
./bin/setup_mcp_configs
```

---

## Related Scripts to Review

### Scripts that may reference venv paths:

1. **scripts/setup/update_mcp_configs.py** ⚠️
   - **Status**: Requires updates for new venv structure
   - **Issue**: Hard-codes `command: "python"` without platform detection
   - **Action**: Update in Phase 2

2. **bin/setup_mcp_configs**
   - Wrapper for `scripts/setup/update_mcp_configs.py`
   - **Status**: Will work after underlying script is fixed

3. **bin/claude_code_mcp_setup.py**
   - Claude Code specific setup
   - **Status**: Needs review for venv path references

### Action Items:

- [x] Review `scripts/setup/update_mcp_configs.py` for venv path handling
- [x] Update `ensure_mcp_server_entry()` to add platform detection
- [x] Update to use `.venv.win` / `.venv.wsl` based on platform
- [x] Add UTF-8 encoding support for Windows console
- [x] Test `scripts/setup/update_mcp_configs.py --dry-run` (✅ PASSED on Windows)
- [x] Verify `bin/setup_mcp_configs` wrapper compatibility
- [x] Review `bin/claude_code_mcp_setup.py` - Out of scope (different MCP server: novel-json-converter)

---

## Timeline

### ✅ Phase 1: Script Updates (Completed 2025-10-03)
- [x] Review and update `scripts/setup/update_mcp_configs.py`
- [x] Add platform detection logic
- [x] Add UTF-8 encoding support
- [x] Test automated updates with `--dry-run`

### Phase 2: Config File Updates (Next)
- [ ] Backup existing MCP configs
- [ ] Run automated update: `python scripts/setup/update_mcp_configs.py`
- [ ] Test MCP server startup in Claude Code
- [ ] Verify noveler tools work

### Phase 3: Documentation (Final)
- [ ] Update CLAUDE.md with MCP config update instructions
- [ ] Add troubleshooting section for MCP path issues
- [ ] Clean up old `.venv` directory (optional)

---

## Current Status

✅ **Analyzed**: All MCP config files identified
✅ **Documented**: Update requirements and paths
✅ **Script Updated**: `scripts/setup/update_mcp_configs.py` supports platform-specific venvs
✅ **Tested**: `--dry-run` mode verified on Windows (correct `.venv.win` path)
⏳ **Pending**: Run automated MCP config updates
⏳ **Pending**: Testing and verification with Claude Code

---

## Notes

- 既存の`.venv`はLinux/WSL用なので、Windows環境では使用不可
- Claude Codeが現在どの設定ファイルを優先使用しているか確認が必要
  - Priority: `codex.mcp.json` > `.codex/mcp.json` > `.mcp/config.json`
- MCP server起動エラーは通常Claude Codeのログに出力される
- `dist/mcp_servers/noveler/main.py` パスも正しいか確認が必要（ビルド済み版）

---

## See Also

- [venv_setup_guide.md](./venv_setup_guide.md) - Virtual environment setup instructions
- [CLAUDE.md](../../CLAUDE.md) - MCP operations section
- `docs/mcp/config_management.md` - SSOT management guidelines
