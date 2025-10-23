#!/bin/bash
# E2Eテスト結果とカバレッジの統合レポート生成
# 使用方法: ./bin/generate_e2e_report.sh [オプション]

set -euo pipefail

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# ヘルプ表示
show_help() {
    cat << EOF
E2Eテスト統合レポート生成スクリプト

使用方法:
    ./bin/generate_e2e_report.sh [オプション]

オプション:
    -h, --help              このヘルプを表示
    -r, --run-tests         レポート生成前にE2Eテストを実行
    -c, --coverage-only     カバレッジ分析のみ実行
    -f, --full              フルレポート生成（テスト実行+カバレッジ+統合レポート）
    -o, --output DIR        出力ディレクトリを指定
    --no-html               HTMLレポートを生成しない
    --no-json               JSONレポートを生成しない
    -v, --verbose           詳細出力

実行例:
    ./bin/generate_e2e_report.sh --full                    # 完全レポート生成
    ./bin/generate_e2e_report.sh --coverage-only           # カバレッジ分析のみ
    ./bin/generate_e2e_report.sh --run-tests --verbose     # テスト実行+レポート生成

EOF
}

# デフォルト設定
RUN_TESTS=false
COVERAGE_ONLY=false
FULL_REPORT=false
OUTPUT_DIR=""
GENERATE_HTML=true
GENERATE_JSON=true
VERBOSE=false

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--run-tests)
            RUN_TESTS=true
            shift
            ;;
        -c|--coverage-only)
            COVERAGE_ONLY=true
            shift
            ;;
        -f|--full)
            FULL_REPORT=true
            RUN_TESTS=true
            shift
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --no-html)
            GENERATE_HTML=false
            shift
            ;;
        --no-json)
            GENERATE_JSON=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            error "不明なオプション: $1"
            ;;
    esac
done

# プロジェクトルートに移動
cd "${PROJECT_ROOT}"

# 出力ディレクトリの設定
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="temp/reports/e2e_$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$OUTPUT_DIR"
log "出力ディレクトリ: $OUTPUT_DIR"

# E2Eテスト実行
if [[ "$RUN_TESTS" == true ]] && [[ "$COVERAGE_ONLY" == false ]]; then
    log "E2Eテスト実行中..."

    # テスト結果出力ファイル
    TEST_LOG="$OUTPUT_DIR/e2e_test_execution.log"
    JUNIT_XML="$OUTPUT_DIR/e2e_test_results.xml"
    HTML_REPORT="$OUTPUT_DIR/e2e_test_report.html"

    # E2Eテスト実行
    TEST_ARGS=()
    TEST_ARGS+=("-c" "tests/e2e/pytest_e2e.ini")
    TEST_ARGS+=("--junit-xml=$JUNIT_XML")

    if [[ "$GENERATE_HTML" == true ]]; then
        TEST_ARGS+=("--html=$HTML_REPORT" "--self-contained-html")
    fi

    if [[ "$VERBOSE" == true ]]; then
        TEST_ARGS+=("-vv")
    fi

    # カバレッジ付きテスト実行
    if [[ "$FULL_REPORT" == true ]]; then
        TEST_ARGS+=("--cov=scripts" "--cov-report=xml:$OUTPUT_DIR/coverage.xml" "--cov-report=html:$OUTPUT_DIR/htmlcov")
    fi

    # テスト実行
    if pytest "${TEST_ARGS[@]}" tests/e2e/ > "$TEST_LOG" 2>&1; then
        success "E2Eテスト完了"
    else
        warn "E2Eテストで一部失敗がありました (詳細: $TEST_LOG)"
    fi

    # テスト結果サマリーの生成
    if [[ -f "$JUNIT_XML" ]]; then
        log "テスト結果解析中..."
        python3 -c "
