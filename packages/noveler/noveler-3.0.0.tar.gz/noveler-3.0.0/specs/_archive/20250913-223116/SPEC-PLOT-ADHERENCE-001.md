# SPEC-PLOT-ADHERENCE-001: プロット準拠検証機能仕様書

**作成日**: 2025-08-31
**バージョン**: 1.0.0
**対象機能**: プロット準拠検証機能（執筆前確認・執筆後検証・レポート生成）
**実装対象**: `/noveler write` コマンドのA30準拠10段階執筆システム統合

## 1.0 概要

### 1.1 機能概要
小説執筆時にプロット（話別プロット）との準拠性を確認する機能。執筆前にプロット要点を表示し、執筆後にプロットとの整合性を検証してレポートを生成する。

### 1.2 実装理由
現状の調査結果：
- ✅ **執筆前のプロット確認**: A30準拠10段階執筆システムの第2段階「プロット分析・設計」で実施済み
- ❌ **執筆後のプロット準拠チェック**: 実装されていない（品質チェック段階にプロット照合機能なし）

### 1.3 期待効果
- プロット準拠率の可視化（95%以上推奨）
- 執筆品質の向上（プロットからの逸脱防止）
- 自動品質チェックによる効率化

---

## 2.0 機能要件

### 2.1 執筆前プロット表示機能
**実装箇所**: `FiveStageWritingUseCase` Stage 2「プロット分析・設計」拡張

#### 2.1.1 プロット要点表示
```yaml
# 表示内容例
episode_summary: "第001話：冒険者ギルドでの依頼受注"
key_events:
  - "主人公がギルドに到着"
  - "受付嬢との会話"
  - "初回依頼の選定"
  - "パーティー結成の提案"
required_elements:
  - character_development: "主人公の性格描写"
  - world_building: "ギルドの雰囲気描写"
  - plot_progression: "依頼選定の理由説明"
```

#### 2.1.2 必須要素チェックリスト
```text
📋 第001話 執筆チェックリスト
□ 主人公の性格描写（内向的だが好奇心旺盛）
□ ギルドの雰囲気描写（活気ある冒険者の集い）
□ 受付嬢との自然な会話
□ 依頼選定の論理的理由
□ 今後の展開への伏線設置
```

### 2.2 執筆後プロット検証機能
**実装箇所**: `FiveStageWritingUseCase` Stage 9「品質仕上げ」拡張

#### 2.2.1 プロット要素照合
- **キーイベント照合**: プロット記載イベントの原稿内存在確認
- **キャラクター描写照合**: 設定されたキャラクター要素の描写確認
- **世界観要素照合**: プロット指定の世界観要素の実装確認
- **伏線要素照合**: 設置予定の伏線の適切な配置確認

#### 2.2.2 準拠率計算
```python
adherence_score = (
    (implemented_key_events / total_key_events) * 0.4 +
    (implemented_character_elements / total_character_elements) * 0.3 +
    (implemented_world_elements / total_world_elements) * 0.2 +
    (implemented_foreshadowing / total_foreshadowing) * 0.1
) * 100
```

### 2.3 可視化レポート機能
**実装箇所**: `src/noveler/application/visualizers/plot_adherence_visualizer.py`

#### 2.3.1 準拠状況レポート
```text
📊 第001話 プロット準拠レポート
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 総合準拠率: 87% (推奨: 95%以上)

🎯 要素別準拠状況:
  ✅ キーイベント: 4/4 (100%)
  ⚠️ キャラクター描写: 2/3 (67%)
  ✅ 世界観描写: 3/3 (100%)
  ❌ 伏線設置: 0/2 (0%)

⚠️ 不足要素:
  - 主人公の内向的性格の具体的描写
  - 次話への伏線「謎の依頼人」言及
  - 長期伏線「古代遺跡の噂」設置

💡 改善提案:
  - パーティー結成場面で主人公の躊躇を描写
  - ギルド掲示板に謎の依頼を追加
  - 酒場での冒険者の雑談に遺跡の話を挿入
```

---

## 3.0 技術要件

### 3.1 アーキテクチャ設計（DDD準拠）

#### 3.1.1 ドメイン層
```
src/noveler/domain/
├── entities/
│   └── plot_adherence_result.py          # プロット準拠結果エンティティ
├── services/
│   ├── plot_adherence_analyzer.py        # プロット準拠分析サービス
│   └── plot_element_matcher.py           # プロット要素照合サービス
└── value_objects/
    ├── adherence_score.py                # 準拠率値オブジェクト
    └── plot_element.py                   # プロット要素値オブジェクト
```

