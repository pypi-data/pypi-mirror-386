# SPEC-EPISODE-013: EpisodeCompletion Entity Specification

## SPEC-EPISODE-007: エピソード完成エンティティ


## 概要
執筆完了エピソードのドメインエンティティ。集約ルートとして、キャラクター成長記録、重要シーン記録、伏線記録を管理する。

## エンティティ構成

### CharacterGrowthRecord
キャラクター成長記録エンティティ

#### プロパティ
- `character_name: str` - キャラクター名
- `episode_number: int` - エピソード番号
- `growth_type: GrowthType` - 成長タイプ
- `description: str` - 成長の説明
- `importance: str` - 重要度（high/medium/low）
- `auto_detected: bool` - 自動検出フラグ
- `recorded_at: datetime` - 記録日時

#### メソッド
- `from_event(episode_number: int, event: CharacterGrowthEvent) -> CharacterGrowthRecord` - イベントから記録を作成
- `to_persistence_dict() -> dict[str, Any]` - 永続化用辞書変換

### ImportantSceneRecord
重要シーン記録エンティティ

#### プロパティ
- `episode_number: int` - エピソード番号
- `scene_id: str` - シーンID
- `scene_type: SceneType` - シーンタイプ
- `description: str` - 説明
- `emotion_level: str` - 感情レベル（high/medium/low）
- `tags: list[str]` - タグリスト
- `recorded_at: datetime` - 記録日時

#### メソッド
- `from_scene(episode_number: int, scene: ImportantScene) -> ImportantSceneRecord` - シーンから記録を作成
- `calculate_importance() -> str` - 重要度計算（critical/high/medium）
- `to_persistence_dict() -> dict[str, Any]` - 永続化用辞書変換

### ForeshadowingRecord
伏線記録エンティティ

#### プロパティ
- `foreshadowing_id: str` - 伏線ID
- `description: str` - 伏線の説明
- `status: ForeshadowingStatus` - ステータス（PLANNED/PLANTED/RESOLVED/ABANDONED）
- `planted_episode: int | None` - 仕込みエピソード番号
- `resolved_episode: int | None` - 回収エピソード番号
- `updated_at: datetime` - 更新日時

#### メソッド
- `plant(episode_number: int)` - 伏線を仕込む
- `resolve(episode_number: int)` - 伏線を回収
- `abandon()` - 伏線を放棄
- `to_persistence_dict() -> dict[str, Any]` - 永続化用辞書変換

### CompletedEpisode（集約ルート）
完了エピソードエンティティ

#### プロパティ
- `episode_number: int` - エピソード番号
- `status: str` - ステータス
- `completed_at: datetime` - 完了日時
- `quality_score: Decimal` - 品質スコア
- `word_count: int` - 文字数
- `plot_data: dict` - プロットデータ
- `character_growth_records: list[CharacterGrowthRecord]` - キャラクター成長記録
- `important_scenes: list[ImportantSceneRecord]` - 重要シーン記録
- `foreshadowing_records: list[ForeshadowingRecord]` - 伏線記録

#### メソッド
- `create_from_event(event: EpisodeCompletionEvent) -> CompletedEpisode` - イベントから作成
- `add_character_growth(event: CharacterGrowthEvent)` - キャラクター成長を追加
- `add_important_scene(scene: ImportantScene)` - 重要シーンを追加
- `plant_foreshadowing(foreshadowing_id: str, description: str)` - 伏線を仕込む
- `resolve_foreshadowing(foreshadowing_id: str)` - 伏線を回収
- `extract_from_plot_data()` - プロットデータから情報を抽出
- `has_quality_warning() -> bool` - 品質警告の有無
- `get_warnings() -> list[str]` - 警告リストを取得
- `get_domain_events() -> list[dict[str, Any]]` - ドメインイベントを取得
- `clear_domain_events()` - ドメインイベントをクリア
- `to_persistence_dict() -> dict[str, Any]` - 永続化用辞書変換

## ビジネスルール

### CharacterGrowthRecord
1. イベントから記録作成時は現在時刻で記録される
2. 永続化時は話数形式（「第N話」）で保存される

### ImportantSceneRecord
1. 重要度計算は感情レベルとシーンタイプを基に行われる
   - 感情レベル: high(3), medium(2), low(1)
   - シーンタイプ: TURNING_POINT/CLIMAX(3), REVELATION/CHARACTER_MOMENT(2), その他(1)
   - 合計スコア: 5以上(critical), 3以上(high), その他(medium)

### ForeshadowingRecord
1. 伏線は計画→仕込み→回収の順でステータス遷移する
2. 仕込み済みでない伏線は回収できない
3. 計画済みでない伏線は仕込めない

### CompletedEpisode
1. 作成時に品質チェックを自動実行する
2. 品質警告条件:
   - quality_score < 80: low_quality
   - word_count < 3000: low_word_count
   - word_count > 8000: high_word_count
3. ドメインイベントの発行:
   - エピソード完了: EpisodeCompleted
   - キャラクター成長追加: CharacterGrowthAdded
   - 重要シーン追加: ImportantSceneAdded
   - 伏線仕込み: ForeshadowingPlanted
   - 伏線回収: ForeshadowingResolved

## 例外処理
- `EpisodeCompletionError`: 伏線の状態遷移エラー時に発生

## 依存関係
- `domain.exceptions.EpisodeCompletionError`
- `domain.value_objects.episode_completion.*`
