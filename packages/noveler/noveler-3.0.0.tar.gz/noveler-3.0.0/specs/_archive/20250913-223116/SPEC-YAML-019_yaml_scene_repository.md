# YAMLシーンリポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、シーンデータのYAMLファイルベース永続化を提供する。

### 1.2 スコープ
- シーンデータの作成・保存・検索・削除の完全な永続化機能
- 重要シーン設計・感覚描写・演出指示の管理
- シーン間の関係性と構造の分析
- レガシーシステムとの互換性確保

### 1.3 アーキテクチャ位置
```
Domain Layer
├── SceneRepository (Interface) ← Infrastructure Layer
└── Scene (Entity)              └── YamlSceneRepository (Implementation)
```

## 2. 機能仕様

### 2.1 基本CRUD操作
```python
# 保存
def save(scene: Scene, project_id: str) -> None

# 検索
def find_by_id(scene_id: str, project_id: str) -> Scene | None
def find_by_episode(project_id: str, episode_number: int) -> list[Scene]
def find_all(project_id: str) -> list[Scene]

# 存在確認
def exists(scene_id: str, project_id: str) -> bool

# 更新
def update_scene_content(scene_id: str, project_id: str, content: dict) -> bool
def update_sensory_description(scene_id: str, project_id: str, sensory_data: dict) -> bool

# 削除
def delete(scene_id: str, project_id: str) -> bool
def delete_by_episode(project_id: str, episode_number: int) -> int
```

### 2.2 高度な検索機能
```python
# シーンタイプ別検索
def find_by_scene_type(project_id: str, scene_type: str) -> list[Scene]

# 重要度別検索
def find_by_importance(
    project_id: str,
    min_importance: int,
    max_importance: int = 10
) -> list[Scene]

# キャラクター登場シーン検索
def find_by_characters(
    project_id: str,
    character_names: list[str],
    match_all: bool = False
) -> list[Scene]

# 感覚描写種類別検索
def find_by_sensory_types(
    project_id: str,
    sensory_types: list[str]
) -> list[Scene]

# タグ検索
def find_by_tags(project_id: str, tags: list[str]) -> list[Scene]

# 期間検索
def find_by_date_range(
    project_id: str,
    start_date: datetime,
    end_date: datetime
) -> list[Scene]
```

### 2.3 シーン分析機能
```python
# シーン統計取得
def get_scene_statistics(project_id: str) -> dict[str, Any]
# 戻り値例:
{
    "total_scenes": 45,
    "scenes_by_type": {
        "アクション": 15,
        "対話": 20,
        "心理描写": 10
    },
    "importance_distribution": {
        "高重要度(8-10)": 12,
        "中重要度(5-7)": 23,
        "低重要度(1-4)": 10
    },
    "sensory_usage": {
        "視覚": 42,
        "聴覚": 38,
        "触覚": 25,
        "嗅覚": 18,
        "味覚": 12
    }
}

# シーン構造分析
def analyze_scene_structure(
    project_id: str,
    episode_range: tuple[int, int] | None = None
) -> dict[str, Any]

# シーン間関係分析
def analyze_scene_relationships(project_id: str) -> dict[str, Any]
```

### 2.4 演出・感覚描写機能
```python
# 感覚描写の強化提案
def suggest_sensory_enhancements(
    scene_id: str,
    project_id: str
) -> list[dict[str, Any]]

# 演出指示の検証
def validate_direction_instructions(
    scene_id: str,
    project_id: str
) -> tuple[bool, list[str]]

# シーンの完成度評価
def evaluate_scene_completeness(
    scene_id: str,
    project_id: str
) -> dict[str, Any]
```

### 2.5 一括操作・管理機能
```python
# 一括シーン更新
def bulk_update_scenes(
    project_id: str,
    updates: dict[str, Any],
    filter_criteria: dict | None = None
) -> int

# シーンテンプレートの適用
def apply_scene_template(
    scene_id: str,
    project_id: str,
    template_name: str
) -> bool

# シーンの複製
def duplicate_scene(
    source_scene_id: str,
    project_id: str,
    new_scene_id: str | None = None
) -> Scene
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/                  # シーンデータ
│   ├── 重要シーン.yaml            # メインのシーンデータ
│   ├── シーン分析結果.yaml        # 分析結果
│   └── シーンテンプレート/        # テンプレート（任意）
│       ├── アクションシーン.yaml
│       ├── 対話シーン.yaml
│       └── 心理描写シーン.yaml
└── backup/                       # バックアップ（任意）
    └── 20250721_143022/
        └── 重要シーン.yaml
```

