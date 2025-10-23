# 統一ログ出力標準

## 📋 概要

プロジェクト全体で一貫したログ出力を実現するための標準ガイドライン。デバッグprint文から統一ログシステムへの移行を完了し、プロダクション・開発モードでの適切なログレベル制御を提供します。

## 🎯 ログ出力方針

### 出力カテゴリの分類
- **🎨 UI出力**: `console.print()` - ユーザー向け表示（保持推奨）
- **🔧 デバッグ**: `logger.debug()` - デバッグ情報
- **ℹ️ 情報**: `logger.info()` - 状態・進捗表示
- **⚠️ 警告**: `logger.warning()` - 警告事項
- **❌ エラー**: `logger.error()` - エラー情報

### 移行完了パターン
```python
# ❌ 旧実装（削除済み）
print("DEBUG: 設定読み込み成功")
print("実行開始...")
print("エラー: 処理失敗")

# ✅ 新実装（統一ログ）
from noveler.infrastructure.logging.unified_logger import get_logger
logger = get_logger(__name__)

logger.debug("設定読み込み成功")
logger.info("実行開始...")
logger.error("エラー: 処理失敗")
```

## 🛠️ 実装方法

### 1. ロガー取得
```python
from noveler.infrastructure.logging.unified_logger import get_logger

# モジュール単位でのロガー作成
logger = get_logger(__name__)
```

### 2. ログレベル使い分け
```python
# デバッグ情報（開発時のみ表示）
logger.debug(f"設定値: {config_dict}")

# 一般情報（常時表示）
logger.info("処理開始")

# 警告（注意が必要）
logger.warning("非推奨機能を使用中")

# エラー（問題発生）
logger.error(f"処理失敗: {error}")
```

## 🔧 ログレベル制御

### 環境変数による制御
```bash
# 開発モード（DEBUGレベル表示）
export NOVEL_DEV_MODE=1
# または
export DEBUG=1

# プロダクションモード（INFOレベル以上）
# 環境変数未設定時のデフォルト
```

### 実装詳細
```python
# 統一ロガーは提供済み実装を使用（自作しない）
from noveler.infrastructure.logging.unified_logger import (
    get_logger, configure_logging, LogFormat, LogLevel
)

logger = get_logger(__name__)
# 例: JSON形式へ切替
configure_logging(console_format=LogFormat.JSON)
```

## 📊 移行実績

### 修正完了箇所
- ✅ `src/noveler/infrastructure/ci/ddd_quality_gate.py`
- ✅ `src/noveler/infrastructure/adapters/path_service_adapter.py`
- ✅ `src/noveler/infrastructure/ai_integration/repositories/yaml_project_config_repository.py`
- ✅ `src/noveler/infrastructure/repositories/yaml_episode_repository.py`

### 対象パターン実績
- **print()文**: 1,773箇所（デバッグ・状態表示用）
- **console.print()**: 1,081箇所（UI表示・保持）
- **get_logger()**: 243箇所（既存統一ログ・拡張完了）

## 🎨 UI出力との使い分け

### Rich Console（保持）
```python
from rich.console import Console
console = Console()

# ユーザー向けインタラクティブ表示
console.print("✨ Smart Auto-Enhancement 完了")
console.print(f"最終品質スコア: [bold]{score}[/bold]")
```

### 統一ログ（開発・運用向け）
```python
# システム内部の状態・デバッグ情報
logger.info("Smart Auto-Enhancement実行開始")
logger.debug(f"設定読み込み: {config}")
logger.error(f"実行エラー: {error}")
```

## 🚀 利用効果

### 開発効率向上
- **デバッグ**: `NOVEL_DEV_MODE=1`でデバッグログ表示
- **プロダクション**: 不要なログを自動的に抑制
- **一貫性**: 統一されたログフォーマット

### 運用品質向上
- **追跡可能性**: タイムスタンプ・モジュール名付きログ
- **レベル分離**: 重要度による適切な出力制御
- **保守性**: 中央管理による設定変更の容易さ

## 📝 実装ガイドライン

### DO（推奨）
```python
# ✅ 統一ロガー使用
from noveler.infrastructure.logging.unified_logger import get_logger
logger = get_logger(__name__)

# ✅ 適切なレベル使い分け
logger.debug("設定詳細情報")
logger.info("処理進捗")
logger.warning("非推奨機能使用")
logger.error("実行エラー")

# ✅ UI表示はconsole.print保持
console.print("[green]✅ 処理完了[/green]")
```

### DON'T（非推奨）
```python
# ❌ print()によるデバッグ出力
print("DEBUG: 変数の値")

# ❌ print()による状態表示
print("処理開始...")

# ❌ print()によるエラー表示
print("エラー: 処理失敗")
```

## 🔄 今後の拡張方針

### Phase 1: 基本実装（完了）
- ✅ 統一ログ関数実装
- ✅ 環境変数によるレベル制御
- ✅ 重要print文の移行

### Phase 2: 全体移行（計画）
- 📋 残りprint文の段階的移行
- 📋 ファイル出力ハンドラー追加
- 📋 JSON形式ログ出力対応

### Phase 3: 高度化（計画）
- 📋 ログローテーション実装
- 📋 分散ログ集約対応
- 📋 メトリクス連携機能

---

## 📞 サポート

ログ実装で不明な点があれば、既存の`get_logger`実装を参考に、適切なログレベルでの出力を心がけてください。

**統一ログシステムにより、開発効率とプロダクション運用品質の両方が向上します。**
