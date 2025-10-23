#!/bin/bash
# migrate_templates_direct.sh - 直接的なファイル移動

set -euo pipefail
BACKUP_DIR="templates_backup_$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="templates_temp_$(date +%Y%m%d_%H%M%S)"
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

# Phase 1: バックアップ
log "Creating backup: $BACKUP_DIR"
cp -r templates "$BACKUP_DIR" || rollback "Backup failed"

# Phase 2: 新構造構築
log "Building new structure..."
mkdir -p "$TEMP_DIR"/{writing,quality/{checks,analysis},plot,special,legacy}

# Phase 3: 具体的なファイル移動

# 執筆ステップ (19ファイル)
log "Moving writing templates..."
cp templates/write_step*.yaml "$TEMP_DIR/writing/"

# チェックステップ (12ファイル)
log "Moving check templates..."
cp templates/check_step*.yaml "$TEMP_DIR/quality/checks/"

# 分析テンプレート (7ファイル)
log "Moving analysis templates..."
cp templates/comprehensive.yaml "$TEMP_DIR/quality/analysis/"
cp templates/consistency_analysis.yaml "$TEMP_DIR/quality/analysis/"
cp templates/creative_focus.yaml "$TEMP_DIR/quality/analysis/"
cp templates/emotional_depth_analyzer.yaml "$TEMP_DIR/quality/analysis/"
cp templates/quick.yaml "$TEMP_DIR/quality/analysis/"
cp templates/reader_experience.yaml "$TEMP_DIR/quality/analysis/"
cp templates/structural.yaml "$TEMP_DIR/quality/analysis/"

# プロットテンプレート (4ファイル)
log "Moving plot templates..."
cp templates/章別プロットテンプレート.yaml "$TEMP_DIR/plot/"
cp templates/章別プロットテンプレート_視点管理拡張.yaml "$TEMP_DIR/plot/"
cp templates/話別プロットテンプレート.yaml "$TEMP_DIR/plot/"
cp templates/chapter_plot.yaml "$TEMP_DIR/plot/"

# 特殊用途 (3ファイル)
log "Moving special templates..."
cp templates/stage5_品質確認テンプレート.yaml "$TEMP_DIR/special/"
cp templates/self_triggering_quality_prompt_template.yaml "$TEMP_DIR/special/"
cp templates/執筆品質ルールテンプレート.yaml "$TEMP_DIR/special/"

# レガシー (2ファイル)
log "Moving legacy templates..."
cp templates/step00_scope_definition.yaml "$TEMP_DIR/legacy/"
cp templates/debug.yaml "$TEMP_DIR/legacy/"

# README.mdコピー
[ -f templates/README.md ] && cp templates/README.md "$TEMP_DIR/"

# Phase 4: 検証
log "Verifying migration..."
ORIGINAL_COUNT=$(find templates -maxdepth 1 -name "*.yaml" -type f | wc -l)
NEW_COUNT=$(find "$TEMP_DIR" -name "*.yaml" -type f | wc -l)

log "Original files: $ORIGINAL_COUNT"
log "New structure files: $NEW_COUNT"

if [ "$ORIGINAL_COUNT" -ne "$NEW_COUNT" ]; then
    log "Detailed file comparison:"
    log "Original files:"
    find templates -maxdepth 1 -name "*.yaml" -type f | sort | tee -a "$MIGRATION_LOG"
    log "New structure files:"
    find "$TEMP_DIR" -name "*.yaml" -type f | sort | tee -a "$MIGRATION_LOG"
    rollback "File count mismatch! Original: $ORIGINAL_COUNT, New: $NEW_COUNT"
fi

# 各ディレクトリのファイル数を確認
log "Directory breakdown:"
for dir in writing quality/checks quality/analysis plot special legacy; do
    count=$(find "$TEMP_DIR/$dir" -name "*.yaml" -type f 2>/dev/null | wc -l)
    log "  $dir: $count files"
done

# Phase 5: アトミック置換
log "Replacing templates directory..."
mv templates "templates_old_$(date +%s)"
mv "$TEMP_DIR" templates
rm -rf templates_old_*

log "Migration completed successfully!"
log "Backup stored in: $BACKUP_DIR"
log "Migration log: $MIGRATION_LOG"
