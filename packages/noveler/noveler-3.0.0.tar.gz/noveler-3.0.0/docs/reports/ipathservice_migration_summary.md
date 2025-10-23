# IPathService Migration Analysis Report

## Executive Summary

**Target**: Complete Domain layer path operation standardization
**Scope**: 38 TODO markers across 20+ files
**Priority**: ⭐⭐⭐⭐⭐ Highest (Architectural consistency)

---

## Current State Analysis

### Files with Multiple TODOs (Top Priority)

| File | TODO Count | Complexity | Priority |
|------|------------|------------|----------|
| `content_quality_enhancer.py` | 5 | Medium | P0 |
| `deliverable_check_service.py` | 4 | Medium | P0 |
| `episode_management_service.py` | 3 | High | P0 |
| `auto_repair_engine.py` | 3 | High | P0 |
| `quality_requirements_auto_fixer.py` | 2 | Medium | P1 |
| `episode_number_resolver.py` | 2 | Low | P1 |
| `b20_integrated_nih_prevention_service.py` | 2 | Medium | P1 |
| `a31_result_integrator.py` | 2 | Medium | P1 |

### Direct os Module Usage (Must Fix)

```
src/noveler/domain/services/auto_repair_engine.py:17
src/noveler/domain/services/enhanced_plot_generation_service.py:41
src/noveler/domain/services/environment_diagnostic_service.py:12
src/noveler/domain/services/episode_management_sync_service.py:16
src/noveler/domain/services/progressive_check_manager.py:27
src/noveler/domain/services/system.py:8
src/noveler/domain/services/system_diagnostics.py:8
src/noveler/domain/value_objects/a31_checklist_data.py:8
```

**Total**: 8 files requiring os module removal

---

## Migration Strategy

### Phase 1: High-Impact Files (Week 1-2)

**Target**: Files with 3+ TODOs or os module usage

1. **content_quality_enhancer.py** (5 TODOs)
   - Pattern: `Path(...).open()` → `path_service.read_yaml()`
   - Pattern: `Path(...).exists()` → `path_service.exists()`
   - Estimated effort: 2 hours

2. **deliverable_check_service.py** (4 TODOs)
   - Similar patterns to above
   - Estimated effort: 2 hours

3. **auto_repair_engine.py** (3 TODOs + os import)
   - Pattern: `os.walk()` → `path_service.walk()`
   - Pattern: `shutil.*` → path_service methods
   - Estimated effort: 3 hours (higher complexity)

4. **episode_management_service.py** (3 TODOs)
   - Estimated effort: 2 hours

### Phase 2: Medium-Impact Files (Week 3)

**Target**: Files with 2 TODOs

- quality_requirements_auto_fixer.py
- episode_number_resolver.py
- b20_integrated_nih_prevention_service.py
- a31_result_integrator.py

**Total estimated effort**: 6 hours

### Phase 3: Single-TODO Files (Week 4)

**Target**: Remaining 12+ files with 1 TODO each

**Estimated effort**: 8 hours (batch processing)

---

## Implementation Pattern

### Before (Current)
```python
# content_quality_enhancer.py:267
project_dir = Path(project_path)  # TODO: IPathServiceを使用するように修正
if not project_dir.exists():
    raise ProjectSettingsNotFoundError(...)

# content_quality_enhancer.py:274
with Path(character_file).open(encoding="utf-8") as f:
    character_data = yaml.safe_load(f)
```

### After (Target)
```python
# Constructor injection
def __init__(self, path_service: IPathService):
    self._path_service = path_service

# Usage
if not self._path_service.exists(project_path):
    raise ProjectSettingsNotFoundError(...)

character_data = self._path_service.read_yaml(
    self._path_service.join(project_path, "キャラクター.yaml")
)
```

---

## Risk Assessment

### Low Risk
- Files with simple Path operations (exists, join)
- Well-tested service layers

### Medium Risk
- Files with complex file I/O (auto_repair_engine.py)
- Files with os.walk() usage

### Mitigation
1. Each file modification must pass existing tests
2. Run full test suite after each batch (5-7 files)
3. Commit after each successful batch

---

## Success Metrics

- ✅ 0 TODO markers for IPathService in Domain layer
- ✅ 0 direct os module imports in Domain layer
- ✅ 100% IPathService DI coverage
- ✅ All existing tests pass
- ✅ importlinter validation pass

---

## Timeline

| Week | Target | Files | Hours |
|------|--------|-------|-------|
| 1-2 | Phase 1 | 4 files | 9h |
| 3 | Phase 2 | 4 files | 6h |
| 4 | Phase 3 | 12+ files | 8h |

**Total**: 23 hours (approximately 3 days of focused work)

