# SPEC-STAGE5-SEPARATION: Stage5分離とClaude Code品質チェック実装仕様

## 概要

話別プロット作成プロセスからStage5（品質確認）を分離し、専用のClaude Code品質チェックプロンプト生成機能として独立実装する。

## 要件定義

### 機能要件

#### FR-001: Stage5プロセス分離
- **現状**: 話別プロット作成時にStage1-5を連続実行
- **変更後**: Stage1-4のみを話別プロット作成の範囲とする
- **目的**: 品質チェックを独立したプロセスに分離

#### FR-002: Claude Code品質チェック機能
- **機能**: 完成したプロット（Stage4まで）を対象とした品質チェックプロンプト生成
- **出力**: Claude Codeで使用可能なプロンプト文字列
- **チェック内容**:
  - 全体整合性確認
  - 品質メトリクス評価
  - 制作指針準拠確認
  - 最終完成度判定

#### FR-003: 独立したCLIインターフェース
- **コマンド**: `novel quality-check {episode_number}`
- **入力**: Stage4完了済みのプロットファイル
- **出力**: Claude Code用品質チェックプロンプト

### 非機能要件

#### NFR-001: アーキテクチャ準拠
- SDD（仕様駆動開発）: 明確な仕様書ベース設計
- DDD（ドメイン駆動設計）: ドメインモデル中心設計
- TDD（テスト駆動開発）: テストファーストアプローチ

#### NFR-002: 既存システムとの互換性
- 既存のStage1-4プロセスに影響なし
- PromptStageの範囲修正（プロット作成: Stage1-4, 品質チェック: 独立）
- テンプレートシステムとの整合性維持

## ドメインモデル設計

### 主要ドメイン概念

#### PlotQualityCheckRequest (Value Object)
```python
@dataclass(frozen=True)
class PlotQualityCheckRequest:
    episode_number: int
    project_name: str
    plot_file_path: Path
    check_level: QualityCheckLevel
```

#### QualityCheckPrompt (Entity)
```python
class QualityCheckPrompt:
    prompt_id: QualityCheckPromptId
    episode_plot: EpisodePlot
    check_criteria: List[QualityCriterion]
    generated_prompt: str
```

#### QualityCheckPromptGenerator (Domain Service)
```python
class QualityCheckPromptGenerator:
    def generate_prompt(self, request: PlotQualityCheckRequest) -> QualityCheckPrompt
    def validate_plot_completeness(self, plot: EpisodePlot) -> ValidationResult
```

### ドメインルール

#### DR-001: プロット完成度チェック
- Stage4まで完了したプロットのみ品質チェック対象
- 必須要素（foreshadowing_integration, technical_elements等）の存在確認

#### DR-002: Claude Code互換性
- 生成プロンプトは Claude Code の制約に準拠
- 適切な文字数制限内でのプロンプト生成

## 実装計画

### Phase 1: ドメインモデル実装 (TDD)
1. Value Objects実装 + テスト
2. Entities実装 + テスト
3. Domain Services実装 + テスト

### Phase 2: インフラストラクチャ実装
1. YAMLベースリポジトリ実装
2. プロンプトテンプレート管理
3. ファイルシステム統合

### Phase 3: アプリケーション層実装
1. Use Case実装
2. DTO定義
3. エラーハンドリング

### Phase 4: プレゼンテーション層実装
1. CLI コマンド実装
2. 既存ワークフローからStage5除去
3. 統合テスト

### Phase 5: 品質保証
1. 単体テスト完備
2. 統合テスト実行
3. エンドツーエンドテスト

## 成功基準

### 技術的成功基準
- [ ] 全テストパス（単体・統合・E2E）
- [ ] 既存機能への影響ゼロ
- [ ] Claude Code互換プロンプト生成成功

### ビジネス成功基準
- [ ] Stage1-4プロット作成時間の短縮
- [ ] 品質チェックの独立実行可能性
- [ ] Claude Codeでの品質評価精度向上

## リスク分析

### 技術リスク
- **R001**: 既存PromptStageの変更影響
  - 軽減策: 段階的移行とテスト強化
- **R002**: Claude Code API制限
  - 軽減策: プロンプト分割機能実装

### 運用リスク
- **R003**: ユーザーワークフロー混乱
  - 軽減策: 明確なドキュメント提供とガイド更新
