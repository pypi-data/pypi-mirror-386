# YAMLプロジェクトリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロジェクトエンティティ全体のYAMLファイルベース永続化を提供する統合リポジトリ。

### 1.2 スコープ
- プロジェクト全体（エピソード・プロット・設定・統計）の統合管理
- プロジェクト作成・削除・コピー・移行の完全な永続化機能
- プロジェクト間の関連性管理と整合性保証
- プロジェクトアーカイブ・復元・バックアップ機能
- 複数プロジェクト間でのリソース共有管理
- プロジェクトテンプレート・雛形管理

### 1.3 アーキテクチャ位置
```
Domain Layer
├── ProjectRepository (Interface) ← Infrastructure Layer
└── Project (Entity)              └── YamlProjectRepository (Implementation)
    ├── Episode[]                     ├── YamlEpisodeRepository
    ├── Plot[]                        ├── YamlPlotRepository
    ├── ProjectInfo                   └── YamlProjectInfoRepository
    └── Settings
```

## 2. 機能仕様

### 2.1 プロジェクト基本CRUD操作
```python
# 作成・保存
def create_project(project: Project) -> None
def save(project: Project) -> None

# 検索・取得
def find_by_id(project_id: str) -> Project | None
def find_by_name(name: str) -> Project | None
def find_all() -> list[Project]
def get_project_summary(project_id: str) -> ProjectSummary | None

# 存在確認
def exists(project_id: str) -> bool
def exists_by_name(name: str) -> bool

# 削除
def delete(project_id: str) -> bool
def archive_project(project_id: str) -> bool
```

### 2.2 プロジェクト構造管理
```python
# プロジェクト構造初期化
def initialize_project_structure(
    project_id: str,
    template_name: str = "default"
) -> bool

# ディレクトリ構造検証
def validate_project_structure(project_id: str) -> dict[str, list[str]]

# 構造修復
def repair_project_structure(project_id: str) -> bool

# 構造情報取得
def get_project_structure_info(project_id: str) -> dict[str, Any]
```

### 2.3 プロジェクトテンプレート管理
```python
# テンプレート作成
def create_template_from_project(
    project_id: str,
    template_name: str,
    template_description: str
) -> bool

# テンプレート適用
def apply_template(
    project_id: str,
    template_name: str
) -> bool

# テンプレート一覧取得
def get_available_templates() -> list[dict[str, Any]]

# テンプレート削除
def delete_template(template_name: str) -> bool
```

### 2.4 プロジェクト複製・移行
```python
# プロジェクト複製
def clone_project(
    source_project_id: str,
    new_project_id: str,
    new_project_name: str,
    clone_options: dict[str, bool] = None
) -> bool

# プロジェクト移行
def migrate_project(
    project_id: str,
    migration_type: str,
    migration_options: dict[str, Any]
) -> bool

# プロジェクトマージ
def merge_projects(
    main_project_id: str,
    merge_project_id: str,
    merge_strategy: str
) -> bool
```

### 2.5 プロジェクト検索・フィルタリング
```python
# 高度な検索
def search_projects(
    query: str,
    filters: dict[str, Any] = None
) -> list[Project]

# ステータス検索
def find_by_status(status: str) -> list[Project]

# ジャンル検索
def find_by_genre(genre: str) -> list[Project]

# 作成日範囲検索
def find_by_creation_date_range(
    start_date: datetime,
    end_date: datetime
) -> list[Project]

# アクティブプロジェクト取得
def get_active_projects() -> list[Project]

# 最近更新されたプロジェクト取得
def get_recently_updated_projects(days: int = 7) -> list[Project]
```

### 2.6 プロジェクト統計・分析
```python
# プロジェクト統計取得
def get_project_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "project_info": {...},
    "episodes": {
        "total": 15,
        "completed": 12,
        "total_words": 45230,
        "average_quality": 87.3
    },
    "plots": {
        "master_plots": 1,
        "chapter_plots": 8,
        "scene_plots": 24,
        "completion_rate": 75.0
    },
    "progress": {
        "overall_completion": 68.5,
        "daily_progress": {...},
        "quality_trend": {...}
    }
}

# 全プロジェクト統計
def get_global_statistics() -> dict[str, Any]

# プロジェクト比較分析
def compare_projects(project_ids: list[str]) -> dict[str, Any]

# プロジェクト進捗レポート
def generate_progress_report(
    project_id: str,
    report_type: str = "comprehensive"
) -> dict[str, Any]
```

