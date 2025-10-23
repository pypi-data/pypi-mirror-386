---
spec_id: SPEC-PLOT-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [E2E, REQ]
tags: [plot]
---
# SPEC-PLOT-001: Claude Code連携プロット生成システム

## 要件トレーサビリティ

**要件ID**: REQ-PLOT-001〜008 (プロット管理機能群)

**主要要件**:
- REQ-PLOT-001: 階層的プロット構造作成
- REQ-PLOT-002: プロット品質評価・改善提案
- REQ-PLOT-003: プロット整合性検証機能
- REQ-PLOT-004: インタラクティブプロット編集
- REQ-PLOT-005: プロットバージョン管理
- REQ-PLOT-006: 章別プロット自動推論機能
- REQ-PLOT-007: プロット要素抽出・分析
- REQ-PLOT-008: プロット進捗管理機能

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/integration/test_interactive_writing_system.py
**関連仕様書**: SPEC-WRITE-INTERACTIVE-001-v2.md

## 概要
`novel plot episode X` コマンド実行時に、章別プロット情報を参照してClaude Codeに動的にプロット内容を問い合わせ、エピソード固有の詳細プロットを生成するシステムを実装する。

## 背景
現在のプロット作成システムは静的テンプレートをコピーするだけで、章別プロット情報を活用していない。ユーザーは章別プロットの内容を基に、Claude Codeが各記載項目について動的に生成することを要求している。

## 要件

### 機能要件

#### FR-PLOT-001: 章別プロット参照機能
- `20_プロット/章別プロット/第X章.yaml` から該当する章情報を読み取る
- エピソード番号から章番号を自動判定する
- 章別プロット内の各項目（キーイベント、テーマ、視点管理等）を構造化して取得する

#### FR-PLOT-002: Claude Code連携プロット生成機能
- 章別プロット情報を基にClaude Codeへの構造化問い合わせを作成
- エピソード固有の詳細プロット項目を動的生成
- 既存のClaudeCodeEvaluationServiceパターンを活用

#### FR-PLOT-003: 生成プロット統合機能
- Claude Codeからの応答をYAML形式のプロットファイルに統合
- 既存のテンプレート構造を維持しつつ、動的生成内容を追加
- 生成された内容と元の章別プロット参照情報を併記

### 非機能要件

#### NFR-PLOT-001: アーキテクチャ準拠
- DDD（ドメイン駆動設計）レイヤー分離の徹底
- 既存のClaude Code連携パターンとの整合性維持
- Repository-Service-UseCase構造の遵守

#### NFR-PLOT-002: 拡張性・保守性
- 新しい章別プロット項目への容易な対応
- Claude Code以外のLLMサービスへの切り替え可能性
- エラーハンドリングとフォールバック機能

## アーキテクチャ設計

### ドメイン層
```
scripts/domain/
├── entities/
│   ├── chapter_plot.py          # 章別プロット情報エンティティ
│   └── generated_episode_plot.py # 生成エピソードプロットエンティティ
├── value_objects/
│   ├── chapter_number.py        # 章番号値オブジェクト
│   └── plot_generation_request.py # プロット生成リクエスト
├── services/
│   └── claude_plot_generation_service.py # Claude連携プロット生成サービス
└── repositories/
    └── chapter_plot_repository.py # 章別プロットリポジトリインターフェース
```

### アプリケーション層
```
scripts/application/use_cases/
└── generate_episode_plot_use_case.py # エピソードプロット生成ユースケース
```

### インフラストラクチャ層
```
scripts/infrastructure/repositories/
└── yaml_chapter_plot_repository.py # YAML章別プロットリポジトリ実装
```

### プレゼンテーション層
- 既存の`plot_episode`コマンドを拡張

## 実装仕様

### 1. ChapterPlot エンティティ
```python
@dataclass
class ChapterPlot:
    chapter_number: ChapterNumber
    title: str
    summary: str
    key_events: list[str]
    episodes: list[dict[str, Any]]
    central_theme: str
    viewpoint_management: dict[str, Any]
    # 他の章別プロット項目
```

### 2. ClaudePlotGenerationService
```python
class ClaudePlotGenerationService:
    def generate_episode_plot(
        self,
        chapter_plot: ChapterPlot,
        episode_number: int
    ) -> GeneratedEpisodePlot:
        # 章別プロット情報からClaude Codeへの問い合わせを構築
        # 既存のClaudeCodeEvaluationServiceパターンを活用
```

### 3. GenerateEpisodePlotUseCase
```python
class GenerateEpisodePlotUseCase:
    def execute(
        self,
        episode_number: int,
        force: bool = False
    ) -> GeneratedEpisodePlot:
        # 1. エピソード番号から章番号を判定
        # 2. 章別プロットを取得
        # 3. Claude Code連携でプロット生成
        # 4. 結果をYAMLファイルに保存
```

## テスト仕様

### 単体テスト
- ドメインエンティティの動作検証
- サービス層のロジック検証
- リポジトリの章別プロット読み取り検証

### 統合テスト
- Claude Code連携の動作検証
- YAML生成・保存の検証
- エラーハンドリングの検証

### E2Eテスト
- `novel plot episode X` コマンドの完全動作検証
- 章別プロット参照から最終YAML生成までの流れ

## 成功基準

1. `novel plot episode 7` 実行時に第7話が属する章の章別プロットを正しく参照
2. Claude Codeへの構造化問い合わせが適切に実行
3. 生成されたプロット内容が既存のYAML構造に適切に統合
4. 既存のテンプレートベース作成との下位互換性維持
5. 全テストがパス（単体・統合・E2E）

## リスク・制約

### リスク
- Claude Code API接続エラー時のフォールバック処理
- 生成内容の品質・妥当性担保
- 大量のエピソード処理時のレート制限対応

### 制約
- 既存のCLI interface変更は最小限
- 章別プロットファイルが存在しない場合の処理
- 静的テンプレート方式との併用サポート

## 実装優先度

### Phase 1: 基盤実装
1. ドメインエンティティ・値オブジェクト
2. リポジトリインターフェース・実装
3. 基本的なユースケース

### Phase 2: Claude Code連携
1. Claude連携サービス実装
2. 問い合わせ構造の最適化
3. エラーハンドリング強化

### Phase 3: CLI統合・テスト
1. 既存コマンドの拡張
2. 包括的テスト実装
3. ドキュメント整備

## 関連仕様書
- SPEC-A31-XXX: A31評価システム（Claude Code連携パターン参考）
- 既存のClaudeCodeEvaluationService実装
