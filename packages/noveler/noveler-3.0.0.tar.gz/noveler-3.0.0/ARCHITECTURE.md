# Architecture Documentation

## DDD Layering Principles

This project follows Domain-Driven Design (DDD) layering to maintain clear separation of concerns:

```
┌─────────────────────────────┐
│     Presentation Layer      │  UI, CLI, MCP Servers
├─────────────────────────────┤
│    Infrastructure Layer     │  Adapters, External Systems
├─────────────────────────────┤
│     Application Layer       │  Use Cases, Service Orchestration
├─────────────────────────────┤
│       Domain Layer          │  Business Logic, Entities
└─────────────────────────────┘
```

### Dependency Rules

**Strict Enforcement via Quality Gates:**

- ✅ **Domain** may import: nothing outside Domain
- ✅ **Application** may import: Domain only
- ✅ **Infrastructure** may import: Domain, Application, and **controlled Presentation** (see exceptions)
- ✅ **Presentation** may import: all layers

**Forbidden Patterns:**
- ❌ Domain → Application/Infrastructure/Presentation
- ❌ Application → Presentation (except through Infrastructure adapters)
- ⚠️ Infrastructure → Presentation (allowed only through documented Adapter Pattern exceptions)

---

## Adapter Pattern for UI System Integration

### Rationale

Infrastructure layer occasionally needs to wrap Presentation layer UI components to provide DDD-compliant interfaces for Application layer consumption. This is an intentional architectural decision that maintains separation of concerns through abstraction.

### Design Principles

1. **Abstraction via Protocols**: Application layer defines Protocol interfaces (e.g., `IBatchProcessingService`, `IAnalyticsService`)
2. **Adapter Implementation**: Infrastructure implements adapters that wrap Presentation UI systems
3. **Lazy Loading**: Adapters use lazy initialization to avoid circular dependencies
4. **Null Object Fallback**: Graceful degradation when Presentation UI is unavailable

### Architectural Justification

**Why Infrastructure→Presentation is acceptable in adapters:**

- Infrastructure serves as an **anti-corruption layer** between Application and Presentation
- Adapters **isolate** Presentation dependencies, preventing leak to Application/Domain
- Application layer depends only on **Protocol abstractions**, not concrete Presentation classes
- Enables **testability** through dependency injection and Null Object pattern

### Approved Adapter Pattern Exceptions

The following files are explicitly allowed to import from Presentation layer:

#### 1. `src/noveler/infrastructure/adapters/analytics_adapter.py`

**Purpose**: Wraps `WritingAnalyticsSystem` from Presentation UI

**Interface**: Implements `IAnalyticsService` Protocol

**Example**:
```python
class AnalyticsAdapter:
    """Adapter for analytics operations."""

    def _get_analytics_system(self):
        """Lazy-load analytics system to avoid circular imports."""
        if self._analytics_system is None:
            try:
                from noveler.presentation.ui.analytics import WritingAnalyticsSystem
                self._analytics_system = WritingAnalyticsSystem(self.project_root)
            except ImportError as e:
                self.logger.warning(f"WritingAnalyticsSystem not available: {e}")
                from noveler.application.services.analytics_service import NullAnalyticsService
                self._analytics_system = NullAnalyticsService(self.project_root)
        return self._analytics_system
```

**DDD Compliance**: Application layer uses `IAnalyticsService` Protocol, never imports adapter directly

#### 2. `src/noveler/infrastructure/adapters/batch_processing_adapter.py`

**Purpose**: Wraps `BatchProcessingSystem` from Presentation UI

**Interface**: Implements `IBatchProcessingService` Protocol

**Key Pattern**: Same lazy-loading with Null Object fallback as analytics_adapter

**DDD Compliance**: Application layer (e.g., `writing.py`) injects adapter via constructor, maintains Protocol dependency

#### 3. `src/noveler/infrastructure/mcp/handlers.py`

**Purpose**: MCP request handlers relocated from Presentation layer

**Status**: **Legacy code under gradual refactoring**

**Known Issue**: Still contains import from `noveler.presentation.mcp.adapters.io` (line 87)

**Future Work**: Extract `resolve_path_service` to Infrastructure layer to eliminate Presentation dependency

---

## Quality Gate Configuration

