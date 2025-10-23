#!/bin/bash
# E2Eテスト実行スクリプト
# 使用方法: ./bin/run_e2e_tests.sh [オプション]

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
E2Eテスト実行スクリプト

使用方法:
    ./bin/run_e2e_tests.sh [オプション]

オプション:
    -h, --help              このヘルプを表示
    -a, --all               全てのE2Eテストを実行
    -w, --workflow          ワークフロー統合テストのみ実行
    -q, --quality           品質保証ワークフローのみ実行
    -s, --smoke             スモークテスト（基本機能）のみ実行
    -p, --performance       パフォーマンステストを含む
    -c, --critical          重要テストのみ実行
    -f, --fast              高速実行（slow テストをスキップ）
    -v, --verbose           詳細出力
    -d, --debug             デバッグモード
    -r, --report            HTML レポート生成
    -j, --junit             JUnit XML 出力
    -t, --timeout SECONDS   タイムアウト設定（デフォルト: 300秒）
    -n, --parallel          並列実行（リソース競合注意）

実行例:
    ./bin/run_e2e_tests.sh --smoke                    # スモークテストのみ
    ./bin/run_e2e_tests.sh --workflow --verbose       # ワークフロー統合テスト（詳細出力）
    ./bin/run_e2e_tests.sh --all --report             # 全テスト + HTML レポート
    ./bin/run_e2e_tests.sh --quality --performance    # 品質 + パフォーマンステスト

EOF
}

# デフォルト設定
RUN_ALL=false
RUN_WORKFLOW=false
RUN_QUALITY=false
RUN_SMOKE=false
INCLUDE_PERFORMANCE=false
CRITICAL_ONLY=false
FAST_MODE=false
VERBOSE=false
DEBUG=false
GENERATE_REPORT=false
GENERATE_JUNIT=false
TIMEOUT=300
PARALLEL=false

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -w|--workflow)
            RUN_WORKFLOW=true
            shift
            ;;
        -q|--quality)
            RUN_QUALITY=true
            shift
            ;;
        -s|--smoke)
            RUN_SMOKE=true
            shift
            ;;
        -p|--performance)
            INCLUDE_PERFORMANCE=true
            shift
            ;;
        -c|--critical)
            CRITICAL_ONLY=true
            shift
            ;;
        -f|--fast)
            FAST_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            VERBOSE=true
            shift
            ;;
        -r|--report)
            GENERATE_REPORT=true
            shift
            ;;
        -j|--junit)
            GENERATE_JUNIT=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -n|--parallel)
            PARALLEL=true
            shift
            ;;
        *)
            error "不明なオプション: $1"
            ;;
    esac
done

# プロジェクトルートに移動
cd "${PROJECT_ROOT}"

# 環境チェック
log "E2E テスト環境の確認"

# Python仮想環境の確認
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    warn "仮想環境が有効化されていません"
    if [[ -d "venv" ]]; then
        log "venv を有効化中..."
        source venv/bin/activate || source venv/Scripts/activate
    elif [[ -d ".venv" ]]; then
        log ".venv を有効化中..."
        source .venv/bin/activate || source .venv/Scripts/activate
    else
        warn "仮想環境が見つかりません。グローバル環境で実行します"
    fi
fi

# 必要なディレクトリ作成
mkdir -p temp/cache/pytest_e2e
mkdir -p temp/reports
mkdir -p temp/logs

# pytest の確認
if ! command -v pytest >/dev/null 2>&1; then
    error "pytest がインストールされていません"
fi

log "Python: $(python --version)"
log "pytest: $(pytest --version)"

# テスト対象の決定
PYTEST_ARGS=()

# 基本設定
PYTEST_ARGS+=("-c" "tests/e2e/pytest_e2e.ini")

# マーカー設定
MARKERS=()

if [[ "$RUN_ALL" == true ]]; then
    log "全E2Eテストを実行"
elif [[ "$RUN_SMOKE" == true ]]; then
    log "スモークテストを実行"
    MARKERS+=("smoke")
