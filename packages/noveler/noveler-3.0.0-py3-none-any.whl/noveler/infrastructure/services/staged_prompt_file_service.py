"""
段階的プロンプトファイル管理サービス

A24ワークフローガイドに従った段階別ファイル保存・管理機能
- 保存先: $PROJECT_ROOT/20_プロット/
- ファイル名: 第XXX話_stageX.yaml / 第XXX話_完成版.yaml
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.staged_prompt import StagedPrompt
from noveler.domain.value_objects.prompt_stage import PromptStage
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class StagedPromptFileService:
    """段階的プロンプトファイル管理サービス

    A24段階的ワークフローに従って、段階別のプロンプトファイルを
    適切なディレクトリに保存・管理する。
    """

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """サービス初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = project_root
        self._path_service = create_path_service(project_root)

        # プロットディレクトリの確保
        self._plot_directory = self._path_service.get_common_path_service(project_root).get_plot_dir()
        self._plot_directory.mkdir(exist_ok=True)

        self.logger_service = logger_service
        self.console_service = console_service
    def save_staged_prompt(
        self,
        staged_prompt: StagedPrompt,
        generated_prompt: str,
        stage_content: dict[str, Any],
        episode_title: str | None = None,
    ) -> Path:
        """段階的プロンプトをファイルに保存

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            generated_prompt: 生成されたプロンプト文字列
            stage_content: 段階固有コンテンツ
            episode_title: エピソードタイトル（省略時は仮タイトル）

        Returns:
            保存されたファイルのパス
        """
        # ファイル名の決定
        filename = self._generate_filename(staged_prompt.episode_number, staged_prompt.current_stage, episode_title)

        file_path = self._plot_directory / filename

        # 保存データの構築
        save_data: dict[str, Any] = self._build_save_data(staged_prompt, generated_prompt, stage_content)

        # YAML形式で保存
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

            return file_path

        except Exception as e:
            msg = f"Failed to save staged prompt file: {e!s}"
            raise OSError(msg)

    def load_staged_prompt_file(self, episode_number: int, stage: PromptStage) -> dict[str, Any] | None:
        """段階的プロンプトファイルの読み込み

        Args:
            episode_number: エピソード番号
            stage: 対象段階

        Returns:
            読み込まれたデータ（存在しない場合None）
        """
        # ファイル名パターンの生成
        filename_patterns = [
            self._generate_filename(episode_number, stage, None),
            f"第{episode_number:03d}話_stage{stage.stage_number}.yaml",
            f"第{episode_number:03d}話_完成版.yaml" if stage.stage_number == 5 else None,
        ]

        for pattern in filename_patterns:
            if pattern is None:
                continue

            file_path = self._plot_directory / pattern
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        return yaml.safe_load(f)
                except Exception as e:
                    self.console_service.print(f"Warning: Failed to load {file_path}: {e}")
                    continue

        return None

    def list_staged_prompt_files(self, episode_number: int | None = None) -> dict[str, Any]:
        """段階的プロンプトファイル一覧取得

        Args:
            episode_number: 特定エピソード番号（省略時は全エピソード）

        Returns:
            ファイル一覧辞書
        """
        files_info = {"episodes": {}, "total_files": 0, "scan_time": datetime.now(timezone.utc).isoformat()}

        # パターンマッチングでファイルを検索
        pattern = "第*話_*.yaml" if episode_number is None else f"第{episode_number:03d}話_*.yaml"

        for file_path in self._plot_directory.glob(pattern):
            file_info = self._analyze_staged_prompt_file(file_path)
            if file_info:
                ep_num = file_info["episode_number"]
                if ep_num not in files_info["episodes"]:
                    files_info["episodes"][ep_num] = []

                files_info["episodes"][ep_num].append(file_info)
                files_info["total_files"] += 1

        return files_info

    def cleanup_intermediate_files(self, episode_number: int, keep_completed: bool = True) -> int:
        """中間ファイルのクリーンアップ

        Args:
            episode_number: 対象エピソード番号
            keep_completed: 完成版ファイルを保持するかどうか

        Returns:
            削除されたファイル数
        """
        deleted_count = 0

        # 削除対象パターン
        if keep_completed:
            # stage1-4のみ削除、完成版は保持
            patterns = [f"第{episode_number:03d}話_stage{i}.yaml" for i in range(1, 5)]
        else:
            # 全段階ファイルを削除
            patterns = [f"第{episode_number:03d}話_*.yaml"]

        for pattern in patterns:
            for file_path in self._plot_directory.glob(pattern):
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.console_service.print(f"Warning: Failed to delete {file_path}: {e}")

        return deleted_count

    def backup_staged_prompts(self, episode_number: int) -> Path:
        """段階的プロンプトのバックアップ作成

        Args:
            episode_number: 対象エピソード番号

        Returns:
            バックアップディレクトリパス
        """
        # バックアップディレクトリの作成
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = self._plot_directory / "backup" / f"第{episode_number:03d}話_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 対象ファイルのコピー
        copied_count = 0
        for file_path in self._plot_directory.glob(f"第{episode_number:03d}話_*.yaml"):
            if "backup" not in str(file_path):  # バックアップディレクトリ内のファイルは除外:
                try:
                    backup_file = backup_dir / file_path.name
                    backup_file.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
                    copied_count += 1
                except Exception as e:
                    self.console_service.print(f"Warning: Failed to backup {file_path}: {e}")

        # バックアップメタデータの保存
        metadata = {
            "episode_number": episode_number,
            "backup_time": timestamp,
            "copied_files": copied_count,
            "source_directory": str(self._plot_directory),
        }

        metadata_file = backup_dir / "backup_info.yaml"
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.dump(metadata, f, allow_unicode=True)

        return backup_dir

    def _generate_filename(self, episode_number: int, stage: PromptStage, episode_title: str | None) -> str:
        """ファイル名生成

        Args:
            episode_number: エピソード番号
            stage: 段階
            episode_title: エピソードタイトル

        Returns:
            生成されたファイル名
        """
        if stage.stage_number == 5:
            # Stage 5は完成版
            return f"第{episode_number:03d}話_完成版.yaml"
        # Stage 1-4は段階別
        return f"第{episode_number:03d}話_stage{stage.stage_number}.yaml"

    def _build_save_data(
        self, staged_prompt: StagedPrompt, generated_prompt: str, stage_content: dict[str, Any]
    ) -> dict[str, Any]:
        """保存データの構築

        Args:
            staged_prompt: 段階的プロンプトエンティティ
            generated_prompt: 生成されたプロンプト
            stage_content: 段階コンテンツ

        Returns:
            保存用データ辞書
        """
        return {
            # メタデータ
            "metadata": {
                "episode_number": staged_prompt.episode_number,
                "project_name": staged_prompt.project_name,
                "current_stage": staged_prompt.current_stage.stage_number,
                "stage_name": staged_prompt.current_stage.stage_name,
                "created_at": staged_prompt.created_at.isoformat(),
                "updated_at": staged_prompt.updated_at.isoformat(),
                "quality_score": staged_prompt.get_stage_quality_score(staged_prompt.current_stage),
                "execution_time_minutes": staged_prompt.get_stage_execution_time(staged_prompt.current_stage),
            },
            # 生成されたプロンプト
            "generated_prompt": generated_prompt,
            # 段階固有コンテンツ
            "stage_content": stage_content,
            # 段階進行情報
            "stage_progress": {
                "current_stage": staged_prompt.current_stage.stage_number,
                "completed_stages": [s.stage_number for s in staged_prompt.completed_stages],
                "completion_percentage": staged_prompt.get_completion_percentage(),
                "is_fully_completed": staged_prompt.is_fully_completed(),
            },
            # 段階別結果履歴（完成版の場合のみ）
            "stage_history": {
                f"stage_{stage.stage_number}": {
                    "result": staged_prompt.get_stage_result(stage),
                    "quality_score": staged_prompt.get_stage_quality_score(stage),
                    "execution_time": staged_prompt.get_stage_execution_time(stage),
                }
                for stage in staged_prompt.completed_stages
            }
            if staged_prompt.current_stage.stage_number == 5
            else {},
        }

    def _analyze_staged_prompt_file(self, file_path: Path) -> dict[str, Any] | None:
        """段階的プロンプトファイルの解析

        Args:
            file_path: 解析対象ファイルパス

        Returns:
            ファイル情報辞書（解析失敗時None）
        """
        try:
            # ファイル名から基本情報を抽出
            filename = file_path.name

            # 正規表現でエピソード番号と段階を抽出

            # 第XXX話_stageX.yaml または 第XXX話_完成版.yaml のパターン
            stage_match = re.match(r"第(\d+)話_stage(\d+)\.yaml", filename)
            complete_match = re.match(r"第(\d+)話_完成版\.yaml", filename)

            if stage_match:
                episode_num = int(stage_match.group(1))
                stage_num = int(stage_match.group(2))
                stage_type = "intermediate"
            elif complete_match:
                episode_num = int(complete_match.group(1))
                stage_num = 5
                stage_type = "completed"
            else:
                return None

            # ファイル統計
            stat = file_path.stat()

            return {
                "episode_number": episode_num,
                "stage_number": stage_num,
                "stage_type": stage_type,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }

        except Exception as e:
            self.console_service.print(f"Warning: Failed to analyze file {file_path}: {e}")
            return None

    def get_plot_directory(self) -> Path:
        """プロットディレクトリパス取得

        Returns:
            プロットディレクトリパス
        """
        return self._plot_directory
