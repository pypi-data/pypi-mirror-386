#!/bin/bash
# 安全なクリーンアップ調査スクリプト（削除なし）

set -euo pipefail  # エラー時停止、未定義変数エラー

echo "=== Cleanup DRY RUN Script ==="
echo "This script only SHOWS what can be cleaned. No deletion."
echo

# 1. Python cache
echo "1. Python cache directories:"
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
echo "   Found $PYCACHE_COUNT __pycache__ directories"
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    echo "   Sample locations:"
    find . -type d -name "__pycache__" 2>/dev/null | head -5 | sed 's/^/     /'
fi
echo

# 2. Old temp files
echo "2. Old temp files (30+ days):"
OLD_TEMP=$(find temp/ -type f -mtime +30 2>/dev/null | wc -l)
echo "   Found $OLD_TEMP old files"
if [ "$OLD_TEMP" -gt 0 ]; then
    echo "   Total size: $(find temp/ -type f -mtime +30 -exec du -ch {} + 2>/dev/null | grep total || echo 'N/A')"
fi
echo

# 3. Large files
echo "3. Large temp files (10MB+):"
find temp/ -type f -size +10M -exec ls -lh {} \; 2>/dev/null | head -5 || echo "   No large files found"
echo

# 4. Empty directories
echo "4. Empty directories in root:"
find . -maxdepth 1 -type d -empty 2>/dev/null | sed 's/^/   /'
echo

# 5. Cache directories status
echo "5. Development cache status:"
if [ -L ".ruff_cache" ]; then
    echo "   .ruff_cache -> $(readlink .ruff_cache) (symlinked)"
else
    echo "   .ruff_cache: $([ -d .ruff_cache ] && echo 'directory' || echo 'not found')"
fi

if [ -L ".import_linter_cache" ]; then
    echo "   .import_linter_cache -> $(readlink .import_linter_cache) (symlinked)"
else
    echo "   .import_linter_cache: $([ -d .import_linter_cache ] && echo 'directory' || echo 'not found')"
fi

if [ -L ".hypothesis" ]; then
    echo "   .hypothesis -> $(readlink .hypothesis) (symlinked)"
else
    echo "   .hypothesis: $([ -d .hypothesis ] && echo 'directory' || echo 'not found')"
fi
echo

echo "===== Summary ====="
echo "To perform actual cleanup, review the above and run specific commands manually."
echo "Example commands (USE WITH CAUTION):"
echo '  find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf'
echo '  find temp/ -type f -mtime +30 -delete'
echo "===== End of DRY RUN ====="
