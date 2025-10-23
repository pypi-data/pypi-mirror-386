# SPEC-PLOT-MANUSCRIPT-001: プロット・原稿変換統合システム

**作成日**: 2025-09-11
**最終更新**: 2025-09-11
**状態**: Active
**優先度**: Critical
**実装者**: Claude Code（B20準拠）

## 1.0 概要

プロット（EP001.yaml）と原稿（第001話.md）の不一致問題を解決し、プロットの全シーンが原稿に反映される統合システムを実装する。

### 1.1 問題状況
- **現状**: EP001.yamlに9シーン定義されているが、原稿には5シーンのみ
- **欠落**: 「あすか」キャラクターとの出会い・協力シーン（シーン4-9）
- **根本原因**: ManuscriptGeneratorServiceが原稿テンプレート作成のみで、プロット内容変換未実装

### 1.2 目標
- EP001.yamlの全9シーンを原稿に完全反映
- 「あすか」との出会いと協力関係を正しく描写
- DEBUGログ覚醒から危機解決までの完全なストーリー実現

## 2.0 アーキテクチャ設計（B20準拠）

### 2.1 DDD準拠レイヤー構造
```
Domain Layer (ドメイン層)
├── services/writing_steps/
│   ├── plot_analyzer_service.py (改修)
│   └── manuscript_generator_service.py (改修)
└── value_objects/
    └── scene_data.py (新規)

Application Layer (アプリケーション層)
└── use_cases/
    └── integrated_writing_use_case.py (改修)

Infrastructure Layer (インフラ層)
└── adapters/
    └── yaml_plot_parser.py (新規)
```

### 2.2 依存性注入（B20必須）
```python
# B20準拠：共有コンポーネント使用
from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger

class PlotAnalyzerService:
    def __init__(self):
        self.console = ConsoleServiceAdapter()  # 統一Console
        self.path_service = create_path_service()  # 統一PathService
        self.logger = get_logger(__name__)  # 統一Logger
```

## 3.0 機能要件

### 3.1 既存実装活用（Phase 1必須チェック完了）

#### 3.1.1 PlotAnalyzerService（既存・改修）
**既存機能**:
- プロットファイル検索・読み込み
- 基本プロット要素抽出（conflicts, events, characters）

**追加機能**:
- シーン構造抽出（scenes配列のパース）
- キャラクター登場管理
- シーン間関係性解析

#### 3.1.2 ManuscriptGeneratorService（既存・改修）
**既存機能**:
- 原稿テンプレート作成
- ファイルパス生成
- 基本メタデータ処理

**追加機能**:
- プロット解析結果からの原稿生成
- シーン別コンテンツ変換
- キャラクター描写統合

#### 3.1.3 IntegratedWritingUseCase（既存・改修）
**既存機能**:
- 基本ワークフロー管理
- Phase制御

**追加機能**:
- PlotAnalyzerService統合
- プロット→原稿変換プロセス

### 3.2 新規実装要件

#### 3.2.1 SceneData Value Object
```python
@dataclass
class SceneData:
    scene_number: int
    title: str
    description: str
    characters: list[str]
    events: list[str]
    location: str | None = None
    time_setting: str | None = None
```

#### 3.2.2 YamlPlotParser Adapter
```python
class YamlPlotParser:
    """YAML形式プロット解析専用アダプター"""

    def parse_scenes(self, yaml_content: dict) -> list[SceneData]:
        """シーン配列を構造化データに変換"""

    def extract_characters(self, yaml_content: dict) -> dict[str, dict]:
        """キャラクター情報抽出"""
```

## 4.0 既存実装調査（B20必須）

### 4.1 CODEMAP.yaml確認結果
✅ **PlotAnalyzerService**: `src/noveler/domain/services/writing_steps/plot_analyzer_service.py` 存在確認
✅ **ManuscriptGeneratorService**: `src/noveler/domain/services/writing_steps/manuscript_generator_service.py` 存在確認
✅ **IntegratedWritingUseCase**: `src/noveler/application/use_cases/integrated_writing_use_case.py` 存在確認

