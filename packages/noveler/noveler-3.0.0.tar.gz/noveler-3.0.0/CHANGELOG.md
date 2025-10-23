# Changelog

## [3.0.0] - 2025-10-22

### 🎯 Initial Release

#### Highlights
- **MCP Server Integration**: Claude Code との完全統合
- **TDD + DDD Compliance**: テスト駆動開発とドメイン駆動設計
- **Comprehensive Quality System**: 品質管理システム統合
- **GitHub Actions CI/CD**: 自動テスト・デプロイパイプライン

#### Major Features
- ✨ MCP ツール 17 個の統合実装
- ✨ 品質チェック統合システム（rhythm/readability/grammar/style）
- ✨ 構造化ログ・分散トレーシング
- ✨ ブランチ保護ルール + CI/CD パイプライン

#### Quality Metrics
- Test Coverage: ≥ 80%
- Ruff Compliance: ✅ (with known exceptions)
- MyPy Strict: ✅
- ImportLinter DDD: ✅
- Code Quality Gate: ✅

#### Documentation
- Complete implementation guides (docs/guides/)
- Branch strategy and CI/CD documentation
- MCP integration documentation
- First release manual and automation setup

#### Infrastructure
- GitHub Actions PR check pipeline (lint/test/quality-gate)
- Automated deployment to PyPI on tag push
- GitHub Releases auto-generation from CHANGELOG
- Branch protection rules (main/dev)

---

## [Unreleased]

### 🎯 B20 Project Completions

#### Template Variable Expansion System - 2025-10-20
**Overall Score**: ✅ 95/100

**Purpose**: Jinja2ベースのYAMLテンプレート変数展開システム実装
**Implementation**: 3層アーキテクチャ（Domain/Infrastructure/Application）、6クラス、758 LOC

**Quality Metrics**:
- SOLID Compliance: ✅ 100% (5/5 principles)
- Test Coverage: ✅ 公開インターフェース100% (68 contract tests)
- Test Pass Rate: ✅ 100% (68/68 passing)
- Code Quality: ✅ All thresholds met
  - File max lines: 195/300
  - Class max methods: 5/10
  - Function max lines: 48/50
  - Cyclomatic complexity: All ≤10
  - Nesting depth: 3/4
- Risk Level: 🟢 LOW (高度なテストカバレッジ、純粋関数設計)

**Commits**:
- Implementation: `(pending)`
- Tests: `(pending)`
- Documentation: `(pending)`

**Deliverables**:
- [Requirements](b20-outputs/01_requirements.md) - 要求整理
- [Dependency List](b20-outputs/02_dependency_list.yaml) - 依存関係一覧
- [NFR Summary](b20-outputs/03_nfr_summary.md) - 非機能要件
- [CODEMAP Tree](b20-outputs/04_codemap_tree.txt) - 構造図
- [CODEMAP YAML](b20-outputs/05_codemap_yaml.yaml) - コンポーネント責任定義
- [SOLID Validation](b20-outputs/06_solid_validation.md) - SOLID準拠検証
- [Sequence Diagrams](b20-outputs/07_sequence_diagrams.md) - シーケンス図
- [Phase 3 Summary](b20-outputs/08_phase3_implementation_summary.md) - 実装サマリ
- [SOLID Compliance Report](b20-outputs/09_solid_compliance_report.md) - 最終SOLID検証
- [Phase 4 Testing Summary](b20-outputs/10_phase4_testing_summary.md) - テストサマリ
- [Output Contract Validation](b20-outputs/11_output_contract_validation.md) - 契約検証
- [Decision Log](b20-outputs/decision_log.yaml) - 9決定記録 (DEC-001～DEC-009)
- Contract Tests: 68 tests in `tests/contracts/templates/`

**Key Features**:
- ✨ Jinja2変数展開エンジン（VariableExpander）
- ✨ .novelerrc.yaml設定読み込み（ConfigLoader）
- ✨ LRUキャッシュ管理（CacheManager、mtime-based invalidation）
- ✨ テンプレートレンダラー統合（TemplateRenderer）
- ✨ Dataclass設定スキーマ（WritingStyleConfig）
- ✨ DI対応設計（Constructor Injection）

**Technical Decisions**:
- DEC-001: 3層アーキテクチャ採用（DDD準拠）
- DEC-002: Jinja2選定（標準的、YAML親和性高）
- DEC-003: LRU Cache + mtime invalidation
- DEC-004: Dataclass for Configuration Schema
- DEC-005: Constructor DI for testability
- DEC-006: B20閾値100%準拠
- DEC-007: Contract Testing Strategy
- DEC-008: Windows pytest-timeout解決
- DEC-009: YAML-Based Jinja2検証

