# File: scripts/diagnostics/service_locator_xdist_diagnosis.py
# Purpose: Provide tooling to inspect ServiceLocator and related caches during pytest-xdist runs.
# Context: Helps diagnose cache sharing issues across xdist workers before implementing PID-based isolation.

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _project_root() -> Path:
    """Return repository root path, ensuring imports work when executed directly."""

    return Path(__file__).resolve().parents[2]


def _ensure_sys_path() -> None:
    """Insert project root and src path into sys.path for local execution."""

    root = _project_root()
    src = root / "src"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _utc_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format with millisecond precision."""

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely fetch attribute from object, returning default on AttributeError."""

    try:
        return getattr(obj, attr)
    except AttributeError:
        return default


def collect_snapshot() -> dict[str, Any]:
    """Collect the current ServiceLocator and path-service cache state.

    Returns:
        dict[str, Any]: A JSON-serialisable snapshot describing cache state.
    """

    _ensure_sys_path()

    from noveler.infrastructure.di.service_locator import ServiceLocatorManager
    from noveler.presentation.shared import shared_utilities

    manager = ServiceLocatorManager()
    locator = manager.locator
    locator_cache = _safe_getattr(locator, "_cache", {}) or {}

    cached_services: list[str] = sorted(locator_cache.keys())
    initialized_services: dict[str, bool] = {
        service_name: bool(locator.is_initialized(service_name))
        for service_name in cached_services
    }

    path_service = _safe_getattr(shared_utilities, "_common_path_service")
    path_service_origin = _safe_getattr(shared_utilities, "_common_path_service_origin")

    env = os.environ
    worker_id = env.get("PYTEST_XDIST_WORKER") or "main"
    worker_count = env.get("PYTEST_XDIST_WORKER_COUNT")

    snapshot: dict[str, Any] = {
        "meta": {
            "timestamp": _utc_timestamp(),
            "epoch_ts": time.time(),
            "python": sys.version,
        },
        "process": {
            "pid": os.getpid(),
            "ppid": os.getppid() if hasattr(os, "getppid") else None,
            "worker_id": worker_id,
            "worker_count": worker_count,
            "cwd": str(Path.cwd()),
        },
        "service_locator": {
            "object_id": id(locator),
            "repr": repr(locator),
            "cached_services": cached_services,
            "initialized_services": initialized_services,
        },
        "path_service": {
            "object_id": id(path_service) if path_service is not None else None,
            "origin": path_service_origin,
            "repr": repr(path_service) if path_service is not None else None,
        },
        "environment": {
            "PROJECT_ROOT": env.get("PROJECT_ROOT"),
            "TARGET_PROJECT_ROOT": env.get("TARGET_PROJECT_ROOT"),
            "PYTHONPATH": env.get("PYTHONPATH"),
        },
    }

    return snapshot


def write_snapshot(snapshot: dict[str, Any], dump_dir: Path) -> Path:
    """Serialize snapshot to the specified directory.

    Args:
        snapshot: Snapshot payload.
        dump_dir: Directory to create JSON artifact inside.

    Returns:
        Path: Path to the written JSON file.
    """

    dump_dir.mkdir(parents=True, exist_ok=True)
    worker_id = snapshot["process"]["worker_id"]
    pid = snapshot["process"]["pid"]
    timestamp = snapshot["meta"]["timestamp"].replace(":", "-")
    filename = f"service_locator_{worker_id}_pid{pid}_{timestamp}.json"
    path = dump_dir / filename
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_existing_snapshots(dump_dir: Path) -> list[dict[str, Any]]:
    """Load previously written snapshots from disk.

    Args:
        dump_dir: Directory that may contain JSON snapshots.

    Returns:
        list[dict[str, Any]]: Parsed snapshots sorted by timestamp ascending.
    """

    if not dump_dir.exists():
        return []

    snapshots: list[dict[str, Any]] = []
    for path in sorted(dump_dir.glob("service_locator_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        else:
            snapshots.append(data)
    snapshots.sort(key=lambda item: item.get("meta", {}).get("epoch_ts", 0.0))
    return snapshots


def detect_conflicts(current: dict[str, Any], others: Iterable[dict[str, Any]]) -> list[str]:
    """Detect potential shared cache conflicts between current snapshot and existing ones."""

    conflicts: list[str] = []
    current_locator_id = current["service_locator"]["object_id"]
    current_path_service_id = current["path_service"]["object_id"]
    current_worker = current["process"]["worker_id"]

    for entry in others:
        worker = entry.get("process", {}).get("worker_id")
        if worker == current_worker:
            continue

        locator_id = entry.get("service_locator", {}).get("object_id")
        if locator_id and locator_id == current_locator_id:
            conflicts.append(
                f"ServiceLocator object {locator_id} shared between workers "
                f"{current_worker!r} and {worker!r}"
            )

        path_obj_id = entry.get("path_service", {}).get("object_id")
        if (
            path_obj_id is not None
            and current_path_service_id is not None
            and path_obj_id == current_path_service_id
        ):
            conflicts.append(
                f"CommonPathService object {path_obj_id} shared between workers "
                f"{current_worker!r} and {worker!r}"
            )

        env_roots = ("PROJECT_ROOT", "TARGET_PROJECT_ROOT")
        for key in env_roots:
            current_val = current["environment"].get(key)
            other_val = entry.get("environment", {}).get(key)
            if current_val and other_val and current_val != other_val:
                conflicts.append(
                    f"Environment mismatch for {key}: {current_worker!r}={current_val!r}, "
                    f"{worker!r}={other_val!r}"
                )

    return conflicts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Diagnose ServiceLocator cache state under pytest-xdist."
    )
    parser.add_argument(
        "--dump-dir",
        type=Path,
        default=_project_root() / "reports" / "xdist_diagnostics",
        help="Directory to store snapshot JSON artifacts (default: %(default)s).",
    )
    parser.add_argument(
        "--no-detect",
        action="store_true",
        help="Skip conflict detection phase (only dump current snapshot).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for CLI execution."""

    args = parse_args(argv)
    snapshot = collect_snapshot()
    dump_path = write_snapshot(snapshot, args.dump_dir)

    print(f"[diagnosis] Snapshot written to {dump_path}")

    if not args.no_detect:
        existing = load_existing_snapshots(args.dump_dir)
        conflicts = detect_conflicts(snapshot, existing)
        if conflicts:
            print("[diagnosis] Potential conflicts detected:")
            for issue in conflicts:
                print(f"  - {issue}")
            return 2
        print("[diagnosis] No conflicts detected across existing snapshots.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
