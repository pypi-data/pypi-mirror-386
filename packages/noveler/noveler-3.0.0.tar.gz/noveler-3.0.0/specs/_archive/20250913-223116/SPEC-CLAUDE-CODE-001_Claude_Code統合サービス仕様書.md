# SPEC-CLAUDE-CODE-001: Claude Code統合サービス仕様書

## 1. 概要

> ステータス: Active（入口はMCPツールに移行済み）
> 備考: 旧CLIフラグ仕様は参考情報。現行はMCPツールの引数/内部設定で等価制御します。

### 1.1 目的
`novel write`等のプロンプト生成コマンドにおいて、従来の「YAMLプロンプト生成→ファイル出力→手動実行」ワークフローを「Claude Codeヘッドレスモード直接実行」に変更し、自動化・効率化を実現する。

### 1.2 スコープ
- Claude Codeヘッドレスモード（`-p` + `--output-format json`）統合
- 統合執筆ワークフローへの組み込み
- エラーハンドリング・フォールバック機能
- 実行結果管理・追跡機能

### 1.3 成功基準
- プロンプト実行時間90%削減（30分→3分）
- 手動コピペエラー完全排除
- 既存ワークフロー後方互換性保持

## 2. 要件仕様

### REQ-1: Claude Code統合サービス層実装
**REQ-1.1** `ClaudeCodeIntegrationService`をインフラストラクチャ層に実装
**REQ-1.2** 統合設定管理システムによる実行パス・オプション管理
**REQ-1.3** JSON出力解析・構造化データ取得機能
**REQ-1.4** タイムアウト・エラーハンドリング機能

### REQ-2: ドメインエンティティ設計
**REQ-2.1** `ClaudeCodeExecutionRequest`バリューオブジェクト実装
**REQ-2.2** `ClaudeCodeExecutionResponse`レスポンスエンティティ実装
**REQ-2.3** 実行履歴・メタデータ管理機能

### REQ-3: アプリケーション層統合
**REQ-3.1** `EnhancedIntegratedWritingUseCase`実装
**REQ-3.2** 既存`IntegratedWritingUseCase`との統合
**REQ-3.3** プロンプト生成→実行→結果処理の一体化

### REQ-4: プレゼンテーション層統合（MCPツール）
**REQ-4.1** MCPツール`write`への統合（`src/mcp_servers/noveler/json_conversion_server.py`）
**REQ-4.2** 自動判定モード実装（Claude Code利用可能性チェック）
**REQ-4.3** 参考: 旧CLIフラグ（`--direct-claude`, `--prompt-only`）はMCP側引数/内部設定で等価制御

### REQ-5: エラーハンドリング・フォールバック
**REQ-5.1** Claude Code実行失敗時の従来ワークフローフォールバック
**REQ-5.2** 詳細エラーメッセージ・ログ出力
**REQ-5.3** リトライ機能実装

### REQ-6: 品質・パフォーマンス要件
**REQ-6.1** CommonPathService統合（ハードコーディング排除）
**REQ-6.2** Console統一利用（shared_utilities使用）
**REQ-6.3** 統合インポート管理システム準拠
**REQ-6.4** DDD依存方向遵守（Domain ← Application → Infrastructure）

## 3. 実装構成要素

### 3.1 インフラストラクチャ層
```python
# src/noveler/infrastructure/integrations/claude_code_integration_service.py
class ClaudeCodeIntegrationService:
    async def execute_claude_code_prompt(self, prompt: str) -> ClaudeCodeExecutionResponse
    async def execute_with_turn_limit(self, prompt: str, max_turns: int = 5) -> dict[str, Any]
```

### 3.2 ドメイン層
```python
# src/noveler/domain/value_objects/claude_code_execution.py
@dataclass
class ClaudeCodeExecutionRequest:
    prompt_content: str
    output_format: str = "json"
    max_turns: int = 3
    project_context_paths: list[Path] = None

@dataclass
class ClaudeCodeExecutionResponse:
    success: bool
    response_content: str
    json_data: dict | None = None
    execution_time_ms: float = 0.0
    error_message: str | None = None
```

### 3.3 アプリケーション層
```python
# src/noveler/application/use_cases/enhanced_integrated_writing_use_case.py
class EnhancedIntegratedWritingUseCase:
    def __init__(self, claude_code_service: ClaudeCodeIntegrationService, ...)
    async def execute(self, request: IntegratedWritingRequest) -> IntegratedWritingResponse
```

### 3.4 プレゼンテーション層（現行エントリポイント）
```python
# src/mcp_servers/noveler/json_conversion_server.py
@self.server.tool(name="write")
def write(episode_number: int, project_root: str | None = None) -> str
```

#### MCPパラメータ対応（CLIフラグ互換の具体例）
- 旧 `--direct-claude`（Claude Codeを強制的に直接実行）
  - MCPツール: `write_with_claude`
  - 例: `write_with_claude(episode=1)`
  - 効果: Claude内で利用する「原稿生成プロンプト」と保存先パスを返す（外部CLI不要のダイレクト運用）

