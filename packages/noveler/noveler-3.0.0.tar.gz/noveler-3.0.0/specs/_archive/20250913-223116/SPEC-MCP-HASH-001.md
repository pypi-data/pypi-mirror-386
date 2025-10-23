# SPEC-MCP-HASH-001: MCPハッシュベースファイル参照機能

**仕様書ID**: SPEC-MCP-HASH-001
**作成日**: 2025年01月11日
**ステータス**: 実装中
**優先度**: 高
**担当者**: Claude
**レビュアー**: System Architect

## 1.0 概要

### 1.1 目的
LLMがMCPツールを介してSHA256ハッシュでファイルを特定・取得できる機能を実装し、ファイル内容の変更検知とバージョン管理を可能にする。

### 1.2 背景
- 現在のMCPツールはファイルパス指定でのアクセスのみ対応
- ファイル内容の変更検知機能が不在
- ハッシュベースでの確実なファイル特定が必要
- 95%トークン削減システムの基盤技術として活用

### 1.3 スコープ
- **含む**: SHA256ハッシュベースのファイル検索・取得・変更検知
- **含まない**: ファイル暗号化、アクセス権限管理

## 2.0 機能要件

### FR-001: SHA256ハッシュによるファイル検索
**説明**: ファイル内容のSHA256ハッシュでファイルを検索する
**入力**: SHA256ハッシュ値（64文字の16進文字列）
**出力**: 該当するFileReferenceModelまたはNone
**制約**:
- ハッシュ形式の検証必須
- 複数ファイルが同じハッシュを持つ場合は全て返却

### FR-002: ハッシュ指定でのファイル内容取得
**説明**: ハッシュでファイルを特定し、メタデータと内容を取得
**入力**: SHA256ハッシュ値
**出力**: (FileReferenceModel, content)のタプルまたはNone
**制約**:
- ファイル完全性検証を実行
- エンコーディングはUTF-8を基本とする

### FR-003: ファイル変更検知機能
**説明**: 保存済みハッシュと現在のファイルハッシュを比較して変更を検知
**入力**: ファイルパスまたはFileReferenceModel
**出力**: 変更有無のboolean値
**制約**:
- 1バイトの変更でも検知すること
- ファイル不在時は明確にエラー報告

### FR-004: MCPツールインターフェース
**説明**: MCPサーバー経由でLLMがハッシュアクセス可能
**機能**:
- `get_file_by_hash(hash: str)` - ハッシュ指定ファイル取得
- `check_file_changes(file_paths: list[str])` - 一括変更検知
- `list_files_with_hashes()` - ファイル・ハッシュ一覧取得

## 3.0 非機能要件

### NFR-001: 性能要件
- **検索性能**: O(1)でのハッシュ検索（ハッシュインデックス使用）
- **レスポンス時間**: ファイル取得は100ms以内
- **同時実行**: 複数のMCPクライアントからの同時アクセス対応

### NFR-002: 可用性要件
- **ファイル欠損対応**: 参照先ファイルが削除された場合の適切なエラー処理
- **インデックス復旧**: ハッシュインデックス破損時の自動再構築

### NFR-003: 拡張性要件
- **ハッシュアルゴリズム**: SHA256以外への拡張可能性を考慮
- **ストレージ**: ローカルファイルシステム以外への対応余地

## 4.0 既存実装調査（必須）

### 4.1 CODEMAP確認結果
```bash
# 実行コマンド
grep -i "hash\|file.*reference\|ファイル参照" CODEMAP.yaml
# 結果: 該当機能なし（類似機能は発見されず）
```

### 4.2 関連する既存実装
- **FileReferenceManager**: `src/noveler/infrastructure/json/file_managers/file_reference_manager.py`
  - 既存機能: ファイル保存、完全性検証、内容読み込み
  - **拡張対象**: ハッシュ検索機能を追加
- **get_file_reference_info**: `src/mcp_servers/noveler/json_conversion_adapter.py`
  - 既存機能: ファイル基本情報取得
  - **拡張対象**: ハッシュベースアクセス機能を追加
- **hash_utils**: `src/noveler/infrastructure/json/utils/hash_utils.py`
  - 既存機能: SHA256計算、ハッシュ検証
  - **利用**: 既存ユーティリティをそのまま活用

### 4.3 共有コンポーネント利用計画
**B20準拠必須事項**:
```python
from scripts.presentation.cli.shared_utilities import (
    console,                    # 統一Console（Console()直接禁止）
    get_logger,                # 統一Logger（import logging禁止）
    handle_command_error,      # エラーハンドリング
    get_common_path_service,   # パス管理（ハードコーディング禁止）
    show_success_summary       # 成功サマリー表示
)
```

### 4.4 重複実装回避確認
- Console重複: 統一console使用で回避
- Logger重複: get_logger()使用で回避
- パスハードコーディング: get_common_path_service()使用で回避
- Repository ABC: 既存FileReferenceManagerを拡張（新規作成回避）

## 5.0 設計

### 5.1 アーキテクチャ
**DDD + Clean Architecture準拠**:
- **Domain層**: FileReferenceModel（既存）
- **Application層**: ハッシュ検索ユースケース
- **Infrastructure層**: FileReferenceManager拡張（永続化）
- **Presentation層**: MCPツール関数（インターフェース）

### 5.2 クラス設計

