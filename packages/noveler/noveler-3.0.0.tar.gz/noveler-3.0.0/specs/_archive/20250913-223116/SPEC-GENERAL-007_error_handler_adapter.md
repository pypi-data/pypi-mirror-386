# SPEC-GENERAL-007: ErrorHandlerAdapter 仕様書

## 1. 目的
レガシーコードとの互換性を保ちつつ、統一的なエラーハンドリング機能を提供するインフラストラクチャ層のアダプター。エラー処理の標準化とログ管理を担当。

## 2. 前提条件
- ErrorHandlingService（共有エラーハンドリングサービス）が実装済みであること
- ログディレクトリ（~/.novel/logs）への書き込み権限があること
- レガシーコードが既存のエラーハンドリングパターンに依存していること
- Python logging モジュールが利用可能であること

## 3. 主要な振る舞い

### 3.1 エラーハンドリングフロー
**機能**: 統一的なエラー処理とログ記録
**処理**:
1. エラーの種別自動判定（ConfigError, FileAccessError, ValidationError等）
2. エラーコンテキストの構築と保存
3. 適切なログレベルでの記録（ERROR/WARNING/INFO）
4. Fatal エラー時のプログラム終了処理
5. エラーレポートの生成と保存

### 3.2 ロギング管理
**機能**: プロジェクト統一ログ管理
**処理**:
1. ロガーの自動セットアップ（ファイル・コンソール出力）
2. ログディレクトリの自動作成（~/.novel/logs）
3. パフォーマンスログの記録
4. ログローテーションの管理

### 3.3 安全操作デコレータ
**機能**: ファイル・YAML操作の例外処理自動化
**処理**:
1. ファイル操作例外の自動キャッチ
2. YAML解析エラーの統一処理
3. リトライ機能（設定可能）
4. 詳細エラーメッセージの生成

## 4. インターフェース仕様

### 4.1 主要関数
```python
# ロガー管理
def setup_logger(name: str, log_file: str | None = None) -> logging.Logger
logger: logging.Logger = setup_logger(__name__)  # デフォルトロガー

# エラーハンドリング
def handle_error(error: Exception, context: str = "", fatal: bool = True) -> None
def create_error_report(error: Exception, context: dict | None = None) -> dict

# 検証機能
def validate_required_fields(
    data: dict,
    required_fields: list,
    context: str = ""
) -> None

# 安全操作デコレータ
def safe_file_operation(operation_name: str = "ファイル操作")
def safe_yaml_operation(operation_name: str = "YAML操作")

# パフォーマンス監視
def log_performance(
    operation_name: str,
    duration: float,
    context: dict | None = None
) -> None
```

### 4.2 エラー種別
```python
# 標準エラーレベル
class NovelSystemError(Exception):       # システム基底例外
class ConfigError(NovelSystemError):     # 設定ファイルエラー
class FileAccessError(NovelSystemError): # ファイルアクセスエラー
class ValidationError(NovelSystemError): # データ検証エラー
class DependencyError(NovelSystemError): # 依存関係エラー

# エラーコンテキスト
@dataclass
class ErrorContext:
    operation: str           # 実行中の操作
    file_path: str | None    # 関連ファイルパス
    user_data: dict         # ユーザー提供データ
    system_state: dict      # システム状態情報
```

### 4.3 エラーレポート形式
```python
{
    "error_type": "FileAccessError",
    "message": "プロジェクト設定ファイルが見つかりません",
    "context": {
        "operation": "load_project_config",
        "file_path": "/path/to/プロジェクト設定.yaml",
        "attempted_paths": ["/path/to/..."]
    },
    "timestamp": "2025-07-21T14:30:45.123456",
    "level": "ERROR",
    "traceback": "Traceback (most recent call last)...",
    "additional_info": {
        "recovery_suggestions": ["設定ファイルを作成してください"],
        "related_files": ["/path/to/template.yaml"]
    }
}
```

## 5. デコレータ使用例

### 5.1 安全ファイル操作
```python
@safe_file_operation("プロジェクト設定読み込み")
def load_project_config(config_path: Path) -> dict:
    """プロジェクト設定を安全に読み込み"""
    return yaml.safe_load(config_path.read_text(encoding='utf-8'))

# 使用時：ファイル不在・権限エラー等を自動処理
try:
    config = load_project_config(Path("プロジェクト設定.yaml"))
except FileAccessError as e:
    # 詳細なエラー情報が自動で構築される
    logger.error(f"設定読み込み失敗: {e}")
```

### 5.2 安全YAML操作
```python
@safe_yaml_operation("話数管理データ保存")
def save_episode_metadata(data: dict, filepath: Path) -> None:
    """話数管理データを安全に保存"""
    filepath.write_text(yaml.dump(data, ensure_ascii=False), encoding='utf-8')

# YAML形式エラー・エンコーディングエラー等を自動処理
```

## 6. レガシー互換性

### 6.1 既存コード移行パターン
**Before (レガシーパターン):**
```python
import logging
import sys

logger = logging.getLogger(__name__)

try:
    # ファイル操作
    with open("設定.yaml", "r") as f:
        data = yaml.safe_load(f)
except Exception as e:
    logger.error(f"エラー: {e}")
    sys.exit(1)
```

**After (アダプター使用):**
```python
from infrastructure.adapters.error_handler_adapter import (
    logger, safe_yaml_operation, handle_error
)

@safe_yaml_operation("設定ファイル読み込み")
def load_config(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

# エラー処理が自動化・標準化される
config = load_config("設定.yaml")
```

