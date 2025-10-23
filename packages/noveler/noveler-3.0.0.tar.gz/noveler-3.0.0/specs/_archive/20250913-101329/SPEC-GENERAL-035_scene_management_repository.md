# SPEC-GENERAL-035: SceneManagementRepository 仕様書

## 1. 概要

### 1.1 目的
SceneManagementRepository は、シーン管理に関するインフラストラクチャ層のリポジトリ実装を定義します。YAMLファイルベースで以下の機能を提供します：
- シーンデータの永続化と取得
- シーンメタデータの管理
- シーン間の関係性と順序管理
- シーンテンプレートと構成管理
- シーン分析とメトリクス収集

### 1.2 責務
- シーンデータのYAML形式での読み書き
- シーンの検索・フィルタリング機能
- シーン間の依存関係管理
- テンプレートベースのシーン生成
- シーン統計情報の集計

### 1.3 位置づけ
```
Infrastructure Layer
└── repositories/
    └── scene_management_repository.py  # 本仕様書の対象
```

## 2. 機能要件

### 2.1 シーンデータ管理
- シーンの作成・読取・更新・削除（CRUD）操作
- シーンのバージョン管理
- シーンのバックアップとリストア
- シーンの一括操作（バルク処理）

### 2.2 シーンメタデータ管理
- シーンタグの管理
- 登場人物・場所・時間の記録
- 感情曲線・テンション値の保存
- カスタムメタデータの拡張

### 2.3 シーン関係性管理
- シーン間の前後関係
- 並行シーンの管理
- 伏線と回収の関連付け
- シーングループ化機能

### 2.4 シーンテンプレート機能
- 標準シーンテンプレートの提供
- カスタムテンプレートの作成・保存
- テンプレートからのシーン生成
- テンプレートパラメータの管理

### 2.5 シーン分析機能
- シーン長の統計
- 登場頻度分析
- 感情推移の可視化データ
- シーン間隔の分析

## 3. データ構造

### 3.1 シーンデータ構造
```yaml
scenes:
  - scene_id: "scene_001"
    episode_number: 1
    scene_number: 1
    title: "運命の出会い"
    type: "encounter"  # encounter, battle, dialogue, description, etc.

    metadata:
      location: "王都の市場"
      time: "朝"
      weather: "晴れ"
      characters:
        - name: "主人公"
          role: "protagonist"
        - name: "ヒロイン"
          role: "heroine"

    content:
      summary: "主人公が市場でヒロインと出会う"
      key_points:
        - "偶然の出会い"
        - "運命を感じる瞬間"
      dialogue_ratio: 0.4
      action_ratio: 0.3
      description_ratio: 0.3

    emotional_curve:
      start: 3
      peak: 8
      end: 6

    relations:
      previous_scene: null
      next_scene: "scene_002"
      related_scenes:
        - scene_id: "scene_045"
          relation_type: "foreshadowing"

    tags:
      - "重要シーン"
      - "出会い"
      - "伏線"

    quality_metrics:
      impact_score: 9
      pacing_score: 7
      coherence_score: 8

    revision_history:
      - version: 1
        date: "2024-01-15"
        changes: "初稿作成"
      - version: 2
        date: "2024-01-18"
        changes: "対話追加"
```

### 3.2 シーンテンプレート構造
```yaml
scene_templates:
  - template_id: "battle_scene"
    name: "戦闘シーン"
    category: "action"

    structure:
      phases:
        - name: "導入"
          duration_ratio: 0.2
          elements:
            - "状況説明"
            - "緊張感の演出"
        - name: "展開"
          duration_ratio: 0.6
          elements:
            - "戦闘描写"
            - "駆け引き"
        - name: "決着"
          duration_ratio: 0.2
          elements:
            - "勝敗決定"
            - "余韻"

    parameters:
      - name: "intensity"
        type: "integer"
        range: [1, 10]
      - name: "participants"
        type: "list"
        required: true
      - name: "location"
        type: "string"

    default_values:
      emotional_curve:
        start: 5
        peak: 9
        end: 3
      dialogue_ratio: 0.2
      action_ratio: 0.7
      description_ratio: 0.1
```