- 旧 `--prompt-only`（プロンプト生成のみ・実行しない）
  - MCPツール（2通りの等価制御）:
    - 1) `noveler_write(episode_number=1, dry_run=True)` → ドライラン出力（ファイル出力あり/実行なし）
    - 2) `write_with_claude(episode=1)` → Claude用プロンプトと保存先を返却（実行はユーザー/Claude側）

- 旧 自動判定（デフォルト）
  - MCPツール: `noveler_write(episode_number=1, dry_run=False)`
  - 挙動: 利用可能性チェックによりClaude統合/フォールバックを内部判断

参考（実体実装箇所）
- `noveler_write`: `src/mcp_servers/noveler/json_conversion_server.py`（_register_individual_novel_tools）
- `write_with_claude`: 同上（Claude内ダイレクト原稿生成用ツール）

## 4. 受け入れ条件

### AC-1: 基本機能
- [ ] Claude Code実行パス自動検出
- [ ] プロンプト内容をClaude Codeに渡して実行
- [ ] JSON出力の解析・構造化データ取得
- [ ] 実行結果からの原稿内容抽出・保存

### AC-2: エラーハンドリング
- [ ] Claude Code実行失敗時の適切なエラーメッセージ表示
- [ ] フォールバック機能による従来ワークフロー継続
- [ ] タイムアウト処理・リソース管理

### AC-3: 品質基準
- [ ] B30品質作業指示書100%準拠
- [ ] 統合設定管理システム使用
- [ ] CommonPathService統合
- [ ] 仕様書マーク付きテスト実装（`@pytest.mark.spec("SPEC-CLAUDE-CODE-001")`）

### AC-4: パフォーマンス
- [ ] プロンプト実行時間3分以内
- [ ] メモリ使用量増加10%以内
- [ ] 並行実行対応

### AC-5: 後方互換性
- [ ] 既存`novel write`コマンド動作保持
- [ ] YAMLプロンプト生成機能継続利用可能
- [ ] 設定による動作モード切り替え

## 5. テスト戦略

### 5.1 単体テスト
```python
@pytest.mark.spec("SPEC-CLAUDE-CODE-001")
class TestClaudeCodeIntegrationService:
    def test_execute_prompt_成功時_正常なレスポンス返却(self)
    def test_execute_prompt_失敗時_エラー情報含むレスポンス返却(self)
    def test_claude_code_availability_実行可能時_True返却(self)
```

### 5.2 統合テスト
```python
@pytest.mark.spec("SPEC-CLAUDE-CODE-001")
class TestEnhancedIntegratedWritingWorkflow:
    async def test_enhanced_workflow_Claude_Code直接実行_成功(self)
    async def test_enhanced_workflow_フォールバック_動作確認(self)
```

### 5.3 アーキテクチャテスト
```python
@pytest.mark.spec("SPEC-CLAUDE-CODE-001")
class TestClaudeCodeIntegrationArchitecture:
    def test_dependency_direction_DDD準拠確認(self)
    def test_import_management_scripts_prefix_確認(self)
```

## 6. 実装スケジュール

### Phase 1: 基盤実装（2日）
1. 仕様書作成・レビュー
2. 失敗テスト作成（RED）
3. `ClaudeCodeIntegrationService`最小実装（GREEN）

### Phase 2: 統合実装（2日）
4. ドメインエンティティ実装
5. `EnhancedIntegratedWritingUseCase`実装
6. DDD適用リファクタリング（REFACTOR）

### Phase 3: MCP統合（1日）
7. MCPツール登録・引数連携
8. エラーハンドリング強化
9. 品質ゲートチェック・統合テスト

## 7. リスク・対応策

### R-1: Claude Code実行環境依存
**対応策**: 利用可能性自動チェック・フォールバック機能

### R-2: JSON解析エラー
**対応策**: 柔軟なパーサー実装・エラー時再試行

### R-3: 既存ワークフロー影響
**対応策**: 段階的移行・後方互換性保持

## 8. 品質基準

### B30準拠チェックリスト
- [x] 3コミット開発サイクル遵守
- [ ] 統合インポート管理システム使用
- [ ] 統合設定管理システム活用
- [ ] CommonPathService統合
- [ ] Console統一利用
- [ ] アーキテクチャテスト実装
- [ ] 仕様書マーク付きテスト実装

---
**作成日**: 2025年8月8日
**更新日**: 2025年9月13日
**承認**: 待機中
**実装担当**: Claude Code
**仕様書ID**: SPEC-CLAUDE-CODE-001

### 付録: 実装差分メモ（最新コード準拠）
- インフラ実装は `ClaudeCodeExecutionResponse(success=..., result=..., execution_time_ms=..., metadata=...)` の形で返す箇所あり。
  - ドメインVOのフィールド名は `response_content` / `json_data` であり、`result`/`metadata` はオプショナル互換として扱われています（利用側で `getattr` 参照）。
- 入口はMCPツール（server.tool: `write`）に移行。CLIフラグは内部設定/引数により等価制御。
