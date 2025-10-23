# File: src/noveler/infrastructure/adapters/configuration_source_adapter.py
# Purpose: Provide ConfigurationSourcePort implementation backed by IConfigurationService.
# Context: Enables configuration snapshotting and diff detection for infrastructure integration.

"""Configuration source adapter for infrastructure integration."""

from __future__ import annotations

import hashlib
import json
import threading
from time import time
from typing import Dict, Tuple

from noveler.domain.interfaces.configuration_service import IConfigurationService
from noveler.domain.interfaces.configuration_source_port import ConfigurationSourcePort
from noveler.infrastructure.logging.unified_logger import get_logger


class ConfigurationSourceAdapter(ConfigurationSourcePort):
    """Snapshot configuration state via IConfigurationService with change tokens."""

    def __init__(self, configuration_service: IConfigurationService) -> None:
        self._configuration_service = configuration_service
        self._token_cache: Dict[tuple[str, str], dict] = {}
        self._latest_tokens: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._logger = get_logger(__name__)

    def snapshot(self, project_id: str) -> tuple[dict, str]:
        """Return configuration snapshot and change token."""
        features = self._configuration_service.get_feature_flags()
        environment = getattr(self._configuration_service, "get_environment", lambda: "unknown")()
        # Generate token from stable config data only (exclude timestamp)
        stable_config = {
            "features": features,
            "environment": environment,
        }
        token = self._generate_token(project_id, stable_config)
        # Include timestamp in snapshot for observability
        snapshot = {
            **stable_config,
            "timestamp": time(),
        }
        with self._lock:
            self._token_cache[(project_id, token)] = snapshot
            self._latest_tokens[project_id] = token
            # Remove stale entries for the same project to avoid unbounded growth
            stale_keys = [key for key in self._token_cache if key[0] == project_id and key[1] != token]
            for stale_key in stale_keys:
                self._token_cache.pop(stale_key, None)
        return snapshot, token

    def diff_since(self, project_id: str, token: str) -> Tuple[dict, dict]:
        """Return configuration diff since the provided token."""
        with self._lock:
            old_snapshot = self._token_cache.get((project_id, token), {})
            latest_token = self._latest_tokens.get(project_id, token)
            new_snapshot = self._token_cache.get((project_id, latest_token), old_snapshot)
        return old_snapshot, new_snapshot

    def _generate_token(self, project_id: str, snapshot: dict) -> str:
        payload = json.dumps(
            {"project_id": project_id, "snapshot": snapshot},
            ensure_ascii=False,
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._logger.debug("Configuration snapshot generated token %s for %s", digest[:8], project_id)
        return digest