### 2.7 プロジェクトバックアップ・復元
```python
# フルバックアップ作成
def create_full_backup(project_id: str) -> str

# 差分バックアップ作成
def create_incremental_backup(project_id: str) -> str

# バックアップ一覧取得
def list_backups(project_id: str) -> list[dict[str, Any]]

# プロジェクト復元
def restore_from_backup(
    project_id: str,
    backup_id: str,
    restore_options: dict[str, bool] = None
) -> bool

# バックアップ削除
def delete_backup(project_id: str, backup_id: str) -> bool
```

### 2.8 プロジェクト関連性・依存関係
```python
# プロジェクト関連性管理
def add_project_relation(
    project_id: str,
    related_project_id: str,
    relation_type: str
) -> None

def remove_project_relation(
    project_id: str,
    related_project_id: str
) -> None

def get_related_projects(project_id: str) -> list[dict[str, str]]

# 依存関係管理
def add_project_dependency(
    project_id: str,
    dependency_project_id: str,
    dependency_type: str
) -> None

def check_dependency_conflicts(project_id: str) -> list[dict[str, str]]

# シリーズ・世界観管理
def add_to_universe(project_id: str, universe_name: str) -> None
def get_universe_projects(universe_name: str) -> list[Project]
```

### 2.9 プロジェクト統合管理
```python
# 整合性チェック
def validate_project_integrity(project_id: str) -> dict[str, list[str]]

# プロジェクト最適化
def optimize_project(
    project_id: str,
    optimization_options: dict[str, bool] = None
) -> dict[str, Any]

# リソース使用量分析
def analyze_resource_usage(project_id: str) -> dict[str, Any]

# プロジェクト健全性チェック
def check_project_health(project_id: str) -> dict[str, Any]
```

## 3. データ構造仕様

### 3.1 プロジェクト全体ファイル配置
```
プロジェクトルート/
├── プロジェクト設定.yaml         # プロジェクト基本設定
├── 📁 10_企画/                  # 企画・設定ファイル
│   ├── 企画書.yaml
│   ├── 読者分析.yaml
│   └── 市場調査.yaml
├── 📁 20_プロット/              # プロット管理
│   ├── 全体構成.yaml
│   ├── 章別プロット/
│   └── リソース配分.yaml
├── 📁 30_設定集/                # 世界観・キャラ設定
│   ├── 世界観.yaml
│   ├── キャラクター.yaml
│   └── 用語集.yaml
├── 📁 40_原稿/                  # 原稿ファイル
│   ├── 第001話_タイトル.md
│   └── ...
├── 📁 50_管理資料/              # 管理・統計データ
│   ├── 話数管理.yaml
│   ├── プロット管理.yaml
│   ├── プロジェクト詳細.yaml
│   ├── 品質記録.yaml
│   └── アクセス分析.yaml
└── 📁 backup/                   # バックアップディレクトリ
    ├── full_20250721_143022/
    └── incremental_20250721_150000/
```

### 3.2 プロジェクト統合管理YAML構造
```yaml
# 50_管理資料/プロジェクト管理統合.yaml
project_metadata:
  id: "project-001"
  name: "転生したら最強の魔法使いだった件"
  description: "異世界転生ファンタジー小説"
  created_at: "2025-07-15T10:00:00"
  updated_at: "2025-07-21T14:30:22"
  version: 5

project_structure:
  directories:
    - name: "10_企画"
      status: "COMPLETE"
      file_count: 3
    - name: "20_プロット"
      status: "IN_PROGRESS"
      file_count: 12
    - name: "30_設定集"
      status: "COMPLETE"
      file_count: 5
    - name: "40_原稿"
      status: "ACTIVE"
      file_count: 15
    - name: "50_管理資料"
      status: "AUTO_MANAGED"
      file_count: 8

  validation_status: "VALID"
  last_structure_check: "2025-07-21T14:00:00"

components_status:
  episodes:
    total: 15
    status_distribution:
      COMPLETED: 12
      IN_PROGRESS: 2
      DRAFT: 1
    total_words: 45230
    average_quality: 87.3

  plots:
    master_plots: 1
    chapter_plots: 8
    scene_plots: 24
    completion_rate: 75.0

  settings:
    characters: 25
    locations: 12
    magic_system: "COMPLETE"
    world_building: "IN_PROGRESS"

integration_status:
  episode_plot_sync: "SYNCED"
  character_consistency: "VALIDATED"
  world_building_consistency: "PARTIAL"
  quality_standards: "APPLIED"

backup_info:
  last_full_backup: "2025-07-21T06:00:00"
  last_incremental_backup: "2025-07-21T14:00:00"
  backup_count: 15
  total_backup_size: "245MB"

statistics:
  creation_date: "2025-07-15"
  active_days: 7
  total_commits: 45
  last_activity: "2025-07-21T14:30:22"
  productivity_score: 82.5

updated_at: "2025-07-21T14:30:22"
```

