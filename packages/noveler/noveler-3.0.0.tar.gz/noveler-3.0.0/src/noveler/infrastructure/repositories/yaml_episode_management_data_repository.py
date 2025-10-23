"""YAMLエピソード管理データリポジトリ実装."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.episode_management_data_repository import EpisodeManagementDataRepository


class YamlEpisodeManagementDataRepository(EpisodeManagementDataRepository):
    """YAMLファイルベースのエピソード管理データリポジトリ実装."""

    def __init__(self, data_file_path: Path) -> None:
        """初期化.

        Args:
            data_file_path: エピソード管理データファイルのパス
        """
        self.data_file_path = data_file_path
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_episode_data(self, episode_id: str, management_data: dict[str, Any]) -> bool:
        """エピソード管理データを保存.

        Args:
            episode_id: エピソードID
            management_data: 管理データ

        Returns:
            保存成功時True
        """
        try:
            # 既存データを読み込み
            all_data: dict[str, Any] = self._load_all_data()

            # エピソードデータを更新
            all_data[episode_id] = {**management_data, "last_updated": datetime.now(timezone.utc).isoformat()}

            # ファイルに保存
            self._save_all_data(all_data)
            return True

        except Exception:
            return False

    def load_episode_data(self, episode_id: str) -> dict[str, Any] | None:
        """エピソード管理データを読み込み.

        Args:
            episode_id: エピソードID

        Returns:
            管理データ、見つからない場合はNone
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            return all_data.get(episode_id)

        except Exception:
            return None

    def list_episode_ids(self) -> list[str]:
        """管理対象エピソードID一覧を取得.

        Returns:
            エピソードIDのリスト
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            return sorted(all_data.keys())

        except Exception:
            return []

    def delete_episode_data(self, episode_id: str) -> bool:
        """エピソード管理データを削除.

        Args:
            episode_id: エピソードID

        Returns:
            削除成功時True
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()

            if episode_id in all_data:
                del all_data[episode_id]
                self._save_all_data(all_data)
                return True

            return False

        except Exception:
            return False

    def update_episode_status(self, episode_id: str, status: str) -> bool:
        """エピソードステータスを更新.

        Args:
            episode_id: エピソードID
            status: 新しいステータス

        Returns:
            更新成功時True
        """
        try:
            episode_data: dict[str, Any] = self.load_episode_data(episode_id)
            if episode_data is None:
                # 新規データとして作成
                episode_data: dict[str, Any] = {}

            episode_data["status"] = status
            episode_data["status_updated_at"] = datetime.now(timezone.utc).isoformat()

            return self.save_episode_data(episode_id, episode_data)

        except Exception:
            return False

    def get_episodes_by_status(self, status: str) -> list[str]:
        """指定ステータスのエピソード一覧を取得.

        Args:
            status: フィルタするステータス

        Returns:
            マッチしたエピソードIDのリスト
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            matched_ids = []

            for episode_id, data in all_data.items():
                if data.get("status") == status:
                    matched_ids.append(episode_id)

            return sorted(matched_ids)

        except Exception:
            return []

    def update_word_count(self, episode_id: str, word_count: int) -> bool:
        """エピソードの文字数を更新.

        Args:
            episode_id: エピソードID
            word_count: 文字数

        Returns:
            更新成功時True
        """
        try:
            episode_data: dict[str, Any] = self.load_episode_data(episode_id)
            if episode_data is None:
                episode_data: dict[str, Any] = {}

            episode_data["word_count"] = word_count
            episode_data["word_count_updated_at"] = datetime.now(timezone.utc).isoformat()

            return self.save_episode_data(episode_id, episode_data)

        except Exception:
            return False

    def get_word_count_history(self, episode_id: str) -> list[dict[str, Any]]:
        """エピソードの文字数履歴を取得.

        Args:
            episode_id: エピソードID

        Returns:
            文字数履歴のリスト
        """
        try:
            episode_data: dict[str, Any] = self.load_episode_data(episode_id)
            if episode_data is None:
                return []

            return episode_data.get("word_count_history", [])

        except Exception:
            return []

    def add_word_count_history_entry(self, episode_id: str, word_count: int, timestamp: str | None = None) -> bool:
        """文字数履歴にエントリを追加.

        Args:
            episode_id: エピソードID
            word_count: 文字数
            timestamp: タイムスタンプ(省略時は現在時刻)

        Returns:
            追加成功時True
        """
        try:
            episode_data: dict[str, Any] = self.load_episode_data(episode_id)
            if episode_data is None:
                episode_data: dict[str, Any] = {}

            if "word_count_history" not in episode_data:
                episode_data["word_count_history"] = []

            entry = {"word_count": word_count, "timestamp": timestamp or datetime.now(timezone.utc).isoformat()}

            episode_data["word_count_history"].append(entry)

            # 履歴が多すぎる場合は古いものを削除(最新100件まで保持)
            if len(episode_data["word_count_history"]) > 100:
                episode_data["word_count_history"] = episode_data["word_count_history"][-100:]

            return self.save_episode_data(episode_id, episode_data)

        except Exception:
            return False

    def get_statistics(self) -> dict[str, Any]:
        """管理データの統計情報を取得.

        Returns:
            統計情報
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()

            # ステータス別の統計
            status_counts = {}
            total_word_count = 0
            episode_count = len(all_data)

            for episode_data in all_data.values():
                status = episode_data.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

                word_count = episode_data.get("word_count", 0)
                if isinstance(word_count, int):
                    total_word_count += word_count

            return {
                "total_episodes": episode_count,
                "total_word_count": total_word_count,
                "average_word_count": total_word_count / episode_count if episode_count > 0 else 0,
                "status_distribution": status_counts,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception:
            return {}

    def _load_all_data(self) -> dict[str, dict[str, Any]]:
        """全データを読み込み.

        Returns:
            全エピソード管理データ
        """
        if not self.data_file_path.exists():
            return {}

        try:
            with self.data_file_path.Path(encoding="utf-8").open() as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_all_data(self, data: dict[str, dict[str, Any]]) -> None:
        """全データを保存.

        Args:
            data: 保存するデータ
        """
        with self.data_file_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
