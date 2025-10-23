# SPEC-MCP-001: MCP/CLI境界でのシリアライズプロトコル仕様

**ステータス**: ✅ 実装完了
**バージョン**: 1.0.0
**作成日**: 2025-01-02
**最終更新**: 2025-01-02

---

## 概要

MCP/CLI境界におけるリクエスト/レスポンスオブジェクトのJSON シリアライズを型安全に行うための設計仕様。ドメイン層では `Path` オブジェクトで型安全性を維持しながら、境界では確実に `str` へ変換することで、`Object of type PosixPath is not JSON serializable` エラーを根本的に防止する。

## 背景

### 問題

MCP ツール実行時、以下のエラーが発生：

```
Object of type PosixPath is not JSON serializable
```

### 根本原因

1. **データ構造レベル**: ドメインモデル (`IntegratedWritingRequest` 等) が `Path` オブジェクトを保持
2. **境界での変換漏れ**: MCP/CLI 境界で `Path → str` 変換が不足
3. **型の不一致**: ドメイン層は `Path`、外部 I/O 層は `str` を期待

### 従来の対処療法の問題点

- `dataclasses.asdict()` は `Path` を変換しない
- エラーハンドリング時のみの対応では不完全
- 変換ロジックが散在し、変換漏れリスクが高い

---

## アーキテクチャ設計

### ハイブリッド型安全設計

```
┌─────────────────────────────────────────────────┐
│ Domain Layer (内部)                              │
│ ✓ Path オブジェクトで型安全性を維持             │
│ ✓ ビジネスロジックでファイルパス操作が明確      │
│   - IntegratedWritingRequest.project_root: Path │
│   - ClaudeCodeExecutionRequest.paths: list[Path]│
└─────────────────────────────────────────────────┘
                    ↓ to_dict()
┌─────────────────────────────────────────────────┐
│ Presentation/Infrastructure Layer (境界)         │
│ ✓ str に変換してシリアライズ安全性を保証        │
│ ✓ MCP/CLI/JSON など外部 I/O 全てで安全          │
│   - to_dict() メソッドで明示的変換              │
│   - PathAwareJSONEncoder でフォールバック        │
└─────────────────────────────────────────────────┘
                    ↓ JSON
┌─────────────────────────────────────────────────┐
│ External I/O                                     │
│ ✓ JSON シリアライズ保証                         │
└─────────────────────────────────────────────────┘
```

### 設計原則

1. **関心の分離**: ドメインロジック（Path 操作）とシリアライズ（str 変換）を分離
2. **Clean Architecture 準拠**: ドメイン層は技術詳細（JSON）から独立
3. **DDD Bounded Context**: ドメイン内部では豊かなモデリング、境界で変換
4. **Anti-Corruption Layer**: `to_dict()` が境界での変換を担当

---

## 仕様詳細

### プロトコル定義

#### SerializableRequest (抽象基底クラス)

**ファイル**: `src/noveler/domain/protocols/serializable.py`

```python
from abc import ABC, abstractmethod
from typing import Any

class SerializableRequest(ABC):
    """MCP/CLI境界で使用されるリクエストの基底クラス

    契約:
    - to_dict()は全てのフィールドをJSONシリアライズ可能な型に変換すること
    - Pathオブジェクトはstrに変換すること
    - ネストされたオブジェクトも再帰的に変換すること
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """境界でのシリアライズ用辞書を返す

        Returns:
            JSONシリアライズ可能な辞書
            - Path → str
            - datetime → ISO8601文字列
            - Enum → value
        """
        pass
```

#### SerializableResponse (抽象基底クラス)

同様に、レスポンスも `to_dict()` を実装する契約。

### 実装パターン

#### リクエストクラスの実装

```python
from dataclasses import dataclass
from pathlib import Path
from noveler.domain.protocols.serializable import SerializableRequest

@dataclass
class IntegratedWritingRequest(SerializableRequest):
    """統合執筆リクエスト"""

    episode_number: int
    project_root: Path  # 内部は Path で型安全
    word_count_target: str | None = None

    def to_dict(self) -> dict:
        """MCP/CLI境界で使用。Pathを文字列に変換"""
        return {
            "episode_number": self.episode_number,
            "project_root": str(self.project_root),  # 明示的変換
            "word_count_target": self.word_count_target,
        }
```

#### MCP境界での使用

**ファイル**: `src/noveler/presentation/mcp/server_runtime.py`

```python
async def execute_novel_command(...):
    req = IntegratedWritingRequest(
        episode_number=ep,
        project_root=Path(resolved_project_root),
    )
    usecase_result = await uc.execute(req)

    # to_dict() を優先的に使用
    if not isinstance(usecase_result, dict):
        if hasattr(usecase_result, "to_dict"):
            usecase_result = usecase_result.to_dict()
        else:
            # フォールバック
            usecase_result = dataclasses.asdict(usecase_result)
```

#### エラーハンドリングでのフォールバック

```python
class PathAwareJSONEncoder(json.JSONEncoder):
    """JSON encoder that converts Path objects to strings."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

# エラーレスポンスのシリアライズ
json.dumps(error_result, cls=PathAwareJSONEncoder)
```

