"""Infrastructure Layer - External I/O and caching.

Exports:
    - ConfigLoader: .novelerrc.yaml file I/O
    - CacheManager: In-memory LRU cache
"""

from .config_loader import ConfigLoader
from .cache_manager import CacheManager

__all__ = ["ConfigLoader", "CacheManager"]