import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse('$JUNIT_XML')
    root = tree.getroot()

    # テストスイートの情報取得
    tests = int(root.get('tests', 0))
    failures = int(root.get('failures', 0))
    errors = int(root.get('errors', 0))
    skipped = int(root.get('skipped', 0))
    time = float(root.get('time', 0))

    success = tests - failures - errors - skipped
    success_rate = (success / max(tests, 1)) * 100

    print(f'テスト実行サマリー:')
    print(f'  総テスト数: {tests}')
    print(f'  成功: {success}')
    print(f'  失敗: {failures}')
    print(f'  エラー: {errors}')
    print(f'  スキップ: {skipped}')
    print(f'  成功率: {success_rate:.1f}%')
    print(f'  実行時間: {time:.1f}秒')

    # 結果をファイルに保存
    with open('$OUTPUT_DIR/test_summary.txt', 'w') as f:
        f.write(f'E2Eテスト実行サマリー\\n')
        f.write(f'実行日時: $(date)\\n')
        f.write(f'総テスト数: {tests}\\n')
        f.write(f'成功: {success}\\n')
        f.write(f'失敗: {failures}\\n')
        f.write(f'エラー: {errors}\\n')
        f.write(f'スキップ: {skipped}\\n')
        f.write(f'成功率: {success_rate:.1f}%\\n')
        f.write(f'実行時間: {time:.1f}秒\\n')

except Exception as e:
    print(f'テスト結果解析エラー: {e}', file=sys.stderr)
"
    fi
fi

# カバレッジ分析実行
log "E2Eカバレッジ分析実行中..."

COVERAGE_ARGS=("$PROJECT_ROOT")
if [[ "$VERBOSE" == true ]]; then
    if python3 "$SCRIPT_DIR/analyze_e2e_coverage.py" "${COVERAGE_ARGS[@]}"; then
        success "カバレッジ分析完了"
    else
        error "カバレッジ分析に失敗しました"
    fi
else
    if python3 "$SCRIPT_DIR/analyze_e2e_coverage.py" "${COVERAGE_ARGS[@]}" > "$OUTPUT_DIR/coverage_analysis.log" 2>&1; then
        success "カバレッジ分析完了"
    else
        warn "カバレッジ分析で問題が発生しました (詳細: $OUTPUT_DIR/coverage_analysis.log)"
    fi
fi

# カバレッジレポートの移動
log "カバレッジレポートの統合中..."
COVERAGE_REPORTS_DIR="temp/reports/e2e"

if [[ -d "$COVERAGE_REPORTS_DIR" ]]; then
    # 最新のカバレッジレポートを探す
    LATEST_JSON=$(find "$COVERAGE_REPORTS_DIR" -name "e2e_coverage_report_*.json" -type f | sort | tail -1)
    LATEST_HTML=$(find "$COVERAGE_REPORTS_DIR" -name "e2e_coverage_report_*.html" -type f | sort | tail -1)

    if [[ -n "$LATEST_JSON" ]] && [[ -f "$LATEST_JSON" ]]; then
        cp "$LATEST_JSON" "$OUTPUT_DIR/e2e_coverage_report.json"
        log "カバレッジJSONレポートをコピー: $(basename "$LATEST_JSON")"
    fi

    if [[ -n "$LATEST_HTML" ]] && [[ -f "$LATEST_HTML" ]]; then
        cp "$LATEST_HTML" "$OUTPUT_DIR/e2e_coverage_report.html"
        log "カバレッジHTMLレポートをコピー: $(basename "$LATEST_HTML")"
    fi
fi

