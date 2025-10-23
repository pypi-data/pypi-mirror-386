# .novelerrc.yaml 執筆スタイル設定スキーマ

## 概要

このドキュメントは `.novelerrc.yaml` に追加された執筆スタイル設定のスキーマ定義です。

**作成日**: 2025-10-20
**Version**: 1.0.0
**関連ガイド**:
- [guide.md Phase 1](../../guide.md#phase-1) - 短文統合技法の詳細
- [A38_執筆プロンプトガイド.md](../A38_執筆プロンプトガイド.md) - 18-step執筆システム

---

## 設定セクション

### `writing_style`

執筆スタイルを制御する設定。プリセット方式により、なろう/文芸/Golden Sampleの3つのスタイルを切り替え可能。

---

### `writing_style.active_preset`

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `active_preset` | string | `"narou"` | 使用するプリセット名 |

**選択肢**:
- `narou` - なろう小説向け（スマホ最適化・テンポ重視）
- `literary` - 文芸向け（読み応え重視・バランス型）
- `golden_sample` - Golden Sample（渡辺温「恋」・太宰治「斜陽」スタイル）

---

### `writing_style.presets`

プリセット定義オブジェクト。各プリセットは以下のフィールドを持つ。

---

## プリセット共通フィールド

### 基本情報

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `description` | string | プリセットの説明 |
| `target_chars_per_episode` | array[int, int] | エピソード文字数範囲 [最小, 最大] |
| `structure` | string | 構成タイプ（`three_act` or `custom`） |
| `section_ratio` | array[int, int, int] | 導入/展開/結末の比率（%） |

---

### 地の文（ナラティブ）設定

`narrative_sentence_length` オブジェクト:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `target_average` | int | 平均文長目標（文字数） |
| `distribution` | array[int, int] | 自然な分布範囲 [最小, 最大]（文字数） |
| `consolidation_enabled` | boolean | Phase 1短文統合を有効化 |
| `consolidation_threshold` | int | この文字数未満を統合対象とする |

**Phase 1短文統合について**:
- guide.md Phase 1で定義された技法
- 20-35文字の短文を統合し、`target_average`文字前後に調整
- 統合により文の質が向上し、結果として文字数が自然に調整される
- 削除・追加はせず、統合の質を優先

---

### 会話文設定

`dialogue_sentence_length` オブジェクト:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `phase_0c_target` | array[int, int] | Phase 0C（会話文長文化）適用時の文長範囲 |
| `tempo_driven` | array[int, int] | テンポ重視の短尺会話の文長範囲 |
| `narrative_driven` | array[int, int] | 会話に語り機能を持たせる場合の文長範囲（golden_sampleのみ） |
| `default_mode` | string | デフォルトモード（`tempo_driven` / `balanced` / `narrative_driven`） |

**Phase 0Cについて**:
- guide.md Phase 0Cで定義された会話文長文化技法
- 75-85文字の長文会話により、会話に語り機能を付与
- 観察型/分析型/回想型の3パターン

---

### 内省型技法設定（golden_sampleのみ）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `introspection_enabled` | boolean | Phase 0D内省型技法を有効化 |

**Phase 0Dについて**:
- guide.md Phase 0Aで定義された太宰治「斜陽」スタイル
- 意識の流れ、物への執着と象徴化、不意の告白と自己発見など
- 内省型シーンに適用

---

## グローバル設定

`writing_style` 直下のグローバル設定:

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `phase_1_enabled` | boolean | `true` | Phase 1短文統合を有効化 |
| `phase_0c_enabled` | boolean | `true` | Phase 0C会話文長文化を有効化 |
| `forbidden_expressions_check` | boolean | `true` | 禁止表現チェックを有効化 |

---

## プリセット詳細

### narou（なろう小説向け）

```yaml
narou:
  description: "なろう小説向け・スマホ最適化・テンポ重視"
  target_chars_per_episode: [4000, 6000]

  narrative_sentence_length:
    target_average: 38        # やや短め
    distribution: [20, 60]
    consolidation_enabled: true
    consolidation_threshold: 35

  dialogue_sentence_length:
    phase_0c_target: [75, 85]
    tempo_driven: [15, 40]
    default_mode: "tempo_driven"  # テンポ優先

  structure: "three_act"
  section_ratio: [15, 70, 15]
```

**特徴**:
- スマホでの読みやすさを重視
- 会話はテンポ重視の短尺（15-40文字）
- 地文は38文字平均で軽快なリズム

---

### literary（文芸向け）

```yaml
literary:
  description: "文芸向け・読み応え重視・バランス型"
  target_chars_per_episode: [8000, 12000]

  narrative_sentence_length:
    target_average: 43        # golden_sample_02実測値
    distribution: [20, 60]
    consolidation_enabled: true
    consolidation_threshold: 35

  dialogue_sentence_length:
    phase_0c_target: [75, 85]
    tempo_driven: [15, 40]
    default_mode: "balanced"  # バランス型

  structure: "custom"
  section_ratio: [20, 60, 20]
```

**特徴**:
- 読み応え重視で文字数多め（8,000-12,000文字）
- 会話はテンポと語りのバランス
- 地文は43文字平均（golden_sample_02準拠）

---

### golden_sample（渡辺温・太宰治スタイル）

```yaml
golden_sample:
  description: "渡辺温「恋」・太宰治「斜陽」スタイル・内省型対応"
  target_chars_per_episode: [6000, 8000]

  narrative_sentence_length:
    target_average: 43
    distribution: [20, 80]        # 内省型では長文も許容
    consolidation_enabled: true
    consolidation_threshold: 35

  dialogue_sentence_length:
    phase_0c_target: [75, 85]
    narrative_driven: [100, 450]  # 会話に語り機能を持たせる
    default_mode: "narrative_driven"

  structure: "three_act"
  section_ratio: [25, 50, 25]
  introspection_enabled: true     # Phase 0D内省型技法
```

**特徴**:
- 文芸性を重視したGolden Sampleスタイル
- 会話は語り機能を持つ長文（100-450文字）
- 内省型技法により意識の流れを表現可能
- 地文は最大80文字まで許容（太宰治スタイル）

---

## 使用例

### 基本的な設定（なろう向け）

```yaml
writing_style:
  active_preset: "narou"

  phase_1_enabled: true
  phase_0c_enabled: true
  forbidden_expressions_check: true
```

### 文芸作品向け設定

```yaml
writing_style:
  active_preset: "literary"

  # 全機能有効化
  phase_1_enabled: true
  phase_0c_enabled: true
  forbidden_expressions_check: true
```

### Golden Sample準拠

```yaml
writing_style:
  active_preset: "golden_sample"

  # 内省型技法も有効化
  phase_1_enabled: true
  phase_0c_enabled: true
  forbidden_expressions_check: true
```

---

## テンプレートでの変数展開

18-step執筆システムのテンプレート（write_step12, write_step13）では、以下の変数が自動展開されます:

```yaml
# write_step12_first_draft.yaml での使用例
inputs:
  variables:
    writing_style: {
      type: object,
      required: true,
      source: ".novelerrc.yaml:writing_style.presets[active_preset]"
    }

llm_config:
  role_messages:
    user: |
      【設定値】
      - 文体スタイル: {writing_style.active_preset}
      - 地文平均目標: {writing_style.target_average}文字
      - 文長分布範囲: {writing_style.distribution[0]}-{writing_style.distribution[1]}文字
      - エピソード文字数目安: {writing_style.target_chars_per_episode[0]}-{writing_style.target_chars_per_episode[1]}文字
```

---

## STEP 12（初稿執筆）での適用

### 変更内容

**変更前**:
- 文字数制約: 8000字以上（ハードルール）
- 会話主導のテンポ（地の文は補助）
- 固定的な設定値

**変更後**:
- 文字数制約を削除（自由執筆）
- 文体スタイルは.novelerrc.yamlから動的に取得
- 文字数調整は次のSTEP（Phase 1短文統合）に委譲

### 設計思想

- **STEP 12**: 書きたいことを制約なく書き出す
- **STEP 13**: Phase 1短文統合により質を向上させながら自然に文字数を調整

---

## STEP 13（スタイル調整）での適用

### Phase 1短文統合の実装

```yaml
tasks:
  details:
    - name: Phase 1短文統合
      items:
        - id: consolidate.short_sentences
          text: "20-35文字の短文を統合し、{writing_style.target_average}文字前後に調整"
        - id: consolidate.maintain_rhythm
          text: "短文と中長文のバランスを保持（リズム重視）"
        - id: consolidate.target_distribution
          text: "{writing_style.distribution}範囲内に90%以上を収める"
        - id: consolidate.quality_over_count
          text: "統合の質を優先し、文字数不足でも削除・追加はしない"
```

### 重要な原則

1. **文字数は副産物**: Phase 1短文統合により質が向上し、結果として文字数が調整される
2. **削除・追加禁止**: 目標文字数に届かなくても無理な水増しはしない
3. **質優先**: 統合の質を優先し、不自然な統合はしない

---

## マイグレーションパス

### 既存プロジェクトへの適用

#### Step 1: .novelerrc.yaml作成

```bash
# プロジェクトルートに.novelerrc.yamlを作成
cp ../00_ガイド/templates/.novelerrc.yaml.template .novelerrc.yaml

# プロジェクトに合わせて編集
nano .novelerrc.yaml
```

#### Step 2: active_preset選択

```yaml
writing_style:
  active_preset: "narou"  # または "literary" / "golden_sample"
```

#### Step 3: 既存のプロジェクト設定.yamlから情報を移行

```yaml
# プロジェクト設定.yamlの内容を.novelerrc.yamlのprojectセクションに統合
project:
  name: "プロジェクト名"
  genre: "ジャンル"
  # ...
```

---

## パフォーマンス影響

| 設定 | 追加レイテンシ | 説明 |
|------|--------------|------|
| Phase 1有効化 | +5-10秒 | 短文統合処理 |
| Phase 0C有効化 | +3-5秒 | 会話文長文化処理 |
| Phase 0D有効化 | +10-15秒 | 内省型技法処理（golden_sampleのみ） |

---

## トラブルシューティング

### 文字数が目標に届かない

**原因**: Phase 1短文統合により質を優先した結果、統合候補が少ない

**対処法**:
1. STEP 12で執筆量を増やす（制約なく書き出す）
2. `consolidation_threshold`を調整（35 → 40）
3. 文字数不足を許容する（質優先の設計思想）

### 文長分布が偏る

**原因**: 統合しすぎて長文が増えた

**対処法**:
1. `target_average`を下げる（43 → 40）
2. `distribution`範囲を狭める（[20, 60] → [20, 50]）
3. Phase 1のバランス保持を強調

### テンプレート変数が展開されない

**原因**: 設定読み込み機構が未実装

**対処法**:
- 現在は手動で設定値をテンプレートに記述
- 今後、自動展開機構を実装予定

---

## 関連ドキュメント

- [guide.md](../../guide.md) - Phase 0A/0C/0D/1の詳細仕様
- [A38_執筆プロンプトガイド.md](../A38_執筆プロンプトガイド.md) - 18-step執筆システム
- [A32_執筆コマンドガイド.md](../A32_執筆コマンドガイド.md) - CLIコマンド詳細
- [novelerrc_ml_optimization_schema.md](./novelerrc_ml_optimization_schema.md) - ML最適化設定

---

## 更新履歴

| Version | Date | Summary |
|---------|------|---------|
| 1.0.0 | 2025-10-20 | 初版: 執筆スタイル設定スキーマ定義 |