**Script**: `scripts/quality_gates/forbidden_imports_gate.py`

**Mechanism**: Pattern-based detection of forbidden cross-layer imports

**Enforcement**: Pre-commit hook in `.pre-commit-config.yaml`

**Adapter Exceptions**: Configured via `ADAPTER_PATTERN_EXCEPTIONS` list (lines 63-72)

**Exit Codes**:
- `0`: No violations (CI passes)
- `1`: Violations detected (CI fails)
- `2`: Script execution error

**Verification**:
```bash
python scripts/quality_gates/forbidden_imports_gate.py
# Expected: ✅ No forbidden imports detected
```

---

## Migration History

**Initiative**: Infrastructure Console/Path DI Rollout (2025)

**Objective**: Eliminate 67 DDD layering violations

**Results**:
- Phase 1: Console imports (59 files, 67→8 violations)
- Phase 2: Path service imports (12 files, 27→12 violations)
- Phase 3-1: UI system DI pattern (6 violations, 12→8)
- Phase 3-2: MCP handler relocation (3 violations, 8→5)
- Phase 3-3: Domain factory DI refactoring (2 violations, 5→3)
- **Total**: 95.5% violation reduction (67→3 → 0 with exceptions)

**Commits**:
- `030163f4`: Phase 2 path/utility imports migration
- `f95a09cc`: Phase 3-1 UI system adapter pattern
- `1b9f9f02`: Phase 3-2 MCP handler relocation
- `27882979`: Phase 3-3 Domain factory DI refactoring
- `ff4e7f16`: Documentation update

**Documentation**: See `TODO.md` lines 16-55 for detailed phase breakdown

---

## Testing Strategy

**Principle**: New features follow **Specification → Test → Implementation → Refactor** workflow

**Test Markers**: `@pytest.mark.spec('SPEC-XXX')` links tests to specifications

**Quality Checks**: Unified via `run_quality_checks` with `.novelerrc.yaml` configuration

**LLM-Friendly Output**: `reports/llm_summary.{jsonl,txt}` for machine-readable test results

**Pre-commit Integration**: Forbidden imports gate runs automatically before commit

---

## Quality Gate System (Gate B/C)

The project implements a two-gate quality system for manuscript validation:

### Gate B: Automated Quality Checks

**Purpose**: Validates rhythm, readability, and grammar against configurable thresholds

**Configuration**: `config/quality/gate_defaults.yaml`

**Metadata Output**:
```json
{
  "gate_b_pass": true,
  "gate_b_should_fail": false,
  "gate_b_thresholds": {"rhythm": 80, "readability": 80, "grammar": 90},
  "gate_b_evaluation": {
    "rhythm": {"required": 80, "actual": 85, "pass": true}
  }
}
```

**MCP Integration**: Available via `run_quality_checks` tool with `gate_thresholds` parameter

### Gate C: Editorial Checklist

**Purpose**: Validates 12-step editorial checklist completion

**Evaluation**: Subprocess call to `scripts/tools/editorial_checklist_evaluator.py`

**Metadata Output**:
```json
{
  "gate_c_pass": true,
  "gate_c_should_fail": false,
  "gate_c_counts": {
    "total": 12,
    "pass": 12,
    "note": 0,
    "todo": 0,
    "unknown": 0,
    "checked": 12,
    "unchecked": 0
  },
  "gate_c_counts_by_status": {"PASS": 12, "NOTE": 0, "TODO": 0, "UNKNOWN": 0}
}
```

**MCP Integration**: Enable with `enable_gate_c: true` and `editorial_report` path

### CI/CD Integration

**Unified Metadata**: Both gates contribute to `should_fail` flag for build decision-making

**Usage**:
```bash
# CLI wrapper
bin/check-all --episode 1

# MCP tool with both gates
noveler mcp call run_quality_checks '{
  "episode_number": 1,
  "gate_thresholds": {"rhythm": 80},
  "enable_gate_c": true
}'
```

**Documentation**: See `docs/guides/quality_gate_workflow.md` for complete guide

---

## YAML Validator Array Addressing (v2.1)

**Feature**: Path resolution with array wildcard support for validators

**Implementation**: `src/noveler/infrastructure/utils/path_resolver.py`

**Specification**: SPEC-YAML-021

