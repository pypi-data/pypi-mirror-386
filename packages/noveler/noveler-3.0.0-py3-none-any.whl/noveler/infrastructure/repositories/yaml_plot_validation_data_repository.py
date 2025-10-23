"""YAMLプロット検証データリポジトリ実装."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_validation_data_repository import PlotValidationDataRepository


class YamlPlotValidationDataRepository(PlotValidationDataRepository):
    """YAMLファイルベースのプロット検証データリポジトリ実装."""

    def __init__(self, data_file_path: Path | str) -> None:
        """初期化.

        Args:
            data_file_path: プロット検証データファイルのパス
        """
        self.data_file_path = Path(data_file_path) if isinstance(data_file_path, str) else data_file_path
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_validation_data(self, plot_id: str, validation_data: dict[str, Any]) -> bool:
        """プロット検証データを保存.

        Args:
            plot_id: プロットID
            validation_data: 検証データ

        Returns:
            保存成功時True
        """
        try:
            # 既存データを読み込み
            all_data: dict[str, Any] = self._load_all_data()

            # プロット検証データを更新
            all_data[plot_id] = {**validation_data, "last_validated": datetime.now(timezone.utc).isoformat()}

            # ファイルに保存
            self._save_all_data(all_data)
            return True

        except Exception:
            return False

    def load_validation_data(self, plot_id: str) -> dict[str, Any] | None:
        """プロット検証データを読み込み.

        Args:
            plot_id: プロットID

        Returns:
            検証データ、見つからない場合はNone
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            return all_data.get(plot_id)

        except Exception:
            return None

    def list_plot_ids(self) -> list[str]:
        """検証対象プロットID一覧を取得.

        Returns:
            プロットIDのリスト
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            return sorted(all_data.keys())

        except Exception:
            return []

    def delete_validation_data(self, plot_id: str) -> bool:
        """プロット検証データを削除.

        Args:
            plot_id: プロットID

        Returns:
            削除成功時True
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()

            if plot_id in all_data:
                del all_data[plot_id]
                self._save_all_data(all_data)
                return True

            return False

        except Exception:
            return False

    def update_validation_status(self, plot_id: str, status: str) -> bool:
        """プロット検証ステータスを更新.

        Args:
            plot_id: プロットID
            status: 新しい検証ステータス

        Returns:
            更新成功時True
        """
        try:
            validation_data: dict[str, Any] = self.load_validation_data(plot_id)
            if validation_data is None:
                # 新規データとして作成
                validation_data: dict[str, Any] = {}

            validation_data["validation_status"] = status
            validation_data["status_updated_at"] = datetime.now(timezone.utc).isoformat()

            return self.save_validation_data(plot_id, validation_data)

        except Exception:
            return False

    def get_plots_by_validation_status(self, status: str) -> list[str]:
        """指定検証ステータスのプロット一覧を取得.

        Args:
            status: フィルタする検証ステータス

        Returns:
            マッチしたプロットIDのリスト
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            matched_ids = []

            for plot_id, data in all_data.items():
                if data.get("validation_status") == status:
                    matched_ids.append(plot_id)

            return sorted(matched_ids)

        except Exception:
            return []

    def add_validation_result(self, plot_id: str, validation_result: dict[str, Any]) -> bool:
        """検証結果を追加.

        Args:
            plot_id: プロットID
            validation_result: 検証結果

        Returns:
            追加成功時True
        """
        try:
            validation_data: dict[str, Any] = self.load_validation_data(plot_id)
            if validation_data is None:
                validation_data: dict[str, Any] = {}

            if "validation_results" not in validation_data:
                validation_data["validation_results"] = []

            result_entry = {**validation_result, "validated_at": datetime.now(timezone.utc).isoformat()}

            validation_data["validation_results"].append(result_entry)

            # 検証結果が多すぎる場合は古いものを削除(最新50件まで保持)
            if len(validation_data["validation_results"]) > 50:
                validation_data["validation_results"] = validation_data["validation_results"][-50:]

            return self.save_validation_data(plot_id, validation_data)

        except Exception:
            return False

    def get_validation_history(self, plot_id: str) -> list[dict[str, Any]]:
        """プロットの検証履歴を取得.

        Args:
            plot_id: プロットID

        Returns:
            検証履歴のリスト
        """
        try:
            validation_data: dict[str, Any] = self.load_validation_data(plot_id)
            if validation_data is None:
                return []

            return validation_data.get("validation_results", [])

        except Exception:
            return []

    def get_latest_validation_result(self, plot_id: str) -> dict[str, Any] | None:
        """最新の検証結果を取得.

        Args:
            plot_id: プロットID

        Returns:
            最新の検証結果、見つからない場合はNone
        """
        try:
            history = self.get_validation_history(plot_id)
            if history:
                return history[-1]  # 最新の結果
            return None

        except Exception:
            return None

    def update_validation_score(self, plot_id: str, score: float | int) -> bool:
        """プロット検証スコアを更新.

        Args:
            plot_id: プロットID
            score: 検証スコア

        Returns:
            更新成功時True
        """
        try:
            validation_data: dict[str, Any] = self.load_validation_data(plot_id)
            if validation_data is None:
                validation_data: dict[str, Any] = {}

            validation_data["validation_score"] = score
            validation_data["score_updated_at"] = datetime.now(timezone.utc).isoformat()

            return self.save_validation_data(plot_id, validation_data)

        except Exception:
            return False

    def get_validation_statistics(self) -> dict[str, Any]:
        """検証データの統計情報を取得.

        Returns:
            統計情報
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()

            # 検証ステータス別の統計
            status_counts = {}
            total_score = 0
            score_count = 0
            plot_count = len(all_data)

            for validation_data in all_data.values():
                status = validation_data.get("validation_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

                score = validation_data.get("validation_score")
                if isinstance(score, int | float):
                    total_score += score
                    score_count += 1

            return {
                "total_plots": plot_count,
                "average_score": total_score / score_count if score_count > 0 else 0,
                "status_distribution": status_counts,
                "validated_plots": score_count,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception:
            return {}

    def search_by_validation_criteria(self, criteria: dict[str, Any]) -> list[str]:
        """検証条件に基づいてプロットを検索.

        Args:
            criteria: 検索条件

        Returns:
            マッチしたプロットIDのリスト
        """
        try:
            all_data: dict[str, Any] = self._load_all_data()
            matched_ids = []

            for plot_id, validation_data in all_data.items():
                match = True

                # スコアの範囲チェック
                if "min_score" in criteria:
                    score = validation_data.get("validation_score", 0)
                    if score < criteria["min_score"]:
                        match = False

                if "max_score" in criteria:
                    score = validation_data.get("validation_score", 0)
                    if score > criteria["max_score"]:
                        match = False

                # ステータスチェック
                if "status" in criteria:
                    status = validation_data.get("validation_status", "")
                    if status != criteria["status"]:
                        match = False

                # 日付範囲チェック
                if "validated_after" in criteria:
                    last_validated = validation_data.get("last_validated", "")
                    if last_validated < criteria["validated_after"]:
                        match = False

                if match:
                    matched_ids.append(plot_id)

            return sorted(matched_ids)

        except Exception:
            return []

    def _load_all_data(self) -> dict[str, dict[str, Any]]:
        """全データを読み込み.

        Returns:
            全プロット検証データ
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
