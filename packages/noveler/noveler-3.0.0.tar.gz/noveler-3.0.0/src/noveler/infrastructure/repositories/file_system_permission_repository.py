"""ファイルシステム権限リポジトリ実装."""

import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.repositories.file_permission_repository import FilePermissionRepository, PermissionLevel


class FileSystemPermissionRepository(FilePermissionRepository):
    """ファイルシステムを使用した権限リポジトリ実装."""

    def __init__(self, permission_cache_path: Path | str | None = None) -> None:
        """初期化.

        Args:
            permission_cache_path: 権限キャッシュファイルのパス
        """
        self.permission_cache_path = permission_cache_path or Path.cwd() / ".permission_cache.json"

    def get_file_permissions(self, file_path: Path) -> dict[str, list[PermissionLevel]]:
        """ファイルの権限設定を取得.

        Args:
            file_path: 対象ファイルパス

        Returns:
            ユーザー/グループごとの権限設定
        """
        if not file_path.exists():
            return {}

        try:
            file_stat = file_path.stat()
            mode = file_stat.st_mode

            permissions = {}

            # オーナー権限
            owner_perms = []
            if mode & stat.S_IRUSR:
                owner_perms.append(PermissionLevel.READ)
            if mode & stat.S_IWUSR:
                owner_perms.append(PermissionLevel.WRITE)
            if mode & stat.S_IXUSR:
                owner_perms.append(PermissionLevel.EXECUTE)
            permissions["owner"] = owner_perms

            # グループ権限
            group_perms = []
            if mode & stat.S_IRGRP:
                group_perms.append(PermissionLevel.READ)
            if mode & stat.S_IWGRP:
                group_perms.append(PermissionLevel.WRITE)
            if mode & stat.S_IXGRP:
                group_perms.append(PermissionLevel.EXECUTE)
            permissions["group"] = group_perms

            # その他の権限
            other_perms = []
            if mode & stat.S_IROTH:
                other_perms.append(PermissionLevel.READ)
            if mode & stat.S_IWOTH:
                other_perms.append(PermissionLevel.WRITE)
            if mode & stat.S_IXOTH:
                other_perms.append(PermissionLevel.EXECUTE)
            permissions["other"] = other_perms

            return permissions

        except (OSError, AttributeError):
            return {}

    def set_file_permissions(self, file_path: Path, permissions: dict[str, list[PermissionLevel]]) -> bool:
        """ファイルの権限設定を更新.

        Args:
            file_path: 対象ファイルパス
            permissions: 設定する権限

        Returns:
            設定成功時True
        """
        if not file_path.exists():
            return False

        try:
            mode = 0

            # オーナー権限
            owner_perms = permissions.get("owner", [])
            if PermissionLevel.READ in owner_perms:
                mode |= stat.S_IRUSR
            if PermissionLevel.WRITE in owner_perms:
                mode |= stat.S_IWUSR
            if PermissionLevel.EXECUTE in owner_perms:
                mode |= stat.S_IXUSR

            # グループ権限
            group_perms = permissions.get("group", [])
            if PermissionLevel.READ in group_perms:
                mode |= stat.S_IRGRP
            if PermissionLevel.WRITE in group_perms:
                mode |= stat.S_IWGRP
            if PermissionLevel.EXECUTE in group_perms:
                mode |= stat.S_IXGRP

            # その他の権限
            other_perms = permissions.get("other", [])
            if PermissionLevel.READ in other_perms:
                mode |= stat.S_IROTH
            if PermissionLevel.WRITE in other_perms:
                mode |= stat.S_IWOTH
            if PermissionLevel.EXECUTE in other_perms:
                mode |= stat.S_IXOTH

            file_path.chmod(mode)
            return True

        except (OSError, AttributeError):
            return False

    def check_permission(self, file_path: Path, user: str, permission: PermissionLevel) -> bool:
        """特定ユーザーの権限を確認.

        Args:
            file_path: 対象ファイルパス
            user: ユーザー名
            permission: 確認する権限

        Returns:
            権限がある場合True
        """
        if not file_path.exists():
            return False

        permissions = self.get_file_permissions(file_path)

        # 簡易実装:現在のユーザーの場合はオーナー権限をチェック
        current_user = os.getenv("USER", os.getenv("USERNAME", ""))
        if user in (current_user, "owner"):
            owner_perms = permissions.get("owner", [])
            return permission in owner_perms

        # その他のユーザーは other 権限をチェック
        other_perms = permissions.get("other", [])
        return permission in other_perms

    def list_accessible_files(self, user: str, permission: PermissionLevel) -> list[Path]:
        """ユーザーがアクセス可能なファイル一覧を取得.

        Args:
            user: ユーザー名
            permission: 必要な権限レベル

        Returns:
            アクセス可能なファイルパスのリスト
        """
        # キャッシュから取得を試みる
        cache_data: dict[str, Any] = self._load_permission_cache()
        accessible_files = []

        for file_path_str in cache_data:
            file_path = Path(file_path_str)
            if file_path.exists():
                if self.check_permission(file_path, user, permission):
                    accessible_files.append(file_path)

        return accessible_files

    def backup_permissions(self, directory: Path) -> str | None:
        """ディレクトリの権限設定をバックアップ.

        Args:
            directory: バックアップ対象ディレクトリ

        Returns:
            バックアップID、失敗時はNone
        """
        if not directory.exists() or not directory.is_dir():
            return None

        backup_id = f"permissions_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        backup_data: dict[str, Any] = {
            "backup_id": backup_id,
            "directory": str(directory),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "permissions": {},
        }

        try:
            # ディレクトリ内のファイルの権限を収集
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    permissions = self.get_file_permissions(file_path)
                    backup_data["permissions"][str(file_path)] = {
                        perm_type: [perm.value for perm in perm_list] for perm_type, perm_list in permissions.items()
                    }

            # バックアップデータを保存
            self._save_permission_backup(backup_id, backup_data)
            return backup_id

        except (OSError, ValueError, TypeError):
            return None

    def restore_permissions(self, backup_id: str) -> bool:
        """権限設定を復元.

        Args:
            backup_id: バックアップID

        Returns:
            復元成功時True
        """
        backup_data: dict[str, Any] = self._load_permission_backup(backup_id)
        if not backup_data:
            return False

        try:
            permissions_data: dict[str, Any] = backup_data.get("permissions", {})

            for file_path_str, permissions_dict in permissions_data.items():
                file_path = Path(file_path_str)
                if file_path.exists():
                    # 権限データを復元
                    permissions = {}
                    for perm_type, perm_values in permissions_dict.items():
                        perm_list = [PermissionLevel(val) for val in perm_values]
                        permissions[perm_type] = perm_list

                    self.set_file_permissions(file_path, permissions)

            return True

        except (OSError, ValueError, TypeError):
            return False

    def _load_permission_cache(self) -> dict:
        """権限キャッシュを読み込み."""
        if not self.permission_cache_path.exists():
            return {}

        try:
            with Path(self.permission_cache_path).open(encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    def _save_permission_cache(self, cache_data: dict[str, Any]) -> None:
        """権限キャッシュを保存."""
        try:
            self.permission_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with Path(self.permission_cache_path).open("w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except (OSError, ValueError, json.JSONEncodeError):
            pass

    def _save_permission_backup(self, backup_id: str, backup_data: dict[str, Any]) -> None:
        """権限バックアップを保存."""
        backup_file = self.permission_cache_path.parent / f"{backup_id}.json"
        try:
            with Path(backup_file).open("w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
        except (OSError, ValueError, json.JSONEncodeError):
            pass

    def _load_permission_backup(self, backup_id: str) -> dict[str, Any] | None:
        """権限バックアップを読み込み."""
        backup_file = self.permission_cache_path.parent / f"{backup_id}.json"
        if not backup_file.exists():
            return None

        try:
            with Path(backup_file).open(encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError, json.JSONDecodeError):
            return None
