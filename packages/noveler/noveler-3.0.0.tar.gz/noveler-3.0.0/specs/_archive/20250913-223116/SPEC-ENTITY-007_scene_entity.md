# Scene エンティティ仕様書

## SPEC-SCENE-001: シーンエンティティ


**作成日**: 2025-01-22
**バージョン**: 1.0
**カテゴリ**: Domain Entity
**依存関係**: SceneSetting, SceneDirection, SceneCategory, ImportanceLevel

## 概要

重要シーンのドメインエンティティ。小説執筆における重要なシーンの詳細設計、演出指示、品質管理を統合的に管理し、シーンの完成度評価と品質向上をサポートする。

## ドメインコンテキスト

**問題領域**: 重要シーンの設計と品質管理
- シーンカテゴリ別の管理（クライマックス、感情、ロマンス、アクション等）
- 重要度レベル別の優先制御（S/A/B/C）
- 設定情報と演出指示の統合管理
- 登場キャラクターと重要要素の追跡
- 執筆ノートと品質チェックリストの管理
- シーン完成度の定量的評価

**解決アプローチ**: リッチドメインエンティティによる包括的シーン管理
- dataclass基盤の構造化データ管理
- 値オブジェクトとの協調による設計情報管理
- 更新時刻の自動追跡による変更履歴管理
- 完成度スコア計算による品質可視化
- 辞書変換による永続化サポート

## エンティティ設計

### 1. Scene（集約ルート）

重要シーンの完全なライフサイクルと詳細設計を管理。

**責務**:
- シーン基本情報の管理（ID、タイトル、カテゴリ、重要度）
- 設定情報と演出指示の統合管理
- 登場キャラクターと重要要素の追跡
- 執筆ノートと品質チェックの管理
- 完成度評価と重要度判定
- データ永続化のサポート

**ビジネス不変条件**:
1. **シーンID**: 必須、空文字列不可
2. **タイトル**: 必須、空文字列不可
3. **エピソード範囲**: 必須、空文字列不可
4. **カテゴリ**: SceneCategoryの有効値
5. **重要度**: ImportanceLevelの有効値
6. **更新時刻**: 変更時に自動更新
7. **リスト要素**: 重複排除（キャラクター、重要要素）

### 2. 列挙型定義

#### 2.1 SceneCategory
```python
class SceneCategory(Enum):
    CLIMAX = "climax_scenes"      # クライマックスシーン
    EMOTIONAL = "emotional_scenes" # 感情シーン
    ROMANCE = "romance_scenes"     # ロマンスシーン
    ACTION = "action_scenes"       # アクションシーン
    MYSTERY = "mystery_scenes"     # ミステリーシーン
    COMEDY = "comedy_scenes"       # コメディシーン
    DAILY = "daily_scenes"         # 日常シーン
```

#### 2.2 ImportanceLevel
```python
class ImportanceLevel(Enum):
    S = "S"  # 最重要（物語の核心）
    A = "A"  # 重要（大きな転換点）
    B = "B"  # 中程度（キャラ成長等）
    C = "C"  # 軽微（雰囲気作り等）
```

### 3. ビジネスルール

#### 3.1 初期化と検証
```python
def __post_init__(self) -> None:
    self._validate()

def _validate(self) -> None:
    # BR-1: シーンIDの必須検証
    if not self.scene_id or not self.scene_id.strip():
        raise ValueError("scene_id は必須です")

    # BR-2: タイトルの必須検証
    if not self.title or not self.title.strip():
        raise ValueError("title は必須です")

    # BR-3: エピソード範囲の必須検証
    if not self.episode_range or not self.episode_range.strip():
        raise ValueError("episode_range は必須です")
```

#### 3.2 設定情報管理
```python
# BR-4: 設定情報の更新と時刻記録
def set_setting(self, setting: SceneSetting) -> None:
    self.setting = setting
    self.updated_at = datetime.now()

# BR-5: 演出指示の更新と時刻記録
def set_direction(self, direction: SceneDirection) -> None:
    self.direction = direction
    self.updated_at = datetime.now()
```