### 3.3 シーン分析データ構造
```yaml
scene_analytics:
  episode_number: 1
  total_scenes: 12

  scene_type_distribution:
    encounter: 2
    battle: 3
    dialogue: 4
    description: 3

  character_appearances:
    - character: "主人公"
      scene_count: 12
      screen_time_ratio: 0.95
    - character: "ヒロイン"
      scene_count: 8
      screen_time_ratio: 0.45

  emotional_summary:
    average_intensity: 6.5
    peak_scenes:
      - scene_id: "scene_008"
        intensity: 10
    valley_scenes:
      - scene_id: "scene_003"
        intensity: 2

  pacing_analysis:
    fast_paced_ratio: 0.4
    slow_paced_ratio: 0.3
    medium_paced_ratio: 0.3

  scene_connections:
    total_connections: 23
    foreshadowing_count: 8
    callback_count: 5
    parallel_count: 10
```

## 4. インターフェース設計

### 4.1 基本インターフェース
```python
class SceneManagementRepository(ABC):
    @abstractmethod
    def save_scene(self, project_name: str, scene: Scene) -> None:
        """シーンを保存"""
        pass

    @abstractmethod
    def get_scene(self, project_name: str, scene_id: str) -> Optional[Scene]:
        """シーンIDでシーンを取得"""
        pass

    @abstractmethod
    def get_scenes_by_episode(self, project_name: str, episode_number: int) -> List[Scene]:
        """エピソード番号でシーン一覧を取得"""
        pass

    @abstractmethod
    def update_scene(self, project_name: str, scene_id: str, updates: Dict[str, Any]) -> None:
        """シーンを更新"""
        pass

    @abstractmethod
    def delete_scene(self, project_name: str, scene_id: str) -> None:
        """シーンを削除"""
        pass
```

### 4.2 検索・フィルタリングインターフェース
```python
class SceneSearchRepository(ABC):
    @abstractmethod
    def search_scenes(self, project_name: str, criteria: SceneSearchCriteria) -> List[Scene]:
        """条件に基づいてシーンを検索"""
        pass

    @abstractmethod
    def find_scenes_by_character(self, project_name: str, character_name: str) -> List[Scene]:
        """キャラクター名でシーンを検索"""
        pass

    @abstractmethod
    def find_scenes_by_location(self, project_name: str, location: str) -> List[Scene]:
        """場所でシーンを検索"""
        pass

    @abstractmethod
    def find_related_scenes(self, project_name: str, scene_id: str, relation_type: Optional[str] = None) -> List[Scene]:
        """関連シーンを検索"""
        pass
```

### 4.3 テンプレート管理インターフェース
```python
class SceneTemplateRepository(ABC):
    @abstractmethod
    def get_template(self, template_id: str) -> Optional[SceneTemplate]:
        """テンプレートを取得"""
        pass

    @abstractmethod
    def list_templates(self, category: Optional[str] = None) -> List[SceneTemplate]:
        """テンプレート一覧を取得"""
        pass

    @abstractmethod
    def save_custom_template(self, project_name: str, template: SceneTemplate) -> None:
        """カスタムテンプレートを保存"""
        pass

    @abstractmethod
    def create_scene_from_template(self, template_id: str, parameters: Dict[str, Any]) -> Scene:
        """テンプレートからシーンを生成"""
        pass
```

### 4.4 分析インターフェース
```python
class SceneAnalyticsRepository(ABC):
    @abstractmethod
    def get_scene_statistics(self, project_name: str, episode_number: Optional[int] = None) -> SceneStatistics:
        """シーン統計を取得"""
        pass

    @abstractmethod
    def analyze_emotional_flow(self, project_name: str, episode_number: int) -> EmotionalFlowAnalysis:
        """感情曲線分析を実行"""
        pass

    @abstractmethod
    def analyze_character_distribution(self, project_name: str) -> CharacterDistribution:
        """キャラクター出現分布を分析"""
        pass

    @abstractmethod
    def generate_scene_report(self, project_name: str, report_type: str) -> SceneReport:
        """シーンレポートを生成"""
        pass
```