#### 5.2.1 FileReferenceManager拡張
```python
class FileReferenceManager:
    def __init__(self, base_output_dir: Path) -> None:
        # 既存実装をそのまま維持
        self._hash_index: dict[str, list[Path]] = {}
        self._load_hash_index()

    # 新規メソッド
    def find_file_by_hash(self, sha256: str) -> FileReferenceModel | None:
    def get_file_by_hash(self, sha256: str) -> tuple[FileReferenceModel, str] | None:
    def has_file_changed(self, file_path: Path, previous_hash: str) -> bool:
    def track_changes(self) -> dict[str, bool]:
    def list_files_with_hashes(self) -> dict[str, list[str]]:
    def _build_hash_index(self) -> dict[str, list[Path]]:
    def _save_hash_index(self) -> None:
    def _load_hash_index(self) -> None:
```

#### 5.2.2 ハッシュインデックスモデル
```python
@dataclass
class HashIndexEntry:
    hash: str
    file_paths: list[str]
    last_updated: datetime

class HashIndexManager:
    def build_index(self, directory: Path) -> dict[str, HashIndexEntry]
    def save_index(self, index: dict[str, HashIndexEntry]) -> None
    def load_index(self) -> dict[str, HashIndexEntry]
```

### 5.3 MCPツール設計
```python
def get_file_by_hash(hash: str) -> dict[str, Any]:
    """
    戻り値:
    {
        "found": bool,
        "hash": str,
        "file": {
            "path": str,
            "size": int,
            "content": str,
            "content_type": str,
            "created_at": str
        } | None,
        "error": str | None
    }
    """

def check_file_changes(file_paths: list[str]) -> dict[str, Any]:
    """
    戻り値:
    {
        "results": {
            "file_path": {
                "changed": bool,
                "previous_hash": str,
                "current_hash": str,
                "error": str | None
            }
        },
        "summary": {
            "total": int,
            "changed": int,
            "errors": int
        }
    }
    """
```

## 6.0 実装計画

### 6.1 実装順序（B20準拠3コミット開発サイクル）

#### Phase 1: 仕様書・テスト作成
- [ ] 仕様書作成（本ドキュメント）
- [ ] テストケース作成（テストファースト）
- [ ] テストデータ準備

#### Phase 2: 実装（共有コンポーネント利用）
- [ ] FileReferenceManager拡張
- [ ] ハッシュインデックス実装
- [ ] MCPツール関数実装

#### Phase 3: 統合・リファクタリング
- [ ] MCPサーバー統合
- [ ] パフォーマンス最適化
- [ ] ドキュメント更新

### 6.2 テスト戦略
**テストファースト開発**:
1. **ユニットテスト**: 各メソッドの個別テスト
2. **統合テスト**: MCPサーバー経由のエンドツーエンドテスト
3. **パフォーマンステスト**: 大量ファイルでの検索性能確認
4. **エラーテスト**: 異常系パターンの網羅的テスト

## 7.0 品質基準

### 7.1 品質ゲート（B30準拠）
- **テストカバレッジ**: 80%以上
- **重複実装検出**: 0件
- **静的解析**: Ruff・mypy・pylintで警告0件
- **パフォーマンス**: 要件NFR-001準拠

### 7.2 検証項目
- [ ] ハッシュ計算の正確性
- [ ] ファイル変更検知の確実性
- [ ] MCPツール経由のアクセス成功
- [ ] エラーハンドリングの適切性
- [ ] ドキュメント整合性

## 8.0 リスク分析

### 8.1 技術リスク
- **リスク**: ハッシュ衝突（理論的に極小）
- **対策**: 複数ファイル対応、ログによる監視

- **リスク**: インデックス破損
- **対策**: 自動再構築機能、バックアップ仕組み

### 8.2 パフォーマンスリスク
- **リスク**: 大量ファイル時の初期インデックス構築時間
- **対策**: 段階的インデックス構築、進捗表示

## 9.0 受け入れ基準

### 9.1 機能確認
- [ ] SHA256ハッシュでファイル検索成功
- [ ] ハッシュ指定でファイル内容取得成功
- [ ] ファイル変更検知成功（1バイト変更でも検知）
- [ ] MCPツール経由でのアクセス成功

### 9.2 性能確認
- [ ] 1000ファイル環境でO(1)検索確認
- [ ] レスポンス時間100ms以内確認
- [ ] 同時アクセス5クライアント対応確認

### 9.3 品質確認
- [ ] テストカバレッジ80%以上
- [ ] B20準拠チェック通過
- [ ] Git Hooks品質ゲート通過

## 10.0 付録

### 10.1 用語集
- **SHA256**: Secure Hash Algorithm 256-bit、暗号学的ハッシュ関数
- **ハッシュインデックス**: ハッシュ値をキーとするファイル検索インデックス
- **FileReferenceModel**: ファイル参照情報を格納するデータモデル

### 10.2 関連ドキュメント
- B20_Claude_Code開発作業指示書.md
- docs/references/shared_components_catalog.md
- CODEMAP.yaml
- B30_Claude_Code品質作業指示書.md

### 10.3 変更履歴
| 日付 | バージョン | 変更内容 | 担当者 |
|------|-----------|----------|--------|
| 2025-01-11 | 1.0.0 | 初版作成 | Claude |

---
**承認**: [ ] 技術レビューア  [ ] プロジェクトマネージャー
**実装開始日**: 2025年01月11日