### 3.2 重要シーンYAML構造
```yaml
metadata:
  project_name: "転生したら最強の魔法使いだった件"
  last_updated: "2025-07-21T14:30:22"
  version: "1.0"

scenes:
  - scene_id: "scene_001_001"
    episode_number: 1
    scene_number: 1
    title: "異世界転移の瞬間"
    scene_type: "転換点"
    importance: 10

    # 基本情報
    basic_info:
      location: "現実世界の教室→異世界の森"
      time_setting: "昼間→夕暮れ"
      duration_minutes: 3
      characters:
        - name: "田中太郎"
          role: "主人公"
          emotional_state: "混乱→驚愕"
        - name: "クラスメート達"
          role: "転移対象"
          emotional_state: "恐怖"

    # 詳細設計
    detailed_design:
      opening: "数学の授業中、突然教室が白い光に包まれる"
      climax: "光が消えたとき、そこは見知らぬ森だった"
      resolution: "転移したことを理解し、周囲を警戒する"

      key_moments:
        - timing: "00:30"
          event: "異変の始まり - 机が振動し始める"
          importance: 8
        - timing: "01:45"
          event: "転移の発動 - 白い光が教室を包む"
          importance: 10
        - timing: "02:30"
          event: "新世界への到着 - 森の中に立つ"
          importance: 9

    # 感覚描写詳細
    sensory_descriptions:
      visual:
        - element: "転移の光"
          description: "眩しすぎて目を開けていられない純白の光"
          intensity: 10
          narrative_purpose: "非現実感の演出"
        - element: "異世界の森"
          description: "見たことのない巨大な木々と色鮮やかな植物"
          intensity: 8
          narrative_purpose: "新世界への導入"

      auditory:
        - element: "転移時の音"
          description: "低く響く唸り声のような振動音"
          intensity: 7
          narrative_purpose: "不安感の醸成"
        - element: "森の音"
          description: "未知の鳥の鳴き声と風が葉を揺らす音"
          intensity: 6
          narrative_purpose: "異世界感の演出"

      tactile:
        - element: "転移時の感覚"
          description: "全身を包む電流のようなピリピリした感覚"
          intensity: 8
          narrative_purpose: "身体的リアリティ"
        - element: "森の空気"
          description: "湿度が高く、肌にまとわりつくような空気"
          intensity: 5
          narrative_purpose: "環境の実感"

      olfactory:
        - element: "森の香り"
          description: "青々とした植物の香りと土の匂い"
          intensity: 6
          narrative_purpose: "異世界の実在感"

      gustatory:
        - element: "空気の味"
          description: "わずかに甘みのある清浄な空気"
          intensity: 3
          narrative_purpose: "新鮮さの表現"

    # 演出指示
    direction_instructions:
      pacing:
        overall_rhythm: "徐々に加速→急停止→ゆっくり再開"
        key_beats:
          - timing: "冒頭"
            instruction: "日常的なペースでゆっくりと"
          - timing: "異変発生"
            instruction: "急激にテンポアップ"
          - timing: "転移完了"
            instruction: "静寂を演出し、ゆっくりと状況説明"

      emotional_arc:
        protagonist_journey:
          - phase: "日常"
            emotion: "退屈"
            intensity: 2
          - phase: "異変察知"
            emotion: "困惑"
            intensity: 5
          - phase: "転移中"
            emotion: "恐怖"
            intensity: 9
          - phase: "転移完了"
            emotion: "驚愕"
            intensity: 10

      visual_presentation:
        color_palette:
          - scene_phase: "現実世界"
            dominant_colors: ["灰色", "白", "茶色"]
            mood: "単調"
          - scene_phase: "転移"
            dominant_colors: ["純白", "金色"]
            mood: "神秘的"
          - scene_phase: "異世界"
            dominant_colors: ["緑", "青", "オレンジ"]
            mood: "生命力溢れる"

      sound_design:
        ambient_sounds:
          - phase: "現実世界"
            sounds: ["時計の秒針", "鉛筆の音", "ざわめき"]
          - phase: "転移"
            sounds: ["低周波の唸り", "風切り音", "エネルギー音"]
          - phase: "異世界"
            sounds: ["鳥の鳴き声", "風の音", "葉擦れの音"]

    # メタ情報
    meta_information:
      creation_date: "2025-07-15T10:30:00"
      last_revision: "2025-07-21T14:30:22"
      revision_count: 3
      author_notes: "転移シーンは作品全体の基調を決める重要な場面"

      tags:
        - "重要シーン"
        - "転換点"
        - "異世界転移"
        - "導入部"
        - "世界観説明"

      related_scenes:
        - scene_id: "scene_001_005"
          relationship: "直接的な続き"
          description: "転移後の初めての魔法発見"
        - scene_id: "scene_005_012"
          relationship: "呼応・対比"
          description: "現実世界への一時帰還シーン"

      plot_significance:
        main_plot: "物語の出発点として機能"
        character_development: "主人公の成長の起点"
        world_building: "異世界の第一印象を決定"
        theme_establishment: "冒険と成長のテーマ設定"

# シーン分析結果
scene_analysis:
  completion_score: 92.0
  sensory_richness: 8.5
  emotional_impact: 9.2
  plot_integration: 8.8

  strengths:
    - "感覚描写の豊富さ"
    - "感情の変遷の明確さ"
    - "演出指示の具体性"

  improvement_suggestions:
    - category: "味覚描写"
      suggestion: "異世界の空気の味をより詳細に"
      priority: "low"
    - category: "キャラクター描写"
      suggestion: "クラスメートの個別反応を追加"
      priority: "medium"

updated_at: "2025-07-21T14:30:22"
```

