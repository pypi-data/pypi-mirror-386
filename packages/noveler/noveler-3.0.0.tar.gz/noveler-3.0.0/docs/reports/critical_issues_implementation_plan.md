# 最重要課題実装計画書

**作成日**: 2025-10-03
**分析対象**: Novelerコードベース全体（1,278ソースファイル、7,107テスト）
**分析手法**: Serena深層モード (-d -s -c)

---

## 📊 Executive Summary

### プロジェクト健全性評価

| 指標 | 現状 | 評価 |
|------|------|------|
| **技術負債削減率** | 85.7% | 🟢 優秀 |
| **DDD準拠率** | 100% (違反0件) | 🟢 優秀 |
| **テストカバレッジ** | 未測定 | 🟡 要改善 |
| **Path API統一率** | 91.4% (102件残存) | 🟡 要改善 |
| **Repository命名統一** | 78% (レガシー12件) | 🟡 進行中 |

### 最重要課題トップ3

1. **IPathService完全統一** - 影響度⭐⭐⭐⭐⭐（最優先）
2. **Repository命名規則統一** - 影響度⭐⭐⭐⭐（高）
3. **テストカバレッジ可視化** - 影響度⭐⭐⭐（中）

---

## 🥇 課題1: IPathService完全統一プロジェクト

### 1.1 問題の詳細

#### 現状分析
- **38箇所のTODOマーカー**が Domain層に残存
- **8箇所の os module 直接import**（DDD原則違反）
- Path操作の一貫性が未達成（91.4%）
- 最後の9%が技術負債として蓄積中

#### 影響範囲
```
高頻度影響ファイル（3+ TODOs）:
├─ content_quality_enhancer.py (5 TODOs)
├─ deliverable_check_service.py (4 TODOs)
├─ episode_management_service.py (3 TODOs)
└─ auto_repair_engine.py (3 TODOs + os import)

os module 直接使用:
├─ auto_repair_engine.py (os.walk)
├─ enhanced_plot_generation_service.py
├─ environment_diagnostic_service.py
├─ episode_management_sync_service.py
├─ progressive_check_manager.py
├─ system.py
├─ system_diagnostics.py
└─ a31_checklist_data.py (ValueObject層)
```

#### ビジネスリスク
1. **クロスプラットフォーム互換性の脆弱性**
   - Windows/WSL/Linux間でパス処理が不統一
   - 環境依存バグの潜在リスク

2. **テスタビリティの低下**
   - os module直接使用により単体テストでのモックが困難
   - CI/CDパイプラインでのテスト信頼性低下

3. **保守性の悪化**
   - パス操作ロジックが散在
   - 将来的な変更コスト増大

---

### 1.2 実装計画

#### Phase 1: 高影響ファイル修正（Week 1-2）

**Day 1-2: content_quality_enhancer.py**
```python
# 修正パターン例
# Before:
project_dir = Path(project_path)  # TODO
if not project_dir.exists():
    raise ProjectSettingsNotFoundError(...)
with Path(character_file).open(encoding="utf-8") as f:
    data = yaml.safe_load(f)

# After:
def __init__(self, path_service: IPathService):
    self._path_service = path_service

if not self._path_service.exists(project_path):
    raise ProjectSettingsNotFoundError(...)
data = self._path_service.read_yaml(
    self._path_service.join(project_path, "キャラクター.yaml")
)
```

**実装ステップ**:
1. Constructor に `path_service: IPathService` を追加
2. 5箇所のPath操作を `_path_service` メソッドに置換
3. 既存テストの実行確認（pytest -xvs tests/unit/domain/services/test_content_quality_enhancer.py）
4. コミット + importlinter 実行

**Day 3-4: deliverable_check_service.py**
- 同様のパターン（4箇所修正）

**Day 5-7: auto_repair_engine.py**（複雑度高）
```python
# os.walk() の置換例
# Before:
for dirpath, dirnames, filenames in os.walk(directory):
    total_size += sum(file_path.stat().st_size for ...)

# After:
for entry in self._path_service.walk(directory):
    if entry.is_file():
        total_size += entry.stat().st_size
```

**Day 8-10: episode_management_service.py**
- 同様のパターン（3箇所修正）

**Phase 1 完了基準**:
- ✅ 4ファイル、計15箇所のTODO解消
- ✅ os import 1箇所削除（auto_repair_engine.py）
- ✅ 全単体テスト通過
- ✅ importlinter 検証通過

---

#### Phase 2: 中影響ファイル修正（Week 3）

**対象ファイル**（各2 TODOs）:
1. quality_requirements_auto_fixer.py
2. episode_number_resolver.py
3. b20_integrated_nih_prevention_service.py
4. a31_result_integrator.py

**実装戦略**:
- バッチ処理（2ファイル/日）
- 各ファイル修正後にテスト実行
- 2日ごとにコミット

**Phase 2 完了基準**:
- ✅ 4ファイル、計8箇所のTODO解消
- ✅ 累計23箇所（38箇所中60%）完了

