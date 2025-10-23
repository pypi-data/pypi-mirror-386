# YAMLプロットリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロットエンティティの統合的なYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- マスタープロット・章別プロット・シーンプロットの統合管理
- プロット要素の作成・保存・検索・削除の完全な永続化機能
- プロット間の関連性・依存関係の追跡と整合性保証
- 進捗管理・完成度評価・品質チェック統合機能
- プロット変更履歴の管理とバージョンコントロール

### 1.3 アーキテクチャ位置
```
Domain Layer
├── PlotRepository (Interface) ← Infrastructure Layer
└── Plot (Entity)              └── YamlPlotRepository (Implementation)
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

### 2.2 階層別プロット管理
```python
# マスタープロット操作
def save_master_plot(plot: Plot, project_id: str) -> None
def get_master_plot(project_id: str) -> Plot | None

# 章別プロット操作
def save_chapter_plot(plot: Plot, project_id: str, chapter_number: int) -> None
def get_chapter_plot(project_id: str, chapter_number: int) -> Plot | None
def get_all_chapter_plots(project_id: str) -> list[Plot]

# シーンプロット操作
def save_scene_plot(
    plot: Plot,
    project_id: str,
    chapter_number: int,
    scene_number: int
) -> None
def get_scene_plot(
    project_id: str,
    chapter_number: int,
    scene_number: int
) -> Plot | None
def get_chapter_scenes(project_id: str, chapter_number: int) -> list[Plot]
```

### 2.3 プロット関連性管理
```python
# 関連プロット検索
def find_related_plots(plot_id: str, project_id: str) -> list[Plot]

# 依存関係管理
def add_dependency(
    parent_plot_id: str,
    child_plot_id: str,
    project_id: str
) -> bool

def remove_dependency(
    parent_plot_id: str,
    child_plot_id: str,
    project_id: str
) -> bool

# 整合性チェック
def validate_plot_consistency(project_id: str) -> dict[str, list[str]]
```

### 2.4 プロット検索・フィルタリング
```python
# ステータス検索
def find_by_status(project_id: str, status: str) -> list[Plot]

# タイプ検索
def find_by_type(project_id: str, plot_type: str) -> list[Plot]

# タグ検索
def find_by_tags(project_id: str, tags: list[str]) -> list[Plot]

# 完成度検索
def find_by_completion_rate(
    project_id: str,
    min_rate: float,
    max_rate: float
) -> list[Plot]

# 日付範囲検索
def find_by_date_range(
    project_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[Plot]
```

### 2.5 統計・分析機能
```python
# プロット統計取得
def get_plot_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_plots": 25,
    "master_plots": 1,
    "chapter_plots": 12,
    "scene_plots": 12,
    "completion_rate": 68.5,
    "status_distribution": {
        "DRAFT": 8,
        "IN_PROGRESS": 10,
        "COMPLETED": 7
    },
    "average_quality_score": 82.1
}

# 進捗レポート生成
def generate_progress_report(project_id: str) -> dict[str, Any]

# 品質分析
def analyze_plot_quality(project_id: str) -> dict[str, Any]
```

### 2.6 バージョン管理・履歴機能
```python
# バージョン管理
def create_plot_version(plot_id: str, project_id: str) -> str
def get_plot_versions(plot_id: str, project_id: str) -> list[dict[str, Any]]
def restore_plot_version(
    plot_id: str,
    project_id: str,
    version_id: str
) -> bool

# 変更履歴
def get_change_history(plot_id: str, project_id: str) -> list[dict[str, Any]]
def add_change_log(
    plot_id: str,
    project_id: str,
    change_type: str,
    description: str
) -> None
```

### 2.7 バックアップ・復元機能
```python
# バックアップ作成
def backup_all_plots(project_id: str) -> bool
def backup_plot(plot_id: str, project_id: str) -> bool

# バックアップからの復元
def restore_from_backup(
    project_id: str,
    backup_timestamp: str
) -> bool
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 20_プロット/                  # プロットファイル（YAML）
│   ├── 全体構成.yaml             # マスタープロット
│   ├── 章別プロット/
│   │   ├── 第1章.yaml
│   │   ├── 第2章.yaml
│   │   └── ...
│   └── リソース配分.yaml         # プロット管理メタデータ
├── 50_管理資料/                  # 管理データ
│   └── プロット管理.yaml         # プロット統合管理ファイル
└── backup/                       # バックアップ（任意）
    └── plots_20250721_143022/
        ├── 全体構成.yaml
        └── 章別プロット/
