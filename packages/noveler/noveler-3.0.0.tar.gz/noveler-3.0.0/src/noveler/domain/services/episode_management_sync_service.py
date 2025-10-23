#!/usr/bin/env python3

"""Domain.services.episode_management_sync_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""話数管理同期サービス
話数管理.yaml自動同期機能のドメイン層
"""


import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import yaml

from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager

if TYPE_CHECKING:
    from noveler.domain.interfaces.i_path_service import IPathService

from noveler.domain.exceptions import ValidationError
from noveler.domain.interfaces.yaml_handler import IYamlHandler
from noveler.domain.value_objects.episode_completion_data import EpisodeCompletionData
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.sync_result import SyncResult

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class CompletionData(Protocol):
    """エピソード完成データのプロトコル"""

    project_name: str
    episode_number: int

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        ...


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class EpisodeManagementSyncService:
    """話数管理同期サービス"""

    def __init__(
        self,
        project_base_path: str | Path | None = None,
        yaml_handler: IYamlHandler | None = None,
        path_service: IPathService | None = None,
    ) -> None:
        """初期化

        Args:
            project_base_path: プロジェクトのベースパス
            yaml_handler: YAML操作のハンドラー(依存性注入)
        """
        base_path = Path(project_base_path) if project_base_path is not None else None

        if path_service is None:
            path_service = self._create_default_path_service(base_path)

        if base_path is None:
            try:
                base_path = Path(path_service.project_root)
            except AttributeError:
                base_path = Path.cwd()

        self._path_service = path_service
        self.project_base_path = base_path
        self.yaml_handler = yaml_handler or _DefaultYamlHandler()

    def sync_episode_completion(self, completion_data: EpisodeCompletionData) -> SyncResult:
        """エピソード完成データを話数管理.yamlに同期"""

        # セキュリティチェック:パストラバーサル攻撃防止
        if ".." in completion_data.project_name or "/" in completion_data.project_name:
            msg = "不正なパスが検出されました"
            raise ValidationError(msg)

        # 話数管理.yamlのパスを構築
        yaml_path = self._get_episode_management_yaml_path(completion_data.project_name)

        # ファイル存在確認
        if not yaml_path.exists():
            msg = f"話数管理.yamlファイルが見つかりません: {yaml_path}"
            raise FileNotFoundError(msg)

        # 権限チェック
        self.validate_file_permissions(yaml_path)

        # バックアップ作成
        backup_path = self.create_backup(yaml_path)

        try:
            # YAMLファイルを読み込み(依存性注入されたハンドラーを使用)
            yaml_data: dict[str, Any] = self.yaml_handler.load_yaml(str(yaml_path))

            # エピソード情報を更新
            updated_fields = self._update_episode_data(yaml_data, completion_data)

            # 統計情報を更新
            self._update_statistics(yaml_data)

            # YAMLファイルに保存(依存性注入されたハンドラーを使用)
            self.yaml_handler.save_yaml(yaml_data, str(yaml_path))

            return SyncResult(success=True, updated_fields=updated_fields, error_message=None, backup_created=True)

        except ValidationError:
            # ValidationErrorは再送出(エピソードが見つからない等)
            if backup_path.exists():
                backup_path.unlink()  # バックアップを削除
            raise
        except Exception as e:
            # その他のエラー時はバックアップから復元
            if backup_path.exists():
                shutil.copy2(backup_path, yaml_path)

            return SyncResult(
                success=False,
                updated_fields=[],
                error_message=f"同期中にエラーが発生しました: {e!s}",
                backup_created=True,
            )

    def _get_episode_management_yaml_path(self, project_name: str) -> Path:
        """話数管理.yamlファイルのパスを取得"""
        project_root = self._resolve_project_root(project_name)

        path_service = self._path_service
        try:
            current_root = Path(path_service.project_root)
        except AttributeError:
            current_root = None

        if current_root is None or current_root.resolve() != project_root.resolve():
            path_service = self._create_default_path_service(project_root)
            self._path_service = path_service

        # Use path service episode management file to honour templates
        yaml_path = Path(path_service.get_episode_management_file())
        if not yaml_path.is_absolute():
            yaml_path = project_root / yaml_path
        return yaml_path

    def _update_episode_data(self, yaml_data: dict[str, Any], completion_data: EpisodeCompletionData) -> list[str]:
        """エピソードデータを更新"""
        updated_fields: list[str] = []

        # エピソードキーを構築
        episode_key = f"第{completion_data.episode_number:03d}話"

        # エピソードが存在しない場合はエラー
        if "episodes" not in yaml_data or episode_key not in yaml_data["episodes"]:
            msg = f"エピソード番号{completion_data.episode_number}が見つかりません"
            raise ValidationError(msg)

        # エピソード情報を更新
        episode_data: dict[str, Any] = yaml_data["episodes"][episode_key]
        completion_dict = completion_data.to_dict()

        for field, value in completion_dict.items():
            if field not in episode_data or episode_data[field] != value:
                episode_data[field] = value
                updated_fields.append(field)

        return updated_fields

    def _update_statistics(self, yaml_data: dict[str, Any]) -> None:
        """統計情報を更新"""
        if "episodes" not in yaml_data:
            return

        # 統計情報を計算
        stats = self.calculate_statistics(yaml_data)

        # 統計情報を更新
        if "statistics" not in yaml_data:
            yaml_data["statistics"] = {}

        yaml_data["statistics"].update(stats)
        yaml_data["statistics"]["last_updated"] = project_now().datetime.isoformat()

    def calculate_statistics(self, yaml_data: dict[str, Any]) -> dict[str, Any]:
        """統計情報を計算"""
        if "episodes" not in yaml_data:
            return {}

        episodes = yaml_data["episodes"]
        total_episodes = len(episodes)
        completed_episodes = 0
        quality_scores: list[float] = []

        for episode_data in episodes.values():
            if episode_data.get("completion_status") in ["執筆済み", "推敲済み", "公開済み"]:
                completed_episodes += 1

            if episode_data.get("quality_score") is not None:
                quality_scores.append(episode_data["quality_score"])

        average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        completion_rate = (completed_episodes / total_episodes * 100) if total_episodes > 0 else 0

        return {
            "total_episodes": total_episodes,
            "completed_episodes": completed_episodes,
            "average_quality_score": round(average_quality_score, 1),
            "completion_rate": round(completion_rate, 1),
        }

    def create_backup(self, yaml_path: Path) -> Path:
        """バックアップを作成"""
        backup_path = yaml_path.with_suffix(yaml_path.suffix + ".bak")
        shutil.copy2(yaml_path, backup_path)
        return backup_path

    def validate_file_permissions(self, yaml_path: Path) -> None:
        """ファイル権限を検証"""
        if not os.access(yaml_path, os.W_OK):
            msg = f"書き込み権限がありません: {yaml_path}"
            raise ValidationError(msg)

        if not os.access(yaml_path, os.R_OK):
            msg = f"読み取り権限がありません: {yaml_path}"
            raise ValidationError(msg)

    def _create_default_path_service(self, project_root: Path | None) -> IPathService:
        """テストや簡易利用向けのデフォルトPathServiceを生成"""
        target_root = project_root or Path.cwd()

        try:
            manager = get_path_service_manager()
            return manager.create_common_path_service(project_root=target_root)
        except Exception:
            return _FallbackPathService(target_root)

    def _resolve_project_root(self, project_name: str) -> Path:
        """プロジェクト名から実際のプロジェクトルートを推定"""
        if project_name and self.project_base_path.name == project_name:
            return self.project_base_path

        if project_name:
            return self.project_base_path / project_name

        return self.project_base_path


class _DefaultYamlHandler(IYamlHandler):
    """YAML操作の簡易実装"""

    def load_yaml(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {}

        with path.open(encoding="utf-8") as fp:
            return yaml.safe_load(fp) or {}

    def save_yaml(self, data: dict[str, Any], file_path: str) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            yaml.safe_dump(data, fp, allow_unicode=True, sort_keys=False)

    def format_yaml(self, data: dict[str, Any]) -> str:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


class _FallbackPathService:
    """Minimal IPathService 実装 (テスト用フォールバック)"""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        return self._project_root

    def get_management_dir(self) -> Path:
        directory = self._project_root / "50_管理資料"
        directory.mkdir(parents=True, exist_ok=True)
        return directory
