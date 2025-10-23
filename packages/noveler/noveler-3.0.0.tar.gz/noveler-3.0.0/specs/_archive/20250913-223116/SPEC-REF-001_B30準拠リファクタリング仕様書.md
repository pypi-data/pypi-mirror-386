# SPEC-REF-001: B30準拠システム全体リファクタリング仕様書

**仕様書ID**: SPEC-REF-001
**作成日**: 2025-08-30
**更新日**: 2025-08-30
**対象システム**: novelerシステム全体
**優先度**: 最高（システム安定性・品質担保に直結）

## 1. 背景と目的

### 1.1 背景
- 現状6,337件のF821エラー（主に未定義変数・self参照問題）
- 3,763件のANN001エラー（型アノテーション不足）
- B30品質作業指示書違反（direct print()使用、import統一不備）
- 共有コンポーネントの重複実装・直接インスタンス化

### 1.2 目的
B30品質作業指示書完全準拠によるシステム品質向上
- 統一インポート方針（novelerプレフィックス強制）
- 共有コンポーネント強制使用
- 品質ゲート実装

## 2. 対象範囲

### 2.1 対象ファイル
- `src/noveler/**/*.py` （全Pythonファイル）
- `tests/**/*.py` （全テストファイル）
- `scripts/**/*.py` （実行スクリプト）

### 2.2 対象エラーパターン
1. **F821エラー**: 未定義変数・self参照問題（6,337件）
2. **ANN001エラー**: 型アノテーション不足（3,763件）
3. **B30違反**: 直接print()使用、インポート規則違反

## 3. 実装要件

### 3.1 インポート統一要件
```python
# 必須パターン
from noveler.domain.services.xxx import XXXService
from noveler.infrastructure.factories.xxx import get_xxx_service

# 禁止パターン
from scripts.xxx import XXX  # novelerプレフィックス必須
import sys  # 例外：標準ライブラリは除く
```

### 3.2 共有コンポーネント強制使用
```python
# Console使用（必須）
from noveler.presentation.cli.shared_utilities import console
console.print("メッセージ")  # 直接print()禁止

# Logger使用（必須）
from noveler.presentation.cli.shared_utilities import get_logger
logger = get_logger(__name__)

# パス管理（必須）
from noveler.presentation.cli.shared_utilities import get_common_path_service
path_service = get_common_path_service()
```

### 3.3 依存性注入要件
```python
# コンストラクタ注入パターン（必須）
def __init__(self,
    console_service: IConsoleService = None,
    logger_service: ILoggerService = None,
    path_service: IPathService = None) -> None:

    self.console_service = console_service or get_console_service()
    self.logger_service = logger_service or get_logger_service()
    self.path_service = path_service or get_path_service()
```

## 4. 実装フェーズ

### Phase 1: 緊急修正（実装済み完了）
- **既存のshared_utilities.py修正** （緊急）
  - 118行目: `console.self.console_service.print_` 文法エラー修正
  - 193行目: `console.print` → 統一Console使用
  - 227行目: `console.self.console_service.print_` 文法エラー修正

### Phase 2: インポート統一（6,337エラー対応）
1. **self未定義エラー修正**
   - コンストラクタ注入パターン適用
   - DI container経由でのサービス取得

2. **novelerプレフィックス強制**
   - 全相対インポートを絶対インポートに変更
   - scriptsプレフィックス削除、novelerプレフィックス適用

### Phase 3: 品質ゲート実装
1. **pytest.mark.spec追加**
   - 全テストファイルに仕様書リンクマーカー追加
   - 型アノテーション追加（3,763 ANN001対応）

2. **品質チェック自動化**
   - pre-commit hook強化
   - CI/CD品質ゲート実装

## 5. 受け入れ基準

### 5.1 エラー解消基準
- F821エラー: 0件（完全解消）
- ANN001エラー: 0件（完全解消）
- B30チェック: 違反0件

### 5.2 品質基準
- 全インポートがnovelerプレフィックス準拠
- print()文が0件（統一Console使用）
- 共有コンポーネントの重複実装0件

### 5.3 テスト基準
- 全テストにpytest.mark.spec追加
- テストカバレッジ80%以上維持

## 6. リスク管理

### 6.1 高リスク項目
- **循環インポート発生リスク** → インポート順序最適化で対応
- **DI container未初期化** → フォールバック仕様実装
- **テスト実行時間増加** → 並列実行・キャッシュ活用

### 6.2 回避策
- 段階的実装（1ファイルずつ修正・テスト）
- バックアップ作成（重要ファイル）
- ロールバック手順準備

## 7. 実装スケジュール

### 即座実行
1. shared_utilities.py緊急修正（文法エラー3箇所）
2. 高頻度使用ファイルの優先修正

### 段階実行
1. Stage 2: インポート統一（F821エラー対応）
2. Stage 3: 品質ゲート（ANN001・テストマーカー対応）
3. Stage 4: 最終検証・品質確認

---

**承認要件**: Claude Code実装チーム承認
**実装責任者**: AI Assistant（Claude Code）
**品質責任者**: B30品質作業指示書準拠チェックシステム
