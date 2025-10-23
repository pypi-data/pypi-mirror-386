from __future__ import annotations
from dataclasses import dataclass
@dataclass
class Tool:
    name: str
    description: str | None = None
    inputSchema: dict | None = None
