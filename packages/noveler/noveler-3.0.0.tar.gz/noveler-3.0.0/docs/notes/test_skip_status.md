# Test Skip Status (2025-09-27)

## Summary
- `tests/unit/infrastructure/test_comprehensive_performance_optimizer.py`: now executes by default. Import stubs ensure optional deps are no longer required.
- `tests/unit/domain/test_domain_plot_workflow.py::test_verification_required_on_file_conflict`: skip removed after PlotCreationService confirmation fix.
- Remaining skip guards are limited to known integration gaps (`pytest-xdist` absent, SPEC-LLM-001). See table below.

## Current Skip Inventory
| Test Suite | Marker | Reason | Recovery Plan |
|------------|--------|--------|---------------|
| `tests/unit/reporting/test_fail_only_ndjson_xdist.py` | `skipif not _have_xdist()` | Guarded: still auto-bypassed when `pytest-xdist` missing locally, but CI now installs `pytest-xdist` so suite runs there. | None — documentation only. |
| `tests/integration/mcp/test_mcp_server_compliance.py` | `skipif not MCP_SERVER_AVAILABLE` | Pending MCP server harness bootstrap. | Remains open (Priority C); outside current scope. |
| `tests/integration/test_mcp_polish_integration.py` | `skipif not SPEC_LLM_001_COMPLETED` | Feature work still tracked separately. | See TODO.md Priority D. |

## Action Items
1. Ensure onboarding guides reference the lightweight performance stubs (done in this change set).
2. Keep TODO.md in sync when new skips are introduced or resolved.
