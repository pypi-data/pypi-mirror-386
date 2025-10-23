# プロット進捗追跡リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロット進捗エンティティのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- プロット進捗の作成・保存・検索・更新・削除機能
- 執筆進捗とプロット完成度の連動追跡
- タイムライン管理・マイルストーン設定・進捗分析機能
- 執筆者の作業パターン分析・生産性向上支援

### 1.3 アーキテクチャ位置
```
Domain Layer
├── PlotProgressRepository (Interface) ← Infrastructure Layer
└── PlotProgress (Entity)              └── YamlPlotProgressRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(progress: PlotProgress, project_id: str) -> None

# 検索
def find_by_id(progress_id: str, project_id: str) -> PlotProgress | None
def find_by_plot_id(project_id: str, plot_id: str) -> PlotProgress | None
def find_all(project_id: str) -> list[PlotProgress]

# 存在確認
def exists(project_id: str, progress_id: str) -> bool

# 削除
def delete(progress_id: str, project_id: str) -> bool
```

### 2.2 高度な検索機能
```python
# ステータス別検索
def find_by_status(project_id: str, status: str) -> list[PlotProgress]

# 日付範囲検索
def find_by_date_range(
    project_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[PlotProgress]

# 進捗率範囲検索
def find_by_completion_range(
    project_id: str,
    min_completion: float,
    max_completion: float
) -> list[PlotProgress]

# 遅延プロット検索
def find_delayed_plots(project_id: str) -> list[PlotProgress]

# 完了間近プロット検索
def find_near_completion(project_id: str, threshold: float = 90.0) -> list[PlotProgress]

# アクティブプロット検索
def find_active_plots(project_id: str) -> list[PlotProgress]

# マイルストーン検索
def find_by_milestone(project_id: str, milestone_name: str) -> list[PlotProgress]
```

### 2.3 統計・分析機能
```python
# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_plots": 45,
    "active_plots": 12,
    "completed_plots": 28,
    "delayed_plots": 5,
    "overall_completion": 74.5,
    "average_daily_progress": 2.3,
    "estimated_completion_date": "2025-10-15",
    "productivity_metrics": {
        "plots_per_week": 3.2,
        "average_plot_duration": 4.5,  # days
        "consistency_score": 87.5
    }
}

# 進捗トレンド分析
def analyze_progress_trend(project_id: str, days: int = 30) -> dict[str, Any]

# 生産性分析
def analyze_productivity(project_id: str) -> dict[str, Any]

# ボトルネック分析
def identify_bottlenecks(project_id: str) -> list[dict[str, Any]]

# 予測分析
def predict_completion_dates(project_id: str) -> dict[str, datetime]
```

### 2.4 進捗管理機能
```python
# 進捗更新
def update_progress(
    progress_id: str,
    project_id: str,
    completion_percentage: float,
    notes: str = ""
) -> bool

# マイルストーン設定
def set_milestone(
    progress_id: str,
    project_id: str,
    milestone_name: str,
    target_date: datetime
) -> bool

# マイルストーン達成記録
def achieve_milestone(
    progress_id: str,
    project_id: str,
    milestone_name: str,
    achievement_date: datetime
) -> bool

# 作業時間記録
def log_work_session(
    progress_id: str,
    project_id: str,
    start_time: datetime,
    end_time: datetime,
    work_type: str,
    productivity_score: float
) -> bool
```

### 2.5 タイムライン機能
```python
# タイムライン生成
def generate_timeline(project_id: str) -> list[dict[str, Any]]

# スケジュール調整
def adjust_schedule(
    project_id: str,
    delay_days: int,
    affected_plots: list[str]
) -> bool

# デッドライン管理
def check_deadlines(project_id: str) -> list[dict[str, Any]]
```

### 2.6 一括操作
```python
# 一括進捗更新
def bulk_update_progress(
    project_id: str,
    updates: list[dict[str, Any]]
) -> int

# 一括スケジュール調整
def bulk_adjust_schedules(
    project_id: str,
    adjustment_factor: float
) -> int
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/
│   ├── プロット進捗.yaml         # メイン進捗データ
│   ├── 作業記録.yaml             # 詳細作業記録
│   └── スケジュール.yaml         # スケジュール・マイルストーン
└── backup/
    └── 20250721_143022/
        └── プロット進捗_backup.yaml
```

