# テスト後自動クリーンアップシステム仕様書

## 📋 システム概要

### 目的
テスト実行で生成される一時ファイル・サンプルファイルを自動的に削除し、開発環境を常にクリーンな状態に保つ。

### スコープ
- pytest実行後の自動クリーンアップ
- 手動クリーンアップ機能
- ファイル・ディレクトリの安全な削除
- 重要ファイルの確実な保護

## 🏗️ アーキテクチャ設計

### システム構成
```
テスト後自動クリーンアップシステム
├── 自動実行機能 (pytest_sessionfinish)
├── 手動実行機能 (CLI・novelコマンド)
├── クリーンアップマネージャー (TestCleanupManager)
└── 安全性保護機能 (パターンマッチング)
```

### 実装ファイル
- （参考）旧構成: `scripts/tools/test_cleanup_manager.py` - メインロジック
- 現行ユーティリティ例: `src/noveler/tools/cleanup_pycache.py`（目的に応じて適宜活用）
- pytest統合: `tests/` 配下の `conftest.py`
- CLI実行: `bin/noveler`（MCP連携）

## 🎯 機能要件

### FR-1: 自動クリーンアップ実行
**説明**: pytest終了時に自動でクリーンアップを実行する

**受入基準**:
- pytest実行完了時に自動実行される
- テスト成功時のみ実行される（失敗時は保持）
- 実行結果がコンソールに表示される

**実装方法**:
```python
def pytest_sessionfinish(session, exitstatus) -> None:
    if exitstatus != 0:  # テスト失敗時はスキップ
        return
    cleanup_after_tests(project_root=project_root, dry_run=False)
```

### FR-2: 手動クリーンアップ実行
**説明**: コマンドラインから任意のタイミングでクリーンアップを実行する

**受入基準**:
- `python scripts/tools/test_cleanup_manager.py` で実行可能
- `novel cleanup` で実行可能
- `--dry-run` オプションでドライラン実行可能
- `--verbose` オプションで詳細表示可能

**実装方法**:
```bash
# 直接実行
python scripts/tools/test_cleanup_manager.py --dry-run --verbose

# novelコマンド経由
novel cleanup --dry-run --verbose
```

### FR-3: ファイル削除判定
**説明**: 正規表現パターンに基づいてファイルの削除可否を判定する

**削除対象パターン**:
```python
CLEANUP_PATTERNS = [
    r".*_サンプル\.yaml$",         # サンプルファイル
    r".*_テスト.*\.yaml$",         # テスト系ファイル
    r".*_test_.*\.yaml$",          # test付きファイル
    r".*_sample\.yaml$",           # sampleファイル
    r"^第\d+話_テスト.*\.md$",     # テスト用エピソード
    r".*_test\.log$",              # テストログ
    r"品質テスト結果_\d{8}_\d{6}\.yaml$",  # 品質テスト結果
]
```

**保護対象パターン**:
```python
EXCLUDE_PATTERNS = [
    r".*テンプレート\.yaml$",      # テンプレートファイル
    r".*template\.yaml$",          # テンプレートファイル
    r"requirements.*\.txt$",       # 依存関係ファイル
    r"pyproject\.toml$",          # プロジェクト設定
    r"CLAUDE\.md$",               # プロジェクト指示書
    r"README\.md$",               # ドキュメント
]
```

### FR-4: ディレクトリ削除判定
**説明**: 安全性を考慮してディレクトリの削除可否を判定する

**削除対象ディレクトリ**:
```python
SAFE_CLEANUP_DIRS = [
    "__pycache__",    # Pythonキャッシュ
    ".pytest_cache",  # pytestキャッシュ
    ".mypy_cache",    # MyPyキャッシュ
    ".ruff_cache",    # Ruffキャッシュ
    "temp",           # 一時ディレクトリ
    "logs",           # ログディレクトリ
    "cache",          # キャッシュディレクトリ
]
```

**削除条件**:
- ディレクトリ名が `SAFE_CLEANUP_DIRS` に含まれる
- 空ディレクトリである
- またはキャッシュディレクトリ（`.`で始まり`cache`を含む）

