"""Infrastructure.adapters.memory_episode_repository
Where: Infrastructure adapter storing episodes in memory for testing.
What: Provides an in-memory repository implementation supporting the domain contract.
Why: Enables fast tests and prototyping without filesystem dependencies.
"""

from __future__ import annotations

from noveler.infrastructure.ports.episode_repository import Episode, EpisodeRepository


class InMemoryEpisodeRepository(EpisodeRepository):
    def __init__(self) -> None:
        self._store: dict[str, Episode] = {}

    def save(self, ep: Episode) -> None:
        self._store[ep.id] = ep

    def get(self, id: str) -> Episode | None:
        return self._store.get(id)
