"""
品質チェックプロンプトリポジトリの実装

SPEC-STAGE5-SEPARATION対応
品質チェックプロンプトの永続化・取得機能
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.quality_check_prompt import QualityCheckPrompt, QualityCheckPromptId, QualityCheckResult
from noveler.domain.value_objects.quality_check_level import QualityCheckRequest, QualityCriterion


class QualityCheckPromptRepository(ABC):
    """品質チェックプロンプトリポジトリインターフェース"""

    @abstractmethod
    def save(self, prompt: QualityCheckPrompt) -> None:
        """プロンプトを保存"""

    @abstractmethod
    def find_by_id(self, prompt_id: QualityCheckPromptId) -> QualityCheckPrompt | None:
        """ID検索"""

    @abstractmethod
    def find_by_episode(self, project_name: str, episode_number: int) -> list[QualityCheckPrompt]:
        """エピソード別検索"""

    @abstractmethod
    def delete(self, prompt_id: QualityCheckPromptId) -> bool:
        """プロンプト削除"""


class FileSystemQualityCheckPromptRepository(QualityCheckPromptRepository):
    """ファイルシステムベース品質チェックプロンプトリポジトリ"""

    def __init__(self, storage_directory: Path, common_path_service=None, logger_service=None, console_service=None) -> None:
        """リポジトリの初期化

        Args:
            storage_directory: プロンプト保存ディレクトリ（後方互換用）
            common_path_service: 共通パスサービス（優先使用）
        """
        # CommonPathServiceが提供されている場合は優先使用
        if common_path_service:
            self._storage_directory = common_path_service.get_episode_prompts_dir()
            self._common_path_service = common_path_service
        else:
            # フォールバック: 従来の方式
            self._storage_directory = storage_directory
            self._common_path_service = None

        self._storage_directory.mkdir(parents=True, exist_ok=True)

        # メタデータファイルのパス
        self._metadata_file = self._storage_directory / "prompt_metadata.json"
        self._metadata_cache: dict[str, dict[str, Any]] = {}
        self._load_metadata()

        self.logger_service = logger_service
        self.console_service = console_service
    def save(self, prompt: QualityCheckPrompt) -> None:
        """プロンプトを保存"""
        prompt_data: dict[str, Any] = self._serialize_prompt(prompt)

        # プロンプトファイルの保存
        prompt_file = self._get_prompt_file_path(prompt.prompt_id, prompt)
        with prompt_file.open("w", encoding="utf-8") as f:
            yaml.dump(prompt_data, f, default_flow_style=False, indent=2, allow_unicode=True)

        # メタデータの更新
        self._update_metadata(prompt)

        # キャッシュ更新
        self._metadata_cache[str(prompt.prompt_id)] = self._create_metadata_entry(prompt)

    def find_by_id(self, prompt_id: QualityCheckPromptId) -> QualityCheckPrompt | None:
        """ID検索"""
        prompt_file = self._get_prompt_file_path(prompt_id)

        if not prompt_file.exists():
            return None

        try:
            with prompt_file.open(encoding="utf-8") as f:
                prompt_data: dict[str, Any] = yaml.safe_load(f)

            return self._deserialize_prompt(prompt_data)

        except Exception as e:
            self.console_service.print(f"Error loading prompt {prompt_id}: {e}")
            return None

    def find_by_episode(self, project_name: str, episode_number: int) -> list[QualityCheckPrompt]:
        """エピソード別検索"""
        matching_prompts = []

        # 新しいファイル検索方式を使用
        prompt_files = self._find_episode_prompt_files(project_name, episode_number)

        for prompt_file in prompt_files:
            try:
                with prompt_file.open(encoding="utf-8") as f:
                    prompt_data: dict[str, Any] = yaml.safe_load(f)

                # プロンプトデータからプロンプトオブジェクトを復元
                prompt = self._deserialize_prompt(prompt_data)
                if prompt and prompt.request:
                    # プロジェクト名とエピソード番号が一致するかチェック
                    if prompt.request.project_name == project_name and prompt.request.episode_number == episode_number:
                        matching_prompts.append(prompt)

            except Exception as e:
                self.console_service.print(f"Error loading prompt from {prompt_file}: {e}")
                continue

        # 従来のメタデータベース検索もフォールバックとして実行
        for prompt_id_str, metadata in self._metadata_cache.items():
            if metadata.get("project_name") == project_name and metadata.get("episode_number") == episode_number:
                # 既にファイルベースで読み込み済みかチェック
                already_loaded = any(str(p.prompt_id) == prompt_id_str for p in matching_prompts)

                if not already_loaded:
                    prompt_id = QualityCheckPromptId(prompt_id_str)
                    prompt = self.find_by_id(prompt_id)
                    if prompt:
                        matching_prompts.append(prompt)

        # 作成日時順でソート（新しいものから）
        matching_prompts.sort(key=lambda p: p.creation_timestamp, reverse=True)

        return matching_prompts

    def delete(self, prompt_id: QualityCheckPromptId) -> bool:
        """プロンプト削除"""
        prompt_file = self._get_prompt_file_path(prompt_id)

        if not prompt_file.exists():
            return False

        try:
            # ファイル削除
            prompt_file.unlink()

            # メタデータから削除
            prompt_id_str = str(prompt_id)
            if prompt_id_str in self._metadata_cache:
                del self._metadata_cache[prompt_id_str]

            self._save_metadata()
            return True

        except Exception as e:
            self.console_service.print(f"Error deleting prompt {prompt_id}: {e}")
            return False

    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得"""
        total_count = len(self._metadata_cache)

        # レベル別統計
        level_counts = {}
        project_counts = {}

        for metadata in self._metadata_cache.values():
            level = metadata.get("check_level", "unknown")
            project = metadata.get("project_name", "unknown")

            level_counts[level] = level_counts.get(level, 0) + 1
            project_counts[project] = project_counts.get(project, 0) + 1

        return {
            "total_prompts": total_count,
            "level_distribution": level_counts,
            "project_distribution": project_counts,
            "storage_path": str(self._storage_directory),
        }

    def _get_prompt_file_path(self, prompt_id: QualityCheckPromptId, prompt: "QualityCheckPrompt" = None) -> Path:
        """プロンプトファイルパスを取得"""
        # 新しい命名規則を試行: 第000話_{タイトル}.yaml形式
        if self._common_path_service:
            episode_number = None

            # プロンプトオブジェクトから直接取得を試行
            if prompt and prompt.request:
                episode_number = prompt.request.episode_number
            else:
                # メタデータキャッシュから取得を試行
                prompt_id_str = str(prompt_id)
                if prompt_id_str in self._metadata_cache:
                    metadata = self._metadata_cache[prompt_id_str]
                    episode_number = metadata.get("episode_number")

            if episode_number:
                # エピソードタイトルを取得
                episode_title = self._common_path_service.get_episode_title(episode_number)
                return self._common_path_service.get_quality_prompt_file_path(episode_number, episode_title)

        # フォールバック: 従来のUUIDベース命名
        return self._storage_directory / f"prompt_{prompt_id.value}.yaml"

    def _find_episode_prompt_files(self, project_name: str, episode_number: int) -> list[Path]:
        """エピソード用プロンプトファイルを検索

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            見つかったプロンプトファイルのパス一覧
        """
        found_files = []

        # 新しい命名規則でのファイル検索: 第000話_*.yaml
        if self._common_path_service:
            import glob

            pattern = str(self._storage_directory / f"第{episode_number:03d}話_*.yaml")
            episode_files = glob.glob(pattern)
            found_files.extend([Path(f) for f in episode_files])

            # タイトルなしパターンも検索: 第000話.yaml
            pattern_no_title = str(self._storage_directory / f"第{episode_number:03d}話.yaml")
            if Path(pattern_no_title).exists():
                found_files.append(Path(pattern_no_title))

        # 従来の UUID ベースファイルをメタデータから検索
        matching_files = []
        for prompt_id_str, metadata in self._metadata_cache.items():
            if metadata.get("project_name") == project_name and metadata.get("episode_number") == episode_number:
                uuid_file = self._storage_directory / f"prompt_{prompt_id_str}.yaml"
                if uuid_file.exists():
                    matching_files.append(uuid_file)

        found_files.extend(matching_files)

        # 重複除去
        return list(set(found_files))

    def _serialize_prompt(self, prompt: QualityCheckPrompt) -> dict[str, Any]:
        """プロンプトをシリアライズ"""
        data = {
            "prompt_id": str(prompt.prompt_id),
            "creation_timestamp": prompt.creation_timestamp.isoformat(),
            "last_updated": prompt.last_updated.isoformat(),
        }

        # 要求情報
        if prompt.request:
            data["request"] = {
                "episode_number": prompt.request.episode_number,
                "project_name": prompt.request.project_name,
                "plot_file_path": prompt.request.plot_file_path,
                "check_level": prompt.request.check_level.value,
            }

        # チェック基準
        if prompt.check_criteria:
            data["check_criteria"] = [
                {
                    "criterion_id": criterion.criterion_id,
                    "name": criterion.name,
                    "description": criterion.description,
                    "weight": criterion.weight,
                    "check_method": criterion.check_method,
                }
                for criterion in prompt.check_criteria
            ]

        # 生成されたプロンプト
        if prompt.generated_prompt:
            data["generated_prompt"] = prompt.generated_prompt

        # チェック結果
        if prompt.check_result:
            data["check_result"] = {
                "overall_score": prompt.check_result.overall_score,
                "criterion_scores": prompt.check_result.criterion_scores,
                "passed_criteria": prompt.check_result.passed_criteria,
                "failed_criteria": prompt.check_result.failed_criteria,
                "recommendations": prompt.check_result.recommendations,
                "check_timestamp": prompt.check_result.check_timestamp.isoformat(),
            }

        return data

    def _deserialize_prompt(self, data: dict[str, Any]) -> QualityCheckPrompt:
        """プロンプトをデシリアライズ"""
        from noveler.domain.value_objects.quality_check_level import QualityCheckLevel

        # 基本情報
        prompt_id = QualityCheckPromptId(data["prompt_id"])
        prompt = QualityCheckPrompt(prompt_id=prompt_id)

        # 要求情報の復元
        if "request" in data:
            request_data: dict[str, Any] = data["request"]
            request = QualityCheckRequest(
                episode_number=request_data["episode_number"],
                project_name=request_data["project_name"],
                plot_file_path=request_data["plot_file_path"],
                check_level=QualityCheckLevel(request_data["check_level"]),
            )

            prompt.set_request(request)

        # チェック基準の復元
        if "check_criteria" in data:
            criteria = [
                QualityCriterion(
                    criterion_id=c["criterion_id"],
                    name=c["name"],
                    description=c["description"],
                    weight=c["weight"],
                    check_method=c["check_method"],
                )
                for c in data["check_criteria"]
            ]
            prompt.set_check_criteria(criteria)

        # 生成プロンプトの復元
        if "generated_prompt" in data:
            # 直接設定（通常はgenerate_promptメソッドを使用）
            prompt._generated_prompt = data["generated_prompt"]

        # チェック結果の復元
        if "check_result" in data:
            result_data: dict[str, Any] = data["check_result"]
            result = QualityCheckResult(
                overall_score=result_data["overall_score"],
                criterion_scores=result_data["criterion_scores"],
                passed_criteria=result_data["passed_criteria"],
                failed_criteria=result_data["failed_criteria"],
                recommendations=result_data["recommendations"],
                check_timestamp=datetime.fromisoformat(result_data["check_timestamp"]),
            )

            prompt.set_check_result(result)

        return prompt

    def _load_metadata(self) -> None:
        """メタデータを読み込み"""
        if not self._metadata_file.exists():
            self._metadata_cache = {}
            return

        try:
            with self._metadata_file.open(encoding="utf-8") as f:
                self._metadata_cache = json.load(f)
        except Exception as e:
            self.console_service.print(f"Error loading metadata: {e}")
            self._metadata_cache = {}

    def _save_metadata(self) -> None:
        """メタデータを保存"""
        try:
            with self._metadata_file.open("w", encoding="utf-8") as f:
                json.dump(self._metadata_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.console_service.print(f"Error saving metadata: {e}")

    def _update_metadata(self, prompt: QualityCheckPrompt) -> None:
        """メタデータを更新"""
        metadata_entry = self._create_metadata_entry(prompt)
        self._metadata_cache[str(prompt.prompt_id)] = metadata_entry
        self._save_metadata()

    def _create_metadata_entry(self, prompt: QualityCheckPrompt) -> dict[str, Any]:
        """メタデータエントリを作成"""
        entry = {
            "creation_timestamp": prompt.creation_timestamp.isoformat(),
            "last_updated": prompt.last_updated.isoformat(),
            "has_generated_prompt": prompt.generated_prompt is not None,
            "has_result": prompt.check_result is not None,
        }

        if prompt.request:
            entry.update(
                {
                    "episode_number": prompt.request.episode_number,
                    "project_name": prompt.request.project_name,
                    "check_level": prompt.request.check_level.value,
                }
            )

        if prompt.check_result:
            entry["overall_score"] = prompt.check_result.overall_score

        return entry