### FR-5: 実行結果報告
**説明**: クリーンアップ実行結果を構造化して報告する

**報告項目**:
```python
result = {
    "files_deleted": [],      # 削除されたファイルのリスト
    "dirs_deleted": [],       # 削除されたディレクトリのリスト
    "files_protected": [],    # 保護されたファイルのリスト
    "errors": [],             # エラーのリスト
    "total_size_freed": 0,    # 解放されたディスク容量（バイト）
}
```

## 🔒 非機能要件

### NFR-1: 安全性
**要件**: 重要ファイルの誤削除を防止する

**実装**:
- ホワイトリスト方式（明示的に指定されたパターンのみ削除）
- 多重チェック機能（保護パターン → 削除パターン）
- ドライランモードでの事前確認

### NFR-2: 信頼性
**要件**: 削除処理の確実性とエラー処理

**実装**:
- 各ファイル削除での個別例外処理
- 削除失敗時の詳細エラー報告
- 部分的失敗でも継続処理

### NFR-3: パフォーマンス
**要件**: 大量ファイルでも合理的な実行時間

**実装**:
- 効率的なファイルスキャン（`Path.rglob()`）
- 早期終了による不要処理のスキップ
- メモリ効率的な処理

### NFR-4: 使いやすさ
**要件**: 直感的で分かりやすいインターフェース

**実装**:
- 明確なコマンドライン引数
- 詳細な実行結果表示
- エラー時の具体的な対処法提示

## 🔧 技術仕様

### クラス設計

#### TestCleanupManager
```python
class TestCleanupManager:
    """テスト後クリーンアップの管理クラス"""

    def __init__(self, project_root: Path):
        """初期化"""

    def cleanup_test_artifacts(self, dry_run: bool = False) -> dict:
        """テスト成果物のクリーンアップ実行"""

    def _cleanup_files(self, result: dict, dry_run: bool) -> None:
        """ファイルのクリーンアップ"""

    def _cleanup_directories(self, result: dict, dry_run: bool) -> None:
        """ディレクトリのクリーンアップ"""

    def _is_protected_file(self, file_name: str) -> bool:
        """重要ファイルの保護チェック"""

    def _should_cleanup_file(self, file_name: str) -> bool:
        """クリーンアップ対象ファイルの判定"""

    def _is_safe_to_delete_dir(self, dir_path: Path) -> bool:
        """ディレクトリの安全削除判定"""
```

### 関数設計

#### cleanup_after_tests
```python
def cleanup_after_tests(project_root: Path = None, dry_run: bool = False) -> dict:
    """テスト後クリーンアップのエントリーポイント

    Args:
        project_root: プロジェクトルート（Noneの場合は自動検出）
        dry_run: True の場合、実際の削除は行わず報告のみ

    Returns:
        クリーンアップ結果の辞書
    """
```

### データ構造

#### クリーンアップ結果
```python
CleanupResult = {
    "files_deleted": List[str],      # 削除されたファイルの相対パス
    "dirs_deleted": List[str],       # 削除されたディレクトリの相対パス
    "files_protected": List[str],    # 保護されたファイルの相対パス
    "errors": List[str],             # エラーメッセージ
    "total_size_freed": int,         # 解放されたバイト数
}
```

## 🧪 テスト仕様

### UT-1: パターンマッチングテスト
```python
def test_cleanup_patterns():
    """削除対象パターンのテスト"""
    manager = TestCleanupManager(Path("/tmp"))

    # 削除対象
    assert manager._should_cleanup_file("プロジェクト設定_サンプル.yaml")
    assert manager._should_cleanup_file("第001話_テスト.md")
    assert manager._should_cleanup_file("quality_test.log")

    # 保護対象
    assert not manager._should_cleanup_file("話数管理テンプレート.yaml")
    assert not manager._should_cleanup_file("第001話_正式版.md")
    assert not manager._should_cleanup_file("CLAUDE.md")
```

