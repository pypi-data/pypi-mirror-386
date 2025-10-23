# プロットデータYAMLリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロットエンティティのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- マスタープロット・章別プロット・シーンプロットの作成・保存・検索・削除機能
- プロット階層構造の管理（全体→章→シーン）
- プロット要素間の関連性・依存関係の追跡
- 進捗管理・完成度評価・品質チェック機能

### 1.3 アーキテクチャ位置
```
Domain Layer
├── PlotRepository (Interface) ← Infrastructure Layer
└── Plot (Entity)              └── YamlPlotDataRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(plot: Plot, project_id: str) -> None

# 検索
def find_by_id(plot_id: str, project_id: str) -> Plot | None
def find_by_title(project_id: str, title: str) -> Plot | None
def find_all(project_id: str) -> list[Plot]

# 存在確認
def exists(project_id: str, plot_id: str) -> bool

# 削除
def delete(plot_id: str, project_id: str) -> bool
```

### 2.2 階層別検索機能
```python
# マスタープロット検索
def find_master_plot(project_id: str) -> Plot | None

# 章別プロット検索
def find_chapter_plots(project_id: str) -> list[Plot]
def find_plot_by_chapter(project_id: str, chapter_number: int) -> Plot | None

# シーンプロット検索
def find_scene_plots(project_id: str, chapter_number: int) -> list[Plot]
def find_plot_by_scene(project_id: str, chapter: int, scene: int) -> Plot | None

# 階層構造検索
def find_plot_hierarchy(project_id: str) -> dict[str, Any]
```

### 2.3 高度な検索機能
```python
# ステータス検索
def find_by_status(project_id: str, status: str) -> list[Plot]

# タイプ別検索
def find_by_type(project_id: str, plot_type: str) -> list[Plot]

# 完成度範囲検索
def find_by_completion_range(
    project_id: str,
    min_completion: float,
    max_completion: float
) -> list[Plot]

# キャラクター関連検索
def find_by_character(project_id: str, character_name: str) -> list[Plot]

# 重要度検索
def find_by_importance(project_id: str, importance_level: str) -> list[Plot]

# 未完成プロット検索
def find_incomplete_plots(project_id: str) -> list[Plot]

# 依存関係検索
def find_dependent_plots(project_id: str, plot_id: str) -> list[Plot]
```

### 2.4 統計・分析機能
```python
# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_plots": 45,
    "master_plots": 1,
    "chapter_plots": 12,
    "scene_plots": 32,
    "completion_rates": {
        "master": 95.5,
        "chapter_average": 78.3,
        "scene_average": 65.8
    },
    "status_distribution": {
        "完成": 15,
        "進行中": 20,
        "計画中": 10
    },
    "total_estimated_episodes": 120
}

# プロット完成度分析
def analyze_plot_completion(project_id: str) -> dict[str, float]

# プロット密度分析（章あたりのプロット要素数）
def analyze_plot_density(project_id: str) -> dict[int, int]

# プロット整合性チェック
def check_plot_consistency(project_id: str) -> list[str]
```

### 2.5 関係性管理機能
```python
# プロット依存関係設定
def set_plot_dependency(
    project_id: str,
    dependent_plot_id: str,
    prerequisite_plot_id: str
) -> bool

# プロット関連性更新
def update_plot_relations(
    project_id: str,
    plot_id: str,
    related_plot_ids: list[str]
) -> bool

# 階層構造更新
def update_plot_hierarchy(
    project_id: str,
    plot_id: str,
    parent_id: str | None,
    children_ids: list[str]
) -> bool
```

### 2.6 一括操作
```python
# 一括ステータス更新
def bulk_update_status(
    project_id: str,
    plot_ids: list[str],
    new_status: str
) -> int

# 章単位プロット作成
def create_chapter_plot_structure(
    project_id: str,
    chapter_count: int
) -> list[str]
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 20_プロット/
│   ├── 全体構成.yaml              # マスタープロット
│   ├── 章別プロット/
│   │   ├── 第1章.yaml
│   │   ├── 第2章.yaml
│   │   └── ...
│   ├── シーンプロット/
│   │   ├── 第1章_シーン1.yaml
│   │   ├── 第1章_シーン2.yaml
│   │   └── ...
│   └── リソース配分.yaml          # プロット管理メタデータ
└── backup/
    └── 20250721_143022/
        └── プロット_backup.yaml
```