# 統合レポートの生成
if [[ "$FULL_REPORT" == true ]]; then
    log "統合レポート生成中..."

    INTEGRATED_REPORT="$OUTPUT_DIR/integrated_e2e_report.html"

    cat > "$INTEGRATED_REPORT" << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2Eテスト統合レポート</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        .nav { display: flex; justify-content: center; margin: 20px 0; gap: 10px; }
        .nav a { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; transition: background 0.3s; }
        .nav a:hover { background: #2980b9; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }
        .timestamp { color: #6c757d; text-align: center; margin-bottom: 30px; }
        iframe { width: 100%; height: 600px; border: 1px solid #dee2e6; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 E2Eテスト統合レポート</h1>
        <div class="timestamp">生成日時: $(date)</div>

        <div class="nav">
            <a href="#test-results">テスト結果</a>
            <a href="#coverage">カバレッジ分析</a>
            <a href="#files">生成ファイル</a>
        </div>

        <div class="section" id="test-results">
            <h2>📊 テスト実行結果</h2>
EOF

    # テストサマリーがある場合は追加
    if [[ -f "$OUTPUT_DIR/test_summary.txt" ]]; then
        cat >> "$INTEGRATED_REPORT" << EOF
            <pre>$(cat "$OUTPUT_DIR/test_summary.txt")</pre>
EOF
    fi

    # HTMLテストレポートがある場合は埋め込み
    if [[ -f "$OUTPUT_DIR/e2e_test_report.html" ]]; then
        cat >> "$INTEGRATED_REPORT" << EOF
            <h3>詳細テストレポート</h3>
            <iframe src="e2e_test_report.html"></iframe>
EOF
    fi

    cat >> "$INTEGRATED_REPORT" << EOF
        </div>

        <div class="section" id="coverage">
            <h2>📈 カバレッジ分析</h2>
EOF

    # カバレッジレポートがある場合は埋め込み
    if [[ -f "$OUTPUT_DIR/e2e_coverage_report.html" ]]; then
        cat >> "$INTEGRATED_REPORT" << EOF
            <iframe src="e2e_coverage_report.html"></iframe>
EOF
    fi

    cat >> "$INTEGRATED_REPORT" << EOF
        </div>

        <div class="section" id="files">
            <h2>📁 生成ファイル</h2>
            <ul>
EOF

    # 生成されたファイルのリストを作成
    for file in "$OUTPUT_DIR"/*; do
        if [[ -f "$file" ]]; then
            filename=$(basename "$file")
            filesize=$(ls -lh "$file" | awk '{print $5}')
            cat >> "$INTEGRATED_REPORT" << EOF
                <li><strong>$filename</strong> ($filesize)</li>
EOF
        fi
    done

    cat >> "$INTEGRATED_REPORT" << 'EOF'
            </ul>
        </div>

        <footer style="text-align: center; margin-top: 50px; color: #6c757d;">
            <p>このレポートは E2E Report Generator により自動生成されました。</p>
        </footer>
    </div>
</body>
</html>
EOF

    success "統合レポート生成完了: $INTEGRATED_REPORT"
fi

# 結果サマリーの出力
log "=== E2Eレポート生成完了 ==="
log "出力ディレクトリ: $OUTPUT_DIR"

echo
log "生成されたファイル:"
find "$OUTPUT_DIR" -type f | while read -r file; do
    filename=$(basename "$file")
    filesize=$(ls -lh "$file" | awk '{print $5}')
    echo "  📄 $filename ($filesize)"
done

# メインレポートファイルの表示
MAIN_REPORTS=()
if [[ -f "$OUTPUT_DIR/integrated_e2e_report.html" ]]; then
    MAIN_REPORTS+=("統合レポート: $OUTPUT_DIR/integrated_e2e_report.html")
fi
if [[ -f "$OUTPUT_DIR/e2e_coverage_report.html" ]]; then
    MAIN_REPORTS+=("カバレッジレポート: $OUTPUT_DIR/e2e_coverage_report.html")
fi
if [[ -f "$OUTPUT_DIR/e2e_test_report.html" ]]; then
    MAIN_REPORTS+=("テストレポート: $OUTPUT_DIR/e2e_test_report.html")
fi

if [[ ${#MAIN_REPORTS[@]} -gt 0 ]]; then
    echo
    success "メインレポート:"
    for report in "${MAIN_REPORTS[@]}"; do
        echo "  🌟 $report"
    done
fi

echo
success "E2E統合レポート生成が完了しました！"
