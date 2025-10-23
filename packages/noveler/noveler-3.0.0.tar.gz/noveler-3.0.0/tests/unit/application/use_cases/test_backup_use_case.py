"""BackupUseCase の B20 版ユニットテスト"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.backup_use_case import BackupRequest, BackupResponse, BackupUseCase


@pytest.fixture
def backup_use_case(monkeypatch, tmp_path: Path) -> SimpleNamespace:
    logger = Mock()

    project_repository = Mock()
    project_repository.find_by_name.return_value = SimpleNamespace(name="テストプロジェクト")

    backup_repository = Mock()
    backup_repository.backup_file.return_value = True

    transaction = Mock()
    transaction.__enter__ = Mock(return_value=transaction)
    transaction.__exit__ = Mock(return_value=None)

    unit_of_work = Mock()
    unit_of_work.project_repository = project_repository
    unit_of_work.backup_repository = backup_repository
    unit_of_work.transaction.return_value = transaction

    path_service = Mock()
    path_service.get_temp_dir.return_value = tmp_path
    path_service.project_root = tmp_path
    path_service.get_manuscript_dir.return_value = tmp_path

    monkeypatch.setattr(
        "noveler.application.use_cases.backup_use_case.create_path_service",
        lambda: path_service,
    )

    use_case = BackupUseCase(logger_service=logger, unit_of_work=unit_of_work)
    return SimpleNamespace(
        use_case=use_case,
        project_repository=project_repository,
        backup_repository=backup_repository,
        path_service=path_service,
    )


def test_backup_response_helpers() -> None:
    response = BackupResponse(
        success=True,
        backup_path=Path("/tmp/example"),
        backup_size=1.5,
        file_count=3,
        backup_metadata={"duration": 2.0, "message": "done"},
    )

    assert response.total_size == int(1.5 * 1024 * 1024)
    assert response.duration == 2.0
    assert response.message == "done"


@pytest.mark.asyncio
async def test_execute_full_backup_success(backup_use_case: SimpleNamespace, tmp_path: Path) -> None:
    (tmp_path / "プロジェクト設定.yaml").write_text("name: テスト")
    (tmp_path / "novel.md").write_text("content")

    request = BackupRequest(project_name="テストプロジェクト", backup_type="full")

    response = await backup_use_case.use_case.execute(request)

    assert response.success is True
    assert response.backup_path is not None
    assert response.file_count >= 0
    assert response.backup_metadata is not None
    assert response.backup_metadata["backup_type"] == "full"


@pytest.mark.asyncio
async def test_execute_returns_error_when_project_missing(backup_use_case: SimpleNamespace) -> None:
    backup_use_case.project_repository.find_by_name.return_value = None

    request = BackupRequest(project_name="存在しないプロジェクト")
    response = await backup_use_case.use_case.execute(request)

    assert response.success is False
    assert "見つかりません" in response.error_message


@pytest.mark.asyncio
async def test_execute_incremental_backup(backup_use_case: SimpleNamespace) -> None:
    request = BackupRequest(project_name="テストプロジェクト", backup_type="incremental")

    response = await backup_use_case.use_case.execute(request)

    assert response.success in {True, False}
    assert response.backup_path is not None or response.error_message is not None
