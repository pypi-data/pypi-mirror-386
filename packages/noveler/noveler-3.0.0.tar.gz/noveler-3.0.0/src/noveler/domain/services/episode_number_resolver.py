"""Domain.services.episode_number_resolver
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""エピソード番号解決サービス
仕様: specs/episode_number_resolver.spec.md
"""


import re
from pathlib import Path

from noveler.domain.value_objects.path_configuration import get_default_manuscript_dir
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager

if TYPE_CHECKING:
    from noveler.domain.interfaces.i_path_service import IPathService

import yaml

from noveler.domain.exceptions import DomainException

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class EpisodeNotFoundError(DomainException):
    """指定された話数が存在しない場合のエラー"""


class ManagementFileNotFoundError(DomainException):
    """話数管理.yamlが見つからない場合のエラー"""


class InvalidEpisodeNumberError(DomainException):
    """話数が無効(負数、0など)な場合のエラー"""


class EpisodeFileInfo:
    """エピソードファイル情報"""

    def __init__(
        self,
        episode_number: int,
        title: str,
        path_service: IPathService | None = None,
        file_path: Path | None = None,
        exists: bool = False,
    ) -> None:
        self._path_service = path_service
        self.episode_number = episode_number
        self.title = title
        self.file_path = file_path
        self.exists = exists