### 3.3 プロジェクトテンプレート構造
```yaml
# templates/project_templates/fantasy_novel.yaml
template_info:
  name: "fantasy_novel"
  display_name: "異世界ファンタジー小説テンプレート"
  description: "異世界転生・魔法系ファンタジー小説の標準テンプレート"
  version: "1.2"
  author: "system"
  created_at: "2025-07-01T00:00:00"

directory_structure:
  - path: "10_企画"
    files:
      - "企画書.yaml": "templates/企画書テンプレート_異世界.yaml"
      - "読者分析.yaml": "templates/読者分析テンプレート_ファンタジー.yaml"
  - path: "20_プロット"
    files:
      - "全体構成.yaml": "templates/マスタープロットテンプレート_異世界.yaml"
  - path: "30_設定集"
    files:
      - "世界観.yaml": "templates/世界観テンプレート_異世界.yaml"
      - "キャラクター.yaml": "templates/キャラクターテンプレート.yaml"
      - "魔法システム.yaml": "templates/魔法システムテンプレート.yaml"

default_settings:
  project_status: "PLANNING"
  project_phase: "PLOTTING"
  genre: "異世界ファンタジー"
  target_audience: "10代～30代"
  writing_settings:
    default_episode_length: 3000
    narrative_tense: "過去形"
    writing_style: "三人称"

required_components:
  - "world_building"
  - "magic_system"
  - "character_profiles"
  - "plot_structure"

optional_components:
  - "glossary"
  - "timeline"
  - "map_data"
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

# ドメイン層
from domain.entities.project import Project, ProjectStatus
from domain.repositories.project_repository import ProjectRepository
from domain.value_objects.project_id import ProjectId
from domain.value_objects.project_name import ProjectName

# 他のリポジトリ（統合）
from infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository
from infrastructure.repositories.yaml_plot_repository import YamlPlotRepository
from infrastructure.repositories.yaml_project_info_repository import YamlProjectInfoRepository
```

### 4.2 統合アーキテクチャ
```python
class YamlProjectRepository:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        # 子リポジトリの統合
        self.episode_repo = YamlEpisodeRepository(base_path)
        self.plot_repo = YamlPlotRepository(base_path)
        self.info_repo = YamlProjectInfoRepository(base_path)

    def save(self, project: Project) -> None:
        # 統合保存処理
        self.info_repo.save(project.info, project.id)
        for episode in project.episodes:
            self.episode_repo.save(episode, project.id)
        for plot in project.plots:
            self.plot_repo.save(plot, project.id)
```

### 4.3 エラーハンドリング
```python
# カスタム例外
class ProjectRepositoryError(Exception):
    pass

class ProjectNotFoundError(ProjectRepositoryError):
    pass

class ProjectStructureError(ProjectRepositoryError):
    pass

class ProjectIntegrityError(ProjectRepositoryError):
    pass

class ProjectTemplateError(ProjectRepositoryError):
    pass

class ProjectBackupError(ProjectRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- プロジェクト作成: 1000ms以内
- プロジェクト読み込み: 500ms以内
- プロジェクト保存: 300ms以内
- 統計計算: 200ms以内
- バックアップ作成: 5000ms以内

### 5.2 メモリ使用量
- 単一プロジェクト全体: 100MB以内
- 複数プロジェクト同時: 500MB以内
- バックアップ処理時: 200MB以内

### 5.3 ディスク使用量
- 標準プロジェクト: 50MB以内
- 大規模プロジェクト: 500MB以内
- バックアップ効率: 50%圧縮率

## 6. 品質保証

### 6.1 データ整合性
- プロジェクト全体の整合性検証
- コンポーネント間の関連性チェック
- ファイル構造の完全性検証
- バックアップデータの整合性保証

### 6.2 エラー回復
- プロジェクト構造の自動修復
- 欠損ファイルの自動復元
- 破損データの検出・隔離
- 段階的復旧プロセス

### 6.3 トランザクション制御
- プロジェクト操作の原子性保証
- 部分的失敗からの自動復旧
- ロールバック機能
- 操作ログによる追跡性

## 7. セキュリティ

### 7.1 アクセス制御
- プロジェクト単位でのアクセス権管理
- ファイルシステム権限の活用
- 機密情報の保護

### 7.2 データ保護
- バックアップデータの暗号化オプション
- 個人情報のマスキング
- 安全な削除・アーカイブ処理

## 8. 互換性

### 8.1 既存システム
- 既存プロジェクト構造との完全互換
- 段階的移行サポート
- レガシーファイル形式の自動変換

### 8.2 将来拡張性
- 新しいコンポーネントタイプの追加対応
- 外部システム連携インターフェース
- クラウドストレージ対応準備
- 分散プロジェクト管理への拡張

## 9. 使用例

### 9.1 プロジェクト作成・初期化
```python
# リポジトリ初期化
base_path = Path("/path/to/projects")
repo = YamlProjectRepository(base_path)

