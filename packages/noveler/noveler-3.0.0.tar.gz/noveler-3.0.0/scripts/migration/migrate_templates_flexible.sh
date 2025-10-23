#!/bin/bash
# migrate_templates_flexible.sh

set -euo pipefail
BACKUP_DIR="templates_backup_$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="templates_temp_$(date +%Y%m%d_%H%M%S)"
INVENTORY_FILE="templates_inventory.txt"
FILES_LIST="templates_files.txt"
MIGRATION_LOG="templates_migration_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$MIGRATION_LOG"
}

rollback() {
    log "ERROR: $1"
    log "Rolling back changes..."
    rm -rf templates
    [ -d "$BACKUP_DIR" ] && mv "$BACKUP_DIR" templates
    rm -rf "$TEMP_DIR"
    exit 1
}

# Phase 1: インベントリ確認
log "Checking inventory file..."
if [ ! -f "$INVENTORY_FILE" ]; then
    rollback "Inventory file $INVENTORY_FILE not found"
fi

# Phase 2: バックアップ
log "Creating backup: $BACKUP_DIR"
cp -r templates "$BACKUP_DIR" || rollback "Backup failed"

# Phase 3: 新構造構築
log "Building new structure..."
mkdir -p "$TEMP_DIR"/{writing,quality/{checks,analysis},plot,special,legacy}

# Phase 4: インベントリベースの移動
log "Moving files based on inventory..."
while read -r line; do
    # コメント行スキップ
    [[ "$line" =~ ^#.*$ ]] && continue

    # 空行スキップ
    [ -z "$line" ] && continue

    # -> で分割
    if [[ "$line" =~ ^(.+)\ -\>\ (.+)$ ]]; then
        pattern="${BASH_REMATCH[1]// /}"
        target="${BASH_REMATCH[2]// /}"

        # ファイル移動
        find templates -maxdepth 1 -name "$pattern" -type f 2>/dev/null | \
            while IFS= read -r file; do
                if [ -f "$file" ]; then
                    target_dir="$TEMP_DIR/$target"
                    filename=$(basename "$file")
                    log "  Moving: $filename -> $target"
                    cp "$file" "$target_dir" || log "  Warning: Failed to copy $file"
                fi
            done
    fi
done < "$INVENTORY_FILE"

# README.mdコピー
[ -f templates/README.md ] && cp templates/README.md "$TEMP_DIR/"

# Phase 5: 検証
log "Verifying migration..."
ORIGINAL_COUNT=$(find templates -maxdepth 1 -name "*.yaml" -type f | wc -l)
NEW_COUNT=$(find "$TEMP_DIR" -name "*.yaml" -type f | wc -l)

log "Original files: $ORIGINAL_COUNT"
log "New structure files: $NEW_COUNT"

if [ "$ORIGINAL_COUNT" -ne "$NEW_COUNT" ]; then
    rollback "File count mismatch! Original: $ORIGINAL_COUNT, New: $NEW_COUNT"
fi

# 各ディレクトリのファイル数を確認
log "Directory breakdown:"
for dir in writing quality/checks quality/analysis plot special legacy; do
    count=$(find "$TEMP_DIR/$dir" -name "*.yaml" -type f 2>/dev/null | wc -l)
    log "  $dir: $count files"
done

# Phase 6: アトミック置換
log "Replacing templates directory..."
mv templates "templates_old_$(date +%s)"
mv "$TEMP_DIR" templates
rm -rf templates_old_*

log "Migration completed successfully!"
log "Backup stored in: $BACKUP_DIR"
log "Migration log: $MIGRATION_LOG"