**Capabilities**:
- Dotted path resolution: `metadata.title`
- Array indexing: `episodes[0].title`
- Array wildcards: `episodes[*].word_count`
- Nested wildcards: `chapters[*].sections[*].hook`
- Numeric aggregation: min/max/avg

**Usage Example**:
```python
from noveler.infrastructure.utils.path_resolver import PathResolver

data = {"episodes": [{"word_count": 4500}, {"word_count": 5200}]}

# Wildcard resolution
counts = PathResolver.resolve(data, "episodes[*].word_count")  # [4500, 5200]

# Aggregation
avg = PathResolver.aggregate(data, "episodes[*].word_count", "avg")  # 4850.0
```

**Test Coverage**: 39 tests (100% pass rate) in `tests/unit/infrastructure/utils/test_path_resolver.py`

---

## Test Stability and Filesystem Isolation (SPEC-TEST-022)

**Objective**: Minimize hardcoded absolute paths in tests and improve filesystem isolation

**Specification**: `specs/SPEC-TEST-022_filesystem_test_stability.md`

**Key Principles**:
- Use `pytest.tmpdir` or `tempfile.TemporaryDirectory` for integration tests
- Mock `Path` operations consistently for unit tests
- Add explicit comments explaining test isolation approach
- Classify tests into categories: A (fully mocked), B (partial mock), C (integration)

**Completed Improvements**:
- **Phase 1** (2025-10-01): Modified 7 files to improve filesystem isolation
  - `test_enhanced_prompt_save_integration.py`: Changed `/nonexistent/path` to `tmp_path / "nonexistent_project"`
  - `test_enhanced_previous_episode_integration.py`: Same pattern for error handling tests
  - Added explanatory docstrings to 5 unit test files
  - Isolation Score: 95%+ (実ファイルシステムに依存しないテスト)

- **Phase 2** (2025-10-01): PlotViewpointRepository suite refactoring
  - Unified mocking pattern: `patch.object(Path, "exists")` instead of `patch("pathlib.Path.exists")`
  - Removed unnecessary `tempfile.TemporaryDirectory` usage in unit tests
  - Added explanatory docstrings to all 11 test methods
  - All tests passing with consistent mocking strategy
  - File: `test_plot_viewpoint_repository_error_handling.py` (11 tests, 306 lines)

- **Phase 3** (2025-10-01): Systematic audit of remaining persistence/path-related tests ✅ **COMPLETE**
  - Integration tests (2 files):
    - `test_artifact_mcp_tools.py`: 2 tests modified to use `tmp_path` fixture
    - `test_message_bus_integration.py`: 1 test modified to use `tmp_path` fixture
  - Unit tests (5 files):
    - `test_claude_analysis_request_generation_use_case.py`: Added isolation docstring
    - `test_settings_file_watcher_refactored.py`: Added isolation docstring
    - `test_plot_progress_repository.py` (2 files): Added isolation docstrings
    - `test_step_output_manager.py`: Modified to use `temp_project_root` fixture
  - All 7 files modified with improved isolation patterns
  - Tests verified passing with filesystem isolation

**Best Practices**:
```python
# ✅ Integration tests: Use tmp_path fixture
def test_error_handling(self, tmp_path: Path):
    """Note: 存在しないプロジェクトルートでのエラーハンドリングを検証。
    一時ディレクトリ内の存在しないサブディレクトリを使用してファイルシステムの隔離を保証。
    """
    invalid_root = tmp_path / "nonexistent_project"
    # Test code...

# ✅ Unit tests: Explicit mocking with comments
def test_nonexistent_path(self):
    """Note: Path.exists をモック - 実ファイルシステムへのアクセスなし。
    パス文字列は任意の値で良いため/nonexistentを使用。
    """
    with patch.object(Path, "exists", return_value=False):
        # Test code...
```

**Summary**: 15 files total modified across Phase 1-3 with improved filesystem isolation patterns.

---

## References

- **CLAUDE.md**: MCP operations, B20 workflow, testing contracts
- **AGENTS.md**: Code style, commenting standards, collaboration principles
- **TODO.md**: Current task status and initiative tracking
- **CODEMAP.yaml**: Full codebase dependency map (134KB+)
- **SPEC-YAML-021**: Array addressing specification
- **SPEC-TEST-022**: Filesystem test stability specification
