"""Domain.services.environment_diagnostic_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from typing import Any

"環境診断サービス\n\nシステム診断の環境チェック専用ドメインサービス\n"
import os
import sys


class EnvironmentDiagnosticService:
    """環境診断専用サービス"""

    def check_environment(self, quiet: bool = False) -> dict:
        """環境変数と基本設定のチェック"""
        log_messages: list[dict[str, str]] = []
        self._append_log(log_messages, "info", "📋 環境チェック...", quiet)
        env_check = {"status": "OK", "details": {}}
        errors: list[Any] = []
        warnings = []
        py_version = sys.version_info
        env_check["details"]["python_version"] = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 6):
            env_check["status"] = "ERROR"
            errors.append("Python 3.6以上が必要です")
        env_vars = {
            "PROJECT_ROOT": os.environ.get("PROJECT_ROOT"),
            "GUIDE_ROOT": os.environ.get("GUIDE_ROOT"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "NOVEL_CONFIG_HOME": os.environ.get("NOVEL_CONFIG_HOME"),
        }
        env_check["details"]["environment_variables"] = env_vars
        if not env_vars["PROJECT_ROOT"]:
            env_check["status"] = "WARNING" if env_check["status"] == "OK" else env_check["status"]
            warnings.append("PROJECT_ROOT環境変数が設定されていません")
        if not env_vars["GUIDE_ROOT"]:
            env_check["status"] = "WARNING" if env_check["status"] == "OK" else env_check["status"]
            warnings.append("GUIDE_ROOT環境変数が設定されていません")
        return {
            "check_result": env_check,
            "errors": errors,
            "warnings": warnings,
            "log_messages": log_messages,
        }

    @staticmethod
    def _append_log(
        log_messages: list[dict[str, str]],
        level: str,
        message: str,
        quiet: bool,
    ) -> None:
        """Record diagnostic log entries when output is not suppressed."""
        if quiet:
            return
        log_messages.append({"level": level, "message": message})
