"""Unit of Work実装"""

# 循環インポートを避けるため、実装クラスのみエクスポート
from noveler.infrastructure.unit_of_work.backup_unit_of_work import BackupUnitOfWork
from noveler.infrastructure.unit_of_work.filesystem_backup_unit_of_work import FilesystemBackupUnitOfWork


# IUnitOfWorkは循環インポートを避けるため、遅延インポートで提供
def __getattr__(name: str) -> type:
    if name in {"IUnitOfWork", "UnitOfWork", "create_unit_of_work"}:
        # 親ディレクトリから直接インポート
        from pathlib import Path

        # 親のunit_of_work.pyのパス
        parent_path = Path(__file__).parent / "../unit_of_work.py"
        parent_path = parent_path.resolve()

        import importlib.util

        spec = importlib.util.spec_from_file_location("parent_uow", parent_path)
        if spec and spec.loader:
            parent_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parent_module)
            return getattr(parent_module, name)

    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)


__all__ = [
    "BackupUnitOfWork",
    "FilesystemBackupUnitOfWork",
    "IUnitOfWork",
    "UnitOfWork",
    "create_unit_of_work",
]
