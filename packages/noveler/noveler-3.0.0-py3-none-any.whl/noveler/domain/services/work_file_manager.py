#!/usr/bin/env python3

"""Domain.services.work_file_manager
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""作業ファイル管理サービス

SPEC-STEPWISE-WRITING-001に基づくバージョン管理付き作業ファイル管理
B20準拠: Functional Core実装（副作用は最小限に局所化）
"""


import datetime
import re
import time
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger

# デフォルトではNullLoggerを使用（依存性注入で実装を提供）
logger: ILogger = NullLogger()


class WorkFileManagerError(Exception):
    """作業ファイル管理エラー"""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        self.file_path = file_path
        super().__init__(message)


class WorkFile:
    """作業ファイルを表すValueObject"""

    def __init__(
        self,
        episode_number: int,
        step_number: int,
        version: int,
        content: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.episode_number = episode_number
        self.step_number = step_number
        self.version = version
        self.content = content
        self.metadata = metadata or {}

        # メタデータの自動設定
        if "_metadata" not in self.content:
            self.content["_metadata"] = {}

        self.content["_metadata"].update(
            {"version": version, "episode_number": episode_number, "step_number": step_number, **self.metadata}
        )

    @property
    def filename(self) -> str:
        """ファイル名を生成"""
        return f"episode{self.episode_number:03d}_step{self.step_number:02d}_v{self.version}.yaml"

    @property
    def backup_filename(self) -> str:
        """バックアップファイル名を生成"""
        return f"episode{self.episode_number:03d}_step{self.step_number:02d}_v{self.version}_backup.yaml"

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "episode_number": self.episode_number,
            "step_number": self.step_number,
            "version": self.version,
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkFile:
        """辞書から作業ファイルを復元"""
        return cls(
            episode_number=data["episode_number"],
            step_number=data["step_number"],
            version=data["version"],
            content=data["content"],
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_file_path(cls, file_path: Path) -> WorkFile:
        """ファイルパスから作業ファイルを復元"""
        # ファイル名パターン: episode001_step00_v1.yaml

        pattern = r"episode(\d{3})_step(\d{2})_v(\d+)\.yaml$"
        match = re.match(pattern, file_path.name)

        if not match:
            msg = f"無効なファイル名形式: {file_path.name}"
            raise WorkFileManagerError(msg, file_path)

        episode_number = int(match.group(1))
        step_number = int(match.group(2))
        version = int(match.group(3))

        # ファイル内容を読み込み
        try:
            with open(file_path, encoding="utf-8") as f:
                content = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            msg = f"YAMLファイルの読み込みに失敗: {e}"
            raise WorkFileManagerError(msg, file_path)
        except Exception as e:
            msg = f"ファイルの読み込みに失敗: {e}"
            raise WorkFileManagerError(msg, file_path)

        metadata = content.get("_metadata", {})

        return cls(
            episode_number=episode_number, step_number=step_number, version=version, content=content, metadata=metadata
        )


class WorkFileManager:
    """作業ファイル管理サービス

    B20準拠: 副作用（ファイルI/O）は明示的に分離
    """

    def __init__(self, work_directory: Path | None = None) -> None:
        """初期化

        Args:
            work_directory: 作業ファイルディレクトリ（None の場合は相対パス使用）
        """
        self.work_directory = work_directory or Path("60_作業ファイル")  # TODO: IPathServiceを使用するように修正
        logger.debug(f"WorkFileManager initialized with directory: {self.work_directory}")

    def find_existing_work_files(self, episode_number: int) -> dict[int, Path]:
        """指定エピソードの既存作業ファイルを検索

        B20準拠: Functional Core（読み取り専用・副作用なし）

        Args:
            episode_number: エピソード番号

        Returns:
            Dict[int, Path]: {ステップ番号: ファイルパス} の辞書
        """
        existing_files: dict[int, Path] = {}

        if not self.work_directory.exists():
            logger.debug(f"Work directory does not exist: {self.work_directory}")
            return existing_files

        # パターンマッチングでファイル検索
        pattern = f"episode{episode_number:03d}_step*_v*.yaml"

        try:
            for file_path in self.work_directory.glob(pattern):
                if file_path.is_file() and not file_path.name.endswith("_backup.yaml"):
                    try:
                        work_file = WorkFile.from_file_path(file_path)
                        step_num = work_file.step_number

                        # 最新バージョンのみ保持
                        if step_num not in existing_files:
                            existing_files[step_num] = file_path
                        else:
                            existing_work_file = WorkFile.from_file_path(existing_files[step_num])
                            if work_file.version > existing_work_file.version:
                                existing_files[step_num] = file_path

                    except WorkFileManagerError as e:
                        logger.warning(f"Invalid work file ignored: {file_path}, error: {e}")
                        continue

        except Exception as e:
            logger.exception(f"Error searching for work files: {e}")
            msg = f"作業ファイル検索中にエラーが発生: {e}"
            raise WorkFileManagerError(msg)

        logger.debug(f"Found {len(existing_files)} existing work files for episode {episode_number}")
        return existing_files

    def load_work_file(self, file_path: Path) -> WorkFile:
        """作業ファイルを読み込み

        B20準拠: Functional Core（副作用なし）

        Args:
            file_path: ファイルパス

        Returns:
            WorkFile: 読み込まれた作業ファイル

        Raises:
            WorkFileManagerError: ファイル読み込みに失敗した場合
        """
        if not file_path.exists():
            msg = f"ファイルが存在しません: {file_path}"
            raise WorkFileManagerError(msg, file_path)

        try:
            work_file = WorkFile.from_file_path(file_path)
            logger.debug(f"Work file loaded: {file_path}")
            return work_file

        except Exception as e:
            logger.exception(f"Failed to load work file {file_path}: {e}")
            msg = f"作業ファイルの読み込みに失敗: {e}"
            raise WorkFileManagerError(msg, file_path)

    def save_work_file_with_version(
        self, episode_number: int, step_number: int, content: dict[str, Any], improvement_mode: bool = False
    ) -> Path:
        """バージョン管理付きで作業ファイルを保存

        B20準拠: Imperative Shell（副作用を明示的に実行）

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号
            content: 保存する内容
            improvement_mode: 改善モードかどうか

        Returns:
            Path: 保存されたファイルのパス

        Raises:
            WorkFileManagerError: 保存に失敗した場合
        """
        try:
            # ディレクトリ作成
            self.work_directory.mkdir(parents=True, exist_ok=True)

            # 既存ファイルから次のバージョン番号を決定
            next_version = self._determine_next_version(episode_number, step_number)

            # 前のバージョン情報を取得
            previous_version = next_version - 1 if next_version > 1 else None

            # メタデータを構築
            metadata = {
                "created_at": datetime.project_now().datetime.isoformat(),
                "improvement_mode": improvement_mode,
                "previous_version": previous_version,
            }

            # 品質スコアを計算（コンテンツに含まれている場合）
            if "quality_score" in content:
                metadata["quality_score"] = content["quality_score"]

            # 作業ファイルオブジェクトを作成
            work_file = WorkFile(
                episode_number=episode_number,
                step_number=step_number,
                version=next_version,
                content=content,
                metadata=metadata,
            )

            # ファイル保存
            file_path = self.work_directory / work_file.filename
            execution_time = self._save_file_with_backup(file_path, work_file.content)

            # 実行時間をメタデータに追加
            work_file.content["_metadata"]["execution_time"] = execution_time
            self._save_file_with_backup(file_path, work_file.content)  # メタデータ更新で再保存

            logger.info(f"Work file saved: {file_path} (Version {next_version})")
            return file_path

        except Exception as e:
            logger.exception(f"Failed to save work file: {e}")
            msg = f"作業ファイルの保存に失敗: {e}"
            raise WorkFileManagerError(msg)

    def _determine_next_version(self, episode_number: int, step_number: int) -> int:
        """次のバージョン番号を決定

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号

        Returns:
            int: 次のバージョン番号
        """
        if not self.work_directory.exists():
            return 1

        # 同じエピソード・ステップの既存ファイルを検索
        pattern = f"episode{episode_number:03d}_step{step_number:02d}_v*.yaml"
        max_version = 0

        for file_path in self.work_directory.glob(pattern):
            if file_path.is_file() and not file_path.name.endswith("_backup.yaml"):
                try:
                    work_file = WorkFile.from_file_path(file_path)
                    max_version = max(max_version, work_file.version)
                except WorkFileManagerError:
                    # 無効なファイルは無視
                    continue

        return max_version + 1

    def _save_file_with_backup(self, file_path: Path, content: dict[str, Any]) -> float:
        """バックアップ付きでファイルを保存

        Args:
            file_path: 保存先ファイルパス
            content: 保存内容

        Returns:
            float: 実行時間（秒）
        """
        start_time = time.time()

        try:
            # 既存ファイルがあればバックアップ作成
            if file_path.exists():
                backup_path = file_path.parent / f"{file_path.stem}_backup{file_path.suffix}"
                backup_path.write_bytes(file_path.read_bytes())
                logger.debug(f"Backup created: {backup_path}")

            # 新しいファイルを保存
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(content, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            end_time = time.time()
            execution_time = end_time - start_time

            logger.debug(f"File saved in {execution_time:.3f}s: {file_path}")
            return execution_time

        except Exception as e:
            msg = f"ファイル保存エラー: {e}"
            raise WorkFileManagerError(msg, file_path)

    def get_work_file_history(self, episode_number: int, step_number: int) -> list[WorkFile]:
        """作業ファイルの履歴を取得

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号

        Returns:
            List[WorkFile]: バージョン順の作業ファイルリスト
        """
        history: list[WorkFile] = []

        if not self.work_directory.exists():
            return history

        pattern = f"episode{episode_number:03d}_step{step_number:02d}_v*.yaml"

        for file_path in self.work_directory.glob(pattern):
            if file_path.is_file() and not file_path.name.endswith("_backup.yaml"):
                try:
                    work_file = WorkFile.from_file_path(file_path)
                    history.append(work_file)
                except WorkFileManagerError:
                    continue

        # バージョン順でソート
        history.sort(key=lambda x: x.version)
        logger.debug(f"Found {len(history)} versions for episode {episode_number} step {step_number}")

        return history

    def cleanup_old_versions(self, episode_number: int, step_number: int, keep_versions: int = 5) -> list[Path]:
        """古いバージョンをクリーンアップ

        Args:
            episode_number: エピソード番号
            step_number: ステップ番号
            keep_versions: 保持するバージョン数

        Returns:
            List[Path]: 削除されたファイルパスのリスト
        """
        history = self.get_work_file_history(episode_number, step_number)

        if len(history) <= keep_versions:
            return []

        # 古いバージョンを特定（最新から keep_versions 個を除く）
        old_versions = history[:-keep_versions]
        deleted_files: list[Path] = []

        for work_file in old_versions:
            file_path = self.work_directory / work_file.filename
            backup_path = self.work_directory / work_file.backup_filename

            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_files.append(file_path)

                if backup_path.exists():
                    backup_path.unlink()
                    deleted_files.append(backup_path)

                logger.debug(f"Cleaned up version {work_file.version}: {file_path}")

            except Exception as e:
                logger.warning(f"Failed to delete old version {file_path}: {e}")

        logger.info(f"Cleaned up {len(deleted_files)} old files for episode {episode_number} step {step_number}")
        return deleted_files

    def get_summary_statistics(self) -> dict[str, Any]:
        """作業ファイルの統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        if not self.work_directory.exists():
            return {"total_files": 0, "episodes": 0, "steps": 0, "total_versions": 0}

        episodes = set()
        steps = set()
        total_versions = 0
        total_files = 0

        for file_path in self.work_directory.glob("episode*_step*_v*.yaml"):
            if file_path.is_file() and not file_path.name.endswith("_backup.yaml"):
                try:
                    work_file = WorkFile.from_file_path(file_path)
                    episodes.add(work_file.episode_number)
                    steps.add(work_file.step_number)
                    total_versions += work_file.version
                    total_files += 1
                except WorkFileManagerError:
                    continue

        return {
            "total_files": total_files,
            "episodes": len(episodes),
            "steps": len(steps),
            "total_versions": total_versions,
            "avg_versions_per_file": total_versions / total_files if total_files > 0 else 0,
        }


def create_work_file_manager(work_directory: Path | None = None) -> WorkFileManager:
    """WorkFileManagerのファクトリ関数

    Args:
        work_directory: 作業ディレクトリ（オプション）

    Returns:
        WorkFileManager: 初期化済みのインスタンス
    """
    return WorkFileManager(work_directory)
