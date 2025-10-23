# File: tests/unit/domain/services/test_configuration_dependency_repair_services.py
# Purpose: Validate that repair services expose structured logs instead of relying on console output.
# Context: Supports B35/B30 unified logging effort by exercising domain log capture paths.

from noveler.domain.services.configuration_repair_service import ConfigurationRepairService
from noveler.domain.services.dependency_repair_service import DependencyRepairService
from noveler.domain.utils.domain_logging import capture_domain_logs


def test_configuration_repair_collects_logs_when_global_config_missing() -> None:
    service = ConfigurationRepairService()
    config_check = {"status": "ERROR", "details": {"global_config": "Not found"}}

    with capture_domain_logs() as captured_logs:
        result = service.repair_configurations(config_check, dry_run=True, quiet=True)

    assert result["success"] is True
    assert result["repairs_made"] == ["グローバル設定作成予定"]
    assert result["repairs_failed"] == []

    messages = [entry["message"] for entry in result["log_entries"]]
    assert messages == [entry["message"] for entry in captured_logs]
    assert messages and messages[0].startswith("\n⚙️ グローバル設定を初期化")


def test_dependency_repair_collects_logs_for_missing_packages_dry_run() -> None:
    service = DependencyRepairService()
    deps_check = {
        "status": "ERROR",
        "details": {"required_packages": {"pyyaml": "Missing", "requests": "Installed"}},
    }

    with capture_domain_logs() as captured_logs:
        result = service.repair_dependencies(deps_check, dry_run=True, quiet=True)

    assert result["success"] is True
    assert result["packages_installed"] == []
    assert any("パッケージインストール予定" in entry for entry in result["repairs_made"])

    messages = [entry["message"] for entry in result["log_entries"]]
    assert messages == [entry["message"] for entry in captured_logs]
    assert any("不足しているパッケージ" in message for message in messages)
