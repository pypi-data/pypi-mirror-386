# SPEC-PROMPT-002: 外部テンプレート読み込み機能テスト仕様書

## 基本情報

- **仕様書ID**: SPEC-PROMPT-002
- **作成日**: 2025-01-09
- **更新日**: 2025-01-09
- **関連仕様**: SPEC-PROMPT-001
- **実装対象**: ProgressiveTaskManagerの外部テンプレート読み込み機能
- **テストレベル**: ユニットテスト

## 概要

18ステップ執筆システムの外部テンプレート読み込み機能について、包括的なテストケースによる品質保証を行う。LLMの一括実行を防ぐ段階実行制御メッセージの正常動作と、全18ステップのテンプレート対応を確認する。

## テスト対象機能

### 主要機能
1. **外部テンプレートファイルの読み込み**
   - write_step*.yamlファイルの正常読み込み
   - STEP 0-17の全ステップ対応
   - 小数点ステップ（2.5）の対応

2. **テンプレート変数置換**
   - {step_id}, {step_name}, {episode_number}等の置換
   - 動的な進捗情報の挿入
   - フェーズ情報の適切な反映

3. **段階実行制御メッセージ**
   - LLM一括実行防止メッセージの挿入
   - 単一ステップ実行強制メッセージ
   - 次ステップ制御指示

4. **エラーハンドリング**
   - テンプレートファイル未発見時のフォールバック
   - 不正YAML形式の処理
   - 破損ファイルの適切な処理

## テストケース一覧

### 1. 基本機能テスト

#### 1.1 テンプレートファイル読み込み成功
- **テストID**: TEST-TEMPLATE-001
- **目的**: write_step*.yamlファイルが正常に読み込まれることを確認
- **前提条件**: templates/write_step00_scope_definition.yamlが存在
- **テスト手順**:
  1. ProgressiveTaskManagerインスタンス作成
  2. _load_prompt_template(0)メソッド呼び出し
  3. 戻り値の検証
- **期待結果**:
  - テンプレートデータが正常に返される
  - metadata, prompt, control_settingsが含まれる
  - step_id=0, step_name="スコープ定義"が正しく設定

#### 1.2 テンプレート変数置換
- **テストID**: TEST-TEMPLATE-002
- **目的**: テンプレート内の変数が適切に置換されることを確認
- **テスト手順**:
  1. テンプレート読み込み
  2. _prepare_template_variables()で変数準備
  3. _replace_variables()で置換実行
  4. 置換結果の検証
- **期待結果**:
  - 全ての{variable}形式が実際の値に置換
  - STEP 0, エピソード1, 0/19等が正しく挿入

#### 1.3 段階実行制御メッセージ挿入
- **テストID**: TEST-TEMPLATE-003
- **目的**: LLM一括実行を防ぐ制御メッセージが正しく挿入されることを確認
- **テスト手順**:
  1. get_writing_tasks()実行
  2. llm_instruction内容確認
- **期待結果**:
  - "このステップ（STEP 0）のみを実行してください"
  - "複数ステップを一括で実行しないでください"
  - "次のステップは別途指示があるまで実行しないでください"
  - "このステップの完了を確認してから進んでください"

### 2. 全ステップ対応テスト

#### 2.1 18ステップ完全対応
- **テストID**: TEST-TEMPLATE-004
- **目的**: STEP 0-17の全テンプレートが読み込み可能であることを確認
- **前提条件**: 全18個のwrite_step*.yamlファイル存在
- **テスト手順**:
  1. 各ステップのテンプレートファイル作成
  2. 各ステップで_load_prompt_template()実行
  3. 全ステップの読み込み成功確認
- **期待結果**:
  - 全18ステップでtemplate_data != None
  - 各ステップのmetadata.step_idが正しく設定

#### 2.2 小数点ステップ対応
- **テストID**: TEST-TEMPLATE-005
- **目的**: STEP 2.5等の小数点ステップが正常処理されることを確認
- **テスト手順**:
  1. write_step2_5_theme_uniqueness.yaml作成
  2. _load_prompt_template(2.5)実行
- **期待結果**:
  - ファイル名の"."が"_"に変換される
  - step_id=2.5で正常に読み込まれる

### 3. エラーハンドリングテスト

#### 3.1 テンプレートファイル未発見時のフォールバック
- **テストID**: TEST-TEMPLATE-006
- **目的**: テンプレートファイルが存在しない場合の適切な処理を確認
- **前提条件**: テンプレートファイルが存在しない状態
- **テスト手順**:
  1. _load_prompt_template(0)実行
  2. get_writing_tasks()実行
- **期待結果**:
  - _load_prompt_template()がNoneを返す
  - get_writing_tasks()でフォールバック処理が動作
  - 基本的なLLM指示は生成される

#### 3.2 不正YAML形式のエラー処理
- **テストID**: TEST-TEMPLATE-007
- **目的**: 不正なYAMLファイルの適切な処理を確認
- **前提条件**: 構文エラーのあるYAMLファイル
- **テスト手順**:
  1. 不正YAML形式のファイル作成
  2. _load_prompt_template()実行
