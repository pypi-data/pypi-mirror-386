from __future__ import annotations
class FastMCP:  # pragma: no cover - minimal test stub
    def __init__(self, name: str, instructions: str | None = None) -> None:
        self.name = name
        self.instructions = instructions or ''
        self._tools = {}
    def tool(self, name: str, description: str | None = None):
        def deco(fn):
            self._tools[name] = fn
            return fn
        return deco
    async def run_stdio_async(self) -> None:
        # Stub does nothing in tests relying on main.py
        return None