#### 3.3 要素管理（重複排除）
```python
# BR-6: キャラクター重複排除
def add_character(self, character_name: str) -> None:
    if character_name and character_name not in self.characters:
        self.characters.append(character_name)
        self.updated_at = datetime.now()

# BR-7: 重要要素重複排除
def add_key_element(self, element: str) -> None:
    if element and element not in self.key_elements:
        self.key_elements.append(element)
        self.updated_at = datetime.now()
```

#### 3.4 品質管理
```python
# BR-8: 品質チェック項目の重複排除
def add_quality_check(self, category: str, check_item: str) -> None:
    if category not in self.quality_checklist:
        self.quality_checklist[category] = []

    if check_item not in self.quality_checklist[category]:
        self.quality_checklist[category].append(check_item)
        self.updated_at = datetime.now()
```

#### 3.5 完成度評価
```python
# BR-9: 8項目による完成度スコア計算（0.0-1.0）
def get_completion_score(self) -> float:
    score = 0.0
    total_criteria = 8

    # 各項目の存在チェック
    if self.title and self.title.strip(): score += 1
    if self.episode_range and self.episode_range.strip(): score += 1
    if self.setting: score += 1
    if self.direction: score += 1
    if self.characters: score += 1
    if self.key_elements: score += 1
    if self.writing_notes: score += 1
    if self.quality_checklist: score += 1

    return score / total_criteria
```

#### 3.6 重要度判定
```python
# BR-10: S/Aレベルをクリティカルと判定
def is_critical(self) -> bool:
    return self.importance_level in [ImportanceLevel.S, ImportanceLevel.A]
```

## テスト要求仕様

### 1. 初期化と検証テスト

#### 1.1 正常な初期化
- **TEST-1**: `test_valid_initialization_required_fields_only`
  - 必須フィールドのみでの正常初期化
  - デフォルト値の確認
- **TEST-2**: `test_initialization_with_all_fields`
  - 全フィールド指定での初期化

#### 1.2 必須フィールド検証
- **TEST-3**: `test_empty_scene_id_raises_error`
  - 空のscene_idでValueError
- **TEST-4**: `test_whitespace_scene_id_raises_error`
  - 空白のみのscene_idでValueError
- **TEST-5**: `test_empty_title_raises_error`
  - 空のtitleでValueError
- **TEST-6**: `test_whitespace_title_raises_error`
  - 空白のみのtitleでValueError
- **TEST-7**: `test_empty_episode_range_raises_error`
  - 空のepisode_rangeでValueError
- **TEST-8**: `test_whitespace_episode_range_raises_error`
  - 空白のみのepisode_rangeでValueError

#### 1.3 列挙型検証
- **TEST-9**: `test_all_scene_categories_accepted`
  - 全SceneCategoryの受け入れ確認
- **TEST-10**: `test_all_importance_levels_accepted`
  - 全ImportanceLevelの受け入れ確認

### 2. 設定情報管理テスト

#### 2.1 設定情報の設定
- **TEST-11**: `test_set_setting_updates_field_and_time`
  - 設定情報の更新と時刻記録
- **TEST-12**: `test_set_direction_updates_field_and_time`
  - 演出指示の更新と時刻記録

#### 2.2 更新時刻の管理
- **TEST-13**: `test_updated_at_changes_on_modifications`
  - 各種更新時のupdated_at変更確認

### 3. 要素管理テスト

#### 3.1 キャラクター管理
- **TEST-14**: `test_add_character_normal_case`
  - 通常のキャラクター追加
- **TEST-15**: `test_add_character_duplicate_prevention`
  - 重複キャラクターの排除
- **TEST-16**: `test_add_character_empty_string_ignored`
  - 空文字列キャラクターの無視

#### 3.2 重要要素管理
- **TEST-17**: `test_add_key_element_normal_case`
  - 通常の重要要素追加
- **TEST-18**: `test_add_key_element_duplicate_prevention`
  - 重複要素の排除
- **TEST-19**: `test_add_key_element_empty_string_ignored`
  - 空文字列要素の無視

### 4. 執筆ノート管理テスト

