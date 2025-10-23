"""Bootstrap helpers for wiring the in-memory message bus."""

from __future__ import annotations

from typing import Any

from noveler.application.simple_message_bus import MessageBus
from noveler.application.uow import InMemoryUnitOfWork
from noveler.infrastructure.ports.episode_repository import Episode, EpisodeRepository


async def _cmd_write_episode(data: dict[str, Any], *, uow: InMemoryUnitOfWork) -> dict[str, Any]:
    """Persist an episode using the provided unit of work.

    Args:
        data: Payload containing episode fields such as ``id`` and ``title``.
        uow: Unit of work that exposes an ``episode_repo`` for persistence.

    Returns:
        dict[str, Any]: Result payload including the stored episode identifier.
    """
    ep_id = data.get("id") or f"ep-{data.get('episode_number', 0)}"
    ep = Episode(id=str(ep_id), title=data.get("title", "Untitled"), content=data.get("content", ""))
    # UoW配下のレポジトリ操作（InMemoryUnitOfWork は episode_repo を持つ想定）
    uow.episode_repo.save(ep)
    # トランザクションコミット後に発行されるようイベントはUoWへ積む
    uow.add_event("episode_written", {"id": ep.id})
    return {"success": True, "episode_id": ep.id}


async def _on_episode_written(event) -> None:  # type: ignore[no-untyped-def]
    """Handle the ``episode_written`` event emitted by the bus."""
    # 最小実装: 何もしない（イベントが処理されたという事実のみ残す）
    return None


def bootstrap_message_bus(*, episode_repo: EpisodeRepository) -> MessageBus:
    """Create a message bus configured with in-memory dependencies.

    Args:
        episode_repo: Repository instance used by the unit of work factory.

    Returns:
        MessageBus: Bus instance with command and event handlers wired.
    """
    bus = MessageBus()

    # UoWファクトリ（1リポジトリ構成の最小実装）
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=episode_repo)

    # 依存を束縛したハンドラ（UoWはBus側から注入される）
    async def cmd_write(data, *, uow):  # type: ignore[no-redef]
        """Adapter that forwards command payloads to ``_cmd_write_episode``."""
        return await _cmd_write_episode(data, uow=uow)

    bus.command_handlers["write_episode"] = cmd_write
    bus.event_handlers.setdefault("episode_written", []).append(_on_episode_written)
    return bus