- **期待結果**:
  - 例外が発生せずNoneが返される
  - システム全体が継続動作する

### 4. 統合テスト

#### 4.1 get_writing_tasks統合テスト
- **テストID**: TEST-TEMPLATE-008
- **目的**: get_writing_tasks()での外部テンプレート統合が正常動作することを確認
- **テスト手順**:
  1. テンプレートファイル配置
  2. get_writing_tasks()実行
  3. 結果の包括的検証
- **期待結果**:
  - 外部テンプレート由来の内容が含まれる
  - 基本的なレスポンス構造が維持される
  - episode_number, current_step等の基本情報が正しい

#### 4.2 制御設定適用テスト
- **テストID**: TEST-TEMPLATE-009
- **目的**: テンプレートのcontrol_settingsが適切に適用されることを確認
- **テスト手順**:
  1. control_settingsを含むテンプレート作成
  2. テンプレート読み込み
  3. 設定値の確認
- **期待結果**:
  - strict_single_step: true
  - require_completion_confirm: true
  - auto_advance_disabled: true
  - batch_execution_blocked: true

### 5. 命名規則テスト

#### 5.1 writeコマンド用命名規則
- **テストID**: TEST-TEMPLATE-010
- **目的**: write_step*形式の命名規則が正しく適用されることを確認
- **テスト手順**:
  1. 各ステップの期待ファイル名算出
  2. 実際のファイル名生成ロジック確認
- **期待結果**:
  - write_step00_scope_definition.yaml
  - write_step01_chapter_purpose.yaml
  - write_step2_5_theme_uniqueness.yaml
  - write_step17_final_preparation.yaml

## テスト環境要件

### 必要なファイル構造
```
project_root/
├── templates/
│   ├── write_step00_scope_definition.yaml
│   ├── write_step01_chapter_purpose.yaml
│   ├── write_step02_section_goals.yaml
│   ├── write_step2_5_theme_uniqueness.yaml
│   ├── write_step03_section_balance.yaml
│   ├── write_step04_scene_beats.yaml
│   ├── write_step05_logic_verification.yaml
│   ├── write_step06_character_detail.yaml
│   ├── write_step07_dialogue_design.yaml
│   ├── write_step08_emotion_curve.yaml
│   ├── write_step09_atmosphere_worldview.yaml
│   ├── write_step10_foreshadow_placement.yaml
│   ├── write_step11_first_draft.yaml
│   ├── write_step12_style_adjustment.yaml
│   ├── write_step13_description_enhancement.yaml
│   ├── write_step14_readability_optimization.yaml
│   ├── write_step15_quality_check.yaml
│   ├── write_step16_reader_experience.yaml
│   └── write_step17_final_preparation.yaml
└── src/noveler/infrastructure/config/
    └── writing_tasks.yaml
```

### テストデータ要件
- **有効なYAMLテンプレート**: metadata, prompt, variables, control_settings
- **不正なYAMLファイル**: 構文エラーを含むファイル
- **一時ディレクトリ**: pytest.tmp_pathを使用

## 成功基準

### 品質基準
- **テストカバレッジ**: 95%以上
- **全テストケース成功**: 100%
- **パフォーマンス**: 各テストケース1秒以内

### 機能基準
- **全18ステップ対応**: STEP 0-17の完全サポート
- **エラー耐性**: 不正ファイルでもシステム継続動作
- **段階実行制御**: LLM一括実行防止メッセージの確実な挿入

## 実装ファイル

### テストファイル
- `tests/unit/domain/services/test_progressive_task_manager_template_loading.py`

### 対象コード
- `src/scripts/domain/services/progressive_task_manager.py`
  - `_load_prompt_template()` メソッド
  - `_get_step_slug()` メソッド
  - `_prepare_template_variables()` メソッド
  - `_replace_variables()` メソッド
  - `get_writing_tasks()` メソッド

## 実行方法

```bash
# 特定テスト実行
pytest tests/unit/domain/services/test_progressive_task_manager_template_loading.py -v

# SPEC-PROMPT-001関連テスト実行
pytest -m "spec('SPEC-PROMPT-001')" -v

# カバレッジ付き実行
pytest tests/unit/domain/services/test_progressive_task_manager_template_loading.py --cov=src.scripts.domain.services.progressive_task_manager --cov-report=html

# 全外部テンプレート機能テスト実行
pytest -k "template" -v
```

## 関連仕様書

- **SPEC-PROMPT-001**: 外部テンプレート読み込み機能実装仕様
- **SPEC-901**: 段階実行システム実装仕様

## 更新履歴

| バージョン | 日付 | 変更内容 | 担当者 |
|-----------|------|----------|--------|
| 1.0.0 | 2025-01-09 | 初版作成、18ステップ対応テスト仕様策定 | Claude Code |