class _FallbackPathService:
    """Minimal path service used when the real factory is unavailable."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def get_episode_management_file(self) -> Path:
        return self._project_root / "50_管理資料" / "話数管理.yaml"

    def get_manuscript_dir(self) -> Path:
        return get_default_manuscript_dir(self._project_root)

    @property
    def project_root(self) -> Path:
        return self._project_root


class EpisodeNumberResolver:
    """エピソード番号とファイルパスを相互変換するサービス"""

    def __init__(self, project_root: str | Path, path_service: IPathService | None = None) -> None:
        """Args:
        project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = Path(project_root)
        self._path_service = path_service or self._create_path_service(self.project_root)
        # B20準拠: Path ServiceはDI注入されたものを使用
        self.management_file = self._resolve_project_path(self._path_service.get_episode_management_file())
        self._manuscript_dir = self._resolve_project_path(self._path_service.get_manuscript_dir())
        self._cache: dict[str, Any] | None = None
        self._cache_mtime: float | None = None

    def _create_path_service(self, project_root: Path) -> IPathService:
        """Resolve the path service via the factory proxy with a domain-safe fallback."""
        try:
            manager = get_path_service_manager()
            return manager.create_common_path_service(project_root=project_root)
        except Exception:
            return _FallbackPathService(project_root)

    def _resolve_project_path(self, candidate: Path | str) -> Path:
        """プロジェクトルート基準でPathを解決"""
        path = Path(candidate)
        if path.is_absolute():
            return path
        return self.project_root / path

    def resolve_episode_number(self, episode_number: int) -> EpisodeFileInfo:
        """話数からファイルパスを解決する

        Args:
            episode_number: エピソード番号(1以上の整数)

        Returns:
            EpisodeFileInfo: エピソードファイル情報

        Raises:
            InvalidEpisodeNumberError: 話数が無効な場合
            ManagementFileNotFoundError: 話数管理.yamlが存在しない場合
            EpisodeNotFoundError: 指定された話数が存在しない場合
        """
        self._validate_episode_number(episode_number)
        management_data: dict[str, Any] = self._load_management_file()
        episode_data: dict[str, Any] = self._find_episode_in_management_data(management_data, episode_number)
        return self._create_episode_file_info(episode_number, episode_data)

    def resolve_file_name(self, file_name_or_path: str | Path) -> int:
        """ファイル名から話数を逆引きする

        Args:
            file_name_or_path: ファイル名またはパス

        Returns:
            int: エピソード番号

        Raises:
            EpisodeNotFoundError: ファイル名に対応する話数が見つからない場合
        """
        file_path = Path(file_name_or_path)  # TODO: IPathServiceを使用するように修正
        file_name = file_path.name

        # 直接的なパターンマッチングを先に試行
        episode_number = self._extract_episode_number_from_filename(file_name)
        if episode_number is not None:
            return episode_number

        # 管理データから検索
        return self._find_episode_number_in_management_data(file_name)

    def _validate_episode_number(self, episode_number: int) -> None:
        """話数の妥当性をチェックする"""
        if episode_number <= 0:
            msg = f"話数は1以上である必要があります: {episode_number}"
            raise InvalidEpisodeNumberError(msg)

    def _find_episode_in_management_data(self, management_data: dict[str, Any], episode_number: int) -> dict[str, Any]:
        """管理データから指定された話数のエピソードを検索する"""
        episodes = management_data.get("episodes", {})

        if isinstance(episodes, list):
            return self._find_episode_in_list(episodes, episode_number)
        if isinstance(episodes, dict):
            return self._find_episode_in_dict(episodes, episode_number)

        msg = f"話数{episode_number}が話数管理.yamlに存在しません"
        raise EpisodeNotFoundError(msg)

    def _find_episode_in_list(self, episodes: list[dict[str, Any]], episode_number: int) -> dict[str, Any]:
        """リスト形式のエピソードデータから指定された話数を検索する"""
        for ep_data in episodes:
            if isinstance(ep_data, dict) and ep_data.get("episode_number") == episode_number:
                return ep_data

        msg = f"話数{episode_number}が話数管理.yamlに存在しません"
        raise EpisodeNotFoundError(msg)

    def _find_episode_in_dict(self, episodes: dict[str, Any], episode_number: int) -> dict[str, Any]:
        """辞書形式のエピソードデータから指定された話数を検索する"""
        # episode_XXX形式のキーを確認（新形式、優先）
        episode_key = f"episode_{episode_number:03d}"
        episode_data: dict[str, Any] = self._try_get_episode_by_key(episodes, episode_key, episode_number)
        if episode_data is not None:
            return episode_data

        # 第XXX話形式のキーを確認（旧形式、互換性維持）
        legacy_episode_key = f"第{episode_number:03d}話"
        episode_data: dict[str, Any] = self._try_get_episode_by_key(episodes, legacy_episode_key, episode_number)
        if episode_data is not None:
            return episode_data

        # 番号文字列形式のキーを確認(例: "001", "002")
        episode_str_key = f"{episode_number:03d}"
        episode_data: dict[str, Any] = self._try_get_episode_by_key(episodes, episode_str_key, episode_number)
        if episode_data is not None:
            return episode_data

        msg = f"話数{episode_number}が話数管理.yamlに存在しません"
        raise EpisodeNotFoundError(msg)

    def _try_get_episode_by_key(self, episodes: dict[str, Any], key: str, episode_number: int) -> dict[str, Any] | None:
        """指定されたキーでエピソードデータを取得し、必要に応じてepisode_numberを追加する"""
        if key not in episodes or not isinstance(episodes[key], dict):
            return None

        episode_data: dict[str, Any] = episodes[key]
        if "episode_number" not in episode_data:
            episode_data: dict[str, Any] = episode_data.copy()
            episode_data["episode_number"] = episode_number

        return episode_data

    def _create_episode_file_info(self, episode_number: int, episode_data: dict[str, Any]) -> EpisodeFileInfo:
        """エピソードデータからEpisodeFileInfoを作成する"""
        title = episode_data.get("title", "")
        file_path = self._generate_file_path(episode_number, title)
        exists = file_path.exists()

        return EpisodeFileInfo(
            episode_number=episode_number,
            title=title,
            path_service=self._path_service,
            file_path=file_path,
            exists=exists,
        )

    def _generate_file_path(self, episode_number: int, title: str) -> Path:
        """エピソード番号とタイトルからファイルパスを生成する"""
        episode_key = f"第{episode_number:03d}話"
        file_name = f"{episode_key}_{title}.md"
        safe_file_name = self._sanitize_filename(file_name)
        return self._manuscript_dir / safe_file_name

    def _extract_episode_number_from_filename(self, file_name: str) -> int | None:
        """ファイル名から直接話数を抽出する(第XXX話パターン)"""
        match = re.match(r"^第(\d{3})話", file_name)
        return int(match.group(1)) if match else None

    def _find_episode_number_in_management_data(self, file_name: str) -> int:
        """管理データからファイル名に対応する話数を検索する"""
        management_data: dict[str, Any] = self._load_management_file()
        episodes = management_data.get("episodes", {})

        if isinstance(episodes, dict):
            return self._search_in_dict_episodes(episodes, file_name)
        if isinstance(episodes, list):
            return self._search_in_list_episodes(episodes, file_name)

        msg = f"ファイル名 '{file_name}' に対応する話数が見つかりません"
        raise EpisodeNotFoundError(msg)

    def _search_in_dict_episodes(self, episodes: dict[str, Any], file_name: str) -> int:
        """辞書形式のエピソードデータからファイル名を検索する"""
        for episode_key, episode_data in episodes.items():
            if not isinstance(episode_data, dict):
                continue

            episode_number = self._check_episode_key_match(episode_key, episode_data, file_name)
            if episode_number is not None:
                return episode_number

        msg = f"ファイル名 '{file_name}' に対応する話数が見つかりません"
        raise EpisodeNotFoundError(msg)

    def _check_episode_key_match(self, episode_key: str, episode_data: dict[str, Any], file_name: str) -> int | None:
        """エピソードキーとデータからファイル名マッチを確認する"""
        title = episode_data.get("title", "")

        if episode_key.startswith("第"):
            return self._check_formatted_key_match(episode_key, title, file_name)
        if episode_key.isdigit():
            return self._check_numeric_key_match(episode_key, title, file_name)

        return None

    def _check_formatted_key_match(self, episode_key: str, title: str, file_name: str) -> int | None:
        """第XXX話形式のキーでファイル名マッチを確認する"""
        expected_file_name = f"{episode_key}_{title}.md"
        if file_name == expected_file_name:
            match = re.match(r"^第(\d{3})話", episode_key)
            return int(match.group(1)) if match else None
        return None

    def _check_numeric_key_match(self, episode_key: str, title: str, file_name: str) -> int | None:
        """数値形式のキーでファイル名マッチを確認する"""
        episode_num = int(episode_key)
        episode_formatted_key = f"第{episode_num:03d}話"
        expected_file_name = f"{episode_formatted_key}_{title}.md"
        return episode_num if file_name == expected_file_name else None

    def _search_in_list_episodes(self, episodes: list[dict[str, Any]], file_name: str) -> int:
        """リスト形式のエピソードデータからファイル名を検索する"""
        for episode_data in episodes:
            if not isinstance(episode_data, dict):
                continue

            episode_num = episode_data.get("episode_number")
            if episode_num is None:
                continue

            title = episode_data.get("title", "")
            episode_key = f"第{episode_num:03d}話"
            expected_file_name = f"{episode_key}_{title}.md"

            if file_name == expected_file_name:
                return episode_num

        msg = f"ファイル名 '{file_name}' に対応する話数が見つかりません"
        raise EpisodeNotFoundError(msg)

    def _load_management_file(self) -> dict[str, Any]:
        """話数管理ファイルを読み込む(キャッシュ機能付き)

        Returns:
            Dict[str, Any]: 話数管理データ

        Raises:
            ManagementFileNotFoundError: ファイルが存在しない場合
        """
        if not self.management_file.exists():
            msg = f"話数管理.yamlが見つかりません: {self.management_file}"
            raise ManagementFileNotFoundError(msg)

        # ファイルの更新時刻を確認
        current_mtime = self.management_file.stat().st_mtime

        # キャッシュが有効な場合はそれを返す
        if self._cache is not None and self._cache_mtime == current_mtime:
            return self._cache

        # ファイルを読み込み
        with self.management_file.open("r", encoding="utf-8") as f:  # TODO: IPathServiceを使用するように修正
            data = yaml.safe_load(f)

        # キャッシュを更新
        self._cache = data
        self._cache_mtime = current_mtime

        return data

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名から危険な文字を除去する(パストラバーサル対策)

        Args:
            filename: 元のファイル名

        Returns:
            str: 安全なファイル名
        """
        # パス区切り文字を除去
        filename = filename.replace("/", "_")
        filename = filename.replace("\\", "_")
        filename = filename.replace("..", "_")

        # その他の危険な文字を除去
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")

        return filename
