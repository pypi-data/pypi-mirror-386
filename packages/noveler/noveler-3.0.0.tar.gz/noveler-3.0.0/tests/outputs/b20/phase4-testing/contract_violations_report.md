# 契約違反検出レポート

**対象:** B20 Workflow Phase 4 - Testing
**実行日:** 2025-10-03
**検出ツール:** pytest contract tests (計画)

---

## 実行状況

**ステータス:** ⚠️ **検出未実施**

**理由:** テスト収集段階でインポートエラーが発生し、契約テストコードが実行できませんでした。

**エラー原因:**
- モジュール `aiofiles` が未インストール
- 影響範囲: 5つのテストファイル
- エラー箇所: `noveler.infrastructure.performance.async_file_processor:23`

---

## 検出予定だった契約違反タイプ

`.b20rc.yaml` §8.2で定義された5種類の契約違反：

| 違反タイプ | 説明 | 検出方法（計画） |
|-----------|------|---------------|
| `return_type_change` | 戻り値の型変更 | 型ヒント比較、実行時型チェック |
| `parameter_removal` | パラメータ削除 | シグネチャ解析 |
| `exception_type_change` | 例外型変更 | docstring + 実行時検証 |
| `precondition_strengthening` | 事前条件の強化 | 契約テスト（`deal`ライブラリ） |
| `postcondition_weakening` | 事後条件の弱化 | 契約テスト（`deal`ライブラリ） |

---

## 検出結果

**検出された違反:** 0件 (テスト未実行のため)

**警告:** 0件

**保留事項:** 5種類すべて未検証

---

## 影響分析

### テスト実行不可によるリスク

1. **後方互換性の保証なし**
   - パブリックAPI変更が契約違反を引き起こしていても検出不可
   - 既存ユーザーコードが破損する可能性

2. **LSP（リスコフ置換原則）の検証不足**
   - サブタイプが親型と置換可能かの検証ができていない
   - SOLID原則のLSPは静的チェックのみで部分的

3. **例外仕様変更の見逃し**
   - 新しい例外が追加されても検出できない
   - エラーハンドリング不足によるランタイムエラーのリスク

---

## 改善アクション

### 即時対応（Must）

1. **依存関係修正**
   ```bash
   # pyproject.toml に追加
   dependencies = [
       ...
       "aiofiles>=23.0.0",
   ]
   ```

2. **テスト再実行**
   ```bash
   pytest tests/ --contract-only  # 契約テストのみ実行
   ```

### 中期対応（Should）

1. **契約テスト専用マーカー導入**
   ```python
   @pytest.mark.contract
   @pytest.mark.spec("SPEC-CONTRACT-001")
   def test_api_contract_stability():
       """公開API契約の安定性検証"""
       pass
   ```

2. **自動契約検証の追加**
   - `deal` ライブラリの `@deal.pre`, `@deal.post` デコレータ活用
   - CI/CDでの自動契約検証フック追加

3. **契約違反検出の自動化**
   - `pytest-contracts` プラグイン導入検討
   - または独自の契約検証フィクスチャ実装

---

## 契約テストの実装ガイドライン（参考）

### 推奨パターン

```python
import pytest
from noveler.domain.services import QualityCheckService

@pytest.mark.contract
@pytest.mark.spec("SPEC-QUALITY-001")
class TestQualityCheckServiceContract:
    """品質チェックサービスの契約テスト"""

    def test_run_checks_returns_stable_structure(self):
        """run_checks()の戻り値構造が安定していることを検証"""
        service = QualityCheckService()
        result = service.run_checks(episode=1)

        # 必須キーの存在確認（契約）
        assert "summary" in result
        assert "issues" in result
        assert "metadata" in result

        # 型の安定性確認
        assert isinstance(result["issues"], list)
        assert all("line_number" in issue for issue in result["issues"])

    def test_run_checks_raises_documented_exceptions_only(self):
        """run_checks()が文書化された例外のみを発生させることを検証"""
        service = QualityCheckService()

        with pytest.raises((ValueError, FileNotFoundError)):
            # これら以外の例外が発生したら契約違反
            service.run_checks(episode=-1)
```

---

## 次回検証時の準備

### チェックリスト

- [ ] `aiofiles` 依存関係追加
- [ ] `pip install -e .[dev,test]` で環境更新
- [ ] `pytest tests/ --collect-only` で収集確認
- [ ] `pytest -m contract` で契約テストのみ実行
- [ ] カバレッジレポート再生成（80%目標）
- [ ] 本レポートの更新（実際の検出結果を反映）

---

## 判断ログ (Decision Log 参照)

本件に関連する判断は `tests/outputs/b20/decision_log.yaml` に記録してください：

```yaml
- timestamp: "2025-10-03T01:35:00Z"
  decision_type: "dependency_management"
  rationale: "AsyncFileProcessor が aiofiles に依存しているが pyproject.toml に明記されていなかった"
  alternatives_considered:
    - "条件付きインポート（try-except）"
    - "AsyncFileProcessor を optional dependency 化"
    - "aiofiles を必須依存に昇格"
  impact_assessment:
    - "テスト実行が阻害されている"
    - "契約違反検出が不可能"
    - "CI/CDパイプラインへの影響"
  decision: "aiofiles を必須依存に追加（パフォーマンス最適化に必須のため）"
```

---

**レポート終了**

**次のアクション:** 依存関係修正後、このレポートを実際の検出結果で更新してください。