---

## [2.3.0] - 2025-09-23

### 🚀 Major Features
- **構造化ログ・分散トレーシング完全実装**: logging_guidelines.md準拠の包括的ロギングシステム
  - **Phase 1**: 構造化ログ基盤（PII自動マスク、RequestContext、ErrorCategory）
  - **Phase 2**: パフォーマンス監視統合（LLM詳細ログ、CPU/メモリメトリクス）
  - **Phase 3**: ログ集約・分析基盤（SQLite永続化、異常検出、分散トレーシング）

### ✨ Features
- **StructuredLogger**: PII自動マスキング、extra_data標準化、リクエスト追跡
- **ログデコレーター**: @log_execution、@log_llm_execution（model_name指定・内部でStructuredLogger取得）、@log_cache_operation
- **EnhancedPerformanceMonitor**: CPU/メモリメトリクス統合、閾値ベース自動ログ
- **LogAggregatorService**: SQLiteベース永続化、柔軟クエリ、メトリクス計算
- **LogAnalyzer**: パフォーマンスボトルネック検出、エラーパターン分析、最適化レポート（NumPyベース、`pip install numpy` が必要）
- **DistributedTracer**: エンドツーエンド追跡、スパン管理、クリティカルパス分析

### 🔧 Improvements
- **ClaudeCodeExecutionService**: 構造化ログ対応、LLM実行の詳細メトリクス記録
- **MCP統合**: polish_manuscript_apply_toolの構造化ログ対応
- **デバッグ効率**: 構造化ログによる検索性50%向上、問題特定精度大幅改善

### 📚 Documentation
- Docs: clarify CLI separation (check=評価 / polish=改稿) and template search order (checks→backup→writing); update SPEC-QUALITY-110 / A32 / A33 / A40 / B20 / MCP API / templates README.
- **Release_v2.3.0.md**: 包括的リリースノート作成
- **logging-enhancement-proposal.md**: 改善提案書と実装ガイド

### 🧪 Testing
- **40件のテストケース**: Phase 1-3の包括的品質保証
  - Phase 1: 14件（構造化ログ基盤）
  - Phase 2: 10件（パフォーマンス監視統合）
  - Phase 3: 16件（集約・分析・トレーシング）

### 📊 Performance
- **ログ出力**: 平均 < 1ms（構造化処理含む）
- **分析クエリ**: P95 < 50ms（SQLiteインデックス最適化）
- **トレース記録**: < 0.5ms オーバーヘッド

## [2.2.14] - 2025-09-23

### 🔄 Breaking Changes
- **章番号・話番号フォーマット統一**: 新標準形式に変更
  - 章番号: `ch01` → `chapter01` (chapter00形式)
  - 話番号: `001`/`ep01` → `episode001` (episode000形式)

### ✨ Features
- **PlotViewpointRepository**: 新しいフォーマットサポートを追加
  - `episode001`, `episode010` 形式のエピソード検索
  - `chapter01.yaml` 形式のファイル検索
  - 旧形式との後方互換性を保持

### 🐛 Bug Fixes
- **テスト失敗修正**: 章番号・話番号フォーマット不整合を解決
  - `test_get_episode_viewpoint_info_*`: viewpoint情報がNoneになる問題
  - `test_successful_completion`: 章番号期待値の不整合
  - `test_creation`: メッセージフォーマットの不整合
  - `test_create_fallback_chapter_plot`: タイトルフォーマットの不整合

### 🔧 Improvements
- **CompleteEpisodeUseCase**: chapter00形式での章番号生成
- **ChapterPlotWithScenesUseCase**: chapter00形式メッセージ対応
- **EnhancedPlotGenerationUseCase**: episode000/chapter00形式対応

### 📚 Documentation
- **仕様書更新**: `SPEC-WRITE-018` でテストファイル名を新形式に更新

### 🧪 Testing
- **全テストケース更新**: 新フォーマットに対応
- **後方互換性テスト**: 旧形式データの処理確認

## [2.2.11] - 2025-09-22

- fix(initialization): use timezone-aware timestamps in ProjectInitialization to prevent AttributeError during entity creation on Python 3.12
- test(error-messages): remove unused `_long_sentence_error` fixture parameter to restore pytest setup

- chore: add dist MCP wrapper generator (scripts/ci/ensure_dist_wrapper.py), portable .mcp/config.json (relative args, cwd './', PYTHONPATH '.:./dist'), and optional importlinter integration (make lint-imports, pre-commit hook).
- refactor(domain): decouple Progressive/Deliverable/Configuration/Manuscript from static infra imports; use domain_console/ILogger, importlib, path service manager; keep test compatibility shims.
- test(reporting): default-enable fail-only NDJSON streaming of test progress (per-event records); allow disabling via LLM_REPORT_STREAM_FAIL=0/false/off; refine record schema (test_id, worker_id, duration_s, stdout/stderr, final_outcome).

