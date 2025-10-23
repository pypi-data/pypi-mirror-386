#!/bin/bash
# 実装前チェックスクリプト
#
# 新機能実装前に既存実装の確認を義務化し、重複実装を防ぐ
#
# 使用例:
#   ./scripts/tools/pre_implementation_check.sh "ユーザー認証"
#   ./scripts/tools/pre_implementation_check.sh --interactive

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}🔍 実装前チェックシステム${NC}"
echo "=========================================="

# 機能名の取得
FEATURE_NAME=""
if [[ $# -gt 0 && "$1" != "--interactive" ]]; then
    FEATURE_NAME="$1"
elif [[ $# -eq 0 || "$1" == "--interactive" ]]; then
    echo -e "${YELLOW}実装予定の機能名を入力してください:${NC}"
    read -p "> " FEATURE_NAME
fi

if [[ -z "$FEATURE_NAME" ]]; then
    echo -e "${RED}❌ 機能名が指定されていません${NC}"
    exit 1
fi

echo -e "${BLUE}対象機能: ${FEATURE_NAME}${NC}"
echo

# 1. CODEMAP.yaml確認
echo -e "${YELLOW}📋 Step 1: CODEMAP.yaml確認${NC}"
if [[ -f "$PROJECT_ROOT/CODEMAP.yaml" ]]; then
    echo "関連する既存実装を検索中..."

    # 機能名での検索
    CODEMAP_RESULTS=$(grep -i "$FEATURE_NAME" "$PROJECT_ROOT/CODEMAP.yaml" || true)

    if [[ -n "$CODEMAP_RESULTS" ]]; then
        echo -e "${RED}⚠️ 関連する既存実装が見つかりました:${NC}"
        echo "$CODEMAP_RESULTS"
        echo
        echo -e "${YELLOW}既存実装を拡張・継承できませんか？${NC}"
        read -p "継続しますか？ [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ 実装チェック中断${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ CODEMAPに直接的な重複は見つかりませんでした${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ CODEMAP.yamlが見つかりません${NC}"
fi

echo

# 2. 共有コンポーネント確認
echo -e "${YELLOW}🧩 Step 2: 共有コンポーネント確認${NC}"

# shared_utilitiesの利用可能コンポーネント表示
echo "利用可能な共有コンポーネント:"
echo "  - console (統一Console)"
echo "  - get_logger() (統一Logger)"
echo "  - get_common_path_service() (パス管理)"
echo "  - handle_command_error() (エラーハンドリング)"
echo "  - get_*_handler() (各種ハンドラー)"
echo

echo -e "${YELLOW}これらのコンポーネントを活用しますか？${NC}"
read -p "確認済み [Y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${RED}⚠️ 共有コンポーネントの活用を検討してください${NC}"
fi

echo

# 3. 類似機能検索
echo -e "${YELLOW}🔍 Step 3: 類似機能検索${NC}"
echo "関連キーワードでの既存実装検索..."

# キーワード生成（機能名から）
KEYWORDS=($(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' '\n'))

SIMILAR_FOUND=false
for keyword in "${KEYWORDS[@]}"; do
    if [[ ${#keyword} -gt 2 ]]; then  # 3文字以上のキーワードのみ
        echo "  キーワード: $keyword"
        SEARCH_RESULTS=$(find "$PROJECT_ROOT/src" -name "*.py" -exec grep -l "$keyword" {} \; 2>/dev/null | head -5 || true)

        if [[ -n "$SEARCH_RESULTS" ]]; then
            echo -e "${YELLOW}    関連ファイル:${NC}"
            echo "$SEARCH_RESULTS" | sed 's/^/      /'
            SIMILAR_FOUND=true
        fi
    fi
done

if [[ "$SIMILAR_FOUND" == true ]]; then
    echo -e "${YELLOW}類似実装が見つかりました。これらを参考にしますか？${NC}"
    read -p "確認済み [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${RED}⚠️ 類似実装の確認を推奨します${NC}"
    fi
else
    echo -e "${GREEN}✅ 明確に類似する実装は見つかりませんでした${NC}"
fi

echo

# 4. Repository/ABC継承確認
echo -e "${YELLOW}🏗️ Step 4: アーキテクチャパターン確認${NC}"

# 機能分類の確認
echo "実装予定の機能分類を選択してください:"
echo "1) データアクセス層 (Repository継承必須)"
echo "2) アプリケーション層 (UseCase)"
echo "3) ドメイン層 (Entity, ValueObject)"
echo "4) インフラ層 (外部連携)"
echo "5) プレゼンテーション層 (CLI, UI)"
echo "6) その他"

read -p "選択 [1-6]: " -n 1 -r CATEGORY
echo

case $CATEGORY in
    1)
        echo -e "${YELLOW}Repository ABCを継承してください:${NC}"
        echo "  - EpisodeRepository"
        echo "  - QualityRepository"
        echo "  - PlotRepository"
        echo "  - ProjectRepository"
        ;;
    2)
        echo -e "${YELLOW}UseCase ABCまたはベースクラスの継承を検討してください${NC}"
        ;;
    3)
        echo -e "${YELLOW}DDDパターンに準拠したEntity/ValueObject設計を行ってください${NC}"
        ;;
    4)
        echo -e "${YELLOW}インフラ層の統一インターフェースを活用してください${NC}"
        ;;
    5)
        echo -e "${YELLOW}shared_utilitiesの活用を必須としてください${NC}"
        ;;
    *)
        echo -e "${YELLOW}該当するアーキテクチャパターンを検討してください${NC}"
        ;;
esac

echo

# 5. 仕様書作成確認
echo -e "${YELLOW}📝 Step 5: 仕様書作成確認${NC}"

SPEC_DIR="$PROJECT_ROOT/specs"
echo "仕様書を作成しましたか？"
echo "作成場所: $SPEC_DIR"
echo "形式: SPEC-{CATEGORY}-{NUMBER}_{feature_name}.md"

read -p "仕様書作成済み [Y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${RED}❌ 仕様書作成は必須です${NC}"
    echo "テンプレート: $SPEC_DIR/TEMPLATE_STANDARD_SPEC.md"
    exit 1
fi

echo

# 6. 重複実装チェック実行
echo -e "${YELLOW}🔧 Step 6: 重複実装検出実行${NC}"

if [[ -f "$PROJECT_ROOT/scripts/tools/duplicate_implementation_detector.py" ]]; then
    echo "重複実装検出ツールを実行中..."
    cd "$PROJECT_ROOT"
    python scripts/tools/duplicate_implementation_detector.py

    DETECTOR_EXIT_CODE=$?
    if [[ $DETECTOR_EXIT_CODE -ne 0 ]]; then
        echo -e "${RED}❌ 重複実装違反が検出されました${NC}"
        echo "実装開始前に既存の違反を修正してください"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ 重複実装検出ツールが見つかりません${NC}"
fi

echo

# 7. 最終確認
echo -e "${GREEN}🎯 実装前チェック完了${NC}"
echo "=========================================="
echo "✅ CODEMAP確認済み"
echo "✅ 共有コンポーネント確認済み"
echo "✅ 類似機能検索済み"
echo "✅ アーキテクチャパターン確認済み"
echo "✅ 仕様書作成済み"
echo "✅ 重複実装チェック済み"
echo

echo -e "${GREEN}🚀 実装を開始してください！${NC}"
echo

# 実装ガイダンス表示
echo -e "${BLUE}💡 実装時の注意事項:${NC}"
echo "1. 必ず既存の共有コンポーネントを使用"
echo "2. パスはCommonPathServiceを使用"
echo "3. Console()やimport loggingの直接使用禁止"
echo "4. 仕様書に基づいたテスト先行開発"
echo "5. 3コミットサイクル (仕様→テスト→実装) の遵守"

echo
echo -e "${GREEN}Good luck! 🎉${NC}"
