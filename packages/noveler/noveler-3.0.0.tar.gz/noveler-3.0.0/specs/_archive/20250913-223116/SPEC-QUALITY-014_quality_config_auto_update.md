# SPEC-QUALITY-014: 品質チェック設定自動更新機能 仕様書

## 概要
品質チェック設定を適切なタイミングで自動的に更新・調整する機能を実装する。

## 背景
現在、品質チェック設定（50_管理資料/品質チェック設定.yaml）は手動でのみ更新可能であり、プロジェクトの進行に応じた適切な調整が行われにくい状況にある。

## 目的
- プロジェクトの各フェーズで適切な品質基準を自動設定
- ジャンルやターゲット層に応じた最適化
- 執筆実績に基づく継続的な改善

## 機能要件

### 1. プロジェクト開始時の初期設定
- **タイミング**: `novel new`または`novel init`実行時
- **処理内容**:
  - プロジェクト設定.yamlからジャンルとターゲット層を読み取り
  - ジャンル別のデフォルト品質基準を適用
  - 50_管理資料/品質チェック設定.yamlを生成

### 2. マスタープロット完成時の調整
- **タイミング**: `novel plot master`完了時
- **処理内容**:
  - プロットの内容を分析（キーワード、テーマ）
  - 物語の特性に応じた品質基準の調整
  - 章別の特性を考慮した設定追加

### 3. 執筆中の定期見直し
- **タイミング**: `novel complete-episode`実行時（10話ごと）
- **処理内容**:
  - 過去10話の品質チェック結果を分析
  - 基準値の妥当性を評価
  - 必要に応じて微調整を提案（自動適用はしない）

## 技術仕様

### ドメインモデル

#### エンティティ
- `QualityConfigTemplate`: 品質設定テンプレート
  - ジャンル別の基本設定を保持
  - カスタマイズ可能な項目を定義

#### 値オブジェクト
- `GenreType`: ジャンルタイプ（ファンタジー、恋愛、ミステリー等）
- `TargetAudience`: ターゲット読者層（男性向け、女性向け、一般向け等）
- `QualityThreshold`: 品質基準値（各チェック項目の閾値）

#### ドメインサービス
- `QualityConfigAutoUpdateService`: 品質設定自動更新サービス
  - ジャンル別テンプレートの適用
  - プロット分析による調整
  - 実績に基づく最適化提案

### ユースケース
- `InitializeQualityConfigUseCase`: 初期設定作成
- `AdjustQualityConfigByPlotUseCase`: プロットベースの調整
- `SuggestQualityConfigOptimizationUseCase`: 最適化提案

### リポジトリ
- `QualityConfigRepository`: 品質設定の永続化
- `QualityResultsRepository`: 品質チェック結果の取得

## ジャンル別デフォルト設定

### ファンタジー
```yaml
basic_style:
  max_hiragana_ratio: 0.45  # やや高め（魔法用語等のルビ考慮）
  min_sentence_variety: 0.25

composition:
  dialog_ratio_range: [0.25, 0.55]  # バトルシーン考慮
  short_sentence_ratio: 0.4  # アクション描写用
```

### 恋愛
```yaml
basic_style:
  max_hiragana_ratio: 0.40
  min_sentence_variety: 0.30

composition:
  dialog_ratio_range: [0.35, 0.65]  # 会話重視
  short_sentence_ratio: 0.3
```

### ミステリー
```yaml
basic_style:
  max_hiragana_ratio: 0.35  # 説明的文章多め
  min_sentence_variety: 0.35

composition:
  dialog_ratio_range: [0.30, 0.55]
  short_sentence_ratio: 0.25  # 論理的説明重視
```

## 非機能要件
- 既存の設定ファイルがある場合はバックアップを作成
- 自動更新時は更新理由をコメントとして記録
- ユーザーによる手動編集を尊重（上書きしない）

## エラーハンドリング
- 設定ファイルの読み書きエラー
- 不正なジャンル指定
- プロット分析の失敗

## テスト要件
- 各ジャンルのテンプレート適用テスト
- プロット分析による調整テスト
- 既存設定の保護テスト
- 統合テスト（CLI経由）
