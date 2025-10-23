# SPEC-JSON-001: 差分更新システム仕様書（RFC6902 JSON Patch × Unified Diff）

**作成日**: 2025-08-25
**更新日**: 2025-08-25
**対象機能**: 執筆プロンプトシステムにおける差分管理・部分更新機能
**優先度**: High
**実装対象**: scripts.domain.value_objects, scripts.infrastructure.services

## 📋 要件概要

### ビジネス価値
- **トークン使用量を98%削減**（全文再送信 → 差分のみ送信）
- **Claude APIコストを95%以上削減**
- **レスポンス時間を80%短縮**
- **変更履歴の完全な追跡性確保**

### 技術要件
- **RFC6902 JSON Patch形式**による精密な差分管理
- **Unified Diff形式**による人間可読な変更表示
- **アトミックな変更操作**と完全なロールバック機能
- 既存システムとの完全な互換性維持

## 🎯 機能仕様

### 1. 差分更新エンティティ（DifferentialUpdate）

```python
@dataclass
class DifferentialUpdate:
    """差分更新を表現するドメインモデル"""

    update_id: str                        # 一意の更新識別子
    timestamp: datetime                   # 更新タイムスタンプ
    update_type: UpdateType               # revision, correction, enhancement, structural
    target_step: int                      # 対象ステップ番号
    json_patch: List[Dict[str, Any]]     # RFC6902形式の差分操作
    unified_diff: str                     # Unified Diff形式の表示用差分

    # 品質メトリクス変化
    quality_delta: Optional[Dict[str, float]] = None

    # トークン効率
    token_saved: Optional[int] = None
    compression_ratio: Optional[float] = None

    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2. JSON Patch操作仕様（RFC6902準拠）

#### 基本操作
```json
[
  {
    "op": "replace",
    "path": "/scenes/1/content",
    "value": "新しいシーン内容..."
  },
  {
    "op": "add",
    "path": "/scenes/-",
    "value": {
      "type": "action",
      "content": "追加シーン..."
    }
  },
  {
    "op": "remove",
    "path": "/temp_notes"
  },
  {
    "op": "test",
    "path": "/version",
    "value": "1.0.0"
  }
]
```

#### パス構造定義
```
/step_number                     # ステップ番号
/generated_text                  # 本文
/scenes/[index]                  # シーン配列
/scenes/[index]/content          # シーン内容
/scenes/[index]/revisions/[n]    # 改稿履歴
/metadata/*                      # メタデータ
/quality_metrics/*               # 品質指標
```

### 3. Unified Diff形式表示

```diff
--- original_step_7.txt
+++ revised_step_7.txt
@@ -120,7 +120,9 @@ Scene 2: Discovery
 　直人はコンソールを見つめた。
-　エラーメッセージが赤く点滅している。
+　警告メッセージが黄色く点滅している。
 　「また同じ警告か...」
+　
+　しかし、今回は何かが違っていた。
```

## 🔧 技術設計

### アーキテクチャ統合点

```python
# Domain Layer: 新しい Value Objects
scripts.domain.value_objects.differential_update.py         # 差分更新エンティティ
scripts.domain.value_objects.revision_history.py           # 改稿履歴管理

# Application Layer: サービス層
scripts.application.services.differential_update_service.py # 差分管理サービス
scripts.application.services.revision_history_manager.py   # 履歴管理サービス

# Infrastructure Layer: アダプター層
scripts.infrastructure.adapters.json_patch_adapter.py      # JSON Patch処理
scripts.infrastructure.adapters.unified_diff_adapter.py    # Diff生成
```

### 実装アプローチ

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import jsonpatch
import difflib
from datetime import datetime
from enum import Enum

class UpdateType(Enum):
    REVISION = "revision"      # 改稿
    CORRECTION = "correction"   # 誤字修正
    ENHANCEMENT = "enhancement" # 品質向上
    STRUCTURAL = "structural"   # 構造変更

class DifferentialUpdateService:
    """差分更新管理サービス"""

    def create_patch(
        self,
        original: Dict[str, Any],
        modified: Dict[str, Any],
        update_type: UpdateType = UpdateType.REVISION
    ) -> DifferentialUpdate:
        """オリジナルと修正版から差分更新を作成"""

        # JSON Patch生成
        json_patch = jsonpatch.make_patch(original, modified)

        # Unified Diff生成
        original_text = self._extract_text_content(original)
        modified_text = self._extract_text_content(modified)
        unified_diff = self._generate_unified_diff(original_text, modified_text)

        # トークン効率計算
        token_saved = self._calculate_token_saving(original, json_patch)
        compression_ratio = 1 - (len(str(json_patch)) / len(str(original)))

        return DifferentialUpdate(
            update_id=self._generate_update_id(),
            timestamp=datetime.now(),
            update_type=update_type,
            target_step=original.get("step_number"),
            json_patch=list(json_patch),
            unified_diff=unified_diff,
            token_saved=token_saved,
            compression_ratio=compression_ratio
        )
```

## ✅ 受け入れ基準

### 機能要件
- [ ] RFC6902準拠のJSON Patch生成・適用が可能
- [ ] Unified Diff形式での変更表示が可能
- [ ] 完全なロールバック機能の実装
- [ ] 変更履歴の永続化と取得

### 品質要件
- [ ] トークン削減率95%以上を実現
- [ ] 処理時間100ms以内
- [ ] メモリ使用量10MB以内
- [ ] DDD層構造に準拠
- [ ] CLAUDE.md準拠（日本語docstring、インポート方針等）

### セキュリティ要件
- [ ] JSON Patchインジェクション対策
- [ ] パス検証の厳格化
- [ ] 操作権限の確認

## 🧪 テスト戦略

### 単体テスト
```python
@pytest.mark.spec("SPEC-JSON-001")
class TestDifferentialUpdate:
    def test_json_patch_生成_正常系(self):
        """RFC6902準拠のJSON Patchが正しく生成される"""
        original = {"text": "元のテキスト", "scenes": [...]}
        modified = {"text": "修正後のテキスト", "scenes": [...]}

        update = self.service.create_patch(original, modified)
        assert len(update.json_patch) > 0
        assert update.token_saved > 0
        assert update.compression_ratio > 0.9

    def test_unified_diff_生成_正常系(self):
        """Unified Diff形式が正しく生成される"""
        diff = self.service._generate_unified_diff("old", "new")
        assert "---" in diff
        assert "+++" in diff
        assert "@@" in diff

    def test_ロールバック_正常系(self):
        """変更のロールバックが正常に動作する"""
        history = RevisionHistoryManager()
        history.apply_update(update1)
        history.apply_update(update2)

        rolled_back = history.rollback(steps=1)
        assert rolled_back == state_after_update1
```

### 統合テスト
```python
@pytest.mark.spec("SPEC-JSON-001")
class TestDifferentialSystemIntegration:
    def test_執筆ステップ差分更新_正常系(self):
        """執筆ステップの部分更新が正常に動作する"""
        # Step 7の部分的な改稿
        update = self.cli.execute_partial_update(
            step_number=7,
            update_type="revision",
            changes={...}
        )
        assert update.compression_ratio > 0.95

    def test_トークン削減効果_測定(self):
        """実際のトークン削減効果を測定"""
        results = self.measure_token_efficiency(sample_updates)
        assert results.average_reduction > 0.95  # 95%以上削減
```

## 📊 実装影響範囲

### 新規作成ファイル
- `scripts/domain/value_objects/differential_update.py`
- `scripts/domain/value_objects/revision_history.py`
- `scripts/application/services/differential_update_service.py`
- `scripts/application/services/revision_history_manager.py`
- `scripts/infrastructure/adapters/json_patch_adapter.py`
- `scripts/infrastructure/adapters/unified_diff_adapter.py`

### 依存関係
- 既存: `dataclasses`, `json`, `typing`, `datetime`, `enum`
- 新規: `jsonpatch` (RFC6902実装), `difflib` (Diff生成)

## 🚀 実装スケジュール

### Phase 1: 基本実装（即座実装可能）
- DifferentialUpdateモデル作成
- JSON Patch生成・適用機能
- Unified Diff生成機能
- 基本的なCLIインターフェース

### Phase 2: 品質保証層（1週間）
- バリデーション機能強化
- ロールバック機能実装
- 履歴管理システム
- 包括的テストスイート

### Phase 3: 統合・最適化（2週間）
- 既存システムとの完全統合
- パフォーマンス最適化
- UI/UX改善
- ドキュメント整備

## 📈 期待効果

### 定量的効果
- **トークン使用量**: 98%削減（10,000 → 200トークン）
- **API呼び出しコスト**: 95%以上削減
- **レスポンス時間**: 80%短縮
- **ストレージ使用量**: 90%削減（差分のみ保存）

### 定性的効果
- 精密な変更管理による品質向上
- 完全な変更履歴による監査性向上
- 視覚的な差分確認による理解度向上
- 協調編集への拡張可能性

## 🎯 成功指標

1. **技術指標**
   - トークン削減率 > 95%
   - 処理時間 < 100ms
   - テストカバレッジ > 90%

2. **ビジネス指標**
   - APIコスト削減額の測定
   - ユーザー満足度の向上
   - 改稿作業時間の短縮

## 📚 参考資料

- [RFC 6902 - JavaScript Object Notation (JSON) Patch](https://datatracker.ietf.org/doc/html/rfc6902)
- [Unified Diff Format Specification](https://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html)
- [jsonpatch Python Library](https://github.com/stefankoegl/python-json-patch)