### 4.2 共有コンポーネント確認
✅ **ConsoleService**: `noveler.infrastructure.adapters.console_service_adapter`
✅ **PathService**: `noveler.infrastructure.factories.path_service_factory`
✅ **UnifiedLogger**: `noveler.infrastructure.logging.unified_logger`

### 4.3 再利用判定
- **PlotAnalyzerService**: 基盤は再利用、シーン解析機能を追加
- **ManuscriptGeneratorService**: 基盤は再利用、内容生成機能を追加
- **既存価値オブジェクト**: PlotElement等を活用

## 5.0 実装方針（TDD準拠）

### 5.1 Phase 1: テスト作成
```python
# tests/test_plot_manuscript_integration.py
@pytest.mark.spec("SPEC-PLOT-MANUSCRIPT-001")
class TestPlotManuscriptIntegration:
    def test_episode001_scene_count_matching(self):
        """EP001.yamlの9シーンが原稿に反映されることを確認"""

    def test_asuka_character_appearance(self):
        """あすかキャラクターの登場を確認"""

    def test_debug_log_awakening_scene(self):
        """DEBUGログ覚醒シーンの生成を確認"""
```

### 5.2 Phase 2: 実装（共有コンポーネント優先）
```python
# PlotAnalyzerServiceの改修例
async def extract_scenes(self, yaml_content: dict) -> list[SceneData]:
    """シーン配列抽出（新規メソッド）"""
    scenes_data = yaml_content.get("scenes", [])
    return [SceneData(**scene) for scene in scenes_data]
```

### 5.3 Phase 3: 統合テスト
```python
# tests/e2e/test_episode001_complete_generation.py
@pytest.mark.spec("SPEC-PLOT-MANUSCRIPT-001")
def test_complete_episode001_generation():
    """EP001の完全生成E2Eテスト"""
    # Given: EP001.yaml
    # When: novel write 1実行
    # Then: 9シーン全て含む第001話.md生成
```

## 6.0 期待される成果物

### 6.1 ファイル生成・修正予定
```
改修ファイル:
- src/noveler/domain/services/writing_steps/plot_analyzer_service.py
- src/noveler/domain/services/writing_steps/manuscript_generator_service.py
- src/noveler/application/use_cases/integrated_writing_use_case.py

新規ファイル:
- src/noveler/domain/value_objects/scene_data.py
- src/noveler/infrastructure/adapters/yaml_plot_parser.py
- tests/test_plot_manuscript_integration.py
- tests/e2e/test_episode001_complete_generation.py
```

### 6.2 動作検証項目
- [ ] EP001.yamlから9シーン全抽出
- [ ] 第001話.mdに9シーン全生成
- [ ] 「あすか」キャラクター正常登場
- [ ] DEBUGログ覚醒シーン描写
- [ ] 危機解決シーン完成
- [ ] B20準拠実装（共有コンポーネント使用）

## 7.0 リスク管理

### 7.1 技術リスク
- **既存テスト破損**: 段階的修正で最小化
- **性能劣化**: PlotAnalyzer処理時間監視
- **メモリ使用量**: 大規模プロットファイル対応

### 7.2 品質保証
- **B20準拠チェック**: `python tools/check_tdd_ddd_compliance.py`
- **重複実装検出**: `python scripts/tools/duplicate_implementation_detector.py`
- **統合テスト**: pytest実行によるE2E検証

## 8.0 実装スケジュール

### 8.1 3コミットサイクル
```bash
# Commit 1: 仕様・テスト
git commit -m "feat: プロット・原稿変換機能の仕様とテスト追加"

# Commit 2: 実装
git commit -m "feat: PlotAnalyzer改修とManuscriptGenerator強化"

# Commit 3: 統合
git commit -m "feat: プロット・原稿変換統合とE2Eテスト完了"
```

### 8.2 品質ゲート
各コミット前に以下を実行:
- [ ] TDDサイクル完了確認
- [ ] B20準拠性チェック
- [ ] 既存テスト全通過
- [ ] 新機能テスト全通過

---

**承認**: 本仕様書は既存実装を最大限活用し、B20_Claude_Code開発作業指示書.mdに完全準拠した設計となっています。
