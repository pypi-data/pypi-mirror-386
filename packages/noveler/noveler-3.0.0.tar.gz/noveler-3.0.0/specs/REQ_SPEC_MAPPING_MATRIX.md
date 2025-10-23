# REQ-SPEC 対応マトリクス (requirements v5.1)
**バージョン**: 2.1
**作成日**: 2025-09-18
**目的**: As-built 要件 (v5.1) と現行仕様書の対応付け

## 1. Writing Workflow

| 要件ID | 要件名 | 主要仕様書 | 実装状況 |
| --- | --- | --- | --- |
| REQ-WRITE-CLI-001 | 18ステップ統合執筆フローをCLIから提供する | `SPEC-WRITE-018_integrated_writing_flow.md` | ✅ 実装済み |
| REQ-WRITE-STEPWISE-002 | A38準拠15ステップ執筆ユースケースを実装する | `SPEC-WRITE-015_stepwise_writing_use_case.md` | ✅ 実装済み |
| REQ-WRITE-MCP-003 | MCP経由で段階的執筆タスクと復旧を制御する | `SPEC-MCP-001_mcp-tool-integration-system.md`, `SPEC-MCP-002_mcp-tools-specification.md` | ✅ 実装済み |
| REQ-WRITE-TEN-004 | 10段階MCPツールで段階執筆を提供する | `SPEC-MCP-002_mcp-tools-specification.md`, `SPEC-WRITE-018_integrated_writing_flow.md` | 🔄 改訂中 |
| REQ-WRITE-DESIGN-005 | 会話/感情/情景/小道具設計ツールを提供する | `SPEC-WRITE-020_conversation_design_suite.md` *(作成予定)* | 📝 作成予定 |

## 2. Quality Management

| 要件ID | 要件名 | 主要仕様書 | 実装状況 |
| --- | --- | --- | --- |
| REQ-QUALITY-001 | 複数アスペクト統合の品質チェックを提供する | `SPEC-QUALITY-001_a31-checklist-automatic-fix-system.md`, `SPEC-A40A41-STAGE1-AUTOFIX.md`, `SPEC-A40A41-STAGE23-POLISH.md` | ✅ 実装済み |
| REQ-QUALITY-002 | 自動改善と品質レポートを生成する | 上記と同じ | ✅ 実装済み |
| REQ-QUALITY-003 | 適応的品質評価をDDD準拠で実装する | `SPEC-QUALITY-019_adaptive_quality_evaluation.md` | ✅ 実装済み |
| REQ-QUALITY-STAGED-004 | 段階的品質チェックフローをMCPで提供する | `SPEC-QUALITY-110_progressive_check_flow.md` *(作成予定)* | 📝 作成予定 |
| REQ-QUALITY-LANG-005 | LangSmith連携によるバグ修正フローを提供する | `SPEC-QUALITY-104_langsmith_bugfix_workflow.md` | 🔄 改訂中 |

## 3. Data Management

| 要件ID | 要件名 | 主要仕様書 | 実装状況 |
| --- | --- | --- | --- |
| REQ-DATA-001 | CLI結果をファイル参照付きJSONとして保存する | `SPEC-MCP-001_mcp-tool-integration-system.md`, `SPEC-ARTIFACT-001_artifact-reference-system.md` | ✅ 実装済み |
| REQ-DATA-002 | SHA256ベースのファイル参照と変更検知を提供する | `SPEC-ARTIFACT-001_artifact-reference-system.md` | ✅ 実装済み |
| REQ-DATA-003 | アーティファクト保管とバックアップ復元を行う | `SPEC-ARTIFACT-001_artifact-reference-system.md` | ✅ 実装済み |

## 4. Operations Management

| 要件ID | 要件名 | 主要仕様書 | 実装状況 |
| --- | --- | --- | --- |
| REQ-OPS-WRITE-001 | MCPクライアントから安全にファイルを書き込む | `SPEC-MCP-001_mcp-tool-integration-system.md`, `SPEC-MCP-002_mcp-tools-specification.md` | 🔄 改訂中 |

## 5. Architecture / Reliability

| 要件ID | 要件名 | 主要仕様書 | 実装状況 |
| --- | --- | --- | --- |
| REQ-ARCH-BUS-901 | MessageBus の Outbox / Idempotency / 再送制御を提供する | `SPEC-901-DDD-REFACTORING.md` | ✅ 実装済み（運用/信頼性機能完備） |

## 6. 参照資料
- Requirements v5.1: `requirements/requirements_definition.md`
- トレーサビリティ: `requirements/requirements_traceability_matrix.yaml`

## 7. 更新履歴
| Version | Date | Summary |
| --- | --- | --- |
| 2.3 | 2025-09-22 | SPEC-901 実装状況を「実装済み（運用/信頼性機能完備）」に更新（DLQ、メトリクス、CLI完全実装） |
| 2.2 | 2025-09-21 | SPEC-901 信頼性要件 (Outbox/Idempotency) を Architecture セクションへ追加 |
| 2.1 | 2025-09-18 | requirements v5.1 に合わせて TenStage/設計支援/段階品質/LangSmith/運用要件を追加し、対応状況を更新 |
| 2.0 | 2025-09-17 | requirements v5.0 に合わせて Writing/Quality/Data の6要件へ再構成 |
| 1.0 | 2025-09-04 | 旧31要件体系に基づく初版 |