### 3.2 マスタープロット（全体構成.yaml）
```yaml
plot_info:
  id: "master_plot_001"
  title: "転生魔法使い物語　全体構成"
  type: "master"
  version: 3
  status: "進行中"
  completion_percentage: 85.0
  created_at: "2025-07-10T14:20:00"
  updated_at: "2025-07-21T14:30:22"

story_structure:
  total_chapters: 12
  estimated_episodes: 120
  target_word_count: 360000

  acts:
    - name: "第一幕：転生と発見"
      chapters: [1, 2, 3, 4]
      description: "主人公の転生から魔法の才能発見まで"
      key_events:
        - "異世界転生"
        - "魔法の才能発覚"
        - "冒険者登録"
        - "最初の仲間との出会い"

    - name: "第二幕：成長と試練"
      chapters: [5, 6, 7, 8]
      description: "実力向上と大きな試練への挑戦"
      key_events:
        - "魔法学校入学"
        - "ライバル登場"
        - "大規模魔獣討伐"
        - "仲間との絆深化"

    - name: "第三幕：真実と決戦"
      chapters: [9, 10, 11, 12]
      description: "世界の真実発覚と最終決戦"
      key_events:
        - "世界の秘密発覚"
        - "真の敵との対峙"
        - "最終決戦"
        - "新世界の構築"

main_characters:
  - name: "主人公（タカシ）"
    role: "protagonist"
    character_arc: "弱者→最強魔法使い→世界の救世主"

  - name: "エリア"
    role: "heroine"
    character_arc: "高慢な貴族→真の仲間→恋人"

central_themes:
  - "成長と自己実現"
  - "友情と信頼"
  - "責任と選択"

plot_threads:
  - id: "thread_001"
    name: "主人公の成長"
    type: "character_development"
    priority: "高"
    chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

  - id: "thread_002"
    name: "世界の謎"
    type: "mystery"
    priority: "高"
    chapters: [1, 3, 6, 9, 10, 11, 12]

dependencies:
  prerequisites: []
  dependents: ["chapter_plot_001", "chapter_plot_002"]

quality_metrics:
  consistency_score: 88.5
  character_development_depth: 92.0
  plot_tension_curve: 85.5
  pacing_balance: 78.0
```

### 3.3 章別プロット（第1章.yaml）
```yaml
plot_info:
  id: "chapter_plot_001"
  title: "第1章：異世界への扉"
  type: "chapter"
  chapter_number: 1
  version: 2
  status: "完成"
  completion_percentage: 100.0
  created_at: "2025-07-12T10:15:00"
  updated_at: "2025-07-20T16:45:00"

chapter_structure:
  target_episodes: 10
  estimated_word_count: 30000
  theme: "新世界での始まり"

  scenes:
    - scene_number: 1
      title: "突然の事故"
      type: "inciting_incident"
      location: "現代日本・交差点"
      characters: ["主人公"]
      description: "トラックに轢かれて死亡"
      purpose: "転生のきっかけ"
      tension_level: 8

    - scene_number: 2
      title: "異世界への目覚め"
      type: "exposition"
      location: "異世界・村の外れ"
      characters: ["主人公", "村人A"]
      description: "赤ん坊として転生、徐々に状況理解"
      purpose: "世界設定の導入"
      tension_level: 3

    - scene_number: 3
      title: "魔法の発見"
      type: "plot_point"
      location: "村・自宅"
      characters: ["主人公", "養父母"]
      description: "偶然魔法を使ってしまう"
      purpose: "能力の発覚"
      tension_level: 6

plot_points:
  opening: "平凡なサラリーマンの日常"
  inciting_incident: "交通事故死"
  first_plot_point: "異世界転生の自覚"
  midpoint: "魔法能力の発覚"
  climax: "村人への能力の露見"
  resolution: "新生活への決意"

character_development:
  - character: "主人公"
    arc_start: "混乱した転生者"
    arc_end: "状況を受け入れた新住民"
    key_moments:
      - "死の受容"
      - "新世界の理解"
      - "魔法への驚愕"

foreshadowing:
  - element: "村長の意味深な視線"
    setup_scene: 2
    purpose: "主人公の出生の秘密"

  - element: "古い魔導書の発見"
    setup_scene: 3
    purpose: "後の魔法修行への伏線"

dependencies:
  prerequisites: ["master_plot_001"]
  dependents: ["chapter_plot_002"]
  related_chapters: []

quality_metrics:
  scene_flow_score: 91.5
  character_consistency: 88.0
  dialogue_quality: 85.5
  description_balance: 89.0
```

