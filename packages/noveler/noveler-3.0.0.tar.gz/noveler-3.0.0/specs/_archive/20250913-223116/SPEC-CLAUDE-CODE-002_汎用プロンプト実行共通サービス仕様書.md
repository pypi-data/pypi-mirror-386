# SPEC-CLAUDE-CODE-002: 汎用プロンプト実行共通サービス仕様書

## 1. 概要

> ステータス: Active（入口はMCPツールに移行済み）
> 備考: CLIフラグは参考情報。現行はMCPツールの引数/内部設定で等価制御します。

### 1.1 目的
Claude Code統合機能を共通サービス化し、`novel write`（執筆）と `novel plot episode`（話別プロット作成）で統一的に「プロンプト生成→手動実行」から「シームレス自動実行」を実現する。

### 1.2 スコープ
- 汎用プロンプト実行共通サービス実装
- 既存2機能（執筆・プロット作成）への統合
- CLI統一インターフェース実装
- B20準拠3コミット開発プロセス

### 1.3 成功基準
- 2機能での統一実行体験実現
- コード重複完全排除
- 既存機能後方互換性保持

## 2. 要件仕様

### REQ-1: 汎用プロンプト実行共通サービス
**REQ-1.1** `UniversalClaudeCodeService`をインフラストラクチャ層に実装
**REQ-1.2** プロンプト内容種別（執筆・プロット・品質チェック等）への対応
**REQ-1.3** コンテキストファイル管理・メタデータ抽出機能
**REQ-1.4** 結果解析・構造化データ取得（種別対応）

### REQ-2: プロンプト実行要求統一
**REQ-2.1** `UniversalPromptRequest`バリューオブジェクト実装
**REQ-2.2** `PromptType`列挙型実装（WRITING, PLOT, QUALITY_CHECK）
**REQ-2.3** 種別固有設定・コンテキスト管理
**REQ-2.4** 実行結果解析ルール定義

### REQ-3: 応答統一・種別対応
**REQ-3.1** `UniversalPromptResponse`レスポンスエンティティ実装
**REQ-3.2** 種別固有の結果抽出メソッド実装
**REQ-3.3** 品質評価・メタデータ管理機能

### REQ-4: 既存機能統合（MCP連携）
**REQ-4.1** `EnhancedIntegratedWritingUseCase`の共通サービス移行
**REQ-4.2** プロット作成ユースケースの共通サービス移行
**REQ-4.3** 参考: CLI統一フラグ（`--direct-claude`, `--prompt-only`）はMCP側引数/内部設定で等価制御

### REQ-5: 拡張性・保守性
**REQ-5.1** 新しいプロンプト種別への容易な追加対応
**REQ-5.2** 種別固有設定の外部化・管理機能
**REQ-5.3** プラグイン的な拡張アーキテクチャ

## 3. 実装構成要素

### 3.1 共通サービス層
```python
# src/noveler/infrastructure/integrations/universal_claude_code_service.py
class UniversalClaudeCodeService:
    async def execute_universal_prompt(
        self,
        request: UniversalPromptRequest
    ) -> UniversalPromptResponse

    def _get_result_extractor(self, prompt_type: PromptType) -> ResultExtractor
    def _apply_context_rules(self, request: UniversalPromptRequest) -> ClaudeCodeExecutionRequest
```

### 3.2 ドメイン層拡張
```python
# src/noveler/domain/value_objects/universal_prompt_execution.py
from enum import Enum

class PromptType(Enum):
    WRITING = "writing"
    PLOT = "plot"
    QUALITY_CHECK = "quality_check"

@dataclass
class UniversalPromptRequest:
    prompt_content: str
    prompt_type: PromptType
    project_context: ProjectContext
    type_specific_config: dict = None

@dataclass
class UniversalPromptResponse:
    success: bool
    response_content: str
    extracted_data: dict
    prompt_type: PromptType
    metadata: dict = None

    def get_writing_content(self) -> str | None
    def get_plot_content(self) -> dict | None
    def get_quality_assessment(self) -> dict | None
```

### 3.3 結果抽出戦略パターン
```python
# src/noveler/domain/services/result_extraction_strategies.py
class WritingResultExtractor:
    def extract(self, response: ClaudeCodeExecutionResponse) -> dict

class PlotResultExtractor:
    def extract(self, response: ClaudeCodeExecutionResponse) -> dict

class QualityCheckResultExtractor:
    def extract(self, response: ClaudeCodeExecutionResponse) -> dict
```

### 3.4 統合アプリケーション層
```python
# src/noveler/application/use_cases/universal_llm_use_case.py
class UniversalLLMUseCase:
    def __init__(
        self, universal_service: UniversalLLMServiceProtocol, console: ConsoleProtocol | None = None
    ):
        ...

    async def execute_with_fallback(
        self,
        request: UniversalPromptRequest
    ) -> UniversalPromptResponse
```

## 4. CLI統一インターフェース設計

### 4.1 統一フラグ仕様（参考・現行はMCP側で制御）
```python
# 統一実装：novel write / novel plot episode 共通
--direct-claude     # Claude Code直接実行強制
--prompt-only       # プロンプト生成のみ（従来モード）
--auto-mode         # 自動判定（デフォルト）
--save-prompt       # プロンプト保存（両機能で統一）
```