#### 3.1.2 アプリケーション層
```
src/noveler/application/
├── use_cases/
│   ├── validate_plot_adherence_use_case.py  # プロット準拠検証ユースケース
│   └── generate_adherence_report_use_case.py # 準拠レポート生成ユースケース
├── validators/
│   └── plot_adherence_validator.py          # プロット準拠バリデーター（新規）
└── visualizers/
    └── plot_adherence_visualizer.py         # プロット準拠可視化（新規）
```

#### 3.1.3 インフラストラクチャ層
```
src/noveler/infrastructure/
├── repositories/
│   └── yaml_plot_adherence_repository.py   # プロット準拠データ永続化
└── adapters/
    └── plot_content_analyzer_adapter.py    # プロット内容分析アダプター
```

### 3.2 既存実装継承・拡張

#### 3.2.1 既存コンポーネント活用
```python
# B20準拠: 既存実装優先使用
from noveler.domain.services.plot_validation_service import PlotValidationService  # 既存
from noveler.domain.value_objects.validation_result import ValidationResult      # 既存
from noveler.infrastructure.services.content_validation_service import ContentValidationService  # 既存

# 共有コンポーネント必須使用
from scripts.presentation.cli.shared_utilities import console, get_logger
from scripts.presentation.cli.shared_utilities import get_common_path_service
```

#### 3.2.2 FiveStageWritingUseCase拡張
```python
# Stage 2 拡張: プロット表示機能追加
async def _execute_plot_analysis_stage(self, context):
    # 既存のプロット分析に追加
    plot_displayer = PlotDisplayService()  # 新規
    plot_displayer.display_episode_checklist(episode_number)

# Stage 9 拡張: プロット検証機能追加
async def _execute_quality_finalization_stage(self, context):
    # 既存の品質チェックに追加
    adherence_validator = PlotAdherenceValidator()  # 新規
    adherence_result = adherence_validator.validate(manuscript, plot_data)
    return adherence_result
```

---

## 4.0 既存実装調査（B20 Phase 1必須）

### 4.1 CODEMAP.yaml確認結果
- `plot_version_use_cases.py`: 原稿状態とプロットバージョン整合性チェック（既存）
- 類似機能は存在するが、執筆時の実時間プロット準拠チェックは未実装

### 4.2 共有コンポーネント確認
- ✅ `PlotValidationService`: プロットファイル構文検証（既存・活用予定）
- ✅ `ValidationResult`: 検証結果値オブジェクト（既存・継承予定）
- ✅ `ContentValidationService`: コンテンツ検証基盤（既存・拡張予定）

### 4.3 再利用可否判定
- **既存活用**: プロットファイル読み込み・基本検証ロジック
- **拡張実装**: 原稿とプロットの照合ロジック・可視化機能
- **新規実装**: 執筆前表示機能・準拠率計算ロジック

---

## 5.0 実装計画

### 5.1 3コミット開発サイクル（B20準拠）

#### Commit 1: 構造コミット
- 仕様書作成（本ファイル）
- ディレクトリ・ファイル構造作成
- インターフェース定義

#### Commit 2: 実装コミット
- プロット準拠バリデーター実装
- 可視化機能実装
- ユニットテスト作成

#### Commit 3: 統合コミット
- FiveStageWritingUseCase統合
- E2Eテスト作成
- ドキュメント更新

### 5.2 テスト戦略
```python
# ユニットテスト
@pytest.mark.spec("SPEC-PLOT-ADHERENCE-001")
def test_plot_adherence_validation():
    """プロット準拠検証のテスト"""

# E2Eテスト
@pytest.mark.e2e
@pytest.mark.spec("SPEC-PLOT-ADHERENCE-001")
def test_full_writing_with_plot_validation():
    """執筆フロー全体でのプロット検証テスト"""
```

### 5.3 品質ゲート
- ✅ F821エラー: 0件（import不足なし）
- ✅ DDD準拠: レイヤー境界遵守
- ✅ B30品質基準: 共有コンポーネント使用・DIパターン適用
- ✅ テストカバレッジ: 90%以上

---

## 6.0 受け入れ基準

### 6.1 機能要件
- [ ] 執筆前にプロット要点とチェックリストが表示される
- [ ] 執筆後にプロット準拠率が算出される（0-100%）
- [ ] 不足要素と改善提案が具体的に表示される
- [ ] 準拠率95%以上の場合は「優秀」評価が表示される

### 6.2 非機能要件
- [ ] プロット読み込み時間: 100ms以下
- [ ] 準拠率計算時間: 500ms以下（3000文字原稿）
- [ ] メモリ使用量: 追加50MB以下

### 6.3 統合要件
- [ ] 既存の執筆フローが影響を受けない
- [ ] エラー時も執筆が継続できる（フォールバック機能）
- [ ] noveler MCPサーバーとの統合が正常動作

---

**仕様策定者**: Claude Code B30開発チーム
**レビュアー**: 未定
**承認者**: 未定
