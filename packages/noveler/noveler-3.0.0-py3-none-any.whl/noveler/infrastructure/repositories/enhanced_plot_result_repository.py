"""Infrastructure.repositories.enhanced_plot_result_repository
Where: Infrastructure repository persisting enhanced plot results.
What: Saves and retrieves augmented plot generation outputs to disk.
Why: Enables reuse of enhanced plot results across application workflows.
"""

from __future__ import annotations

"""Enhanced Plot Result Repository

SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2
コンテキスト駆動プロット生成結果の永続化リポジトリ
"""

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import yaml

from noveler.domain.entities.contextual_plot_generation import ContextualPlotResult, QualityIndicators
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.services.chapter_structure_service import get_chapter_structure_service
from noveler.infrastructure.utils.yaml_utils import get_unified_yaml_service

if TYPE_CHECKING:
    from pathlib import Path


class EnhancedPlotResultRepository:
    """拡張プロット結果リポジトリ

    SPEC-PLOT-004準拠のコンテキスト駆動プロット生成結果を
    YAMLファイルとして永続化・取得するリポジトリ実装。
    CommonPathService統合により、設定可能なパス管理を実現。
    """

    def __init__(self, project_root: Path | None = None, logger_service=None, console_service=None) -> None:
        """リポジトリ初期化

        Args:
            project_root: プロジェクトルートパス(省略時は自動検出)
        """
        self._path_service = create_path_service(project_root)
        self._history_dir_name = "generation_history"

        self.logger_service = logger_service
        self.console_service = console_service
    def set_project_root(self, project_root: Path) -> None:
        """プロジェクトルートパスの設定

        Args:
            project_root: プロジェクトルートパス
        """
        self._path_service = create_path_service(project_root)

    def save_result(self, result: ContextualPlotResult) -> None:
        """生成結果の保存

        Args:
            result: 保存する生成結果

        Raises:
            IOError: ファイル書き込みエラー
        """
        # 保存ディレクトリの確保
        results_dir = self._get_results_directory()
        results_dir.mkdir(parents=True, exist_ok=True)

        history_dir = self._get_history_directory()
        history_dir.mkdir(parents=True, exist_ok=True)

        # メイン結果ファイルの保存（タイトル付きファイル名）
        main_file_path = self._get_main_result_file_path_with_title(result)
        self._save_yaml_file(main_file_path, result.to_dict())

        # 履歴ファイルの保存
        history_file_path = self._get_history_file_path(result)
        self._save_yaml_file(history_file_path, result.to_dict())

        self.console_service.print(f"Enhanced plot result saved: {main_file_path}")

    def get_result(self, episode_number: EpisodeNumber) -> ContextualPlotResult | None:
        """指定エピソードの最新生成結果取得

        Args:
            episode_number: エピソード番号

        Returns:
            Optional[ContextualPlotResult]: 生成結果(存在しない場合はNone)
        """
        # まず、新しい命名規則のファイルを検索
        results_dir = self._get_results_directory()
        pattern = f"第{episode_number.value:03d}話_*.yaml"
        matching_files = list(results_dir.glob(pattern))

        if matching_files:
            # 最新のファイルを選択（複数ある場合）
            latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
            main_file_path = latest_file
        else:
            # 旧い命名規則（後方互換性）
            main_file_path = self._get_main_result_file_path(episode_number)

        if not main_file_path.exists():
            return None

        try:
            data = self._load_yaml_file(main_file_path)
            return self._dict_to_result(data)
        except Exception as e:
            self.console_service.print(f"Failed to load result for episode {episode_number.value}: {e}")
            return None

    def get_generation_history(self, episode_number: int | None = None, limit: int = 10) -> list[ContextualPlotResult]:
        """生成履歴の取得

        Args:
            episode_number: 特定エピソード番号(省略時は全エピソード)
            limit: 取得件数制限

        Returns:
            list[ContextualPlotResult]: 生成履歴リスト(新しい順)
        """
        history_dir = self._get_history_directory()
        if not history_dir.exists():
            return []

        # 履歴ファイルの検索
        pattern = f"*episode_{episode_number:03d}_*.yaml" if episode_number else "*episode_*_*.yaml"
        history_files = sorted(history_dir.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)

        results: list[Any] = []
        for file_path in history_files[:limit]:
            try:
                data = self._load_yaml_file(file_path)
                result = self._dict_to_result(data)
                results.append(result)
            except Exception as e:
                self.console_service.print(f"Failed to load history file {file_path}: {e}")
                continue

        return results

    def delete_result(self, episode_number: EpisodeNumber) -> bool:
        """指定エピソードの結果削除

        Args:
            episode_number: エピソード番号

        Returns:
            bool: 削除成功の場合True
        """
        deleted_any = False
        results_dir = self._get_results_directory()

        # 新しい命名規則のファイルを検索・削除
        pattern = f"第{episode_number.value:03d}話_*.yaml"
        for file_path in results_dir.glob(pattern):
            try:
                file_path.unlink()
                self.console_service.print(f"Deleted result file: {file_path}")
                deleted_any = True
            except Exception as e:
                self.console_service.print(f"Failed to delete file {file_path}: {e}")

        # 旧い命名規則のファイルも削除（後方互換性）
        old_file_path = self._get_main_result_file_path(episode_number)
        if old_file_path.exists():
            try:
                old_file_path.unlink()
                self.console_service.print(f"Deleted old format result file: {old_file_path}")
                deleted_any = True
            except Exception as e:
                self.console_service.print(f"Failed to delete old format file {old_file_path}: {e}")

        return deleted_any

    def list_available_episodes(self) -> list[int]:
        """利用可能なエピソード番号のリスト取得

        Returns:
            list[int]: 結果が保存されているエピソード番号のリスト
        """
        results_dir = self._get_results_directory()
        if not results_dir.exists():
            return []

        episodes = []
        for file_path in results_dir.glob("第*話_*.yaml"):
            try:
                # ファイル名からエピソード番号を抽出
                filename = file_path.stem
                if filename.startswith("第") and "話" in filename:
                    episode_part = filename.split("話")[0].replace("第", "")
                    episode_num = int(episode_part)
                    episodes.append(episode_num)
            except (ValueError, IndexError):
                continue

        return sorted(episodes)

    def _get_results_directory(self) -> Path:
        """結果保存ディレクトリの取得（CommonPathService統合）

        Returns:
            Path: 結果保存ディレクトリパス
        """
        return self._path_service.get_plot_dir() / "話別プロット"

    def _get_history_directory(self) -> Path:
        """履歴保存ディレクトリの取得

        Returns:
            Path: 履歴保存ディレクトリパス
        """
        return self._get_results_directory() / self._history_dir_name

    def _get_main_result_file_path(self, episode_number: EpisodeNumber) -> Path:
        """メイン結果ファイルパスの取得（旧形式・後方互換性）

        Args:
            episode_number: エピソード番号

        Returns:
            Path: メイン結果ファイルパス
        """
        filename = f"第{episode_number.value:03d}話_Enhanced_Plot.yaml"
        return self._get_results_directory() / filename

    def _get_main_result_file_path_with_title(self, result: ContextualPlotResult) -> Path:
        """タイトル付きメイン結果ファイルパスの取得

        Args:
            result: 生成結果

        Returns:
            Path: タイトル付きメイン結果ファイルパス
        """
        # メタデータまたはコンテンツからタイトルを抽出
        title = self._extract_title_from_result(result)
        filename = f"第{result.episode_number.value:03d}話_{title}.yaml"
        return self._get_results_directory() / filename

    def _extract_title_from_result(self, result: ContextualPlotResult) -> str:
        """結果からタイトルを抽出

        Args:
            result: 生成結果

        Returns:
            str: 抽出されたタイトル（デフォルトは"Enhanced_Plot"）
        """
        # 1. 章別プロットからタイトルを取得（最優先）
        chapter_title = self._get_title_from_chapter_plot(result.episode_number)
        if chapter_title:
            return self._sanitize_filename(chapter_title)

        # 2. メタデータからタイトルを検索
        if "title" in result.metadata:
            title = result.metadata["title"]
            # ファイル名に使えない文字を置換
            return self._sanitize_filename(title)

        # 3. コンテンツからタイトルを抽出（YAML形式を想定）
        try:
            content_data: dict[str, Any] = yaml.safe_load(result.content)
            if isinstance(content_data, dict):
                # episode_info > title を優先
                if "episode_info" in content_data and "title" in content_data["episode_info"]:
                    title = content_data["episode_info"]["title"]
                    return self._sanitize_filename(title)
                # 直接title
                if "title" in content_data:
                    title = content_data["title"]
                    return self._sanitize_filename(title)
        except Exception:
            pass

        # フォールバック
        return "Enhanced_Plot"

    def _get_title_from_chapter_plot(self, episode_number: EpisodeNumber) -> str | None:
        """章別プロットからエピソードタイトルを取得

        Args:
            episode_number: エピソード番号

        Returns:
            str | None: タイトル（見つからない場合はNone）
        """
        try:
            # 全体構成.yamlから正確な章情報を取得

            chapter_service = get_chapter_structure_service(self._path_service.project_root)
            chapter_info = chapter_service.get_chapter_by_episode(episode_number)

            if not chapter_info:
                self.console_service.print(f"エピソード{episode_number.value}の章情報が見つかりません")
                return None

            # 章別プロットディレクトリから該当ファイルを検索
            chapter_plot_dir = self._path_service.get_plot_dir() / "章別プロット"
            if not chapter_plot_dir.exists():
                return None

            # 章別プロットファイルを検索（第X章_*.yamlパターン）
            pattern = f"第{chapter_info.chapter_number}章_*.yaml"
            chapter_files = list(chapter_plot_dir.glob(pattern))

            if not chapter_files:
                self.console_service.print(f"第{chapter_info.chapter_number}章の章別プロットファイルが見つかりません")
                return None

            # 最初に見つかった章別プロットファイルを使用
            chapter_file = chapter_files[0]

            # YAMLファイルを読み込み
            with open(chapter_file, encoding="utf-8") as f:
                chapter_data: dict[str, Any] = yaml.safe_load(f)

            if not isinstance(chapter_data, dict):
                return None

            # episodesセクションからタイトルを検索
            episodes = chapter_data.get("episodes", [])
            if not isinstance(episodes, list):
                return None

            for episode in episodes:
                if isinstance(episode, dict) and episode.get("episode_number") == episode_number.value:
                    return episode.get("title")

            return None

        except Exception as e:
            self.console_service.print(f"章別プロットからのタイトル取得に失敗: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名の無効文字をサニタイズ

        Args:
            filename: 元のファイル名

        Returns:
            str: サニタイズされたファイル名
        """

        # 無効文字を置換
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
        # 連続するアンダースコアを単一に
        sanitized = re.sub(r"_{2,}", "_", sanitized)
        # 先頭と末尾のアンダースコアを削除
        sanitized = sanitized.strip("_")
        return sanitized if sanitized else "Enhanced_Plot"

    def _get_history_file_path(self, result: ContextualPlotResult) -> Path:
        """履歴ファイルパスの取得

        Args:
            result: 生成結果

        Returns:
            Path: 履歴ファイルパス
        """
        timestamp = result.generation_timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"episode_{result.episode_number.value:03d}_{timestamp}.yaml"
        return self._get_history_directory() / filename

    def _save_yaml_file(self, file_path: Path, data: dict[str, Any]) -> None:
        """YAMLファイルの保存（統合YAMLサービス使用）

        Args:
            file_path: 保存先ファイルパス
            data: 保存するデータ

        Raises:
            IOError: ファイル書き込みエラー
        """
        try:
            # 統合YAMLサービスを使用した保存

            service = get_unified_yaml_service(enable_validation=True, enable_backup=False)
            success, messages = service.generate_with_validation(
                data=data,
                output_path=file_path,
                format_type="formatted",  # enhanced_plot_resultは整形版を使用
            )

            if not success:
                error_details = "; ".join(messages)
                msg = f"統合YAML生成失敗 {file_path}: {error_details}"
                raise OSError(msg)

        except Exception as e:
            msg = f"Failed to save YAML file {file_path}: {e}"
            raise OSError(msg) from e

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """YAMLファイルの読み込み

        Args:
            file_path: 読み込み対象ファイルパス

        Returns:
            Dict[str, Any]: 読み込まれたデータ

        Raises:
            IOError: ファイル読み込みエラー
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"Failed to load YAML file {file_path}: {e}"
            raise OSError(msg) from e

    def _dict_to_result(self, data: dict[str, Any]) -> ContextualPlotResult:
        """辞書データから生成結果オブジェクトへの変換

        Args:
            data: 辞書データ

        Returns:
            ContextualPlotResult: 生成結果オブジェクト
        """

        # 品質指標の復元
        quality_data: dict[str, Any] = data.get("quality_indicators", {})
        quality_indicators = QualityIndicators(
            technical_accuracy=quality_data.get("technical_accuracy", 0.0),
            character_consistency=quality_data.get("character_consistency", 0.0),
            plot_coherence=quality_data.get("plot_coherence", 0.0),
            overall_score=quality_data.get("overall_score"),
        )

        # 生成タイムスタンプの復元
        timestamp_str = data.get("generation_timestamp", "")
        generation_timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(timezone.utc)

        return ContextualPlotResult(
            episode_number=EpisodeNumber(data.get("episode_number", 1)),
            content=data.get("content", ""),
            quality_indicators=quality_indicators,
            generation_timestamp=generation_timestamp,
            metadata=data.get("metadata", {}),
        )

    def get_statistics(self) -> dict[str, Any]:
        """生成結果の統計情報取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        available_episodes = self.list_available_episodes()
        total_count = len(available_episodes)

        if total_count == 0:
            return {"total_episodes": 0, "average_quality": 0.0, "quality_distribution": {}, "recent_activity": []}

        # 品質統計の計算
        quality_scores = []
        quality_distribution = {"A": 0, "B": 0, "C": 0, "D": 0}

        for episode_num in available_episodes:
            result = self.get_result(EpisodeNumber(episode_num))
            if result and result.quality_indicators.overall_score:
                score = result.quality_indicators.overall_score
                quality_scores.append(score)

                # グレード分類
                if score >= 90.0:
                    quality_distribution["A"] += 1
                elif score >= 80.0:
                    quality_distribution["B"] += 1
                elif score >= 70.0:
                    quality_distribution["C"] += 1
                else:
                    quality_distribution["D"] += 1

        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        # 最近のアクティビティ
        recent_history = self.get_generation_history(limit=5)
        recent_activity = [
            {
                "episode_number": result.episode_number.value,
                "timestamp": result.generation_timestamp.isoformat(),
                "quality_score": result.quality_indicators.overall_score,
            }
            for result in recent_history
        ]

        return {
            "total_episodes": total_count,
            "average_quality": round(average_quality, 2),
            "quality_distribution": quality_distribution,
            "recent_activity": recent_activity,
            "available_episodes": available_episodes,
        }
