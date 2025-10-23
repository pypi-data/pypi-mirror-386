"""ファイルシステムバックアップリポジトリ実装."""

import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.repositories.file_backup_repository import FileBackupRepository
from noveler.domain.value_objects.project_time import project_now


class FileSystemBackupRepository(FileBackupRepository):
    """ファイルシステムを使用したバックアップリポジトリ実装."""

    def __init__(self, backup_root: Path | str) -> None:
        """初期化.

        Args:
            backup_root: バックアップルートディレクトリ
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_root / "backup_metadata.json"

    def create_backup(self, file_path: Path, backup_name: str | None = None) -> str:
        """ファイルのバックアップを作成.

        Args:
            file_path: バックアップ対象のファイルパス
            backup_name: バックアップ名(省略時は自動生成)

        Returns:
            作成されたバックアップID
        """
        if not file_path.exists():
            msg = f"バックアップ対象ファイルが存在しません: {file_path}"
            raise FileNotFoundError(msg)

        # バックアップIDを生成 - 日本語対応とファイル名長制限
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")

        # ファイル名の長さを制限し、ASCII化
        safe_stem = self._make_safe_filename(file_path.stem)
        backup_id = f"{safe_stem}_{timestamp}"

        if backup_name:
            safe_backup_name = self._make_safe_filename(backup_name)
            backup_id = f"{safe_backup_name}_{timestamp}"

        # バックアップディレクトリを作成
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(exist_ok=True)

        # ファイルをコピー
        backup_file_path = backup_dir / file_path.name
        shutil.copy2(file_path, backup_file_path)

        # メタデータを保存
        metadata = {
            "backup_id": backup_id,
            "original_path": str(file_path),
            "backup_path": str(backup_file_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backup_name": backup_name,
            "file_size": file_path.stat().st_size,
        }

        self._save_metadata(backup_id, metadata)
        return backup_id

    def restore_backup(self, backup_id: str, target_path: Path) -> bool:
        """バックアップを復元.

        Args:
            backup_id: バックアップID
            target_path: 復元先のパス

        Returns:
            復元成功時True
        """
        metadata = self._load_metadata(backup_id)
        if not metadata:
            return False

        backup_file_path = Path(metadata["backup_path"])
        if not backup_file_path.exists():
            return False

        try:
            # 復元先ディレクトリを作成
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイルを復元
            shutil.copy2(backup_file_path, target_path)
            return True
        except (OSError, shutil.Error):
            return False

    def list_backups(self, file_path: Path | None = None) -> list[dict[str, Any]]:
        """バックアップリストを取得.

        Args:
            file_path: 特定ファイルのバックアップのみを取得(省略時は全て)

        Returns:
            バックアップ情報のリスト
        """
        all_metadata = self._load_all_metadata()

        if file_path is None:
            return list(all_metadata.values())

        # 指定ファイルのバックアップのみフィルタ
        file_path_str = str(file_path)
        return [metadata for metadata in all_metadata.values() if metadata.get("original_path") == file_path_str]

    def delete_backup(self, backup_id: str) -> bool:
        """バックアップを削除.

        Args:
            backup_id: バックアップID

        Returns:
            削除成功時True
        """
        backup_dir = self.backup_root / backup_id
        if not backup_dir.exists():
            return False

        try:
            # バックアップディレクトリを削除
            shutil.rmtree(backup_dir)

            # メタデータから削除
            self._remove_metadata(backup_id)
            return True
        except (OSError, shutil.Error):
            return False

    def get_backup_info(self, backup_id: str) -> dict[str, Any] | None:
        """バックアップ情報を取得.

        Args:
            backup_id: バックアップID

        Returns:
            バックアップ情報、存在しない場合はNone
        """
        return self._load_metadata(backup_id)

    def cleanup_old_backups(self, days: int) -> int:
        """古いバックアップを削除.

        Args:
            days: 保持期間(日数)

        Returns:
            削除されたバックアップの数
        """
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        all_metadata = self._load_all_metadata()

        deleted_count = 0
        for backup_id, metadata in all_metadata.items():
            created_at_str = metadata.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.timestamp() < cutoff_date:
                    if self.delete_backup(backup_id):
                        deleted_count += 1
            except ValueError:
                continue

        return deleted_count

    def _make_safe_filename(self, filename: str) -> str:
        """ファイル名を安全な形式に変換（日本語文字化け対策）"""

        # Unicode正規化
        filename = unicodedata.normalize("NFKC", filename)

        # 危険な文字を置換
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # 日本語文字をローマ字に変換（簡易版）
        japanese_map = {
            "チェックリスト": "checklist",
            "DEBUGログ": "debuglog",
            "の副作用": "side_effects",
            "第": "ep",
            "話": "",
            "エピソード": "episode",
        }

        for japanese, english in japanese_map.items():
            filename = filename.replace(japanese, english)

        # 残った日本語文字は削除（ASCII文字のみ保持）
        filename = re.sub(r"[^\w\-_.]", "", filename)

        # 長さ制限（50文字以内）
        if len(filename) > 50:
            filename = filename[:50]

        return filename or "backup"

    def _save_metadata(self, backup_id: str, metadata: dict[str, Any]) -> None:
        """メタデータを保存."""
        all_metadata = self._load_all_metadata()
        all_metadata[backup_id] = metadata

        try:
            with self.metadata_file.Path("w").open(encoding="utf-8") as f:
                json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        except (OSError, json.JSONEncodeError):
            pass  # メタデータ保存に失敗してもバックアップ自体は成功とする

    def _load_metadata(self, backup_id: str) -> dict[str, Any] | None:
        """特定のメタデータを読み込み."""
        all_metadata = self._load_all_metadata()
        return all_metadata.get(backup_id)

    def _load_all_metadata(self) -> dict[str, dict[str, Any]]:
        """全メタデータを読み込み."""
        if not self.metadata_file.exists():
            return {}

        try:
            with self.metadata_file.Path(encoding="utf-8").open() as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _remove_metadata(self, backup_id: str) -> None:
        """メタデータから特定のバックアップを削除."""
        all_metadata = self._load_all_metadata()
        if backup_id in all_metadata:
            del all_metadata[backup_id]

            try:
                with self.metadata_file.Path("w").open(encoding="utf-8") as f:
                    json.dump(all_metadata, f, ensure_ascii=False, indent=2)
            except OSError:
                # メタデータ更新に失敗しても続行
                pass
