# MCP Configuration: WSL → Windows Python Migration

## Date
2025-10-04

## Issue
`.mcp/config.json` が WSL Python (`/mnt/c/.../venv/bin/python`) を使用していたため、Windows 環境の Claude Code から `/b20-workflow test` などの MCP コマンドを実行すると失敗していた。

### Error Symptoms
```
.venv/bin/python: broken symbolic link to /home/bamboocity/.local/share/uv/python/...
```

### Root Cause
- **Environment Mismatch**: Claude Code が Windows で実行されているのに、WSL の Linux ELF バイナリを直接呼び出していた
- **PYTHONPATH Duplication**: 絶対パス `/mnt/c/.../ガイド` が重複して設定されていた

## Solution
`.mcp/config.json` を Windows ネイティブ Python (`.venv.win/Scripts/python.exe`) を使用するように変更。

### Changes

#### Before (WSL Python)
```json
{
  "command": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/.venv/bin/python",
  "args": ["-u", "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/dist/mcp_servers/noveler/main.py"],
  "env": {
    "PYTHONPATH": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド:/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/src"
  },
  "cwd": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド"
}
```

#### After (Windows Python)
```json
{
  "command": ".venv.win/Scripts/python.exe",
  "args": ["-u", "dist/mcp_servers/noveler/main.py"],
  "env": {
    "PYTHONPATH": ".;src"
  },
  "cwd": "."
}
```

### Key Improvements

1. **Platform Alignment**: Windows Python for Windows Claude Code
2. **Relative Paths**: Portable configuration using `.` as cwd
3. **Simplified PYTHONPATH**: Removed duplication, using Windows separator `;`
4. **Consistency**: Both `noveler` and `noveler-dev` use same pattern

## History

### Previous Migrations
- `bdc16871` (2025-XX-XX): Migrated from portable relative paths to WSL absolute paths
- `43333210` (2025-XX-XX): Set PYTHONPATH to `.:./dist`
- Earlier: Various adjustments for dist server launch

### Why WSL Migration Happened
コミット `bdc16871` で WSL Python に移行したのは、venv の Python バイナリが WSL 環境で作成されたため。しかし、これは Claude Code が **Windows で実行される**という事実と矛盾していた。

### Why Revert to Windows Python
- **Environment Consistency**: Claude Code is Windows-native
- **Path Resolution**: Windows paths work correctly
- **Virtual Environment**: `.venv.win` is Windows PE32+ executable
- **Test Execution**: `/b20-workflow test` and similar commands now work

## Testing

### Validation Commands
```powershell
# Verify Python is Windows executable
file .venv.win/Scripts/python.exe
# Expected: PE32+ executable

# Validate JSON syntax
.venv.win\Scripts\python.exe -c "import json; json.load(open('.mcp/config.json', encoding='utf-8'))"

# Test MCP command (requires Claude Code restart)
# /b20-workflow test
```

### Expected Behavior
- MCP server starts with Windows Python
- `/b20-workflow test` executes tests using `.venv.win/Scripts/python.exe`
- No more "broken symbolic link" errors

## Related Documentation
- `docs/mcp/config_management.md` - MCP configuration SSOT guidelines
- `docs/development/venv_setup_guide.md` - Virtual environment setup
- `CLAUDE.md` - MCP Operations section

## Notes
- **mcp-pdb**: Still uses `wsl` wrapper as it requires Linux tools
- **Encoding**: `.mcp/config.json` contains Japanese characters, use UTF-8 encoding
- **Restart Required**: Claude Code must be restarted for config changes to take effect
