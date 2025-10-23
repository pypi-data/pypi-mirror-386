# YAML品質チェックリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、品質チェック結果のYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- 品質チェック結果の作成・保存・検索・削除の完全な永続化機能
- チェック履歴とトレンド分析データの管理
- 品質基準とチェック設定の分離管理
- レガシーシステムとの互換性確保

### 1.3 アーキテクチャ位置
```
Domain Layer
├── QualityCheckRepository (Interface) ← Infrastructure Layer
└── QualityCheck (Entity)              └── YamlQualityCheckRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(quality_check: QualityCheck, project_id: str) -> None

# 検索
def find_by_episode(project_id: str, episode_number: int) -> QualityCheck | None
def find_by_id(check_id: str, project_id: str) -> QualityCheck | None
def find_all(project_id: str) -> list[QualityCheck]

# 存在確認
def exists(project_id: str, episode_number: int) -> bool

# 削除
def delete(check_id: str, project_id: str) -> bool
```

### 2.2 高度な検索機能
```python
# 品質スコア範囲検索
def find_by_score_range(
    project_id: str,
    min_score: float,
    max_score: float
) -> list[QualityCheck]

# チェック種別検索
def find_by_check_type(project_id: str, check_type: str) -> list[QualityCheck]

# 日付範囲検索
def find_by_date_range(
    project_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[QualityCheck]

# 合格・不合格検索
def find_by_pass_status(project_id: str, passed: bool) -> list[QualityCheck]

# 最新のチェック結果取得
def find_latest_by_episode(project_id: str, episode_number: int) -> QualityCheck | None
```

### 2.3 統計・分析機能
```python
# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_checks": 45,
    "average_score": 87.3,
    "pass_rate": 0.78,
    "check_type_distribution": {
        "basic_style": 15,
        "story_structure": 15,
        "character_consistency": 15
    },
    "score_distribution": {
        "90-100": 12,
        "80-89": 18,
        "70-79": 10,
        "below_70": 5
    }
}

# トレンド分析
def get_quality_trend(
    project_id: str,
    episode_range: tuple[int, int] | None = None
) -> dict[str, list[float]]
```

### 2.4 履歴・バージョン管理
```python
# チェック履歴取得
def get_check_history(
    project_id: str,
    episode_number: int
) -> list[QualityCheck]

# バックアップ作成
def backup_check_results(project_id: str) -> bool

# 履歴からの復元
def restore_from_backup(
    project_id: str,
    backup_version: str
) -> bool
```

### 2.5 一括操作
```python
# 一括再チェック実行
def bulk_recheck(
    project_id: str,
    episode_numbers: list[int],
    check_types: list[str]
) -> int

# 古いチェック結果のアーカイブ
def archive_old_results(
    project_id: str,
    before_date: datetime
) -> int
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/                  # 品質チェック結果
│   ├── 品質チェック結果.yaml      # メインの品質チェック結果
│   └── 品質チェック履歴.yaml      # 履歴データ（オプション）
└── backup/                       # バックアップ（任意）
    └── 20250721_143022/
        └── 品質チェック結果.yaml
```

### 3.2 品質チェック結果YAML構造
```yaml
metadata:
  project_name: "転生したら最強の魔法使いだった件"
  last_updated: "2025-07-21T14:30:22"
  version: "1.0"

quality_checks:
  - check_id: "qc_001_001"
    episode_number: 1
    check_type: "basic_style"
    executed_at: "2025-07-21T10:30:00"
    overall_score: 88.5
    passed: true
    details:
      文体統一性: 92.0
      誤字脱字: 85.0
      句読点使用: 88.0
      敬語使用: 90.0
    issues:
      - level: "warning"
        message: "第3段落で文体が一部変化しています"
        line_number: 15
        suggestion: "です・ます調で統一してください"
    execution_time: 0.85

  - check_id: "qc_001_002"
    episode_number: 1
    check_type: "story_structure"
    executed_at: "2025-07-21T10:30:15"
    overall_score: 82.0
    passed: true
    details:
      導入部分: 85.0
      展開部分: 80.0
      結末部分: 81.0
      全体構成: 82.0
    issues:
      - level: "info"
        message: "展開部分での緊張感維持に改善の余地があります"
        suggestion: "困難や障害をより具体的に描写してください"
    execution_time: 1.23

summary:
  total_checks: 2
  average_score: 85.25
  pass_rate: 1.0
  last_check: "2025-07-21T10:30:15"
```