### 3.3 シーンテンプレート構造
```yaml
# アクションシーン.yaml
template_metadata:
  name: "標準アクションシーン"
  category: "戦闘・アクション"
  description: "動的な戦闘や追跡シーンのテンプレート"

template_structure:
  basic_info:
    scene_type: "アクション"
    importance: "[5-10の範囲で設定]"
    duration_minutes: "[3-8分程度]"

  required_elements:
    - "明確な目標設定"
    - "障害・敵対要素"
    - "緊張感のある展開"
    - "結果・帰結"

  sensory_focus:
    priority_senses:
      - "視覚（動きの描写）"
      - "聴覚（効果音・衝撃音）"
      - "触覚（痛み・衝撃）"
    optional_senses:
      - "嗅覚（硝煙・血の匂い）"

  direction_guidelines:
    pacing: "高速テンポ、短い文章"
    tension_curve: "急上昇→維持→急降下"
    visual_style: "動きのある描写重視"

  common_patterns:
    opening_patterns:
      - "突然の襲撃"
      - "挑発的な対話"
      - "追跡の開始"
    resolution_patterns:
      - "明確な勝敗"
      - "一時的な逃亡"
      - "予期しない展開"
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List
import uuid

# ドメイン層
from domain.entities.scene import Scene, SensoryDescription, DirectionInstruction
from domain.repositories.scene_repository import SceneRepository
from domain.value_objects.scene_importance import SceneImportance
from domain.value_objects.scene_id import SceneId
```

### 4.2 エラーハンドリング
```python
# カスタム例外
class SceneRepositoryError(Exception):
    pass

class SceneNotFoundError(SceneRepositoryError):
    pass

class InvalidSceneDataError(SceneRepositoryError):
    pass

class SceneValidationError(SceneRepositoryError):
    pass

class SensoryDescriptionError(SceneRepositoryError):
    pass
```

## 5. パフォーマンス要件

### 5.1 応答時間
- 単一シーン検索: 30ms以内
- エピソード別シーン検索: 100ms以内
- 全シーン読み込み: 500ms以内（100シーン）
- 保存操作: 50ms以内

### 5.2 メモリ使用量
- 単一シーン: 5MB以内
- 全シーン同時読み込み: 200MB以内
- 分析処理時: 300MB以内

### 5.3 同時実行性
- 読み取り操作: 並行実行可能
- 書き込み操作: ファイルロック機構で排他制御
- 分析処理: 並行実行可能

## 6. 品質保証

### 6.1 データ整合性
- シーンID の一意性保証
- エピソード番号との整合性確認
- 感覚描写データの妥当性検証
- 演出指示の構文チェック

### 6.2 エラー回復
- 破損したYAMLファイルの自動修復
- 欠損したシーンデータの検出・通知
- バックアップからの自動復元オプション
- 部分的なシーン保存による中断復旧