# 新規プロジェクト作成
project = Project(
    id=ProjectId("project-001"),
    name=ProjectName("転生したら最強の魔法使いだった件"),
    template="fantasy_novel"
)

# プロジェクト作成・構造初期化
repo.create_project(project)
repo.initialize_project_structure("project-001", "fantasy_novel")

# 構造検証
validation_result = repo.validate_project_structure("project-001")
```

### 9.2 プロジェクト管理・操作
```python
# プロジェクト読み込み
project = repo.find_by_id("project-001")

# 統計情報取得
stats = repo.get_project_statistics("project-001")
print(f"完成度: {stats['progress']['overall_completion']:.1f}%")

# プロジェクト複製
success = repo.clone_project(
    "project-001",
    "project-002",
    "転生魔法使いの学園生活",
    {"include_episodes": False, "include_plots": True}
)
```

### 9.3 バックアップ・復元
```python
# フルバックアップ作成
backup_id = repo.create_full_backup("project-001")

# バックアップ一覧確認
backups = repo.list_backups("project-001")
for backup in backups:
    print(f"バックアップ: {backup['id']} - {backup['created_at']}")

# プロジェクト復元
restored = repo.restore_from_backup(
    "project-001",
    backup_id,
    {"restore_episodes": True, "restore_settings": True}
)
```

### 9.4 プロジェクト分析・レポート
```python
# プロジェクト健全性チェック
health = repo.check_project_health("project-001")
print(f"健全性スコア: {health['overall_score']}")

# 進捗レポート生成
report = repo.generate_progress_report("project-001", "weekly")

# プロジェクト比較
comparison = repo.compare_projects(["project-001", "project-002"])
```

## 10. テスト仕様

### 10.1 単体テスト
- 基本CRUD操作のテスト
- プロジェクト構造管理のテスト
- 統合機能の正確性テスト
- エラーハンドリングの検証
- パフォーマンス要件の確認

### 10.2 統合テスト
- 複数コンポーネント連携テスト
- 実ファイルシステムでの動作確認
- 大規模データでの性能テスト
- 同時操作・排他制御テスト
- バックアップ・復元の完全性テスト

### 10.3 エラーシナリオ
- ディスク容量不足時の動作
- ファイルシステム権限エラー
- プロジェクト構造破損の復旧
- 部分的データ損失からの回復
- ネットワーク接続問題の処理

## 11. 運用・監視

### 11.1 ログ出力
- プロジェクト操作の詳細ログ
- エラー・警告の詳細記録
- パフォーマンス測定データ
- バックアップ・復元の実行ログ

### 11.2 メトリクス
- プロジェクト作成・更新頻度
- 各機能の使用状況統計
- システムリソース使用量
- エラー発生率・回復率

### 11.3 アラート
- プロジェクト整合性エラー
- バックアップ失敗・遅延
- ディスク容量不足警告
- 重大なデータ破損検出

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_project_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_project_repository.py`
- **統合テスト**: `tests/integration/test_project_repository_integration.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 統合アーキテクチャによる一元管理
- エラー時の段階的復旧機能
- 高いカスタマイズ性と拡張性
- 運用・監視の容易性

### 12.3 今後の改善点
- [ ] 分散プロジェクト管理対応
- [ ] クラウドバックアップ統合
- [ ] リアルタイム協業機能
- [ ] AI による自動プロジェクト最適化
- [ ] 視覚的プロジェクト管理UI統合
- [ ] 外部版本管理システム連携
- [ ] 自動テスト・品質保証統合
- [ ] プロジェクトテンプレート市場連携