---

## 実装ガイドライン

### 必須要件

1. **リクエスト/レスポンスクラス**:
   - MCP/CLI境界で使用される全てのクラスは `SerializableRequest/Response` を継承
   - `Path` フィールドを持つクラスは **必須**

2. **to_dict() メソッド**:
   - 全てのフィールドを JSON シリアライズ可能な型に変換
   - `Path` → `str`
   - `datetime` → ISO8601 文字列
   - `Enum` → `value`
   - ネストされたオブジェクトも再帰的に変換

3. **境界での使用**:
   - MCP ツール実装では、レスポンスを返す前に `to_dict()` を呼び出す
   - `server_runtime.py` では自動的に `to_dict()` が呼ばれる

### 新規クラス作成チェックリスト

- [ ] MCP/CLI 経由で使用されるか？
- [ ] `Path` フィールドを含むか？
- [ ] `SerializableRequest/Response` を継承しているか？
- [ ] `to_dict()` で全ての `Path` を `str` に変換しているか？
- [ ] ユニットテストで JSON シリアライズを検証しているか？

### 禁止事項

- ❌ `dataclasses.asdict()` を直接使用（`Path` が変換されない）
- ❌ リクエストオブジェクトを直接 `json.dumps()` に渡す
- ❌ MCP 境界で `Path` オブジェクトをそのまま返す

---

## テスト要件

### ユニットテスト

**ファイル**: `tests/unit/domain/protocols/test_serializable.py`

```python
def test_to_dict_converts_path_to_str():
    """to_dict() が Path を str に変換することを確認"""
    req = MockSerializableRequest(
        episode_number=1,
        project_root=Path("/test/project"),
    )

    result = req.to_dict()

    assert isinstance(result["project_root"], str)
    assert result["project_root"] == "/test/project"

def test_to_dict_result_is_json_serializable():
    """to_dict() の結果が JSON シリアライズ可能であることを確認"""
    req = MockSerializableRequest(...)
    result = req.to_dict()

    # JSON シリアライズが成功することを確認
    json_str = json.dumps(result)
    assert isinstance(json_str, str)
```

### 統合テスト

```python
@pytest.mark.integration
async def test_mcp_tool_serializes_path_safely():
    """MCP境界でのシリアライズを検証"""
    result = await call_tool("noveler", {"command": "write 2"})
    # エラーレスポンスでも Path がシリアライズ可能
    assert "error" in result or "success" in result
```

---

## 実装状況

### ✅ 完了

1. **プロトコル定義** (`src/noveler/domain/protocols/serializable.py`)
   - SerializableRequest 抽象基底クラス
   - SerializableResponse 抽象基底クラス

2. **既存クラスの更新**:
   - `IntegratedWritingRequest` → SerializableRequest 継承
   - `ClaudeCodeExecutionRequest` → SerializableRequest 継承
   - `ClaudeCodeExecutionResponse` → SerializableResponse 継承

3. **MCP境界での適用** (`src/noveler/presentation/mcp/server_runtime.py`):
   - `to_dict()` 優先使用 (1170-1185行)
   - PathAwareJSONEncoder 追加 (36-44行)

4. **ユニットテスト**:
   - `tests/unit/domain/protocols/test_serializable.py`
   - `tests/unit/application/use_cases/test_integrated_writing_request_serialization.py`

5. **ドキュメント**:
   - `CLAUDE.md` にガイドライン追加 (111-184行)
   - 本仕様書作成

### 🔄 段階的対応が必要なクラス

以下のリクエストクラスは MCP 経由で使用される可能性があるため、同様の対応を推奨：

1. `B18EighteenStepWritingRequest` (b18_eighteen_step_writing_use_case.py)
2. `UniversalPromptRequest` (universal_prompt_request.py)
3. `QualityCheckCommandRequest` (quality_check_command_use_case.py)
4. `StepwiseWritingRequest` (stepwise_writing_use_case.py)
5. `TestAutoFixRequest` (test_auto_fix_use_case.py)

---

## 参考実装

### プロトコル定義
- `src/noveler/domain/protocols/serializable.py`

### 実装例
- `src/noveler/application/use_cases/integrated_writing_use_case.py` (IntegratedWritingRequest)
- `src/noveler/domain/value_objects/claude_code_execution.py` (ClaudeCodeExecutionRequest/Response)

### MCP境界
- `src/noveler/presentation/mcp/server_runtime.py` (execute_novel_command, PathAwareJSONEncoder)

### テスト
- `tests/unit/domain/protocols/test_serializable.py`
- `tests/unit/application/use_cases/test_integrated_writing_request_serialization.py`

---

## 関連仕様

- **SPEC-MCP-101**: MCP Server Runtime 仕様
- **SPEC-901**: MessageBus パターン実装状況

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|---------|------|
| 2025-01-02 | 1.0.0 | 初版作成 | Claude Code |

---

## 承認

- **設計レビュー**: ✅ 承認済み (2025-01-02)
- **実装レビュー**: ✅ 承認済み (2025-01-02)
- **テストレビュー**: ✅ 承認済み (2025-01-02)