## 5. 実装詳細

### 5.1 YAMLファイル構成
```
プロジェクト/
├── 50_管理資料/
│   ├── シーン管理.yaml         # メインのシーン管理ファイル
│   ├── シーンテンプレート.yaml  # カスタムテンプレート
│   └── シーン分析/
│       ├── 第001話_分析.yaml
│       └── 全体分析.yaml
```

### 5.2 エラーハンドリング
- `SceneNotFoundError`: シーンが見つからない場合
- `InvalidSceneDataError`: シーンデータが不正な場合
- `SceneRelationError`: シーン関係に矛盾がある場合
- `TemplateParameterError`: テンプレートパラメータエラー

### 5.3 パフォーマンス考慮事項
- シーンデータの遅延読み込み
- 頻繁にアクセスされるシーンのキャッシュ
- 大量シーンの分割保存
- インデックスファイルによる高速検索

## 6. 使用例

### 6.1 シーン作成の例
```python
# リポジトリのインスタンス化
repo = YamlSceneManagementRepository()

# 新規シーン作成
scene = Scene(
    scene_id="scene_001",
    episode_number=1,
    scene_number=1,
    title="運命の出会い",
    type="encounter",
    metadata=SceneMetadata(
        location="王都の市場",
        time="朝",
        weather="晴れ",
        characters=[
            Character(name="主人公", role="protagonist"),
            Character(name="ヒロイン", role="heroine")
        ]
    )
)

# シーン保存
repo.save_scene("転生したら最強の魔法使いだった件", scene)
```

### 6.2 シーン検索の例
```python
# キャラクターでシーン検索
scenes = repo.find_scenes_by_character(
    "転生したら最強の魔法使いだった件",
    "ヒロイン"
)

# 関連シーン検索
related = repo.find_related_scenes(
    "転生したら最強の魔法使いだった件",
    "scene_001",
    relation_type="foreshadowing"
)
```

### 6.3 テンプレート使用の例
```python
# 戦闘シーンテンプレートから生成
scene = repo.create_scene_from_template(
    "battle_scene",
    parameters={
        "intensity": 8,
        "participants": ["主人公", "魔王"],
        "location": "魔王城謁見の間"
    }
)
```

## 7. テスト要件

### 7.1 ユニットテスト
- CRUD操作の正常系・異常系
- 検索機能の網羅的テスト
- テンプレート機能のテスト
- 分析機能の精度検証

### 7.2 統合テスト
- 大量シーンでのパフォーマンステスト
- 同時アクセス時の整合性テスト
- ファイル破損時の復旧テスト

### 7.3 E2Eテスト
- シーン作成から分析までの一連フロー
- テンプレートベースの執筆ワークフロー
- シーン関係性の可視化フロー

## 8. セキュリティ考慮事項

### 8.1 データ保護
- シーンデータのバックアップ自動化
- 削除操作の確認プロセス
- 重要シーンの保護フラグ

### 8.2 アクセス制御
- プロジェクトレベルのアクセス制限
- 読み取り専用モード
- 変更履歴の追跡

## 9. 移行計画

### 9.1 既存データの移行
- 旧形式シーンデータの変換スクリプト
- 段階的移行のサポート
- ロールバック機能

### 9.2 互換性維持
- 旧APIの一時的サポート
- 非推奨警告の実装
- 移行ガイドの提供

## 10. 今後の拡張性

### 10.1 機能拡張の可能性
- AIによるシーン自動生成
- シーン間の自動接続提案
- 感情曲線の自動最適化
- マルチメディア要素の統合

### 10.2 統合の可能性
- エピソード管理システムとの連携
- 品質チェックシステムとの統合
- 読者反応データとの相関分析

## 11. 参考資料

### 11.1 関連仕様書
- Domain層 Scene エンティティ仕様書
- Application層 SceneManagementUseCase 仕様書
- プロット管理システム仕様書

### 11.2 設計パターン
- Repositoryパターン
- Factory Method パターン（テンプレート）
- Observer パターン（シーン更新通知）