elif [[ "$CRITICAL_ONLY" == true ]]; then
    log "重要テストのみ実行"
    MARKERS+=("critical")
else
    # 個別テスト指定
    if [[ "$RUN_WORKFLOW" == true ]]; then
        log "ワークフロー統合テストを実行"
        MARKERS+=("workflow")
    fi

    if [[ "$RUN_QUALITY" == true ]]; then
        log "品質保証ワークフローテストを実行"
        MARKERS+=("quality")
    fi

    # デフォルト: 何も指定されていない場合は基本的なE2Eテストを実行
    if [[ ${#MARKERS[@]} -eq 0 ]]; then
        log "基本E2Eテストを実行"
        MARKERS+=("e2e")
    fi
fi

# パフォーマンステスト
if [[ "$INCLUDE_PERFORMANCE" == true ]]; then
    log "パフォーマンステストを含む"
    MARKERS+=("performance")
fi

# 高速モード（slowテストをスキップ）
if [[ "$FAST_MODE" == true ]]; then
    log "高速モード: 時間のかかるテストをスキップ"
    PYTEST_ARGS+=("-m" "not slow")
fi

# マーカーの組み立て
if [[ ${#MARKERS[@]} -gt 0 ]] && [[ "$FAST_MODE" == false ]]; then
    MARKER_EXPR=$(IFS=" or "; echo "${MARKERS[*]}")
    PYTEST_ARGS+=("-m" "${MARKER_EXPR}")
fi

# 詳細出力
if [[ "$VERBOSE" == true ]]; then
    PYTEST_ARGS+=("-vv")
    log "詳細出力モード"
fi

# デバッグモード
if [[ "$DEBUG" == true ]]; then
    PYTEST_ARGS+=("--tb=long" "--showlocals" "--capture=no")
    log "デバッグモード"
fi

# 並列実行
if [[ "$PARALLEL" == true ]]; then
    PYTEST_ARGS+=("-n" "auto")
    log "並列実行モード（リソース競合に注意）"
fi

# タイムアウト
PYTEST_ARGS+=("--timeout=${TIMEOUT}")

# レポート生成
REPORT_FILE=""
if [[ "$GENERATE_REPORT" == true ]]; then
    REPORT_FILE="temp/reports/e2e_report_$(date +%Y%m%d_%H%M%S).html"
    PYTEST_ARGS+=("--html=${REPORT_FILE}" "--self-contained-html")
    log "HTMLレポート: ${REPORT_FILE}"
fi

# JUnit XML出力
JUNIT_FILE=""
if [[ "$GENERATE_JUNIT" == true ]]; then
    JUNIT_FILE="temp/reports/e2e_junit_$(date +%Y%m%d_%H%M%S).xml"
    PYTEST_ARGS+=("--junit-xml=${JUNIT_FILE}")
    log "JUnit XML: ${JUNIT_FILE}"
fi

# ログファイル
LOG_FILE="temp/logs/e2e_test_$(date +%Y%m%d_%H%M%S).log"
PYTEST_ARGS+=("--log-file=${LOG_FILE}")

# 実行開始
log "E2Eテスト実行開始"
log "実行コマンド: pytest ${PYTEST_ARGS[*]}"
log "ログファイル: ${LOG_FILE}"

START_TIME=$(date +%s)

# pytest実行
if pytest "${PYTEST_ARGS[@]}"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    success "E2Eテスト完了 (実行時間: ${DURATION}秒)"

    # 結果サマリー
    echo
    log "=== 実行結果サマリー ==="
    if [[ -n "$REPORT_FILE" ]] && [[ -f "$REPORT_FILE" ]]; then
        log "HTMLレポート: ${REPORT_FILE}"
    fi
    if [[ -n "$JUNIT_FILE" ]] && [[ -f "$JUNIT_FILE" ]]; then
        log "JUnit XML: ${JUNIT_FILE}"
    fi
    log "詳細ログ: ${LOG_FILE}"

else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    error "E2Eテスト失敗 (実行時間: ${DURATION}秒)"
fi
