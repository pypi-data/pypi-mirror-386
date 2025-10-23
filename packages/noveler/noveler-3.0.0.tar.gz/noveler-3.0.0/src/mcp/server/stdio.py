from __future__ import annotations
from contextlib import asynccontextmanager

@asynccontextmanager
async def stdio_server():
    yield (None, None)
