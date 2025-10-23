# YAML伏線データリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、伏線エンティティのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- 伏線作成・保存・検索・削除の完全な永続化機能
- 伏線とエピソードの関連管理
- 伏線の張り方・回収タイミング・影響度の追跡機能
- プロット進行との連動による伏線管理

### 1.3 アーキテクチャ位置
```
Domain Layer
├── ForeshadowingRepository (Interface) ← Infrastructure Layer
└── Foreshadowing (Entity)              └── YamlForeshadowingRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(foreshadowing: Foreshadowing, project_id: str) -> None

# 検索
def find_by_id(foreshadowing_id: str, project_id: str) -> Foreshadowing | None
def find_by_name(project_id: str, name: str) -> Foreshadowing | None
def find_all(project_id: str) -> list[Foreshadowing]

# 存在確認
def exists(project_id: str, foreshadowing_id: str) -> bool

# 削除
def delete(foreshadowing_id: str, project_id: str) -> bool
```

### 2.2 高度な検索機能
```python
# ステータス検索
def find_by_status(project_id: str, status: str) -> list[Foreshadowing]

# 種類別検索
def find_by_type(project_id: str, foreshadowing_type: str) -> list[Foreshadowing]

# エピソード関連検索
def find_by_episode(project_id: str, episode_number: int) -> list[Foreshadowing]

# 重要度範囲検索
def find_by_importance_range(
    project_id: str,
    min_importance: int,
    max_importance: int
) -> list[Foreshadowing]

# 未回収伏線検索
def find_unrevealed(project_id: str) -> list[Foreshadowing]

# 章別伏線検索
def find_by_chapter(project_id: str, chapter: int) -> list[Foreshadowing]

# 関連伏線検索
def find_related(project_id: str, foreshadowing_id: str) -> list[Foreshadowing]
```

### 2.3 統計・分析機能
```python
# 統計情報取得
def get_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_foreshadowings": 25,
    "unrevealed_count": 8,
    "revealed_count": 17,
    "type_distribution": {
        "character": 10,
        "plot": 8,
        "world_building": 7
    },
    "importance_distribution": {
        "高": 5,
        "中": 12,
        "低": 8
    },
    "average_setup_distance": 4.2  # 平均的な張り方〜回収の話数差
}

# 伏線回収率計算
def get_revelation_rate(project_id: str) -> float

# 伏線密度分析（エピソードあたりの伏線数）
def get_foreshadowing_density(project_id: str) -> dict[int, int]
```

### 2.4 伏線管理機能
```python
# 伏線回収処理
def reveal_foreshadowing(
    foreshadowing_id: str,
    project_id: str,
    revelation_episode: int,
    revelation_details: str
) -> bool

# 伏線影響度更新
def update_impact_level(
    foreshadowing_id: str,
    project_id: str,
    new_impact: int
) -> bool

# 関連伏線リンク
def link_foreshadowings(
    project_id: str,
    main_id: str,
    related_ids: list[str]
) -> bool
```

### 2.5 一括操作
```python
# 一括ステータス更新
def bulk_update_status(
    project_id: str,
    foreshadowing_ids: list[str],
    new_status: str
) -> int

# 章単位での伏線活性化
def activate_chapter_foreshadowings(
    project_id: str,
    chapter: int
) -> int
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/
│   ├── 伏線管理.yaml              # メインデータファイル
│   └── 伏線関係図.yaml            # 伏線間の関係性データ
└── backup/
    └── 20250721_143022/
        └── 伏線管理_backup.yaml
```

### 3.2 伏線管理YAML構造
```yaml
foreshadowings:
  - id: "foreshadowing_001"
    name: "主人公の出生の秘密"
    type: "character"
    description: "主人公が実は王族の血を引いていることを示唆"
    importance: "高"
    status: "未回収"
    setup_episode: 1
    setup_details: "村長が主人公の名前を聞いて驚く表情"
    planned_revelation_episode: 15
    actual_revelation_episode: null
    revelation_details: null
    impact_level: 9
    related_characters: ["主人公", "村長", "王"]
    related_plot_points: ["王位継承問題", "魔王討伐依頼"]
    tags: ["出生", "王族", "秘密"]
    notes: "読者の予想を裏切らない程度に自然に回収したい"
    created_at: "2025-07-15T10:30:00"
    updated_at: "2025-07-21T14:30:22"

  - id: "foreshadowing_002"
    name: "魔剣の呪い"
    type: "plot"
    description: "魔剣が使用者の生命力を吸収することの伏線"
    importance: "中"
    status: "回収済み"
    setup_episode: 3
    setup_details: "魔剣を使った後、主人公が軽い疲労を感じる"
    planned_revelation_episode: 8
    actual_revelation_episode: 7
    revelation_details: "賢者が魔剣の真実を説明"
    impact_level: 6
    related_characters: ["主人公", "賢者"]
    related_plot_points: ["魔剣入手", "賢者との出会い"]
    tags: ["魔剣", "呪い", "代償"]
    notes: "予定より1話早く回収。読者の反応良好"
    created_at: "2025-07-16T09:15:00"
    updated_at: "2025-07-18T16:45:00"

relationships:
  - main_foreshadowing: "foreshadowing_001"
    related_foreshadowings: ["foreshadowing_003", "foreshadowing_005"]
    relationship_type: "連鎖"
    description: "王族の血筋に関連する伏線群"

metadata:
  total_foreshadowings: 25
  unrevealed_count: 8
  last_updated: "2025-07-21T14:30:22"
  revision: 15
```

