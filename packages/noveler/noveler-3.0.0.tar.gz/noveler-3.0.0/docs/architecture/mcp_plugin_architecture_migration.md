# 繝励Λ繧ｰ繧､繝ｳ繧｢繝ｼ繧ｭ繝・け繝√Ε遘ｻ陦瑚ｨ育判・亥ｮ牙・繝ｻ谿ｵ髫守噪繧｢繝励Ο繝ｼ繝・ｼ・
**Status**: 笨・**COMPLETED** (2025-09-30)
**Result**: All 6 phases successfully completed, 18/18 tools migrated

## 迴ｾ迥ｶ蛻・梵

### 蝠城｡檎せ
1. **server_runtime.py (1300陦・**: 60+繝・・繝ｫ縺ｮ逋ｻ骭ｲ縺碁寔荳ｭ
2. **handlers.py (1300陦・**: 18繝・・繝ｫ繧ｯ繝ｩ繧ｹ繧貞叉蠎ｧ縺ｫ繧､繝ｳ繝昴・繝茨ｼ・inter縺悟・縺ｫ謌ｻ縺励◆・・3. **dispatcher.py**: 60蛟九・繝上Φ繝峨Λ繝ｼ逋ｻ骭ｲ繧定ｵｷ蜍墓凾縺ｫ隧穂ｾ｡
4. **萓晏ｭ倬未菫・*: 蟇・ｵ仙粋・・erver 竊・dispatcher 竊・handlers 竊・25 tool classes・・
### 繝ｪ繧ｹ繧ｯ隧穂ｾ｡
- **High**: 繝・せ繝亥・髱｢譖ｸ縺肴鋤縺茨ｼ・5+ tests・・- **High**: 譌｢蟄倥・譛ｬ逡ｪ迺ｰ蠅・∈縺ｮ蠖ｱ髻ｿ
- **Medium**: 蠕梧婿莠呈鋤諤ｧ縺ｮ邯ｭ謖・- **Low**: 繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ繝・げ繝ｬ繝ｼ繝・
## 谿ｵ髫守噪遘ｻ陦梧姶逡･・・繧ｹ繝・ャ繝暦ｼ・
### Phase 0: 蝓ｺ逶､貅門ｙ・・-2譌･・俄怛 謗ｨ螂ｨ
**逶ｮ逧・*: 遐ｴ螢顔噪螟画峩縺ｪ縺励↓蝓ｺ逶､繧呈紛蛯・
```python
# 1. Plugin蝓ｺ蠎輔け繝ｩ繧ｹ縺ｮ霑ｽ蜉
# src/noveler/presentation/mcp/plugin_base.py
from abc import ABC, abstractmethod
from typing import Any, Callable

class MCPToolPlugin(ABC):
    """MCP Tool Plugin interface"""
    
    @abstractmethod
    def get_name(self) -> str:
        """繝・・繝ｫ蜷阪ｒ霑斐☆ (萓・ 'run_quality_checks')"""
        pass
    
    @abstractmethod
    def get_handler(self) -> Callable:
        """繝上Φ繝峨Λ繝ｼ髢｢謨ｰ繧定ｿ斐☆"""
        pass
    
    @property
    def lazy_load(self) -> bool:
        """驕・ｻｶ繝ｭ繝ｼ繝峨ｒ譛牙柑縺ｫ縺吶ｋ縺具ｼ域里螳・ True・・""
        return True

# 2. PluginRegistry縺ｮ霑ｽ蜉・域里蟄倥さ繝ｼ繝峨→荳ｦ蟄假ｼ・# src/noveler/presentation/mcp/plugin_registry.py
class PluginRegistry:
    """驕・ｻｶ繝ｭ繝ｼ繝牙ｯｾ蠢懊・繝励Λ繧ｰ繧､繝ｳ繝ｬ繧ｸ繧ｹ繝医Μ"""
    
    def __init__(self):
        self._plugins: dict[str, str] = {}  # name -> module_path
        self._loaded: dict[str, MCPToolPlugin] = {}
        self._legacy_fallback: dict[str, Callable] = {}  # 蠕梧婿莠呈鋤逕ｨ
    
    def register_plugin(self, name: str, module_path: str):
        """繝励Λ繧ｰ繧､繝ｳ逋ｻ骭ｲ・医う繝ｳ繝昴・繝医・逋ｺ逕溘＠縺ｪ縺・ｼ・""
        self._plugins[name] = module_path
    
    def register_legacy(self, name: str, handler: Callable):
        """譌｢蟄倥ワ繝ｳ繝峨Λ繝ｼ縺ｮ逋ｻ骭ｲ・・hase 3縺ｧ蜑企勁・・""
        self._legacy_fallback[name] = handler
    
    def get_handler(self, name: str) -> Callable | None:
        # Legacy fallback蜆ｪ蜈茨ｼ域里蟄倥さ繝ｼ繝峨ｒ螢翫＆縺ｪ縺・ｼ・        if name in self._legacy_fallback:
            return self._legacy_fallback[name]
        
        # Plugin邨檎罰
        if name not in self._loaded and name in self._plugins:
            module = importlib.import_module(self._plugins[name])
            self._loaded[name] = module.create_plugin()
        
        return self._loaded[name].get_handler() if name in self._loaded else None
```

**螟画峩轤ｹ**:
- 笨・譁ｰ隕上ヵ繧｡繧､繝ｫ霑ｽ蜉縺ｮ縺ｿ・域里蟄倥さ繝ｼ繝牙､画峩縺ｪ縺暦ｼ・- 笨・繝・せ繝井ｸ崎ｦ・ｼ域悴菴ｿ逕ｨ縺ｮ縺溘ａ・・- 笨・繝ｪ繧ｹ繧ｯ繧ｼ繝ｭ

**讀懆ｨｼ**:
```bash
# 繧､繝ｳ繝昴・繝医ユ繧ｹ繝医・縺ｿ
python -c "from noveler.presentation.mcp.plugin_base import MCPToolPlugin; print('OK')"
python -c "from noveler.presentation.mcp.plugin_registry import PluginRegistry; print('OK')"
```

---

### Phase 1: 繝代う繝ｭ繝・ヨ螳溯｣・ｼ・-3譌･・・**逶ｮ逧・*: 1繝・・繝ｫ縺ｧ繝励Λ繧ｰ繧､繝ｳ蛹悶ｒ讀懆ｨｼ

```python
# 1. 繝代う繝ｭ繝・ヨ逕ｨ繝励Λ繧ｰ繧､繝ｳ縺ｮ菴懈・
# src/noveler/presentation/mcp/plugins/check_readability_plugin.py
from noveler.presentation.mcp.plugin_base import MCPToolPlugin
from noveler.presentation.mcp.adapters import handlers

class CheckReadabilityPlugin(MCPToolPlugin):
    def get_name(self) -> str:
        return "check_readability"
    
    def get_handler(self):
        return handlers.check_readability

def create_plugin() -> MCPToolPlugin:
    return CheckReadabilityPlugin()

# 2. dispatcher.py 縺ｫ PluginRegistry 繧堤ｵｱ蜷・# src/noveler/presentation/mcp/dispatcher.py
from noveler.presentation.mcp.plugin_registry import PluginRegistry

_registry = PluginRegistry()

# Legacy handlers・域里蟄假ｼ・_TOOL_DISPATCH_TABLE: dict[str, ToolHandler] = {
    "run_quality_checks": handlers.run_quality_checks,
    # ... 59蛟・}

# Plugin逋ｻ骭ｲ・・蛟九・縺ｿ・・_registry.register_plugin("check_readability", 
                          "noveler.presentation.mcp.plugins.check_readability_plugin")

def get_handler(name: str) -> ToolHandler | None:
    # Plugin繧貞━蜈・    plugin_handler = _registry.get_handler(name)
    if plugin_handler:
        return plugin_handler
    
    # Legacy fallback
    return _TOOL_DISPATCH_TABLE.get(name)
```

**螟画峩轤ｹ**:
- 笨・1繝・・繝ｫ縺ｮ縺ｿ繝励Λ繧ｰ繧､繝ｳ蛹・- 笨・譌｢蟄倥ワ繝ｳ繝峨Λ繝ｼ縺ｯfallback
- 笨・繝・せ繝亥ｽｱ髻ｿ: check_readability髢｢騾｣縺ｮ縺ｿ

**讀懆ｨｼ**:
```bash
# check_readability縺ｮ繝・せ繝医・縺ｿ螳溯｡・pytest tests/unit/presentation/mcp/ -k "readability" -v

# 蜈ｨ繝・せ繝医〒蝗槫ｸｰ繝√ぉ繝・け
pytest tests/unit/presentation/mcp/ -v
```

---

### Phase 2: 谿ｵ髫守噪繝励Λ繧ｰ繧､繝ｳ蛹厄ｼ・-2騾ｱ髢難ｼ・**逶ｮ逧・*: 谿九ｊ17繝・・繝ｫ繧帝・ｬ｡繝励Λ繧ｰ繧､繝ｳ蛹・
**蜆ｪ蜈磯・ｽ・*:
1. **騾ｱ1**: Quality邉ｻ (5繝・・繝ｫ) - run_quality_checks, improve_quality_until, fix_quality_issues, get_issue_context, export_quality_report
2. **騾ｱ2**: Readability/Grammar邉ｻ (4繝・・繝ｫ) - check_readability, check_grammar, check_style, check_rhythm
3. **騾ｱ3**: Polish邉ｻ (5繝・・繝ｫ) - polish_manuscript, polish_manuscript_apply, restore_manuscript_from_artifact, polish, generate_episode_preview
4. **騾ｱ4**: 縺昴・莉・(4繝・・繝ｫ) - test_result_analysis, backup_management, list_quality_presets, get_quality_schema

**豈朱ｱ縺ｮ繧ｿ繧ｹ繧ｯ**:
```bash
# 1. 繝励Λ繧ｰ繧､繝ｳ菴懈・
create src/noveler/presentation/mcp/plugins/{tool_name}_plugin.py

# 2. 繝ｬ繧ｸ繧ｹ繝医Μ逋ｻ骭ｲ
edit src/noveler/presentation/mcp/dispatcher.py  # _registry.register_plugin()

# 3. 繝・せ繝亥ｮ溯｡・pytest tests/unit/presentation/mcp/ -k "{tool_name}" -v

# 4. 繝ｪ繧ｰ繝ｬ繝・す繝ｧ繝ｳ繝・せ繝・pytest tests/unit/presentation/mcp/ -v

# 5. 繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ險域ｸｬ
python -m timeit -s "from src.noveler.presentation.mcp import server_runtime" "pass"
```

**繝ｭ繝ｼ繝ｫ繝舌ャ繧ｯ謇矩・*:
```python
# 繝励Λ繧ｰ繧､繝ｳ蜑企勁
_registry.unregister_plugin("{tool_name}")

# Legacy fallback縺瑚・蜍輔〒譛牙柑蛹悶＆繧後ｋ
```

---

### Phase 3: Legacy蜑企勁・・-5譌･・・**逶ｮ逧・*: 螳悟・繝励Λ繧ｰ繧､繝ｳ蛹門ｾ後↓譌ｧ繧ｳ繝ｼ繝峨ｒ蜑企勁

```python
# 1. _TOOL_DISPATCH_TABLE 蜑企勁
# src/noveler/presentation/mcp/dispatcher.py
- from noveler.presentation.mcp.adapters import handlers
- _TOOL_DISPATCH_TABLE: dict[str, ToolHandler] = {...}

def get_handler(name: str) -> ToolHandler | None:
-   plugin_handler = _registry.get_handler(name)
-   if plugin_handler:
-       return plugin_handler
-   return _TOOL_DISPATCH_TABLE.get(name)
+   return _registry.get_handler(name)

# 2. handlers.py 縺ｮ繝・・繝ｫ繧ｯ繝ｩ繧ｹ繧､繝ｳ繝昴・繝亥炎髯､
# src/noveler/presentation/mcp/adapters/handlers.py
- from mcp_servers.noveler.tools.check_readability_tool import CheckReadabilityTool
# ... 17蛟句炎髯､
```

**讀懆ｨｼ**:
```bash
# 繧､繝ｳ繝昴・繝域凾髢楢ｨ域ｸｬ
python -c "import time; s=time.time(); from src.noveler.presentation.mcp import server_runtime; print(f'{time.time()-s:.2f}s')"

# 譛溷ｾ・､: <2遘・
# 蜈ｨ繝・せ繝亥ｮ溯｡・pytest tests/unit/presentation/mcp/ -v
```

---

### Phase 4: 繝励Λ繧ｰ繧､繝ｳ閾ｪ蜍墓､懷・・・騾ｱ髢難ｼ・**逶ｮ逧・*: 蜍慕噪繝励Λ繧ｰ繧､繝ｳ逋ｻ骭ｲ縺ｮ螳溽樟

```python
# src/noveler/presentation/mcp/plugin_registry.py
def auto_discover_plugins(self, base_path: Path):
    """plugins/繝・ぅ繝ｬ繧ｯ繝医Μ縺九ｉ繝励Λ繧ｰ繧､繝ｳ繧定・蜍墓､懷・"""
    for file in base_path.glob("*_plugin.py"):
        module_name = file.stem
        module_path = f"noveler.presentation.mcp.plugins.{module_name}"
        
        module = importlib.import_module(module_path)
        plugin = module.create_plugin()
        self.register_plugin(plugin.get_name(), module_path)

# 菴ｿ逕ｨ萓・_registry = PluginRegistry()
_registry.auto_discover_plugins(Path(__file__).parent / "plugins")
```

**繝｡繝ｪ繝・ヨ**:
- 笨・譁ｰ隕上ヤ繝ｼ繝ｫ霑ｽ蜉譎ゅ↓dispatcher.py邱ｨ髮・ｸ崎ｦ・- 笨・繝励Λ繧ｰ繧､繝ｳ縺ｮ繝帙ャ繝医Μ繝ｭ繝ｼ繝牙庄閭ｽ

---

### Phase 5: 繝・せ繝医Μ繝輔ぃ繧ｯ繧ｿ繝ｪ繝ｳ繧ｰ・・-2騾ｱ髢難ｼ・**逶ｮ逧・*: 繝励Λ繧ｰ繧､繝ｳ縺ｫ蟇ｾ蠢懊＠縺溘ユ繧ｹ繝域ｧ矩縺ｸ縺ｮ遘ｻ陦・
```python
# tests/unit/presentation/mcp/conftest.py
@pytest.fixture
def mock_plugin_registry():
    """繝・せ繝育畑縺ｮ繝励Λ繧ｰ繧､繝ｳ繝ｬ繧ｸ繧ｹ繝医Μ"""
    registry = PluginRegistry()
    
    # Mock繝励Λ繧ｰ繧､繝ｳ繧堤匳骭ｲ
    class MockPlugin(MCPToolPlugin):
        def get_name(self): return "test_tool"
        def get_handler(self): return lambda args: {"success": True}
    
    registry._loaded["test_tool"] = MockPlugin()
    return registry

# tests/unit/presentation/mcp/test_plugin_registry.py
def test_plugin_lazy_loading(mock_plugin_registry):
    # 繝励Λ繧ｰ繧､繝ｳ縺碁≦蟒ｶ繝ｭ繝ｼ繝峨＆繧後ｋ縺薙→繧呈､懆ｨｼ
    assert "test_tool" not in mock_plugin_registry._loaded
    handler = mock_plugin_registry.get_handler("test_tool")
    assert handler is not None
    assert "test_tool" in mock_plugin_registry._loaded
```

---

### Phase 6: 繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ譛驕ｩ蛹厄ｼ・-5譌･・・**逶ｮ逧・*: 繝励Λ繧ｰ繧､繝ｳ繧ｭ繝｣繝・す繝･縺ｨ繧ｦ繧ｩ繝ｼ繝繧｢繝・・

```python
# src/noveler/presentation/mcp/plugin_registry.py
class PluginRegistry:
    def warmup(self, tool_names: list[str]):
        """鬆ｻ郢√↓菴ｿ縺・ヤ繝ｼ繝ｫ繧剃ｺ句燕繝ｭ繝ｼ繝・""
        for name in tool_names:
            self.get_handler(name)  # 繧ｭ繝｣繝・す繝･縺ｫ霈峨○繧・    
    def clear_cache(self):
        """繧ｭ繝｣繝・す繝･繧ｯ繝ｪ繧｢・医ユ繧ｹ繝育畑・・""
        self._loaded.clear()

# codex.mcp.json
{
  "mcpServers": {
    "noveler": {
      "warmup_tools": ["run_quality_checks", "check_readability"]
    }
  }
}
```

---

## 繝ｪ繧ｹ繧ｯ霆ｽ貂帷ｭ・
### 1. Feature Flag蛻ｶ蠕｡
```python
# config.py
PLUGIN_ARCHITECTURE_ENABLED = os.getenv("NOVELER_PLUGIN_ARCH", "false") == "true"

# dispatcher.py
if PLUGIN_ARCHITECTURE_ENABLED:
    return _registry.get_handler(name)
else:
    return _TOOL_DISPATCH_TABLE.get(name)
```

### 2. 繝ｭ繝ｼ繝ｫ繝舌ャ繧ｯ繝励Λ繝ｳ
```bash
# 蜷Пhase縺ｧgit tag繧剃ｽ懈・
git tag phase-0-baseline
git tag phase-1-pilot
git tag phase-2-migration-week1

# 繝ｭ繝ｼ繝ｫ繝舌ャ繧ｯ
git reset --hard phase-1-pilot
```

### 3. 繝｢繝九ち繝ｪ繝ｳ繧ｰ
```python
# plugin_registry.py
class PluginRegistry:
    def __init__(self):
        self._metrics = {"load_count": 0, "load_time_ms": []}
    
    def get_handler(self, name: str):
        start = time.time()
        handler = self._get_handler_impl(name)
        self._metrics["load_time_ms"].append((time.time() - start) * 1000)
        self._metrics["load_count"] += 1
        return handler
```

---

## 謌仙粥蝓ｺ貅・
| Phase | 蝓ｺ貅・|
|-------|------|
| Phase 0 | 繧､繝ｳ繝昴・繝医お繝ｩ繝ｼ縺ｪ縺・|
| Phase 1 | check_readability繝・せ繝亥・騾夐℃ + 襍ｷ蜍墓凾髢・<5遘・|
| Phase 2 | 蜈ｨ55繝・せ繝磯夐℃ + 襍ｷ蜍墓凾髢・<3遘・|
| Phase 3 | 蜈ｨ55繝・せ繝磯夐℃ + 襍ｷ蜍墓凾髢・<2遘・|
| Phase 4 | 譁ｰ隕上・繝ｩ繧ｰ繧､繝ｳ霑ｽ蜉縺ｫ<10蛻・|
| Phase 5 | 繝・せ繝医き繝舌Ξ繝・ず 85%邯ｭ謖・|
| Phase 6 | 2蝗樒岼莉･髯阪・襍ｷ蜍墓凾髢・<0.5遘・|

---

## 謗ｨ螂ｨ繧ｿ繧､繝繝ｩ繧､繝ｳ

```
Week 1:  Phase 0 (蝓ｺ逶､貅門ｙ)
Week 2:  Phase 1 (繝代う繝ｭ繝・ヨ)
Week 3-6: Phase 2 (谿ｵ髫守噪繝励Λ繧ｰ繧､繝ｳ蛹悶・騾ｱ髢・
Week 7:  Phase 3 (Legacy蜑企勁)
Week 8:  Phase 4 (閾ｪ蜍墓､懷・)
Week 9-10: Phase 5 (繝・せ繝医Μ繝輔ぃ繧ｯ繧ｿ繝ｪ繝ｳ繧ｰ)
Week 11: Phase 6 (繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ譛驕ｩ蛹・

Total: 邏・繝ｶ譛・```

---

## 莉｣譖ｿ譯・ 譛蟆城剞繧｢繝励Ο繝ｼ繝・
Phase 2縺ｮ驕・ｻｶ繝ｭ繝ｼ繝画怙驕ｩ蛹悶□縺題｡後＞縲√・繝ｩ繧ｰ繧､繝ｳ蛹悶・隕矩√ｋ驕ｸ謚櫁い繧ゅ≠繧翫∪縺吶・
**繝｡繝ｪ繝・ヨ**:
- 蟾･謨ｰ: 1-2譌･
- 繝ｪ繧ｹ繧ｯ: Low
- 蜉ｹ譫・ 襍ｷ蜍墓凾髢・2-3遘・
**繝・Γ繝ｪ繝・ヨ**:
- 蟇ｾ逞・凾豕輔・縺ｾ縺ｾ
- 蟆・擂縺ｮ諡｡蠑ｵ諤ｧ菴弱＞

縺薙・驕ｸ謚櫁い繧貞叙繧句ｴ蜷医・縲‥ispatcher.py縺ｮ蛟句挨繧､繝ｳ繝昴・繝亥喧縺ｮ縺ｿ螳滓命縺励∪縺吶・
---

## Migration Completion Summary (2025-09-30)

### 笨・All Phases Completed Successfully

**Phase 0** (Foundation): 笨・Complete
- `plugin_base.py`: Abstract MCPToolPlugin interface
- `plugin_registry.py`: Lazy loading registry with error handling

**Phase 1** (Pilot): 笨・Complete
- check_readability tool migrated to plugin
- 10 unit tests for plugin registry
- Verified lazy loading and error handling

**Phase 2** (Gradual Migration): 笨・Complete (18/18 tools, 100%)
- Week 1: Quality tools (5) - run_quality_checks, improve_quality_until, fix_quality_issues, get_issue_context, export_quality_report
- Week 2: Readability/Grammar tools (3) - check_grammar, check_style, check_rhythm
- Week 3: Polish tools (5) - polish_manuscript, polish_manuscript_apply, restore_manuscript_from_artifact, polish, generate_episode_preview
- Week 4: Miscellaneous tools (4) - test_result_analysis, backup_management, list_quality_presets, get_quality_schema

**Phase 3** (Legacy Cleanup): 笨・Complete
- Removed 18 commented legacy dispatch entries (~90 lines deleted)
- Moved plugin registrations to module init
- Simplified dispatcher structure

**Phase 4** (Auto-Discovery): 笨・Complete
- Implemented `PluginRegistry.auto_discover_plugins()` method
- Convention-based registration (`*_plugin.py` files)
- Zero-config plugin addition (just drop file in plugins/)
- Replaced 70+ lines of manual registration with 5-line auto-discovery

**Phase 5** (Test Refactoring): 笨・Complete
- Added 4 comprehensive auto-discovery tests
- Test coverage for edge cases (empty dir, nonexistent dir, naming)
- Verified 18-plugin discovery from real directory
- Total tests: 79 竊・86 (+7 tests)

**Phase 6** (Performance Optimization): 笨・Complete
- Implemented `PluginRegistry.warmup()` for optional preloading
- Selective warmup support (all or specific plugins)
- 3 warmup tests for verification
- Reduces first-call latency for production

### Key Achievements

**Code Quality**:
- 18/18 tools migrated (100%)
- ~200 lines of code reduced
- 86/86 tests passing 笨・- Zero breaking changes

**Architecture**:
- Plugin-first resolution with legacy fallback
- Lazy loading with caching (import on first use)
- Convention-based auto-discovery (zero manual config)
- Optional warmup for performance-critical scenarios

**Developer Experience**:
- New plugin addition: just drop `*_plugin.py` file
- No manual registration needed
- Clear separation of concerns
- Comprehensive test coverage

### Performance Metrics

**Before**:
- Startup: Manual registration of 18+ tools
- Code: 100+ lines of manual registration
- Maintenance: Update dispatcher for each new tool

**After**:
- Startup: Auto-discovery (5 lines)
- Code: Convention-based (`*_plugin.py`)
- Maintenance: Zero-config (drop file)
- Test time: 6.38s (stable)

### Files Changed

**Core Implementation** (3 files):
1. `src/noveler/presentation/mcp/dispatcher.py`: -122 lines, simplified to auto-discovery
2. `src/noveler/presentation/mcp/plugin_registry.py`: +82 lines (auto-discovery + warmup)
3. `tests/unit/presentation/mcp/test_plugin_registry.py`: +127 lines (+7 tests)

**Plugin Files** (18 files created):
- All follow standard pattern with `get_name()`, `get_handler()`, `create_plugin()`
- Located in `src/noveler/presentation/mcp/plugins/`

### Migration Timeline

- **Start**: Initial planning and Phase 0 foundation
- **Phase 1-2**: ~4 weeks (gradual 18-tool migration)
- **Phase 3-6**: ~1 week (cleanup + auto-discovery + optimization)
- **Total**: ~5 weeks from start to completion
- **Complexity**: Handled incrementally with zero downtime

### Future Recommendations

1. **Documentation**: Create plugin development guide (see next section)
2. **Monitoring**: Track plugin load times in production
3. **Warmup Strategy**: Consider warmup for frequently-used plugins in production
4. **Additional Migrations**: Apply same pattern to remaining 40+ legacy tools