## [2.2.10] - 2025-09-21

- feat(mcp): add `fix_style_extended` tool for opt-in style extensions
  - **FULLWIDTH_SPACE normalization**: Convert or remove full-width spaces with dialogue/narrative differentiation
    - Modes: `normalize` (→半角), `remove` (削除), `dialogue_only`, `narrative_only`, `disabled`
    - Smart dialogue detection with regex patterns for accurate text type recognition
  - **BRACKETS_MISMATCH auto-correction**: Simple heuristics to add missing bracket pairs
    - Modes: `auto` (full correction), `conservative` (safe additions only), `disabled`
    - Bracket pair detection and intelligent insertion logic
  - **Safety-first design**: `dry_run=true` by default with detailed preview display
  - **18th MCP tool**: Registered as standalone opt-in feature separate from main quality tools
- docs: update all documentation for new style extension features
  - Update tool count from 17 to 18 across B33_MCPツール統合ガイド, A33_執筆品質管理チェック, SPEC-MCP-002
  - Add comprehensive usage examples and safety feature documentation
  - Update A32_執筆コマンドガイド MCP migration correspondence table

## [2.2.9] - 2025-09-21

- perf(git): migrate .git directory from OneDrive to WSL2 native filesystem for dramatic performance improvement
  - Move `.git` directory from OneDrive sync to `~/.git-noveler` (WSL2 native storage)
  - Configure gitdir pointer for seamless operation with existing worktrees
  - **Performance improvements**:
    - `git status`: 20-30s → **2.15s** (10-15x faster)
    - `git log`: 5-10s → **0.008s** (625-1250x faster)
    - `git add .`: 15-25s → **2.03s** (7-12x faster)
  - Fix all worktree configurations (master + assistant-claude + assistant-codex)
  - Optimize Git settings: disable fsmonitor, enable preloadindex/fscache, generate commit-graph
  - Eliminate OneDrive sync conflicts and lock file issues
  - Complete backup created: `~/noveler-git-backup-20250921.tar.gz` (136MB)
- fix(tests): convert remaining synchronous test functions to async in `test_quality_check_use_case.py`
 - feat(tests): LLM向けpytest要約を導入し、`make test` をパラメトリック化
   - conftest: `--llm-report` オプションと `LLM_REPORT=1` で要約を有効化
   - 出力: `reports/llm_summary.jsonl`（JSONL）, `reports/llm_summary.txt`（テキスト）
   - STDOUTに `LLM:BEGIN ... LLM:END` タグで要約を出力
   - Makefile: `make test` に `FILE`/`K`/`M`/`VV` を追加（個別/絞り込み/冗長度）
   - 新ターゲット: `make test-last`（直近失敗を優先・-x）、`make test-changed`（git差分のテスト、なければlast-failed）

## [2.2.8] - 2025-09-21

- feat(readability): enhance dialogue line exclusion functionality for sentence length checks
  - Improve `_is_dialogue_line()` method to detect closing quotation marks (`」` and `』`) for multi-line dialogue
  - Fix parameter passing in `RunQualityChecksTool` to properly forward `exclude_dialogue_lines` to `CheckReadabilityTool`
  - Add comprehensive test coverage for dialogue exclusion in `test_run_quality_checks_exclude_dialogue.py`
  - Fix syntax errors in test files and async function definitions
- fix(mcp): resolve syntax errors in `mcp_protocol_adapter.py` and test files

## [2.2.7] - 2025-09-21

- refactor(presentation): move MCP server runtime to `noveler.presentation.mcp.server_runtime` and keep `mcp_servers/noveler/main.py` as a thin compatibility wrapper.
- feat(grammar): enhance `GRAMMAR_PUNCTUATION` auto-fix heuristics with morphology-aware boundary scoring and safer fallbacks.
- fix(cli): restore `--exclude-dialogue` handling within `noveler check` legacy path during run_quality_checks delegation.
- chore(ci): extend `make ci-smoke` with polish/apply/restore/write/list_artifacts smoke runs for MCP tools.
- chore(imports): add import-linter contract guarding the thin main delegate boundary.
All notable changes to this project will be documented in this file.
This project adheres to Keep a Changelog (in spirit) and Semantic Versioning.

## [2.0.0] - 2025-09-18

- Type: Breaking / Removed / Docs / Tests

