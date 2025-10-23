# SPEC-EPISODE-012: EpisodeCompletion 値オブジェクト群仕様書

## SPEC-EPISODE-006: エピソード完成処理


## 1. 目的
エピソード執筆完了に関連する情報を管理する値オブジェクト群。イベント情報、成長記録、品質チェック結果などを不変オブジェクトとして扱う。

## 2. 前提条件
- すべての値オブジェクトは不変（frozen=True）
- リストは自動的にタプルに変換して不変性を保証
- 適切なバリデーションを実施

## 3. 主要コンポーネント

### 3.1 列挙型（Enum）

#### GrowthType（キャラクター成長タイプ）
- REALIZATION: 気づき・理解
- SKILL_ACQUISITION: スキル習得
- EMOTIONAL_CHANGE: 感情変化
- RELATIONSHIP_CHANGE: 関係性変化
- WORLDVIEW_CHANGE: 世界観変化

#### SceneType（重要シーンタイプ）
- TURNING_POINT: ターニングポイント
- EMOTIONAL_PEAK: 感情的高まり
- ACTION_SEQUENCE: アクションシーケンス
- REVELATION: 真実の開示
- CLIMAX: クライマックス
- CHARACTER_MOMENT: キャラクターの見せ場

#### ForeshadowingStatus（伏線ステータス）
- PLANNED: 計画中
- PLANTED: 仕込み済み
- RESOLVED: 回収済み
- ABANDONED: 放棄

### 3.2 値オブジェクト

#### EpisodeCompletionEvent
- **必須フィールド**: episode_number, completed_at, quality_score, word_count
- **検証**:
  - episode_number > 0
  - 0 ≤ quality_score ≤ 100
  - word_count ≥ 0

#### CharacterGrowthEvent
- **必須フィールド**: character_name, growth_type, description
- **デフォルト**: importance="medium", auto_detected=False
- **検証**:
  - character_nameは空白不可
  - importanceは["low", "medium", "high"]のいずれか

#### ImportantScene
- **必須フィールド**: scene_id, scene_type, description
- **デフォルト**: emotion_level="medium", tags=()
- **特徴**: tagsはリストでもタプルに自動変換

#### CompletionStatus
- **定数**: WRITTEN="執筆済み", REVISED="推敲済み", PUBLISHED="公開済み"
- **メソッド**:
  - written(): 執筆済みステータス作成
  - revised(): 推敲済みステータス作成
  - published(): 公開済みステータス作成
  - can_transition_to(other): 状態遷移の妥当性チェック
- **状態遷移**:
  - 執筆済み → 推敲済み、公開済み
  - 推敲済み → 公開済み
  - 公開済み → なし

#### ImplementationDiff
- **必須フィールド**: planned_content, actual_content, major_changes, minor_changes
- **メソッド**:
  - has_differences(): 差分の有無
  - is_major_change(): 大きな変更の有無

#### QualityCheckResult
- **必須フィールド**: check_date, overall_score, category_scores, issues, warnings, suggestions
- **メソッド**:
  - has_issues(): 問題の有無
  - is_passing(threshold=80): 合格判定

#### ForeshadowingUpdate
- **必須フィールド**: foreshadowing_id, description, update_type, related_episodes
- **検証**:
  - update_typeは["planted", "resolved", "modified", "new"]のいずれか
  - effectivenessは["excellent", "good", "fair", "poor"]のいずれか（オプション）

## 4. 実装チェックリスト
- [x] 列挙型の定義
- [x] 各値オブジェクトの不変性保証
- [x] 必須フィールドの検証
- [x] リストからタプルへの自動変換
- [x] ビジネスメソッドの実装
- [ ] テストケース作成