### 3.3 伏線関係図YAML構造
```yaml
foreshadowing_network:
  nodes:
    - id: "foreshadowing_001"
      name: "主人公の出生の秘密"
      type: "character"
      importance: "高"
      x: 100
      y: 150

  edges:
    - from: "foreshadowing_001"
      to: "foreshadowing_003"
      relationship: "前提条件"
      strength: 0.9

visualization_settings:
  layout: "force_directed"
  node_size_factor: "importance"
  edge_thickness_factor: "strength"
  color_scheme: "by_type"
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
from domain.entities.foreshadowing import Foreshadowing, ForeshadowingStatus
from domain.repositories.foreshadowing_repository import ForeshadowingRepository
from domain.value_objects.foreshadowing_id import ForeshadowingId
from domain.value_objects.importance_level import ImportanceLevel
from domain.value_objects.episode_number import EpisodeNumber
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class ForeshadowingRepositoryError(Exception):
    pass

class ForeshadowingNotFoundError(ForeshadowingRepositoryError):
    pass

class InvalidForeshadowingDataError(ForeshadowingRepositoryError):
    pass

class ForeshadowingRelationshipError(ForeshadowingRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一伏線検索: 30ms以内
- 全伏線読み込み: 200ms以内（100伏線）
- 保存操作: 50ms以内
- 関係性分析: 500ms以内

### 5.2 メモリ使用量
- 単一伏線: 5KB以内
- 全伏線同時読み込み: 50MB以内
- 関係性グラフ: 100MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御

## 6. 品質保証

### 6.1 データ整合性
- 伏線ID の一意性保証
- エピソード番号の妥当性検証
- 関係性データの整合性チェック
- YAMLフォーマットの妥当性検証

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 循環参照の検出・修正
- 不正な関係性リンクの削除

### 6.3 バージョン管理
- 伏線データのバージョン管理
- 変更履歴の自動記録
- 回収済み伏線の履歴保持

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
- 既存の伏線管理ファイルとの互換性
- 段階的移行サポート
- 手動入力データの自動変換

### 8.2 将来拡張性
- 新しい伏線タイプの追加対応
- AIによる伏線分析機能との連携準備
- グラフィカル伏線管理ツールとの統合

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlForeshadowingRepository(project_path)

# 伏線作成・保存
foreshadowing = Foreshadowing(
    id=ForeshadowingId("foreshadowing_001"),
    name="主人公の出生の秘密",
    type="character",
    description="主人公が実は王族の血を引いていることを示唆",
    importance=ImportanceLevel("高"),
    setup_episode=EpisodeNumber(1)
)
repo.save(foreshadowing, "project-001")

# 検索
found = repo.find_by_id("foreshadowing_001", "project-001")
all_foreshadowings = repo.find_all("project-001")

# 統計取得
stats = repo.get_statistics("project-001")
print(f"総伏線数: {stats['total_foreshadowings']}")
```

### 9.2 高度な検索例
```python
# 未回収伏線の取得
unrevealed = repo.find_unrevealed("project-001")

# 高重要度伏線の検索
important = repo.find_by_importance_range("project-001", 7, 10)

# 関連伏線の検索
related = repo.find_related("project-001", "foreshadowing_001")
```

### 9.3 伏線回収処理例
```python
# 伏線回収
success = repo.reveal_foreshadowing(
    "foreshadowing_001",
    "project-001",
    15,
    "村長が王家の紋章を見せて真実を告白"
)

# 影響度更新
repo.update_impact_level("foreshadowing_001", "project-001", 10)
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- 伏線関係性管理のテスト
- エラーケースの処理確認
- 統計計算の正確性テスト

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- エピソードリポジトリとの連携テスト
- 大量伏線での性能テスト

### 10.3 エラーシナリオ
- YAMLファイル破損
- 循環参照の発生
- 存在しないエピソード参照
- ディスク容量不足

## 11. 運用・監視

### 11.1 ログ出力
- 伏線作成・回収のログ記録
- 関係性変更のログ
- エラー発生時の詳細ログ

### 11.2 メトリクス
- 伏線回収率の推移
- 操作頻度の統計
- パフォーマンス測定

### 11.3 アラート
- 長期未回収伏線の警告
- 関係性データの不整合
- ファイルアクセスエラー

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_foreshadowing_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_foreshadowing_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- 伏線エンティティの完全な復元
- 関係性管理の効率化
- 将来の分析機能拡張を考慮

### 12.3 今後の改善点
- [ ] AI による伏線分析・提案機能
- [ ] グラフィカル伏線関係図表示
- [ ] 読者予想との照合機能
- [ ] 自動伏線品質チェック
- [ ] 伏線密度の最適化提案
