#!/bin/bash
# テストコマンド集 - Makefileスタイル

set -e

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ヘルプ表示
help() {
    echo "🧪 テストコマンド集"
    echo "=================="
    echo
    echo "高速実行:"
    echo "  test-fast       単体テスト（高速、slowテスト除外）"
    echo "  test-unit       単体テストのみ"
    echo "  test-integration 統合テストのみ"
    echo "  test-e2e        E2Eテストのみ"
    echo
    echo "レイヤー別:"
    echo "  test-domain     ドメイン層のみ"
    echo "  test-app        アプリケーション層のみ"
    echo "  test-infra      インフラ層のみ"
    echo
    echo "効率的実行:"
    echo "  test-failed     前回失敗したテストのみ"
    echo "  test-collect    テスト収集のみ（実行時間チェック）"
    echo "  test-coverage   カバレッジ付きテスト"
    echo
    echo "開発支援:"
    echo "  test-watch      ファイル変更を監視してテスト実行"
    echo "  test-profile    パフォーマンス分析付きテスト"
}

# 高速単体テスト
test-fast() {
    echo_info "高速単体テスト実行中..."
    python scripts/tools/fast_test.py --unit --fast
}

# 単体テスト
test-unit() {
    echo_info "単体テスト実行中..."
    python scripts/tools/fast_test.py --unit
}

# 統合テスト
test-integration() {
    echo_info "統合テスト実行中..."
    python scripts/tools/fast_test.py --integration
}

# E2Eテスト
test-e2e() {
    echo_info "E2Eテスト実行中..."
    python scripts/tools/fast_test.py --e2e
}

# ドメイン層テスト
test-domain() {
    echo_info "ドメイン層テスト実行中..."
    python scripts/tools/fast_test.py --domain
}

# アプリケーション層テスト
test-app() {
    echo_info "アプリケーション層テスト実行中..."
    python scripts/tools/fast_test.py --application
}

# インフラ層テスト
test-infra() {
    echo_info "インフラ層テスト実行中..."
    python scripts/tools/fast_test.py --infrastructure
}

# 前回失敗したテストのみ
test-failed() {
    echo_info "前回失敗したテスト実行中..."
    python scripts/tools/fast_test.py --lf --fast
}

# テスト収集のみ
test-collect() {
    echo_info "テスト収集時間計測中..."
    time python scripts/tools/fast_test.py --collect-only
}

# カバレッジ付きテスト
test-coverage() {
    echo_info "カバレッジ付きテスト実行中..."
    python scripts/tools/fast_test.py --unit --coverage
}

# ファイル監視テスト（ptpythonが必要）
test-watch() {
    echo_warning "ファイル監視機能は手動実装が必要です"
    echo_info "代替案: pytest-watch をインストールして ptw を使用"
}

# パフォーマンス分析
test-profile() {
    echo_info "パフォーマンス分析付きテスト実行中..."
    python -m pytest scripts/tests/unit/domain --durations=20 --tb=short -n auto
}

# 全テスト（本格実行）
test-all() {
    echo_info "全テスト実行中（時間がかかります）..."
    python scripts/tools/fast_test.py --coverage --maxfail 10
}

# メイン処理
case "$1" in
    "test-fast")
        test-fast
        ;;
    "test-unit")
        test-unit
        ;;
    "test-integration")
        test-integration
        ;;
    "test-e2e")
        test-e2e
        ;;
    "test-domain")
        test-domain
        ;;
    "test-app")
        test-app
        ;;
    "test-infra")
        test-infra
        ;;
    "test-failed")
        test-failed
        ;;
    "test-collect")
        test-collect
        ;;
    "test-coverage")
        test-coverage
        ;;
    "test-watch")
        test-watch
        ;;
    "test-profile")
        test-profile
        ;;
    "test-all")
        test-all
        ;;
    *)
        help
        ;;
esac