### 6.3 データ検証
- 必須フィールドの存在確認
- 数値範囲の妥当性チェック（重要度1-10等）
- 文字列長の制限チェック
- 関連シーンの参照整合性確認

## 7. セキュリティ

### 7.1 アクセス制御
- ファイルシステム権限に基づくアクセス制御
- プロジェクトID単位でのデータ分離
- シーン編集権限の管理

### 7.2 データ保護
- エンコーディング: UTF-8統一
- 機密情報の除去処理
- バックアップデータの暗号化
- 一時ファイルの安全な削除

## 8. 互換性

### 8.1 レガシーシステム
- 既存のシーンデータとの完全互換
- 段階的移行サポート
- 旧フォーマットの自動変換
- 互換性レイヤーの提供

### 8.2 将来拡張性
- 新しいシーンタイプの動的追加
- VR/AR対応の空間情報拡張
- 多メディア要素（音声・画像）の統合準備
- AIベースの自動シーン生成対応

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
project_path = Path("/path/to/project")
repo = YamlSceneRepository(project_path)

# シーン作成・保存
scene = Scene(
    scene_id=SceneId("scene_001_001"),
    episode_number=1,
    title="異世界転移の瞬間",
    scene_type="転換点",
    importance=SceneImportance(10)
)
repo.save(scene, "project-001")

# 検索
episode_scenes = repo.find_by_episode("project-001", 1)
important_scenes = repo.find_by_importance("project-001", 8, 10)

# 統計取得
stats = repo.get_scene_statistics("project-001")
print(f"総シーン数: {stats['total_scenes']}")
```

### 9.2 高度な検索・分析例
```python
# キャラクター登場シーン検索
character_scenes = repo.find_by_characters(
    "project-001", ["田中太郎", "エルフ姫"], match_all=False
)

# 感覚描写分析
sensory_scenes = repo.find_by_sensory_types(
    "project-001", ["visual", "auditory"]
)

# シーン構造分析
structure_analysis = repo.analyze_scene_structure("project-001", (1, 5))
print(f"シーン密度: {structure_analysis['scene_density']}")
```

### 9.3 演出・強化機能の活用例
```python
# 感覚描写の強化提案
enhancements = repo.suggest_sensory_enhancements("scene_001_001", "project-001")
for enhancement in enhancements:
    print(f"提案: {enhancement['suggestion']}")

# シーンの完成度評価
completeness = repo.evaluate_scene_completeness("scene_001_001", "project-001")
print(f"完成度スコア: {completeness['completion_score']}")

# テンプレート適用
template_applied = repo.apply_scene_template(
    "scene_002_003", "project-001", "アクションシーン"
)
```

## 10. テスト仕様

### 10.1 単体テスト
- 各CRUDメソッドの動作確認
- 検索機能の正確性テスト
- 分析機能のアルゴリズムテスト
- エラーケースの処理確認

### 10.2 統合テスト
- 実際のファイルシステムでの動作確認
- 大量シーンデータでの性能テスト
- 同時実行テスト
- 他のリポジトリとの連携テスト

### 10.3 エラーシナリオ
- ディスク容量不足
- ファイル権限エラー
- 破損したYAMLファイル
- 不正な感覚描写データ
- メモリ不足状況

## 11. 運用・監視

### 11.1 ログ出力
- シーン操作（保存、削除）のログ記録
- エラー発生時の詳細ログ
- 分析処理の実行ログ
- パフォーマンス測定ログ

### 11.2 メトリクス
- シーン操作回数・実行時間の統計
- 分析処理の性能監視
- エラー発生率の監視
- ストレージ使用量の監視

### 11.3 アラート
- シーンデータの整合性エラー
- 分析処理の異常終了
- パフォーマンス劣化
- ディスク容量警告

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_scene_repository.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_scene_repository.py`

### 12.2 設計方針
- DDD原則の厳格な遵守
- シーンデータの豊富な表現力
- 感覚描写の体系的管理
- 演出指示の実用性重視

### 12.3 今後の改善点
- [ ] 3Dシーン可視化機能
- [ ] 音声・映像メディアの統合
- [ ] AI支援による自動感覚描写生成
- [ ] VR/AR環境でのシーンプレビュー
- [ ] 協調編集機能（複数人でのシーン作成）