### 4.2 実行フロー統一
```
1. プロンプト生成（種別固有ロジック）
2. Claude Code利用可能性判定
3. 直接実行 or フォールバック判定
4. 結果解析・保存（種別固有ロジック）
5. UI表示・完了処理
```

### 4.3 CLI→MCPマッピング例（具体）
- 旧 `--direct-claude`
  - 執筆: `write_with_claude(episode=1)`（Claude内ダイレクト原稿生成・プロンプト返却）
  - プロット: `noveler_plot(episode_number=1)` → プロットを既存ファイルから読み出し、Claudeに渡す前提の設計

- 旧 `--prompt-only`
  - 執筆: `noveler_write(episode_number=1, dry_run=True)` または `write_with_claude(episode=1)`
  - プロット: `noveler_plot(episode_number=1)`（必要に応じて `regenerate=False` で参照のみ）

- 旧 自動判定（デフォルト）
  - 執筆: `noveler_write(episode_number=1, dry_run=False)`（内部でClaude利用可否を判定し実行/フォールバック）
  - 品質: `noveler_check(episode_number=1, auto_fix=False)`（必要に応じて `auto_fix=True`）

補足
- MCPツール定義は `src/mcp_servers/noveler/json_conversion_server.py` に集約。
- JSONレスポンス/ファイル参照は `src/noveler/infrastructure/json/...` を参照（モデル/コンバータ/ファイル管理）。

## 5. 受け入れ条件

### AC-1: 共通サービス機能
- [ ] 複数プロンプト種別対応（執筆・プロット・品質チェック）
- [ ] 種別固有結果抽出機能
- [ ] コンテキスト管理・メタデータ処理
- [ ] エラーハンドリング・フォールバック機能

### AC-2: 既存機能統合
- [ ] `novel write` でClaude Code直接実行
- [ ] `novel plot episode` でClaude Code直接実行
- [ ] 統一CLI体験（同じフラグ・挙動）
- [ ] 既存機能完全後方互換性

### AC-3: 品質基準
- [ ] B20品質作業指示書100%準拠
- [ ] 統合設定管理システム使用
- [ ] CommonPathService統合
- [ ] コード重複完全排除

### AC-4: パフォーマンス・UX
- [ ] 実行時間90%削減維持
- [ ] 統一エラーメッセージ・進捗表示
- [ ] プロンプト-結果追跡性確保

## 6. マイグレーション戦略

### Phase 1: 共通サービス実装
1. `UniversalClaudeCodeService` 実装
2. プロンプト種別・結果抽出機能実装
3. 基本テストパス確認

### Phase 2: 既存機能統合（MCP連携）
4. `novel write` の共通サービス移行
5. `novel plot episode` の共通サービス移行
6. MCPツール側パラメータ/内部設定での等価制御

### Phase 3: 品質・統合確認
7. 統合テスト実装
8. B20品質チェック実行
9. 後方互換性確認

## 7. 期待効果

### 開発・保守効率
- **コード重複排除**: 80%のロジック共通化
- **新機能追加コスト**: 60%削減（共通基盤活用）
- **保守性向上**: 統一アーキテクチャによる一元管理

### ユーザー体験
- **操作統一**: 全機能で同じフラグ・挙動
- **実行効率**: 30分→3分の効率化を全機能で実現
- **学習コスト削減**: 統一インターフェースによる直感的操作

### 拡張性
- **新プロンプト種別追加**: プラグイン方式で容易拡張
- **カスタマイゼーション**: 種別固有設定による柔軟対応

---
**作成日**: 2025年8月8日
**更新日**: 2025年9月13日
**承認**: 待機中
**実装担当**: Claude Code
**仕様書ID**: SPEC-CLAUDE-CODE-002
**前提仕様**: SPEC-CLAUDE-CODE-001（Claude Code統合サービス）

---

## 8. 付録: I/Oロギング・参照渡し（B20準拠）

### 8.1 LLM I/O ロギング保存先
- 実装: `src/noveler/infrastructure/llm/llm_io_logger.py`（LLMIOLogger）
- 保存先（JST/JSON整形）
  - write系（PromptType.WRITING, writeステップ） → `.noveler/writes/`
  - check/quality系 → `.noveler/checks/`
  - アーティファクトストア → `.noveler/artifacts/`
- 目的: プロンプト改善のための逐次ログ蓄積（時系列・再現性・監査性の確保）

### 8.2 参照渡し（Artifact）
- 参照ID: `artifact:{hash12}`、保存: `.noveler/artifacts/*.json`
- MCPツール: `fetch_artifact`, `list_artifacts`（novelerサーバー）
- ProgressiveWriteManagerでの自動参照化（存在時）
  - 30_設定集/キャラクター.yaml・世界観.yaml・用語集.yaml・文体/スタイルガイド.yaml
  - 20_プロット/話別プロット/第{episode}話_*.yaml
  - 40_原稿/第{episode-1}話_*.md（前話）
- 要約アーティファクト（summaryタグ）の自動生成（設定: defaults.writing_steps.summarize）
- ステップ種別別の優先参照最適化（会話/文体/プロット等）を適用し、LLM指示に提示