### 6.2 段階的移行サポート
- 既存のloggingモジュール使用コードとの共存
- グローバルロガー（`logger`）による即座の利用開始
- 徐々にデコレータパターンへの移行

## 7. エラー分類と処理方針

### 7.1 Fatal エラー（プログラム終了）
- **ConfigError**: 必須設定ファイル不在・形式エラー
- **DependencyError**: 重要な依存ライブラリ不在
- **システム権限エラー**: ログディレクトリ作成不可等

### 7.2 Non-Fatal エラー（継続可能）
- **ValidationError**: ユーザー入力データの検証失敗
- **一時的FileAccessError**: 一時ファイルアクセス失敗（リトライ可能）
- **軽微な設定エラー**: デフォルト値で代替可能

### 7.3 エラー回復戦略
- **自動リトライ**: 一時的ネットワーク・ファイルロックエラー
- **デフォルト値使用**: オプション設定の不備
- **ユーザー案内**: 手動での修正が必要な場合

## 8. パフォーマンス監視

### 8.1 監視対象操作
- ファイルI/O操作（読み込み・書き込み時間）
- YAML解析・生成処理時間
- 品質チェック実行時間
- プロジェクト初期化時間

### 8.2 パフォーマンスログ形式
```python
# 自動記録される情報
{
    "operation": "episode_quality_check",
    "duration": 2.345,  # 秒
    "context": {
        "file_size": 15420,  # バイト
        "episode_number": 15,
        "check_types": ["basic_style", "composition"]
    }
}
```

## 9. セキュリティ考慮事項

### 9.1 ログ安全性
- **個人情報の自動マスキング**: ファイルパス中のユーザー名等
- **機密情報の除外**: API キー・パスワード等はログ出力しない
- **ログファイル権限**: 600（所有者のみ読み書き可能）

### 9.2 エラー情報制御
- **本番環境**: スタックトレース詳細の抑制
- **開発環境**: 詳細デバッグ情報の出力
- **ユーザー向けメッセージ**: 技術的詳細を隠蔽した分かりやすい表現

## 10. 設定・カスタマイズ

### 10.1 ログ設定
```python
# 環境変数での制御
LOG_LEVEL=DEBUG          # ログレベル（DEBUG/INFO/WARNING/ERROR）
LOG_ROTATION=daily       # ログローテーション（daily/weekly/size）
MAX_LOG_SIZE=10MB        # 最大ログサイズ
LOG_RETENTION=30         # ログ保持日数
```

### 10.2 エラー処理カスタマイズ
```python
# プロジェクト固有の設定
ERROR_CONFIG = {
    "retry_attempts": 3,           # リトライ回数
    "retry_delay": 1.0,           # リトライ間隔（秒）
    "fatal_error_types": [        # Fatal扱いするエラー種別
        "ConfigError",
        "DependencyError"
    ],
    "notification_enabled": True,  # エラー通知機能
    "recovery_suggestions": True   # 回復提案機能
}
```

## 11. 使用例

### 11.1 基本的なエラーハンドリング
```python
from infrastructure.adapters.error_handler_adapter import (
    handle_error, logger, ValidationError
)

def create_new_episode(episode_data: dict):
    try:
        # エピソード作成処理
        validate_episode_data(episode_data)
        save_episode(episode_data)
        logger.info(f"エピソード作成完了: {episode_data['title']}")
    except ValidationError as e:
        handle_error(e, "エピソード作成", fatal=False)
        raise  # 呼び出し元で適切な処理を継続
    except Exception as e:
        handle_error(e, "エピソード作成", fatal=True)
```

### 11.2 必須フィールド検証
```python
from infrastructure.adapters.error_handler_adapter import validate_required_fields

def process_project_config(config_data: dict):
    required = ["project_name", "author", "genre", "target_words"]
    validate_required_fields(config_data, required, "プロジェクト設定")

    # 検証成功時の処理
    return create_project(config_data)
```

### 11.3 パフォーマンス測定
```python
import time
from infrastructure.adapters.error_handler_adapter import log_performance

def analyze_episode_quality(episode_path: Path) -> dict:
    start_time = time.time()

    try:
        # 品質分析処理
        result = perform_quality_analysis(episode_path)

        # パフォーマンス記録
        duration = time.time() - start_time
        log_performance("quality_analysis", duration, {
            "file_size": episode_path.stat().st_size,
            "word_count": result.get("word_count", 0)
        })

        return result
    except Exception as e:
        handle_error(e, f"品質分析: {episode_path}")
```

## 12. 実装メモ
- 実装ファイル: `scripts/infrastructure/adapters/error_handler_adapter.py`
- テストファイル: `tests/unit/infrastructure/adapters/test_error_handler_adapter.py`
- 依存: ErrorHandlingService, logging, pathlib, dataclass
- 作成日: 2025-07-21
- レガシー互換性: 完全後方互換（段階的移行可能）

## 13. 今後の拡張計画
- [ ] 分散ログ集約（ELK Stack連携）
- [ ] リアルタイムエラー監視（Prometheus/Grafana）
- [ ] 機械学習による異常検知
- [ ] エラー傾向分析とプロアクティブ対応
- [ ] 自動障害回復（Self-Healing）機能
- [ ] エラー統計レポートの定期生成
