---
spec_id: SPEC-WRITE-020
status: canonical
owner: bamboocity
last_reviewed: 2025-09-18
category: WRITE
tags: [design, conversation, tools]
requirements:
  - REQ-WRITE-DESIGN-005
---
# SPEC-WRITE-020: 会話・感情・情景設計 MCP ツール仕様書

## 1. 概要

### 1.1 目的
A38 執筆プロンプトガイドの STEPS 7〜11 に対応する設計支援ツール群（`design_conversations`, `track_emotions`, `design_scenes`, `design_senses`, `manage_props`, `get_conversation_context`, `export_design_data`）の仕様を定義し、段階執筆フローと整合させる。

### 1.2 対象コンポーネント
- MCP 実装: `src/mcp_servers/noveler/tools/conversation_design_tool.py`
- ドメインサービス: `src/noveler/domain/services/conversation_design_service.py`
- 付随 ValueObjects: `src/noveler/domain/value_objects/conversation_id.py`
- 設計データ出力: `.noveler/design/`

> TenStage のステップ実行および MCP ツール一覧は `SPEC-MCP-002` を参照。

## 2. 共通仕様

- **ConversationID**: `EP{episode:03d}_SC{scene:02d}_DL{dialogue:03d}` 形式。
- **データ保存**: `.noveler/design/{episode}/design.json`、`.noveler/design/{episode}/dialogues/{scene}.json` 等。
- **バリデーション**: 欠落フィールドや ID 不整合は `errors[]` に蓄積し、`success: False` を返す。

## 3. MCP ツール定義

### 3.1 design_conversations
```yaml
input:
  episode_number: int
  scene_number: int
  dialogues: list[Dialogue]
Dialogue:
  sequence: int?
  speaker: string
  text: string
  purpose: string?
  trigger_id: string?  # ConversationID
  emotion_state: string?
output:
  status: string  # success / error
  scene_id: string
  dialogue_range: {start: string, end: string}
  dialogues: list[NormalizedDialogue]
```

### 3.2 track_emotions
```yaml
input:
  emotions: list[Emotion]
Emotion:
  trigger_id: string
  viewpoint: string
  target_character: string
  observation_type: string  # internal/external/omniscient
  before_level: int
  after_level: int
  emotion_type: string
  expression: dict?
output:
  status: string
  emotion_count: int
  emotions_tracked: int
```

### 3.3 design_scenes
```yaml
input:
  scenes: list[SceneSetting]
SceneSetting:
  scene_id: string
  location: string
  sub_location: string?
  dialogue_range_start: string?
  dialogue_range_end: string?
  location_transitions: list[str]?
  temporal_tracking: list[str]?
  atmospheric_design: list[str]?
output:
  status: string
  scene_count: int
  scenes_designed: int
```

### 3.4 design_senses
```yaml
input:
  triggers: list[SensoryTrigger]
SensoryTrigger:
  trigger_id: string
  sense_type: string  # sight/hearing/touch/smell/taste
  description: string
  intensity: int
  timing: string  # before/during/after
  purpose: string
  linked_emotion: string?
  character_reaction: string?
output:
  status: string
  trigger_count: int
```

### 3.5 manage_props
```yaml
input:
  props: list[Prop]
Prop:
  prop_id: string
  name: string
  introduced: string
  mentioned: list[string]?
  focused: string?
  used: string?
  stored: string?
  emotional_states: dict?
  significance_evolution: list[string]?
output:
  status: string
  prop_count: int
  props: list[NormalizedProp]
```

### 3.6 get_conversation_context
```yaml
input:
  conversation_id: string
output:
  conversation: NormalizedDialogue
  linked_emotions: list[Emotion]
  scene: SceneSetting?
  props: list[Prop]?
```

### 3.7 export_design_data
```yaml
input:
  episode_number: int
output:
  success: bool
  export_path: string  # .noveler/design/{episode}/design.json
  files:
    dialogues: list[string]
    emotions: string
    scenes: string
    senses: string
    props: string
```

## 4. 非機能要件

| 区分 | 要件 |
| --- | --- |
| 性能 | 1回の API 呼び出しで 200 件までのエンティティを処理可能。超過時は `max_items` エラーを返す。 |
| 一貫性 | ConversationID 不整合を検知し、`errors[]` に詳細を付与。 |
| 互換性 | TenStage セッション (`write_step_n`) で生成した会話/感情データを再利用可能。 |

## 5. 入出力保存規約

- Dialogues: `.noveler/design/{episode}/dialogues/EP{episode}_SC{scene}.json`
- Emotions: `.noveler/design/{episode}/emotion_points.json`
- Scenes: `.noveler/design/{episode}/scene_settings.json`
- Senses: `.noveler/design/{episode}/sensory_triggers.json`
- Props: `.noveler/design/{episode}/props.json`
- Export: `.noveler/design/{episode}/design.json`

ファイル構造は JSON lines ではなく indented JSON を採用し、差分レビューをしやすくする。

## 6. エラーコード

| コード | 条件 | 対応 |
| --- | --- | --- |
| CD-001 | ConversationID 形式エラー | 正規形 (`EPxxx_SCxx_DLxxx`) を提示し再入力を促す |
| CD-002 | 引用先会話が存在しない | `missing_conversation_ids[]` を返し、先に `design_conversations` 実行を案内 |
| CD-003 | エクスポート先に書き込み不可 | パスと権限情報を返却し、PathService 設定を再確認させる |
| CD-004 | 入力件数が許容上限を超過 | `max_items` エラーを返し、バッチ分割を促す |
| CD-005 | 既存データとの競合（上書き確認） | `overwrite_required: true` を返し、CLI 側で確認後に再実行させる |

## 7. テスト参照

| テスト | 概要 |
| --- | --- |
| `tests/unit/domain/services/test_conversation_design_service.py` | 会話・感情・情景・小道具管理ロジック |
| `tests/integration/mcp/test_mcp_server_integration.py` | MCP ツール登録と入出力の整合 |

### 7.1 追加テスト TODO
- 大量データ（200件超）の入力に対するバリデーションテスト
- ConversationID が混在するケースでの `missing_conversation_ids[]` の確認


---

本仕様書は REQ-WRITE-DESIGN-005 の準拠を保証する。データモデルや保存形式に変更が入った場合は、本書および `SPEC-MCP-002` を同時に更新すること。