### 3.4 リソース配分メタデータ
```yaml
resource_allocation:
  total_chapters: 12
  total_scenes: 120
  total_episodes: 120

  chapter_distribution:
    - chapter: 1
      scenes: 10
      episodes: 10
      word_count_target: 30000
      completion_status: "完成"

    - chapter: 2
      scenes: 12
      episodes: 12
      word_count_target: 36000
      completion_status: "進行中"

plot_management:
  active_threads: 15
  resolved_threads: 8
  pending_threads: 7

writing_schedule:
  start_date: "2025-07-01"
  target_completion: "2025-12-31"
  current_progress: 25.5

metadata:
  last_updated: "2025-07-21T14:30:22"
  revision: 8
  backup_count: 5
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

# ドメイン層
from domain.entities.plot import Plot, PlotStatus, PlotType
from domain.repositories.plot_repository import PlotRepository
from domain.value_objects.plot_id import PlotId
from domain.value_objects.chapter_number import ChapterNumber
from domain.value_objects.completion_percentage import CompletionPercentage
from domain.value_objects.word_count import WordCount
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class PlotRepositoryError(Exception):
    pass

class PlotNotFoundError(PlotRepositoryError):
    pass

class InvalidPlotDataError(PlotRepositoryError):
    pass

class PlotHierarchyError(PlotRepositoryError):
    pass

class PlotConsistencyError(PlotRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一プロット検索: 40ms以内
- 階層構造読み込み: 150ms以内
- 全プロット読み込み: 300ms以内（50プロット）
- 保存操作: 80ms以内
- 整合性チェック: 1000ms以内

### 5.2 メモリ使用量
- 単一プロット: 50KB以内
- 全プロット同時読み込み: 200MB以内
- 階層構造キャッシュ: 100MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御

## 6. 品質保証

### 6.1 データ整合性
- プロットID の一意性保証
- 階層構造の循環参照チェック
- 依存関係の妥当性検証
- YAMLフォーマットの妥当性検証

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 不整合な階層構造の修正
- 欠損した依存関係の検出・補完

### 6.3 バージョン管理
- プロットデータのバージョン管理
- 変更履歴の自動記録
- 階層構造変更の追跡

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 特殊文字のエスケープ処理
- パス インジェクション攻撃の防止

## 8. 互換性

### 8.1 レガシーシステム
- 既存のプロットファイルとの互換性
- 段階的移行サポート
- 手動作成プロットの自動変換

### 8.2 将来拡張性
- 新しいプロット要素の追加対応
- AIによるプロット分析機能との連携
- グラフィカルプロット編集ツールとの統合

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlPlotDataRepository(project_path)

# マスタープロット作成・保存
master_plot = Plot(
    id=PlotId("master_plot_001"),
    title="転生魔法使い物語　全体構成",
    type=PlotType.MASTER,
    total_chapters=12,
    estimated_episodes=120
)
repo.save(master_plot, "project-001")

# プロット検索
master = repo.find_master_plot("project-001")
all_plots = repo.find_all("project-001")

# 統計取得
stats = repo.get_statistics("project-001")
print(f"総プロット数: {stats['total_plots']}")
```

### 9.2 階層構造操作例
```python
# 章別プロット検索
chapter_plots = repo.find_chapter_plots("project-001")
chapter_1 = repo.find_plot_by_chapter("project-001", 1)

# 階層構造取得
hierarchy = repo.find_plot_hierarchy("project-001")

# 依存関係設定
repo.set_plot_dependency(
    "project-001",
    "chapter_plot_002",
    "chapter_plot_001"
)
```

### 9.3 分析機能例
```python
# 完成度分析
completion = repo.analyze_plot_completion("project-001")

# 整合性チェック
issues = repo.check_plot_consistency("project-001")
if issues:
    print("整合性の問題:", issues)

# プロット密度分析
density = repo.analyze_plot_density("project-001")
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- 階層構造管理のテスト
- 依存関係処理のテスト
- 統計計算の正確性テスト

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- エピソードリポジトリとの連携テスト
- 大量プロットでの性能テスト

### 10.3 エラーシナリオ
- YAMLファイル破損
- 循環依存の発生
- 階層構造の不整合
- ディスク容量不足

## 11. 運用・監視

### 11.1 ログ出力
- プロット作成・更新のログ記録
- 階層構造変更のログ
- 依存関係変更のログ
- エラー発生時の詳細ログ

### 11.2 メトリクス
- プロット完成度の推移
- 操作頻度の統計
- パフォーマンス測定
- 整合性チェック結果

### 11.3 アラート
- 長期未完成プロットの警告
- 階層構造の不整合
- 依存関係の循環参照
- ファイルアクセスエラー

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_plot_data_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_plot_data_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- プロットエンティティの完全な復元
- 階層構造の効率的管理
- 将来の拡張性を考慮した設計

### 12.3 今後の改善点
- [ ] AI によるプロット分析・提案機能
- [ ] グラフィカルプロット構造表示
- [ ] 自動プロット整合性チェック
- [ ] プロット品質評価システム
- [ ] テンプレートベースプロット生成
