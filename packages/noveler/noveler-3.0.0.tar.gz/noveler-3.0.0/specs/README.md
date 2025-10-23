# specs index

このフォルダは仕様書をカテゴリ別に一覧化したものです。現用（ISSUE/稼働コンポーネント紐付け）のみを掲載しています。

運用ポリシー:
- 現用判定は E2E/REQ マッピングを一次ソースとする
- 旧版は `specs/_archive/` に退避
- 仕様書ファイル名は `SPEC-<CATEGORY>-<NNN>_<slug>.md` 形式とする
  - CATEGORYは大文字の英字略称（例: MCP, QUALITY, PLOT）
  - NNNはゼロ埋め3桁の連番を採番（領域毎に昇順管理、900番台は横断アーキ用途）
  - slugは英小文字・ハイフン/アンダースコアで構成した説明語句とし、必要に応じて `-v2` 等のバージョン尾を付与
  - 仕様移動時は参照元ドキュメントのリンク更新を併せて行う

## ARCH

- [SPEC-901-DDD-REFACTORING](./SPEC-901-DDD-REFACTORING.md)  (ARCH-—)

## ARTIFACT

- [SPEC-ARTIFACT-001-artifact-reference-system](./SPEC-ARTIFACT-001-artifact-reference-system.md)  (ARTIFACT-001)

## CLAUDE

- [SPEC-CLAUDE-001_claude_code_integration_system](./SPEC-CLAUDE-001_claude_code_integration_system.md)  (CLAUDE-001)

## EPISODE

- [SPEC-EPISODE-001_episode_management](./SPEC-EPISODE-001_episode_management.md)  (EPISODE-001)

## MCP

- [SPEC-MCP-001_mcp-tool-integration-system](./SPEC-MCP-001_mcp-tool-integration-system.md)  (MCP-001)
- [SPEC-MCP-002_mcp-tools-specification](./SPEC-MCP-002_mcp-tools-specification.md)  (MCP-002)

## PLOT

- [SPEC-PLOT-001_claude-code-integration-plot-generation](./SPEC-PLOT-001_claude-code-integration-plot-generation.md)  (PLOT-001)
- [SPEC-PLOT-002_chapter_plot_consistency_orchestrator](./SPEC-PLOT-002_chapter_plot_consistency_orchestrator.md)  (PLOT-002)

## QUALITY

- [SPEC-A40A41-STAGE1-AUTOFIX](./SPEC-A40A41-STAGE1-AUTOFIX.md)  (QUALITY-—)
- [SPEC-A40A41-STAGE23-POLISH](./SPEC-A40A41-STAGE23-POLISH.md)  (QUALITY-—)
- [SPEC-QUALITY-001_a31-checklist-automatic-fix-system](./SPEC-QUALITY-001_a31-checklist-automatic-fix-system.md)  (QUALITY-001)
- [SPEC-QUALITY-002_history-management](./SPEC-QUALITY-002_history-management.md)  (QUALITY-002)
- [SPEC-QUALITY-003_manual-improvement-process](./SPEC-QUALITY-003_manual-improvement-process.md)  (QUALITY-003)
- [SPEC-QUALITY-104_langsmith_bugfix_workflow](./SPEC-QUALITY-104_langsmith_bugfix_workflow.md)  (QUALITY-104)
 - [SPEC-QUALITY-110_progressive_check_flow](./SPEC-QUALITY-110_progressive_check_flow.md)  (QUALITY-110)

## WRITE

- [SPEC-WRITE-INTERACTIVE-001-v2](./SPEC-WRITE-INTERACTIVE-001-v2.md)  (WRITE-—)
 - [SPEC-WRITE-020_conversation_design_suite](./SPEC-WRITE-020_conversation_design_suite.md)  (WRITE-020)
