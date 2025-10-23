# MCP Plugin Development Guide

**Last Updated**: 2025-09-30
**Status**: Active (Post-Migration)

## Overview

This guide explains how to create new MCP tool plugins for the Noveler system. After the completed plugin architecture migration (Phase 0-6), creating new plugins is straightforward and requires zero manual configuration.

## Quick Start

### 1. Create Plugin File

Create a new file in `src/noveler/presentation/mcp/plugins/` following the naming convention:

```
<tool_name>_plugin.py
```

Example: `my_awesome_tool_plugin.py`

### 2. Implement Plugin Class

```python
#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/my_awesome_tool_plugin.py
# Purpose: Plugin wrapper for my_awesome_tool
# Context: MCP tool plugin - auto-discovered
"""My awesome tool plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class MyAwesomeToolPlugin(MCPToolPlugin):
    """Plugin wrapper for my_awesome_tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "my_awesome_tool"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the my_awesome_tool handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.my_awesome_tool


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return MyAwesomeToolPlugin()
```

### 3. That's It!

No registration needed. The plugin will be automatically discovered on next server startup.

## Naming Convention

### File Name
- **Pattern**: `<tool_name>_plugin.py`
- **Example**: `check_readability_plugin.py`
- **Location**: `src/noveler/presentation/mcp/plugins/`

### Tool Name (from `get_name()`)
- **Pattern**: Derived from filename by removing `_plugin` suffix
- **Example**: `check_readability_plugin.py` 竊・`check_readability`
- **Note**: Must match the tool name expected by MCP clients

### Class Name
- **Pattern**: `PascalCase` version of tool name + `Plugin`
- **Example**: `CheckReadabilityPlugin`
- **Convention**: Clear, descriptive, follows Python naming standards

## Plugin Interface

All plugins must implement the `MCPToolPlugin` interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Callable

class MCPToolPlugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Return the unique tool name (e.g., 'run_quality_checks')"""
        pass

    @abstractmethod
    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the handler function that executes the tool"""
        pass

    @property
    def lazy_load(self) -> bool:
        """Control lazy loading (default: True)"""
        return True
```

### Required Methods

#### `get_name() -> str`
Returns the tool identifier used by MCP clients.

**Example**:
```python
def get_name(self) -> str:
    return "check_readability"
```

#### `get_handler() -> Callable`
Returns the handler function. Import should be done **inside** this method for lazy loading.

**Example**:
```python
def get_handler(self) -> Callable[[dict[str, Any]], Any]:
    from noveler.presentation.mcp.adapters import handlers
    return handlers.check_readability
```

**笶・Bad** (eager import):
```python
from noveler.presentation.mcp.adapters import handlers  # At module level

def get_handler(self) -> Callable:
    return handlers.check_readability  # Already imported
```

**笨・Good** (lazy import):
```python
def get_handler(self) -> Callable:
    from noveler.presentation.mcp.adapters import handlers  # Inside method
    return handlers.check_readability
```

### Optional Properties

#### `lazy_load -> bool`
Control whether the plugin uses lazy loading (default: `True`).

**When to override**:
- Critical plugins that must be loaded at startup
- Plugins with expensive initialization better done at startup

**Example**:
```python
@property
def lazy_load(self) -> bool:
    return False  # Force eager loading
```

## Factory Function

Every plugin file must include a `create_plugin()` factory function:

```python
def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return MyAwesomeToolPlugin()
```

This function is called by the plugin registry during lazy loading.

## Auto-Discovery

Plugins are automatically discovered using the following process:

1. **Scan Directory**: `src/noveler/presentation/mcp/plugins/`
2. **Match Pattern**: Files ending with `_plugin.py`
3. **Extract Name**: Remove `_plugin` suffix from filename
4. **Register**: Add to plugin registry with lazy loading

**Code Reference**:
```python
# In dispatcher.py
_plugins_dir = Path(__file__).parent / "plugins"
_discovered_count = _registry.auto_discover_plugins(
    _plugins_dir,
    "noveler.presentation.mcp.plugins"
)
```

## Testing Your Plugin

### Unit Test Template

Create a test file in `tests/unit/presentation/mcp/`:

```python
#!/usr/bin/env python3
"""Tests for my_awesome_tool plugin."""

