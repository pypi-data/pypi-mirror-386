"""Domain.services.configuration_repair_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from noveler.domain.utils.domain_console import console

"設定修復サービス\n\nシステム修復の設定ファイル処理専用ドメインサービス\n"

import yaml


class ConfigurationRepairService:
    """設定修復専用サービス"""

    def repair_configurations(self, config_check: dict, dry_run: bool = False, quiet: bool = False) -> dict:
        """設定ファイルの修復

        Args:
            config_check: 設定チェック結果
            dry_run: ドライラン実行
            quiet: 静寂モード

        Returns:
            dict: 修復結果
        """
        result = {"success": True, "repairs_made": [], "repairs_failed": []}
        if config_check.get("status") == "OK":
            return result
        details: Any = config_check.get("details", {})
        if details.get("global_config") == "Not found":
            global_result = self._repair_global_config(dry_run, quiet)
            result["repairs_made"].extend(global_result["repairs_made"])
            result["repairs_failed"].extend(global_result["repairs_failed"])
            if not global_result["success"]:
                result["success"] = False
        return result

    def _repair_global_config(self, dry_run: bool, quiet: bool) -> dict:
        """グローバル設定の修復"""
        result = {"success": True, "repairs_made": [], "repairs_failed": []}
        if not quiet:
            console.print("\n⚙️ グローバル設定を初期化...")
        if dry_run:
            if not quiet:
                console.print("  💡 実行内容: グローバル設定ファイルを作成")
            result["repairs_made"].append("グローバル設定作成予定")
            return result
        try:
            config_dir = Path.home() / ".novel"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.yaml"
            self._create_default_global_config(config_path)
            result["repairs_made"].append(f"グローバル設定を作成: {config_path}")
            if not quiet:
                console.print("  ✅ グローバル設定を作成しました")
        except Exception as e:
            error_msg = f"グローバル設定の作成失敗: {e}"
            result["repairs_failed"].append(error_msg)
            result["success"] = False
            if not quiet:
                console.print(f"  ❌ {error_msg}")
        return result

    def _create_default_global_config(self, config_path: Path) -> None:
        """デフォルトグローバル設定の作成"""
        default_config: dict[str, Any] = {
            "default_author": {"pen_name": "未設定", "email": "user@example.com", "website": ""},
            "editor": {"default": "vim", "markdown": "vim"},
            "export": {"default_format": "markdown", "output_directory": "output"},
            "quality": {"auto_check": True, "min_score": 70, "enable_ai_review": False},
            "project": {"default_template": "standard", "auto_backup": True, "version_control": True},
            "theme": {"color_scheme": "default", "font_size": "medium"},
        }
        with config_path.open("w", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)
