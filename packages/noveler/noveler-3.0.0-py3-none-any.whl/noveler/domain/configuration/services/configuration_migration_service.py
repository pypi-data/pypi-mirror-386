"""ConfigurationMigrationService ドメインサービス

SPEC-CONFIGURATION-001準拠
"""

from datetime import datetime, timezone
from typing import Any

from noveler.domain.configuration.entities.configuration_profile import ConfigurationProfile
from noveler.domain.configuration.value_objects.environment import Environment
from noveler.domain.configuration.value_objects.profile_id import ProfileId


class ConfigurationMigrationService:
    """設定移行ドメインサービス"""

    def migrate_legacy_settings(self, legacy_settings: dict[str, Any]) -> ConfigurationProfile:
        """レガシー設定を新形式に移行"""
        # 入力検証
        for key, value in legacy_settings.items():
            if key == "quality_threshold" and not isinstance(value, int | float):
                msg = f"Invalid legacy setting: {key} must be numeric"
                raise TypeError(msg)
            if key == "coverage_threshold" and isinstance(value, int | float) and value < 0:
                msg = f"Invalid legacy setting: {key} cannot be negative"
                raise TypeError(msg)

        # デフォルト値設定
        default_settings = {
            "quality.threshold": 70.0,
            "quality.coverage_threshold": 60.0,
            "performance.complexity_threshold": 10,
            "performance.marathon_session_threshold_hours": 4.0,
            "infrastructure.log_level": "INFO",
        }

        # 新形式に変換
        new_settings = default_settings.copy()

        # レガシー設定をマッピング
        mapping = {
            "quality_threshold": "quality.threshold",
            "coverage_threshold": "quality.coverage_threshold",
            "complexity_threshold": "performance.complexity_threshold",
            "marathon_session_threshold_hours": "performance.marathon_session_threshold_hours",
            "log_level": "infrastructure.log_level",
        }

        for old_key, new_key in mapping.items():
            if old_key in legacy_settings:
                new_settings[new_key] = legacy_settings[old_key]

        # プロファイル作成
        return ConfigurationProfile(
            profile_id=ProfileId("migrated-profile"),
            name="Migrated Settings",
            environment=Environment.DEVELOPMENT,
            settings=new_settings,
            created_at=datetime.now(timezone.utc),
        )
