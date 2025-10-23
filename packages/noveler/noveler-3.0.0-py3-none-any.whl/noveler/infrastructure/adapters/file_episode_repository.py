"""Infrastructure.adapters.file_episode_repository
Where: Infrastructure adapter persisting episodes to the filesystem.
What: Implements repository methods using file-based storage and YAML serialization.
Why: Provides a concrete storage mechanism for domain episode repositories.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from noveler.infrastructure.ports.episode_repository import Episode, EpisodeRepository


class FileEpisodeRepository(EpisodeRepository):
    """簡易ファイル実装（./temp 下へ保存）"""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (Path.cwd() / "temp" / "ddd_repo")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, id: str) -> Path:
        return self.base_dir / f"{id}.json"

    def save(self, ep: Episode) -> None:
        p = self._path(ep.id)
        payload: dict[str, Any] = {"id": ep.id, "title": ep.title, "content": ep.content}
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def get(self, id: str) -> Episode | None:
        p = self._path(id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return Episode(**data)