---

#### Phase 3: 残存os module削除（Week 4: Day 1-3）

**対象**（7ファイル）:
1. enhanced_plot_generation_service.py
2. environment_diagnostic_service.py
3. episode_management_sync_service.py
4. progressive_check_manager.py
5. system.py
6. system_diagnostics.py
7. a31_checklist_data.py

**実装パターン**:
```python
# Before:
import os
env_var = os.getenv("NOVELER_PATH")

# After:
# ConfigurationManagerを使用（既存パターンに準拠）
config = get_configuration_manager()
env_var = config.get_env("NOVELER_PATH")
```

**Phase 3 完了基準**:
- ✅ Domain層から os import 完全削除
- ✅ 環境変数アクセスは ConfigurationManager 経由に統一

---

#### Phase 4: 残り単一TODOファイル（Week 4: Day 4-7）

**対象**: 12+ ファイル（各1 TODO）

**バッチ処理戦略**:
- 1日あたり3-4ファイル処理
- 簡単なパターンマッチで一括修正可能

**Phase 4 完了基準**:
- ✅ 全38箇所のTODO完全解消
- ✅ Domain層Path操作100%統一

---

### 1.3 品質ゲート

#### 各Phase完了時の必須チェック
```bash
# 1. テスト実行
bin/test tests/unit/domain -x

# 2. importlinter検証
python -m importlinter

# 3. TODO残存確認
grep -r "TODO.*IPathService" src/noveler/domain --include="*.py" | wc -l
# Expected: 0

# 4. os import確認
grep -r "import os\|from os import" src/noveler/domain --include="*.py" | wc -l
# Expected: 0
```

---

### 1.4 リスク管理

| リスク | 確率 | 影響 | 軽減策 |
|--------|------|------|--------|
| 既存テスト失敗 | 中 | 高 | 各ファイル修正後に即テスト実行 |
| IPathService未実装メソッド遭遇 | 低 | 中 | Phase 1で検証、必要なら先行実装 |
| 大規模リファクタリングによる予期せぬ副作用 | 低 | 高 | 小規模バッチ＋頻繁なコミット |

---

### 1.5 期待効果

**定量的効果**:
- Path API統一率: 91.4% → 100%（+8.6%）
- Domain層 os import: 8件 → 0件（100%削減）
- TODOマーカー: 38件 → 0件（100%削減）

**定性的効果**:
- クロスプラットフォーム互換性の完全保証
- DDD原則への完全準拠
- テスタビリティの向上
- 将来的なPath操作変更コストの削減

---

## 🥈 課題2: Repository命名規則統一

### 2.1 現状

- 総Repository関連ファイル: **154ファイル**
- レガシーパターン（`File*Repository`）: **12ファイル**
- 推奨パターン（`{Tech}{Entity}Repository`）: **82ファイル**
- ドキュメント整備: ✅ 完了（2025-10-03）
- pre-commit hook: ✅ 実装済み

### 2.2 段階的移行戦略

#### Phase 1: 新規作成時の厳格適用（現在進行中）

**施策**:
- ✅ `docs/architecture/repository_naming_conventions.md` 作成
- ✅ `scripts/hooks/check_repository_naming.py` 実装
- ✅ pre-commit hook 統合

**効果**: 新規ファイルの100%準拠保証

---

#### Phase 2: アクティブファイルの優先移行（Month 1-3）

**対象選定基準**:
1. 過去3ヶ月でcommit履歴のあるファイル
2. 新機能開発で影響を受けるファイル
3. 重複名が存在するファイル

**実装例**:
```bash
# Before: file_episode_repository.py
class FileEpisodeRepository(EpisodeRepository):
    pass

# After: yaml_episode_repository.py
class YamlEpisodeRepository(EpisodeRepository):
    pass
```

**移行手順**:
1. ファイル名変更（`git mv file_*.py yaml_*.py`）
2. クラス名変更
3. 全importパス更新（IDE refactoring推奨）
4. テスト実行（`bin/test tests/unit/infrastructure/repositories/test_*.py`）
5. importlinter検証
6. コミット

**目標**: 月5-10ファイル移行

---

#### Phase 3: 長期的な完全統一（Month 4-12）

**対象**: 残り全レガシーファイル

**戦略**: 新機能開発のタイミングで自然に移行

---

### 2.3 期待効果

**定量的**:
- レガシーパターン: 12件 → 0件（12ヶ月後）
- 命名規則準拠率: 78% → 100%

**定性的**:
- コードベース検索性の向上
- 新規開発者のオンボーディング効率化
- DDD原則の可視化強化

---

## 🥉 課題3: テストカバレッジ可視化プロジェクト

### 3.1 現状

- テストケース: **7,107件**（圧倒的な量）
- テストクラス: **975個**
- **問題**: カバレッジ率が未測定
- リスク: 品質の定量評価が不可能

### 3.2 実装計画

#### Phase 1: カバレッジ測定基盤（Day 1）