import pytest

from noveler.presentation.mcp.plugin_registry import PluginRegistry


def test_my_awesome_tool_plugin_loads():
    """Verify that my_awesome_tool plugin loads correctly."""
    registry = PluginRegistry()
    registry.register_plugin(
        "my_awesome_tool",
        "noveler.presentation.mcp.plugins.my_awesome_tool_plugin"
    )

    handler = registry.get_handler("my_awesome_tool")
    assert handler is not None
    assert callable(handler)


def test_my_awesome_tool_plugin_auto_discovered():
    """Verify that my_awesome_tool is auto-discovered."""
    from pathlib import Path
    from noveler.presentation.mcp.plugin_registry import PluginRegistry

    registry = PluginRegistry()
    plugins_dir = Path(__file__).parent.parent.parent.parent.parent / "src" / "noveler" / "presentation" / "mcp" / "plugins"

    count = registry.auto_discover_plugins(plugins_dir, "noveler.presentation.mcp.plugins")

    tools = registry.get_registered_tools()
    assert "my_awesome_tool" in tools
```

### Integration Test

Verify the plugin works end-to-end through the dispatcher:

```python
def test_my_awesome_tool_via_dispatcher():
    """Verify my_awesome_tool works through dispatcher."""
    from noveler.presentation.mcp.dispatcher import get_handler

    handler = get_handler("my_awesome_tool")
    assert handler is not None

    # Test with sample input
    result = handler({"input": "test"})
    assert result is not None
```

## Best Practices

### 1. Lazy Import Handlers

Always import handlers **inside** `get_handler()` method:

```python
def get_handler(self) -> Callable:
    from noveler.presentation.mcp.adapters import handlers  # 笨・Lazy
    return handlers.my_tool
```

### 2. Clear Documentation

Add clear docstrings and file headers:

```python
#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/my_tool_plugin.py
# Purpose: Plugin wrapper for my_tool
# Context: MCP tool plugin for [brief description]
"""My tool plugin for MCP."""
```

### 3. Follow Naming Convention

Consistent naming makes discovery predictable:
- File: `my_tool_plugin.py`
- Class: `MyToolPlugin`
- Tool: `my_tool`

### 4. Test Auto-Discovery

Always include auto-discovery test to verify the plugin is found:

```python
def test_auto_discovered():
    registry = PluginRegistry()
    # ... auto_discover_plugins call ...
    assert "my_tool" in registry.get_registered_tools()
```

### 5. Keep Plugins Simple

Plugins should be thin wrappers:
- No business logic
- Just tool name + handler reference
- Let handlers do the work

## Performance Optimization

### Warmup for Production

For frequently-used plugins, consider warmup at startup:

```python
# In production startup code
from noveler.presentation.mcp.plugin_registry import PluginRegistry

registry = _registry  # Get global registry
registry.warmup([
    "run_quality_checks",
    "check_readability",
    "polish_manuscript"
])
```

### Selective Warmup vs Lazy Loading

**Lazy Loading** (default):
- 笨・Faster startup
- 笨・Lower memory on startup
- 笶・Slight delay on first use

**Warmup** (optional):
- 笶・Slower startup
- 笶・Higher memory on startup
- 笨・No delay on first use

Choose based on usage patterns:
- **High-frequency tools**: Warmup
- **Occasional tools**: Lazy loading

## Migration from Legacy

If you have an existing tool handler in the legacy dispatch table:

### Before (Legacy)
```python
# In dispatcher.py
return {
    "my_tool": handlers.my_tool,  # Manual registration
    # ...
}
```

### After (Plugin)
1. Create `my_tool_plugin.py` (see Quick Start)
2. Remove from legacy dispatch table
3. Done! Auto-discovery handles the rest

## Troubleshooting

### Plugin Not Found

**Symptom**: `get_handler("my_tool")` returns `None`

**Check**:
1. Filename ends with `_plugin.py`
2. File is in `src/noveler/presentation/mcp/plugins/`
3. `create_plugin()` factory exists
4. `get_name()` returns correct tool name

**Debug**:
```python
from noveler.presentation.mcp.dispatcher import _registry
print(_registry.get_registered_tools())  # Should include "my_tool"
```

### Import Error

**Symptom**: Plugin loads but handler fails

**Check**:
1. Handler import path is correct
2. Handler function exists in `handlers.py`
3. Import is inside `get_handler()` (lazy)

**Debug**:
```python
plugin = create_plugin()
try:
    handler = plugin.get_handler()
