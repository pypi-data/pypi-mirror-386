"""Infrastructure.adapters.file_outbox_repository
Where: Infrastructure adapter handling outbox message persistence via files.
What: Persists and retrieves integration events awaiting delivery.
Why: Supports reliable outbound messaging in file-based deployments.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.application.outbox import OutboxEntry, OutboxRepository


class FileOutboxRepository(OutboxRepository):
    """シンプルなファイルベースOutbox

    - 1イベント=1ファイル(JSON)
    - ステータスはファイル内 `status` で管理（pending/dispatched）
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or (Path.cwd() / "temp" / "bus_outbox")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # DLQ用ディレクトリも作成
        self.dlq_dir = self.base_dir / "dlq"
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, entry_id: str) -> Path:
        return self.base_dir / f"{entry_id}.json"

    def _dlq_path(self, entry_id: str) -> Path:
        return self.dlq_dir / f"{entry_id}.json"

    def add(self, entry: OutboxEntry) -> None:
        base_key = entry.id
        storage_key = base_key
        p = self._path(storage_key)
        counter = 1
        while p.exists():
            storage_key = f"{base_key}__{counter}"
            p = self._path(storage_key)
            counter += 1

        payload: dict[str, Any] = {
            "id": entry.id,
            "name": entry.name,
            "payload": entry.payload,
            "created_at": entry.created_at.astimezone(timezone.utc).isoformat(),
            "attempts": entry.attempts,
            "dispatched_at": entry.dispatched_at.isoformat() if entry.dispatched_at else None,
            "last_error": entry.last_error,
            "failed_at": entry.failed_at.isoformat() if entry.failed_at else None,
            "status": "pending",
            "storage_key": storage_key,
        }
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def load_pending(self, limit: int = 100) -> list[OutboxEntry]:
        entries: list[OutboxEntry] = []
        for fp in sorted(self.base_dir.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                if data.get("status") != "pending":
                    continue
                entry = OutboxEntry(
                    id=data["id"],
                    name=data["name"],
                    payload=data.get("payload", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    attempts=int(data.get("attempts", 0)),
                    dispatched_at=datetime.fromisoformat(data["dispatched_at"]) if data.get("dispatched_at") else None,
                    last_error=data.get("last_error"),
                    failed_at=datetime.fromisoformat(data["failed_at"]) if data.get("failed_at") else None,
                    storage_key=data.get("storage_key", fp.stem),
                )
                entries.append(entry)
                if len(entries) >= limit:
                    break
            except Exception:
                continue
        return entries

    def mark_dispatched(self, entry_id: str) -> None:
        p = self._path(entry_id)
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["status"] = "dispatched"
            data["dispatched_at"] = datetime.now(timezone.utc).isoformat()
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            return

    def increment_attempts(self, entry_id: str, error_message: str) -> None:
        """失敗時の試行回数増加とエラー記録"""
        p = self._path(entry_id)
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["attempts"] = int(data.get("attempts", 0)) + 1
            data["last_error"] = error_message
            data["failed_at"] = datetime.now(timezone.utc).isoformat()
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            return

    def move_to_dlq(self, entry_id: str) -> None:
        """エントリをDead Letter Queueに移動"""
        p = self._path(entry_id)
        dlq_p = self._dlq_path(entry_id)
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["status"] = "dlq"
            data["failed_at"] = datetime.now(timezone.utc).isoformat()
            # DLQディレクトリに移動
            dlq_p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            # 元ファイルを削除
            p.unlink()
        except Exception:
            return

    def load_dlq_entries(self, limit: int = 100) -> list[OutboxEntry]:
        """DLQエントリの読み込み"""
        entries: list[OutboxEntry] = []
        for fp in sorted(self.dlq_dir.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                entry = OutboxEntry(
                    id=data["id"],
                    name=data["name"],
                    payload=data.get("payload", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    attempts=int(data.get("attempts", 0)),
                    dispatched_at=datetime.fromisoformat(data["dispatched_at"]) if data.get("dispatched_at") else None,
                    last_error=data.get("last_error"),
                    failed_at=datetime.fromisoformat(data["failed_at"]) if data.get("failed_at") else None,
                    storage_key=data.get("storage_key", fp.stem),
                )
                entries.append(entry)
                if len(entries) >= limit:
                    break
            except Exception:
                continue
        return entries