### UT-2: ファイル保護テスト
```python
def test_file_protection():
    """重要ファイル保護のテスト"""
    manager = TestCleanupManager(Path("/tmp"))

    # テンプレートファイルは保護される
    assert manager._is_protected_file("話数管理テンプレート.yaml")
    assert manager._is_protected_file("episode_template.yaml")

    # 設定ファイルは保護される
    assert manager._is_protected_file("pyproject.toml")
    assert manager._is_protected_file("requirements.txt")
```

### UT-3: ディレクトリ安全性テスト
```python
def test_directory_safety():
    """ディレクトリ削除安全性のテスト"""
    # キャッシュディレクトリは削除OK
    assert manager._is_safe_to_delete_dir(Path("/tmp/.pytest_cache"))
    assert manager._is_safe_to_delete_dir(Path("/tmp/__pycache__"))

    # 重要ディレクトリは削除NG
    assert not manager._is_safe_to_delete_dir(Path("/tmp/scripts"))
    assert not manager._is_safe_to_delete_dir(Path("/tmp/50_管理資料"))
```

### IT-1: 統合テスト
```python
def test_cleanup_integration(tmp_path):
    """クリーンアップ統合テスト"""
    # テストファイル作成
    (tmp_path / "プロジェクト設定_サンプル.yaml").write_text("test")
    (tmp_path / "重要ファイル.yaml").write_text("important")

    # クリーンアップ実行
    manager = TestCleanupManager(tmp_path)
    result = manager.cleanup_test_artifacts()

    # 結果検証
    assert len(result["files_deleted"]) == 1
    assert "プロジェクト設定_サンプル.yaml" in result["files_deleted"]
    assert len(result["files_protected"]) >= 1
    assert not (tmp_path / "プロジェクト設定_サンプル.yaml").exists()
    assert (tmp_path / "重要ファイル.yaml").exists()
```

## 🚀 運用仕様

### 自動実行
- **タイミング**: pytest実行完了時
- **条件**: テスト成功時のみ（exitstatus == 0）
- **失敗時**: ファイルを保持してデバッグ支援

### 手動実行
```bash
# 基本実行
novel cleanup

# ドライラン（確認のみ）
novel cleanup --dry-run

# 詳細表示
novel cleanup --verbose

# 組み合わせ
novel cleanup --dry-run --verbose
```

### ログ出力
```
🧹 テスト後クリーンアップを実行中...
✅ クリーンアップ完了: 3 ファイル, 5 ディレクトリを削除
💾 解放サイズ: 12,345 bytes
```

## 📊 モニタリング仕様

### 実行メトリクス
- 削除ファイル数
- 削除ディレクトリ数
- 保護ファイル数
- エラー発生数
- 解放ディスク容量
- 実行時間

### エラー監視
- ファイル削除失敗
- 権限エラー
- パス関連エラー
- インポートエラー

## 🔧 保守・拡張仕様

### パターン追加
新しい削除対象パターンを追加する場合：

```python
CLEANUP_PATTERNS = [
    # 既存パターン...
    r"new_pattern_.*\.ext$",  # 新しいパターン
]
```

### 保護パターン追加
重要ファイルを保護する場合：

```python
EXCLUDE_PATTERNS = [
    # 既存パターン...
    r"important_file\.yaml$",  # 新しい保護パターン
]
```

### 設定外部化
将来的に設定ファイル化する場合：

```yaml
# cleanup_config.yaml
cleanup_patterns:
  - ".*_サンプル\\.yaml$"
  - ".*_テスト.*\\.yaml$"

exclude_patterns:
  - ".*テンプレート\\.yaml$"
  - "pyproject\\.toml$"
```

## 📝 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|----------|
| 1.0.0 | 2025-01-23 | 初回リリース - 基本クリーンアップ機能 |

## 🔍 参考資料

- [pytest公式ドキュメント - フック](https://docs.pytest.org/en/stable/reference/hooks.html)
- [Python pathlib公式ドキュメント](https://docs.python.org/3/library/pathlib.html)
- [正規表現公式ドキュメント](https://docs.python.org/3/library/re.html)