```

### 3.2 プロット管理YAML構造
```yaml
# 50_管理資料/プロット管理.yaml
project_info:
  project_id: "project-001"
  project_name: "転生したら最強の魔法使いだった件"
  created_at: "2025-07-15T10:00:00"
  updated_at: "2025-07-21T14:30:22"

master_plot:
  id: "master-001"
  title: "全体構成"
  status: "IN_PROGRESS"
  completion_rate: 75.0
  quality_score: 88.5
  created_at: "2025-07-15T10:00:00"
  updated_at: "2025-07-21T12:00:00"
  version: 3

chapter_plots:
  - id: "chapter-001"
    chapter_number: 1
    title: "異世界転生編"
    status: "COMPLETED"
    completion_rate: 100.0
    quality_score: 92.0
    scenes_count: 5
    dependencies: []
    created_at: "2025-07-15T11:00:00"
    updated_at: "2025-07-20T15:30:00"
    version: 2
  - id: "chapter-002"
    chapter_number: 2
    title: "魔法学校編"
    status: "IN_PROGRESS"
    completion_rate: 60.0
    quality_score: 85.5
    scenes_count: 3
    dependencies: ["chapter-001"]
    created_at: "2025-07-16T09:00:00"
    updated_at: "2025-07-21T14:30:22"
    version: 1

scene_plots:
  - id: "scene-001-001"
    chapter_number: 1
    scene_number: 1
    title: "転生の瞬間"
    status: "COMPLETED"
    completion_rate: 100.0
    quality_score: 95.0
    dependencies: []
    created_at: "2025-07-15T13:00:00"
    updated_at: "2025-07-18T16:00:00"
    version: 1

statistics:
  total_plots: 15
  completion_rate: 68.5
  average_quality: 87.2
  last_calculated: "2025-07-21T14:30:22"

updated_at: "2025-07-21T14:30:22"
```

### 3.3 個別プロットファイル構造例
```yaml
# 20_プロット/章別プロット/第1章.yaml
metadata:
  id: "chapter-001"
  title: "異世界転生編"
  chapter_number: 1
  type: "CHAPTER_PLOT"
  status: "COMPLETED"
  version: 2
  created_at: "2025-07-15T11:00:00"
  updated_at: "2025-07-20T15:30:00"

plot_content:
  overview: "主人公が異世界に転生し、魔法の才能に気づく章"
  objectives:
    - "主人公の転生設定の説明"
    - "魔法世界の基本設定紹介"
    - "主人公の特別な能力の発覚"

  scenes:
    - scene_number: 1
      title: "転生の瞬間"
      summary: "現代日本で事故に遭い、異世界に転生"
      key_events:
        - "交通事故による死亡"
        - "神様との邂逅"
        - "転生の儀式"
      character_development: "主人公の前世の記憶保持"

  themes:
    - "第二の人生への希望"
    - "新しい世界への適応"

  foreshadowing:
    - target: "第3章"
      content: "魔法学校での才能開花の伏線"
    - target: "第10章"
      content: "最終決戦に繋がる特殊能力の暗示"

dependencies:
  required_plots: []
  dependent_plots: ["chapter-002", "chapter-003"]

quality:
  completion_rate: 100.0
  quality_score: 92.0
  last_reviewed: "2025-07-20T15:30:00"

change_history:
  - version: 1
    timestamp: "2025-07-15T11:00:00"
    type: "CREATE"
    description: "初期プロット作成"
  - version: 2
    timestamp: "2025-07-20T15:30:00"
    type: "UPDATE"
    description: "伏線設定の追加と詳細化"
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ドメイン層
from domain.entities.plot import Plot, PlotType, PlotStatus
from domain.repositories.plot_repository import PlotRepository
from domain.value_objects.plot_id import PlotId
from domain.value_objects.plot_title import PlotTitle
from domain.value_objects.completion_rate import CompletionRate
from domain.value_objects.quality_score import QualityScore
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class PlotRepositoryError(Exception):
    pass

class PlotNotFoundError(PlotRepositoryError):
    pass

class PlotDependencyError(PlotRepositoryError):
    pass

class PlotConsistencyError(PlotRepositoryError):
    pass