### 3.2 プロット進捗YAML構造
```yaml
project_progress:
  project_id: "project_001"
  overall_completion: 74.5
  start_date: "2025-07-01T09:00:00"
  target_completion_date: "2025-12-31T23:59:59"
  estimated_completion_date: "2025-10-15T18:00:00"
  last_updated: "2025-07-21T14:30:22"

plot_progress:
  - id: "progress_001"
    plot_id: "master_plot_001"
    plot_title: "転生魔法使い物語　全体構成"
    plot_type: "master"
    status: "進行中"
    completion_percentage: 85.0
    start_date: "2025-07-01T09:00:00"
    target_completion_date: "2025-08-15T18:00:00"
    estimated_completion_date: "2025-08-10T15:30:00"
    actual_completion_date: null

    milestones:
      - name: "プロット骨格完成"
        target_date: "2025-07-10T18:00:00"
        achieved: true
        achievement_date: "2025-07-09T16:45:00"
        notes: "予定より早期完成"

      - name: "キャラクター設定完成"
        target_date: "2025-07-20T18:00:00"
        achieved: true
        achievement_date: "2025-07-18T14:20:00"
        notes: "詳細設定まで完了"

      - name: "最終調整完了"
        target_date: "2025-08-15T18:00:00"
        achieved: false
        achievement_date: null
        notes: "残り15%程度"

    work_sessions:
      - date: "2025-07-21"
        start_time: "09:00:00"
        end_time: "12:30:00"
        work_type: "プロット調整"
        productivity_score: 8.5
        progress_made: 5.0
        notes: "キャラクター関係性を詳細化"

      - date: "2025-07-21"
        start_time: "14:00:00"
        end_time: "17:00:00"
        work_type: "構成見直し"
        productivity_score: 7.2
        progress_made: 3.0
        notes: "第3章の流れを調整"

    dependencies:
      prerequisites: []
      dependents: ["progress_002", "progress_003"]

    quality_metrics:
      consistency_score: 88.5
      depth_score: 92.0
      feasibility_score: 85.5

    created_at: "2025-07-01T09:00:00"
    updated_at: "2025-07-21T14:30:22"

  - id: "progress_002"
    plot_id: "chapter_plot_001"
    plot_title: "第1章：異世界への扉"
    plot_type: "chapter"
    status: "完成"
    completion_percentage: 100.0
    start_date: "2025-07-08T10:00:00"
    target_completion_date: "2025-07-25T18:00:00"
    estimated_completion_date: "2025-07-22T16:00:00"
    actual_completion_date: "2025-07-20T16:45:00"

    milestones:
      - name: "シーン構成完成"
        target_date: "2025-07-15T18:00:00"
        achieved: true
        achievement_date: "2025-07-14T15:30:00"
        notes: "10シーンで構成確定"

    work_sessions:
      - date: "2025-07-20"
        start_time: "13:00:00"
        end_time: "16:45:00"
        work_type: "最終調整"
        productivity_score: 9.0
        progress_made: 12.0
        notes: "完成まで一気に完了"

    dependencies:
      prerequisites: ["progress_001"]
      dependents: ["progress_004"]

productivity_analytics:
  daily_averages:
    - day_of_week: "月曜日"
      average_hours: 4.2
      average_productivity: 7.8
      average_progress: 8.5

    - day_of_week: "火曜日"
      average_hours: 3.8
      average_productivity: 8.2
      average_progress: 7.9

  monthly_trends:
    - month: "2025-07"
      total_hours: 85.5
      average_productivity: 8.1
      total_progress: 156.8
      completed_plots: 5

work_patterns:
  peak_hours: ["09:00-12:00", "14:00-17:00"]
  most_productive_day: "火曜日"
  least_productive_day: "金曜日"
  average_session_length: 3.2
  preferred_work_types: ["プロット作成", "構成見直し"]

metadata:
  version: 8
  last_backup: "2025-07-21T14:00:00"
  total_work_sessions: 45
  total_work_hours: 156.5
```

