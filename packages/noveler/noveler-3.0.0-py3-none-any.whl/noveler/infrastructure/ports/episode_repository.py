"""Infrastructure.ports.episode_repository
Where: Infrastructure port implementation for episode repositories.
What: Bridges domain episode repository interface to infrastructure logic.
Why: Keeps port bindings explicit for dependency injection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Episode:
    id: str
    title: str
    content: str


class EpisodeRepository(Protocol):
    def save(self, ep: Episode) -> None: ...
    def get(self, id: str) -> Episode | None: ...