class InvalidPlotDataError(PlotRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一プロット検索: 30ms以内
- 全プロット読み込み: 300ms以内（50プロット）
- プロット保存操作: 80ms以内
- 関連性チェック: 100ms以内

### 5.2 メモリ使用量
- 単一プロット: 5MB以内
- 全プロット同時読み込み: 500MB以内
- 統計計算時: 100MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: プロジェクト単位でロック
- 整合性チェック: 排他的実行

## 6. 品質保証

### 6.1 データ整合性
- プロットID の一意性保証
- 依存関係の循環参照検出・防止
- 章番号・シーン番号の連続性チェック
- YAMLフォーマットの妥当性検証

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 欠損したプロットファイルの検出・通知
- 依存関係の不整合自動修正
- バックアップからの自動復元オプション

### 6.3 バージョン管理
- プロットバージョンの自動インクリメント
- 変更履歴の詳細記録
- 更新日時の自動記録
- 重要な変更のスナップショット作成

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離
- 機密プロット情報の保護

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 特殊文字・制御文字のエスケープ処理
- パス インジェクション攻撃の防止
- YAMLインジェクション攻撃の防止

## 8. 互換性

### 8.1 レガシーシステム
- 既存のプロットファイル形式との完全互換
- 段階的移行サポート
- 既存データの自動変換・インポート機能

### 8.2 将来拡張性
- 新しいプロットタイプの追加対応
- 異なるファイル形式への拡張（JSON, XML等）
- 分散ストレージへの移行準備
- AI生成プロットの統合準備

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlPlotRepository(project_path)

# マスタープロット作成・保存
master_plot = Plot(
    id=PlotId("master-001"),
    title=PlotTitle("全体構成"),
    plot_type=PlotType.MASTER,
    content="物語全体の構成..."
)
repo.save_master_plot(master_plot, "project-001")

# 章別プロット作成・保存
chapter_plot = Plot(
    id=PlotId("chapter-001"),
    title=PlotTitle("異世界転生編"),
    plot_type=PlotType.CHAPTER,
    chapter_number=1,
    content="第1章の詳細プロット..."
)
repo.save_chapter_plot(chapter_plot, "project-001", 1)

# プロット検索
found_plot = repo.get_chapter_plot("project-001", 1)
all_plots = repo.find_all("project-001")
```

### 9.2 関連性管理の使用例
```python
# 依存関係設定
repo.add_dependency("chapter-001", "chapter-002", "project-001")

# 関連プロット検索
related = repo.find_related_plots("chapter-001", "project-001")

# 整合性チェック
consistency_report = repo.validate_plot_consistency("project-001")
if consistency_report:
    print("整合性エラー:", consistency_report)
```

### 9.3 統計・分析の使用例
```python
# プロット統計取得
stats = repo.get_plot_statistics("project-001")
print(f"総プロット数: {stats['total_plots']}")
print(f"完成度: {stats['completion_rate']:.1f}%")

# 進捗レポート生成
progress = repo.generate_progress_report("project-001")
print(f"章別進捗: {progress['chapter_progress']}")

# 完成したプロット検索
completed = repo.find_by_status("project-001", "COMPLETED")
```

### 9.4 バックアップ・復元例
```python
# 全プロットバックアップ
backup_success = repo.backup_all_plots("project-001")

# バージョン作成
version_id = repo.create_plot_version("chapter-001", "project-001")

# 復元実行
restored = repo.restore_plot_version(
    "chapter-001", "project-001", version_id
)
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- プロット階層管理の正確性テスト
- 依存関係管理機能のテスト
- エラーケースの処理確認
- 境界値・異常値テスト

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- プロット間の関連性保持テスト
- 大量プロットでの性能テスト
- 同時実行・排他制御テスト

### 10.3 エラーシナリオ
- ディスク容量不足時の動作
- ファイル権限エラーの処理
- 破損したYAMLファイルの復旧
- 依存関係循環の検出・解決
- ネットワークドライブでの動作確認

## 11. 運用・監視

### 11.1 ログ出力
- 重要な操作（保存、削除、依存関係変更）のログ記録
- エラー発生時の詳細ログ出力
- パフォーマンス測定・統計ログ
- 整合性チェック結果のログ

### 11.2 メトリクス
- 操作回数・実行時間の統計収集
- エラー発生率の監視
- プロット品質スコアの傾向分析
- ディスク使用量・ファイル数の監視

### 11.3 アラート
- データ整合性エラーの即座通知
- パフォーマンス劣化の検出
- ディスク容量警告
- 重要な依存関係破綻の通知

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_plot_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_plot_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- プロットエンティティの完全な復元
- 階層構造の整合性保証
- エラー時のグレースフルデグラデーション
- 将来の拡張性を考慮した設計

### 12.3 今後の改善点
- [ ] 非同期I/O対応による性能向上
- [ ] 分散ファイルシステム対応
- [ ] リアルタイムプロット同期機能
- [ ] AI自動プロット生成統合
- [ ] プロット可視化機能統合
- [ ] 自動品質評価システム統合
- [ ] プロット共有・コラボレーション機能