### Breaking changes
- Remove Japanese line-width checks and forced line wrapping across all subcommands.
  - No line-width warnings, errors, or auto-fixes are produced anymore.
  - `--auto-fix` never inserts hard line breaks; behavior is idempotent.

### Removed
- CLI/tool schemas and options related to line width and wrapping:
  - `check_rhythm`: aspect `line_width` and thresholds for max line width.
  - `fix_quality_issues`: input options `enable_line_wrap`, `max_line_width`.
  - Quality presets/schema: `LINE_WIDTH_OVERFLOW`, `max_line_width_warn`, `max_line_width_critical`.
- Code paths implementing line-width detection/wrapping.

### Changed
- Update tool descriptions to remove line-width mentions.
- Improve Stage1 (technical polish) scope: safe punctuation/spacing normalization only.
- Update requirements/specs to reflect the new policy.

### Documentation
- Update requirements and specs:
  - `requirements/requirements_definition.md` (v5.2)
  - `requirements/requirements_traceability_matrix.yaml` (v2.1.1)
  - `specs/SPEC-A40A41-STAGE1-AUTOFIX.md` (line-width policy removed; breaking note added)
- Update guides and README:
  - `.novelerrc.yaml` sample (remove line-wrap keys and thresholds)
  - `README.md` (remove line-width examples; clarify behavior)
  - `docs/mcp/tools_usage_best_practices.md` (examples without line width)
  - `docs/A40_推敲品質ガイド.md` (explicitly states no line-width check/wrap provided)
  - `docs/A33_執筆品質管理チェック.md` (policy section updated)
  - `docs/B20_Claude_Code開発作業指示書.md` / `docs/A31_新システム利用ガイド.md`

### Tests
- Add unit tests ensuring line-width is not exposed nor applied:
  - `tests/unit/mcp_servers/tools/test_check_rhythm_no_line_width.py`
  - `tests/unit/mcp_servers/tools/test_fix_quality_issues_no_wrap.py`
  - `tests/unit/mcp_servers/tools/test_quality_metadata_no_line_width.py`

### Migration guide
- Remove from project configs and code:
  - `.novelerrc.*`: `line_wrap.*`, `thresholds.max_line_width_*`, and any use of `LINE_WIDTH_OVERFLOW`.
  - CLI/invocation code expecting `enable_line_wrap` / `max_line_width`.
  - Tests referencing line-width aspects or reason codes.
- Replace examples with punctuation/style/long-short sentence items where needed.

### Versioning note
- Recommended: bump `pyproject.toml` version from `1.0.0` to `2.0.0` upon release cut to reflect breaking changes.

## [Unreleased]

### Docs
- Add: Progressive Check API 仕様書（docs/mcp/progressive_check_api.md）。
- Update: B33_MCPツール統合ガイドに Progressive Check セクションを追記、統一エラー形式を明文化。
- Update: 開発者ガイドに Domain 依存ガードのキャッシュクリア手順と並列実行時の推奨マーカーを追記。

- docs: 旧 `bin/novel` ドキュメントを `noveler` / MCP ワークフローへ移行し、`docs/migration/novel_to_noveler.md` を追加。
- chore: Gitフックと `bin/noveler` のヘルプ出力を最新CLI仕様に合わせて更新。
- Type: Breaking / Docs / Tests

### Breaking changes
- Remove legacy MCP alias tools in favor of canonical noveler_* tools. The following
  aliases are no longer registered by the server:
  - write, write_stage, write_resume
  - check, check_basic, check_story_elements, check_story_structure,
    check_writing_expression, check_rhythm, check_fix
  - plot_generate, plot_validate
  - novel, init
- Use these tools instead: noveler_write, noveler_check, noveler_plot, noveler_complete,
  status, convert_cli_to_json, validate_json_response, get_file_reference_info.

### Documentation
- README: remove/replace legacy alias examples; clarify noveler_* usage only.

### Tests
- Update integration tool-registration expectations to modern tool names only.

### Fixed
- Initialization domain value objects now expose only the five canonical genres
  while retaining legacy aliases for compatibility.
- `InitializationConfig` is frozen to prevent accidental mutation and aligns
  validation feedback with the shared project-name rules.
- Template compatibility scoring applies a mismatch penalty so unrelated genre
  templates no longer outrank 50% suitability thresholds.


- chore: add dist MCP wrapper generator (scripts/ci/ensure_dist_wrapper.py), portable .mcp/config.json (relative args, cwd './', PYTHONPATH '.:./dist'), and optional importlinter integration (make lint-imports, pre-commit hook).
- refactor(domain): decouple Progressive/Deliverable/Configuration/Manuscript from static infra imports; use domain_console/ILogger, importlib, path service manager; keep test compatibility shims.