except Exception as e:
    print(f"Handler error: {e}")
```

### Tool Name Mismatch

**Symptom**: Client requests tool but dispatcher doesn't find it

**Check**:
1. `get_name()` matches client expectation
2. Tool name is lowercase with underscores
3. No typos in tool name

## Examples

### Simple Tool Plugin

```python
#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/hello_world_plugin.py
# Purpose: Example plugin for hello_world tool
# Context: Simple demonstration plugin
"""Hello world plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class HelloWorldPlugin(MCPToolPlugin):
    """Plugin wrapper for hello_world tool."""

    def get_name(self) -> str:
        return "hello_world"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        from noveler.presentation.mcp.adapters import handlers
        return handlers.hello_world


def create_plugin() -> MCPToolPlugin:
    return HelloWorldPlugin()
```

### Async Handler Plugin

```python
#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/async_tool_plugin.py
# Purpose: Example plugin with async handler
# Context: Demonstrates async handler pattern
"""Async tool plugin for MCP."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class AsyncToolPlugin(MCPToolPlugin):
    """Plugin wrapper for async_tool with async handler."""

    def get_name(self) -> str:
        return "async_tool"

    def get_handler(self) -> Callable[[dict[str, Any]], Awaitable[Any]]:
        from noveler.presentation.mcp.adapters import handlers
        return handlers.async_tool  # This is an async function


def create_plugin() -> MCPToolPlugin:
    return AsyncToolPlugin()
```

Note: The dispatcher automatically handles async handlers with `inspect.isawaitable()`.

## Reference

### Key Files

- **Plugin Base**: `src/noveler/presentation/mcp/plugin_base.py`
- **Plugin Registry**: `src/noveler/presentation/mcp/plugin_registry.py`
- **Dispatcher**: `src/noveler/presentation/mcp/dispatcher.py`
- **Plugins Directory**: `src/noveler/presentation/mcp/plugins/`

### Related Documentation

- [MCP Plugin Architecture Migration](../architecture/mcp_plugin_architecture_migration.md)
- [Plugin Registry Tests](../../tests/unit/presentation/mcp/test_plugin_registry.py)

## FAQ

**Q: Do I need to update dispatcher.py?**
A: No. Auto-discovery handles registration automatically.

**Q: Can I have multiple plugins in one file?**
A: No. Follow one-plugin-per-file convention for auto-discovery.

**Q: What if my tool name has special characters?**
A: Use only lowercase letters, numbers, and underscores. No spaces or hyphens.

**Q: Can I disable auto-discovery for a plugin?**
A: Name the file without `_plugin.py` suffix, or place it outside the plugins directory.

**Q: How do I remove a plugin?**
A: Simply delete the `*_plugin.py` file. No registration cleanup needed.

**Q: Can plugins have dependencies on other plugins?**
A: Yes, but be careful of circular dependencies. Use lazy imports inside methods.

## Support

For questions or issues:
1. Check [Migration Documentation](../architecture/mcp_plugin_architecture_migration.md)
2. Review [existing plugin examples](../../src/noveler/presentation/mcp/plugins/)
3. Run test suite: `pytest tests/unit/presentation/mcp/test_plugin_registry.py`