```bash
# 1. pytest-cov インストール
pip install pytest-cov

# 2. 初回カバレッジ測定
pytest --cov=src/noveler \
       --cov-report=html \
       --cov-report=term \
       --cov-report=json \
       > reports/coverage_baseline.txt

# 3. HTMLレポート確認
open htmlcov/index.html
```

---

#### Phase 2: CI/CD統合（Day 2）

**pyproject.toml 設定追加**:
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=src/noveler",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=json",
    "--cov-fail-under=75",  # 初期閾値
]

[tool.coverage.run]
source = ["src/noveler"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

**Makefile 更新**:
```makefile
.PHONY: test-coverage
test-coverage:
	pytest --cov=src/noveler --cov-report=html --cov-report=term

.PHONY: coverage-report
coverage-report:
	open htmlcov/index.html
```

---

#### Phase 3: カバレッジ閾値設定（Day 3）

**ベースライン測定後の設定例**:
```toml
[tool.coverage.report]
fail_under = 75  # Phase 1目標
precision = 2

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.json]
output = "coverage.json"
```

---

#### Phase 4: 低カバレッジモジュール改善（Week 2-4）

**戦略**:
1. カバレッジ60%未満のモジュールを特定
2. 優先度付け（Domain層 > Application層）
3. 週次で3-5モジュール改善

**改善パターン**:
```python
# 例: 未カバーのエラーハンドリング追加
def test_service_with_invalid_input():
    service = MyService(path_service=mock_path_service)
    with pytest.raises(ValidationError):
        service.process(invalid_input)
```

---

### 3.3 品質ゲート

```yaml
# .github/workflows/test.yml（例）
- name: Run tests with coverage
  run: |
    pytest --cov=src/noveler --cov-report=xml --cov-fail-under=75

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

---

### 3.4 期待効果

**定量的**:
- カバレッジ率: 未測定 → 75%+ （Phase 1目標）
- 低カバレッジモジュール: → 0件（3ヶ月後）

**定性的**:
- 品質の可視化
- 回帰リスクの早期検出
- CI/CDパイプラインの信頼性向上

---

## 📅 統合タイムライン（30日間）

### Week 1-2: IPathService Phase 1
- Day 1-2: content_quality_enhancer.py
- Day 3-4: deliverable_check_service.py
- Day 5-7: auto_repair_engine.py
- Day 8-10: episode_management_service.py

### Week 3: IPathService Phase 2 + Coverage Phase 1-3
- Day 11-12: 中影響ファイル（2ファイル）
- Day 13-14: 中影響ファイル（2ファイル）
- Day 15: カバレッジ測定基盤
- Day 16-17: CI/CD統合 + 閾値設定

### Week 4: IPathService Phase 3-4 + Coverage Phase 4
- Day 18-20: os module削除（7ファイル）
- Day 21-24: 単一TODOファイル（12ファイル）
- Day 25-28: 低カバレッジモジュール改善

---

## 🎯 成功基準

### IPathService統一
- ✅ Domain層 TODO: 38件 → 0件
- ✅ os import: 8件 → 0件
- ✅ Path API統一率: 91.4% → 100%
- ✅ 全テスト通過
- ✅ importlinter検証通過

### Repository命名規則
- ✅ 新規ファイル100%準拠（進行中）
- ✅ レガシーファイル: 12件 → 6件（3ヶ月後）

### テストカバレッジ
- ✅ カバレッジ測定基盤稼働
- ✅ CI/CD統合完了
- ✅ 全体カバレッジ: 75%+達成
- ✅ Domain層カバレッジ: 80%+達成

---

## 📊 KPI追跡

```bash
# 毎週実行
./scripts/quality_reports/weekly_metrics.sh

# 出力例:
# IPathService TODO残存: 23/38 (39%減)
# os import残存: 5/8 (37%減)
# カバレッジ: 76.3% (目標達成)
# レガシーRepository: 11/12 (8%減)
```

---

## 🚀 即座に実行可能なアクション

```bash
# 1. 詳細分析レポート生成（完了）
cat reports/ipathservice_migration_summary.md

# 2. カバレッジベースライン測定（次ステップ）
pip install pytest-cov
pytest --cov=src/noveler --cov-report=html > reports/coverage_baseline.txt

# 3. Phase 1開始準備
git checkout -b feature/ipathservice-phase1-high-impact-files

# 4. 最初のファイル編集
code src/noveler/domain/services/content_quality_enhancer.py
```

---

## 📚 関連ドキュメント

- [IPathService Migration Summary](./ipathservice_migration_summary.md)
- [Repository Naming Conventions](../docs/architecture/repository_naming_conventions.md)
- [Technical Debt Assessment](../.serena/memories/final_technical_debt_assessment_2025_09_08.md)
- [CLAUDE.md - Layering Principles](../CLAUDE.md#レイヤリング原則必須)
- [ARCHITECTURE.md](../ARCHITECTURE.md)

---

**最終更新**: 2025-10-03
**次回レビュー**: 2025-10-10（Week 1完了時）