#### 4.1 ノート設定
- **TEST-20**: `test_set_writing_note_various_types`
  - 様々な型の値の設定
- **TEST-21**: `test_set_writing_note_updates_time`
  - ノート設定時の時刻更新

### 5. 品質チェック管理テスト

#### 5.1 チェック項目追加
- **TEST-22**: `test_add_quality_check_new_category`
  - 新カテゴリでのチェック項目追加
- **TEST-23**: `test_add_quality_check_existing_category`
  - 既存カテゴリへのチェック項目追加
- **TEST-24**: `test_add_quality_check_duplicate_prevention`
  - 重複チェック項目の排除

### 6. 完成度評価テスト

#### 6.1 完成度スコア計算
- **TEST-25**: `test_completion_score_minimum_fields`
  - 最小フィールドでのスコア（2/8 = 0.25）
- **TEST-26**: `test_completion_score_all_fields`
  - 全フィールドでのスコア（8/8 = 1.0）
- **TEST-27**: `test_completion_score_partial_fields`
  - 部分フィールドでのスコア計算

#### 6.2 重要度判定
- **TEST-28**: `test_is_critical_s_level`
  - Sレベルでのクリティカル判定
- **TEST-29**: `test_is_critical_a_level`
  - Aレベルでのクリティカル判定
- **TEST-30**: `test_is_critical_b_c_levels`
  - B/Cレベルでの非クリティカル判定

### 7. データ変換テスト

#### 7.1 辞書変換
- **TEST-31**: `test_to_dict_minimal_scene`
  - 最小シーンの辞書変換
- **TEST-32**: `test_to_dict_full_scene`
  - 完全シーンの辞書変換
- **TEST-33**: `test_to_dict_includes_value_objects`
  - 値オブジェクトの変換確認

#### 7.2 辞書からの復元
- **TEST-34**: `test_from_dict_minimal_data`
  - 最小データからの復元
- **TEST-35**: `test_from_dict_full_data`
  - 完全データからの復元
- **TEST-36**: `test_from_dict_with_value_objects`
  - 値オブジェクト付きデータの復元

#### 7.3 往復変換
- **TEST-37**: `test_roundtrip_conversion`
  - to_dict → from_dict の往復変換確認

### 8. エッジケーステスト

#### 8.1 境界値テスト
- **TEST-38**: `test_unicode_fields`
  - Unicode文字のフィールド処理
- **TEST-39**: `test_large_data_handling`
  - 大量データの処理
- **TEST-40**: `test_special_characters_in_fields`
  - 特殊文字のフィールド処理

#### 8.2 時刻精度テスト
- **TEST-41**: `test_timestamp_precision`
  - タイムスタンプ精度の確認
- **TEST-42**: `test_created_updated_time_difference`
  - 作成時刻と更新時刻の差異確認

### 9. 統合テスト

#### 9.1 値オブジェクト統合
- **TEST-43**: `test_integration_with_scene_setting`
  - SceneSetting統合動作
- **TEST-44**: `test_integration_with_scene_direction`
  - SceneDirection統合動作

#### 9.2 複合操作
- **TEST-45**: `test_multiple_modifications_timeline`
  - 複数変更操作のタイムライン確認

## 実装上の注意点

### 1. 型安全性
- 全メソッドでの型ヒント必須
- Enum型の適切な使用
- Optional型の明示的指定

### 2. 不変性保護
- リスト要素の重複排除
- 更新時刻の自動管理
- 値オブジェクトの不変性維持

### 3. パフォーマンス
- 重複チェックの効率化
- 大量データ処理の最適化
- メモリ使用量の管理

### 4. 永続化サポート
- 完全な往復変換の保証
- 型情報の保持
- エラー耐性のある復元処理

## 関連仕様書

- **SceneSetting値オブジェクト**: `scene_setting.spec.md`
- **SceneDirection値オブジェクト**: `scene_direction.spec.md`
- **シーン管理ユースケース**: `scene_management_use_case.spec.md`

---
**更新履歴**:
- 2025-01-22: 初版作成（TDD+DDD原則準拠）
