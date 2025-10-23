#!/bin/bash
# Claude Code用Ruff自動実行スクリプト
# 用途: ファイル保存時の自動品質チェック・修正
# 作成日: 2025-08-31
# バージョン: v1.0.0

set -e

# ===============================================
# 環境変数とパラメーター設定
# ===============================================

# カラー定義
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 設定
readonly CONFIG_FILE="pyproject.toml"
readonly MAX_RETRY=3
readonly TIMEOUT=30

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ===============================================
# ファイルパス処理
# ===============================================

# Claude Code環境変数からファイルパスを取得
get_target_files() {
    local files=""

    # 引数からファイルパスを取得
    if [ "$#" -gt 0 ]; then
        files="$*"
        log_info "引数からファイル指定: $files"
    # Claude Code環境変数から取得
    elif [ -n "$CLAUDE_FILE_PATHS" ]; then
        files="$CLAUDE_FILE_PATHS"
        log_info "CLAUDE_FILE_PATHS環境変数から取得: $files"
    # フォールバック: 変更されたPythonファイルを自動検出
    else
        if command -v git >/dev/null 2>&1; then
            files=$(git diff --name-only --cached --diff-filter=AM | grep '\.py$' || true)
            if [ -n "$files" ]; then
                log_info "Git変更検出: $files"
            else
                log_warning "処理対象ファイルが見つかりません"
                return 1
            fi
        else
            log_error "ファイル指定なし、Git利用不可"
            return 1
        fi
    fi

    echo "$files"
}

# ===============================================
# Ruff実行関数
# ===============================================

# Ruffチェック＆自動修正
run_ruff_check() {
    local file="$1"
    local retry_count=0

    log_info "🔍 Ruffチェック開始: $(basename "$file")"

    while [ $retry_count -lt $MAX_RETRY ]; do
        if timeout $TIMEOUT ruff check --fix --show-fixes --config="$CONFIG_FILE" "$file"; then
            log_success "✅ Lintチェック完了: $(basename "$file")"
            return 0
        else
            retry_count=$((retry_count + 1))
            log_warning "⚠️ Lint警告 (試行 $retry_count/$MAX_RETRY): $(basename "$file")"

            if [ $retry_count -ge $MAX_RETRY ]; then
                log_error "❌ Lintチェック最大試行回数超過: $(basename "$file")"
                return 1
            fi

            sleep 1
        fi
    done
}

# Ruffフォーマット
run_ruff_format() {
    local file="$1"

    log_info "✨ Ruffフォーマット開始: $(basename "$file")"

    if timeout $TIMEOUT ruff format --config="$CONFIG_FILE" "$file"; then
        log_success "🎨 フォーマット完了: $(basename "$file")"
        return 0
    else
        log_error "❌ フォーマット失敗: $(basename "$file")"
        return 1
    fi
}

# ===============================================
# メイン処理
# ===============================================

main() {
    log_info "🚀 Claude Code Ruff統合リンター開始"

    # 設定ファイル存在確認
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "設定ファイル未発見: $CONFIG_FILE"
        exit 1
    fi

    # Ruffコマンド存在確認
    if ! command -v ruff >/dev/null 2>&1; then
        log_error "Ruffコマンドが見つかりません。インストールしてください: pip install ruff"
        exit 1
    fi

    # 処理対象ファイル取得
    local target_files
    if ! target_files=$(get_target_files "$@"); then
        log_error "処理対象ファイルの取得に失敗"
        exit 1
    fi

    # 統計情報
    local processed=0
    local failed=0
    local total=0

    # 各ファイルに対してRuff処理実行
    for file in $target_files; do
        # Pythonファイルのみ処理
        if [[ "$file" == *.py ]]; then
            total=$((total + 1))

            # ファイル存在確認
            if [ ! -f "$file" ]; then
                log_warning "ファイル未発見: $file"
                failed=$((failed + 1))
                continue
            fi

            log_info "📄 処理中: $file"

            # Ruffチェック実行
            if run_ruff_check "$file"; then
                # フォーマット実行
                if run_ruff_format "$file"; then
                    processed=$((processed + 1))
                    log_success "✨ 完了: $(basename "$file")"
                else
                    failed=$((failed + 1))
                fi
            else
                failed=$((failed + 1))
            fi

            echo "---"
        else
            log_info "⏭️ スキップ（非Pythonファイル）: $file"
        fi
    done

    # 結果レポート
    echo ""
    log_info "📊 処理結果レポート"
    log_info "  - 処理対象: $total ファイル"
    log_success "  - 成功: $processed ファイル"
    if [ $failed -gt 0 ]; then
        log_warning "  - 失敗: $failed ファイル"
    else
        log_success "  - 失敗: $failed ファイル"
    fi

    # 成功メッセージ
    if [ $failed -eq 0 ] && [ $total -gt 0 ]; then
        log_success "🎉 Ruff統合リンター処理完了（全件成功）"
        exit 0
    elif [ $total -eq 0 ]; then
        log_info "ℹ️ 処理対象Pythonファイルなし"
        exit 0
    else
        log_warning "⚠️ 一部ファイルで問題が発生しました"
        exit 1
    fi
}

# スクリプト実行
main "$@"