### 3.3 履歴データ構造（オプション）
```yaml
history:
  - episode_number: 1
    checks:
      - timestamp: "2025-07-21T10:30:00"
        type: "basic_style"
        score: 88.5
        passed: true
      - timestamp: "2025-07-20T15:45:00"
        type: "basic_style"
        score: 85.2
        passed: true
        note: "初回チェック"
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
from domain.entities.quality_check import QualityCheck, CheckType, CheckStatus
from domain.repositories.quality_check_repository import QualityCheckRepository
from domain.value_objects.quality_score import QualityScore
from domain.value_objects.episode_number import EpisodeNumber
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class QualityCheckRepositoryError(Exception):
    pass

class QualityCheckNotFoundError(QualityCheckRepositoryError):
    pass

class InvalidQualityCheckDataError(QualityCheckRepositoryError):
    pass

class QualityCheckVersionConflictError(QualityCheckRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一チェック結果検索: 30ms以内
- エピソード別チェック履歴: 100ms以内
- 統計情報取得: 200ms以内（100エピソード）
- 保存操作: 50ms以内

### 5.2 メモリ使用量
- 単一チェック結果: 1MB以内
- 全チェック結果同時読み込み: 500MB以内
- 履歴データ: 100MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御
- チェック実行: 非同期実行サポート

## 6. 品質保証

### 6.1 データ整合性
- チェックID の一意性保証
- エピソード番号とチェック結果の整合性確認
- YAMLフォーマットの妥当性検証
- スコアの範囲チェック（0-100）

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 欠損したチェック結果の検出・通知
- バックアップからの自動復元オプション
- 部分的な結果保存による中断復旧

### 6.3 バージョン管理
- チェック結果バージョンの自動管理
- 更新日時の自動記録
- 変更履歴の追跡
- スキーマバージョンの互換性確認

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離
- チェック実行権限の管理

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 機密情報の除去（パスワード等）
- ログイン情報の暗号化
- 一時ファイルの安全な削除

## 8. 互換性

### 8.1 レガシーシステム
- 既存の品質チェック結果との完全互換
- 段階的移行サポート
- 旧フォーマットの自動変換
- 互換性レイヤーの提供

### 8.2 将来拡張性
- 新しいチェックタイプの追加対応
- カスタムチェックルールの追加
- 外部チェックツール連携
- 分散チェック実行への対応

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlQualityCheckRepository(project_path)

# チェック結果保存
quality_check = QualityCheck(
    episode_number=EpisodeNumber(1),
    check_type=CheckType.BASIC_STYLE,
    overall_score=QualityScore(88.5),
    passed=True,
    details={"文体統一性": 92.0, "誤字脱字": 85.0}
)
repo.save(quality_check, "project-001")

# 検索
latest_check = repo.find_latest_by_episode("project-001", 1)
all_checks = repo.find_all("project-001")

# 統計取得
stats = repo.get_statistics("project-001")
print(f"平均スコア: {stats['average_score']}")
```

### 9.2 高度な検索・分析例
```python
# 品質スコア80点以上の取得
high_quality = repo.find_by_score_range("project-001", 80.0, 100.0)

# トレンド分析
trend = repo.get_quality_trend("project-001", (1, 10))
print(f"基本文体スコアの推移: {trend['basic_style']}")

# 不合格チェックの取得
failed_checks = repo.find_by_pass_status("project-001", False)
```

### 9.3 履歴管理例
```python
# エピソードのチェック履歴取得
history = repo.get_check_history("project-001", 1)
for check in history:
    print(f"{check.executed_at}: {check.overall_score}")

# バックアップ・復元
backup_success = repo.backup_check_results("project-001")
restore_success = repo.restore_from_backup("project-001", "20250721_143022")
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- エラーケースの処理確認
- スコア計算の正確性テスト
- 境界値テスト（スコア0,100）

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- 大量データでの性能テスト
- 同時実行テスト
- チェック実行との統合テスト

### 10.3 エラーシナリオ
- ディスク容量不足
- ファイル権限エラー
- 破損したYAMLファイル
- 不正なスコア値
- チェック実行エラー

## 11. 運用・監視

### 11.1 ログ出力
- チェック実行・保存のログ記録
- エラー発生時の詳細ログ
- パフォーマンス測定ログ
- 品質トレンドの定期ログ

### 11.2 メトリクス
- チェック実行回数・時間の統計
- 品質スコアの推移監視
- エラー発生率の監視
- ストレージ使用量の監視

### 11.3 アラート
- 品質スコア急激な低下
- チェック実行エラーの連続発生
- データ整合性エラー
- ディスク容量警告

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_quality_check_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_quality_check_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 品質データの完全な永続化
- チェック履歴の効率的管理
- 将来の拡張性を考慮した設計

### 12.3 今後の改善点
- [ ] リアルタイム品質監視機能
- [ ] 品質予測モデルとの連携
- [ ] 分散チェック実行対応
- [ ] 機械学習による自動品質改善
- [ ] 外部品質チェックツール連携
