# Domain / Infrastructure Test Inventory & Action Plan (2025-09-17)

目的: TODO「Domain/Infrastructure 層テストのグルーピング」の実行準備として、現状のテスト分布と具体的タスクを整理する。

## 1. 現状サマリ

| セグメント | テスト数（test_*.py） | 備考 |
| --- | --- | --- |
| Domain services | 57 | 品質・学習・アーティファクト等が混在。 |
| Domain value_objects | 50 | Quality/WordCount/Plot等のVOテスト。 |
| Domain entities | 46 | Episode/Quality/Plot系が中心。 |
| Domain repositories | 7 | YAMLやQualityRecord等。 |
| Domain quality/|value_objects|domain直下 | 19 | 品質関連テストが複数ディレクトリに散在。 |
| Domain plot/episode関連 | 11 | Stepwise/IntegratedWritingに関連するが重複多め。 |
| Domain legacy (DDD/Design by Contract 等) | 4 | 旧仕様の検証。 |
| Infrastructure repositories | 6 | YAML系が中心。 |
| Infrastructure adapters/services/json等 | 10 | Config/JSON/Adapterなど多岐にわたる。 |

計測方法: `find tests/unit/domain -name 'test_*.py'` 等でサブディレクトリごとに集計。

## 2. Priority A タスク

### Q1 Qualityドメイン再編 *(完了 2025-09-17)*
- **対象テスト**
  - entities: `tests/unit/domain/entities/test_quality_*.py`
  - services: `tests/unit/domain/services/test_*quality*.py`
  - value objects: `tests/unit/domain/value_objects/test_quality*.py`
  - domain直下: `tests/unit/domain/test_quality_*.py`
- **アクション**
  1. 上記テストを `tests/unit/domain/quality/<entities|services|value_objects|workflows|integration>/` に集約済み。
  2. 各テストに `pytestmark = pytest.mark.quality_domain` を付与。`pyproject.toml` に `quality_domain` マーカーを追加。
  3. 旧仕様テストの棚卸しは継続タスク（アーカイブ候補の精査が必要）。
- **所要時間**: 約3h（整理・移動・マーカー追加）。

### Q2 pytestマーカー整備 *(完了 2025-09-17)*
- **対象**: Quality (`quality_domain`)、Plot/Episode (`plot_episode`)、ValueObjectのsmoke/詳細用 (`vo_smoke` / `vo_full`) 等。
- **アクション**
  1. `pyproject.toml` に `plot_episode`, `vo_smoke` を追加済み（`quality_domain` と合わせて定義）。
  2. 該当テストに `pytestmark = pytest.mark.plot_episode` / `pytestmark = pytest.mark.vo_smoke` を付与。
  3. ドキュメント追記は未（今後のフォローアップ）。
- **所要時間**: 約2h。

### Q3 Plot/Episode テスト整理 *(進行中 2025-09-17)*
- **対象テスト**（一覧）
  - entities: `test_episode*.py`, `test_plot*.py`
  - repositories: `test_plot_progress_repository.py`, `test_episode_and_project_repositories.py`
  - domain直下: `test_domain_plot*.py`, `test_episode_completion*.py`
  - services: `test_episode_*_service.py`, `test_plot_*_service.py`
  - value objects: `test_episode_*`, `test_plot_version_consistency.py`
- **進捗**
  1. `tests/unit/domain/plot_episode/` 配下に `entities/`, `services/`, `value_objects/`, `repositories/`, `workflows/`, `versioning/` を新設し、該当テストを移動済み。
  2. すべてのテストに `pytestmark = pytest.mark.plot_episode` を付与。
  3. Value objects の `vo_smoke` マーカーは plot 系から除外（一般VOのみに付与）。
  4. 仕様がアーカイブに移ったサービス系テスト（`test_episode_management_sync.py`, `test_episode_metadata_management_service.py`）は `archive/tests/plot_episode/services/` へ退避。
- **残課題**
  - 旧仕様・重複テストの棚卸しとアーカイブ判断。
  - `tests/unit/domain/services/test_plot_creation_service.py` 等の冗長ケース整理、テンプレートとの整合確認。
  - ドキュメント更新（Plot/Episodeサブスイートの実行方法）。
- **見積り**: 残作業 2h 目安。

## 3. Priority B・C（参考）
- **V1 ValueObject軽量化**: invariantsテストのParametrize化／Hypothesis統一を検討。
- **I1 YAMLリポジトリFixture統合**: `tests/unit/infrastructure/repositories/test_yaml_*.py` を共通Fixtureへ集約。
- **L1 Legacy資産棚卸し**: `test_ddd_validator.py` 等をアーカイブへ移動し、現行CIから除外。

## 4. 推奨実行順
1. Q1 → Q2 → Q3 の順でQuality/Plot再編に着手。
2. 並行して ValueObjectテスト削減 (V1) の計画を立案。
3. YAMLリポジトリ (I1) や legacy テスト (L1) の整理は後続タスクとして扱う。

---
更新日: 2025-09-17