### 3.3 スケジュール管理YAML構造
```yaml
project_schedule:
  project_id: "project_001"
  created_at: "2025-07-01T09:00:00"
  last_updated: "2025-07-21T14:30:22"

master_timeline:
  phases:
    - name: "プロット構築フェーズ"
      start_date: "2025-07-01"
      end_date: "2025-08-31"
      completion: 78.5
      plots: ["master_plot_001", "chapter_plot_001", "chapter_plot_002"]

    - name: "執筆フェーズ"
      start_date: "2025-08-15"
      end_date: "2025-11-30"
      completion: 0.0
      plots: []

milestones:
  - id: "milestone_001"
    name: "全体プロット完成"
    target_date: "2025-08-15T18:00:00"
    status: "進行中"
    completion: 85.0
    related_plots: ["master_plot_001"]

  - id: "milestone_002"
    name: "第1部プロット完成"
    target_date: "2025-08-31T18:00:00"
    status: "計画中"
    completion: 45.0
    related_plots: ["chapter_plot_001", "chapter_plot_002", "chapter_plot_003"]

deadlines:
  - type: "hard"
    name: "出版社締切"
    date: "2025-12-31T23:59:59"
    buffer_days: 30

  - type: "soft"
    name: "第1部完成目標"
    date: "2025-09-30T18:00:00"
    buffer_days: 7

schedule_adjustments:
  - date: "2025-07-15"
    reason: "体調不良"
    delay_days: 3
    affected_plots: ["chapter_plot_001"]

  - date: "2025-07-18"
    reason: "プロット変更"
    delay_days: -2
    affected_plots: ["chapter_plot_002"]
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
import numpy as np

# ドメイン層
from domain.entities.plot_progress import PlotProgress, ProgressStatus
from domain.repositories.plot_progress_repository import PlotProgressRepository
from domain.value_objects.progress_id import ProgressId
from domain.value_objects.completion_percentage import CompletionPercentage
from domain.value_objects.productivity_score import ProductivityScore
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class PlotProgressRepositoryError(Exception):
    pass

class ProgressNotFoundError(PlotProgressRepositoryError):
    pass

class InvalidProgressDataError(PlotProgressRepositoryError):
    pass

class ScheduleConflictError(PlotProgressRepositoryError):
    pass

class MilestoneError(PlotProgressRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一進捗検索: 30ms以内
- 統計計算: 200ms以内
- 全進捗読み込み: 400ms以内（100進捗）
- 保存操作: 60ms以内
- 予測分析: 1000ms以内

### 5.2 メモリ使用量
- 単一進捗: 20KB以内
- 全進捗同時読み込み: 100MB以内
- 統計キャッシュ: 50MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御

## 6. 品質保証

### 6.1 データ整合性
- 進捗ID の一意性保証
- 日付の妥当性検証（未来日付・順序）
- 完成度の範囲チェック（0-100%）
- スケジュール整合性の確認

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 不正な日付データの修正
- 欠損した依存関係の補完

### 6.3 バージョン管理
- 進捗データのバージョン管理
- 作業記録の不可逆性保証
- 変更履歴の詳細追跡

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 作業記録の改ざん防止
- パス インジェクション攻撃の防止

## 8. 互換性

### 8.1 レガシーシステム
- 既存の進捗管理ファイルとの互換性
- 手動入力データの自動変換
- 段階的移行サポート

### 8.2 将来拡張性
- AIによる進捗予測機能との連携
- 外部プロジェクト管理ツールとの統合
- チーム作業への拡張

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlPlotProgressRepository(project_path)

# 進捗作成・保存
progress = PlotProgress(
    id=ProgressId("progress_001"),
    plot_id="master_plot_001",
    plot_title="転生魔法使い物語　全体構成",
    completion_percentage=CompletionPercentage(85.0),
    start_date=datetime(2025, 7, 1)
)
repo.save(progress, "project-001")

# 進捗検索
found = repo.find_by_plot_id("project-001", "master_plot_001")
all_progress = repo.find_all("project-001")

# 統計取得
stats = repo.get_statistics("project-001")
print(f"全体完成度: {stats['overall_completion']}%")
```

### 9.2 分析機能例
```python
# 進捗トレンド分析
trend = repo.analyze_progress_trend("project-001", 30)
print(f"30日間の平均進捗: {trend['average_daily_progress']}%")

# ボトルネック特定
bottlenecks = repo.identify_bottlenecks("project-001")
for bottleneck in bottlenecks:
    print(f"ボトルネック: {bottleneck['description']}")

# 完成予測
predictions = repo.predict_completion_dates("project-001")
print(f"予想完成日: {predictions['overall_completion']}")
```

### 9.3 作業管理例
```python
# 作業記録
repo.log_work_session(
    "progress_001",
    "project-001",
    datetime(2025, 7, 21, 9, 0),
    datetime(2025, 7, 21, 12, 30),
    "プロット調整",
    8.5
)

# マイルストーン設定
repo.set_milestone(
    "progress_001",
    "project-001",
    "最終調整完了",
    datetime(2025, 8, 15, 18, 0)
)

# 進捗更新
repo.update_progress("progress_001", "project-001", 90.0, "詳細調整中")
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- 統計計算の正確性テスト
- 予測アルゴリズムのテスト
- エラーケースの処理確認

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- プロットリポジトリとの連携テスト
- 長期間データでの分析テスト

### 10.3 エラーシナリオ
- YAMLファイル破損
- 不正な日付データ
- スケジュール競合
- 大量データでの性能劣化

## 11. 運用・監視

### 11.1 ログ出力
- 進捗更新のログ記録
- 作業記録のログ
- 統計計算のログ
- エラー発生時の詳細ログ

### 11.2 メトリクス
- 進捗更新頻度
- 作業時間の統計
- 予測精度の測定
- パフォーマンス測定

### 11.3 アラート
- スケジュール遅延警告
- 長期間未更新の進捗
- 異常な生産性低下
- ファイルアクセスエラー

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_plot_progress_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_plot_progress_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 進捗エンティティの完全な復元
- 分析機能の効率化
- 予測精度の向上を考慮

### 12.3 今後の改善点
- [ ] AI による生産性予測・提案機能
- [ ] リアルタイム進捗ダッシュボード
- [ ] 自動スケジュール調整機能
- [ ] チームコラボレーション機能
- [ ] 外部カレンダー連携機能
