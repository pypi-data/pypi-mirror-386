"""
シーン管理リポジトリのYAML実装

TDD GREEN フェーズ: テストを通すための実装
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.scene_management_entities import (
    SceneCategory,
    SceneInfo,
    ValidationIssue,
)
from noveler.domain.repositories.scene_management_repository import SceneManagementRepository


class YamlSceneManagementRepository(SceneManagementRepository):
    """YAMLベースのシーン管理リポジトリ実装"""

    def __init__(self, logger_service=None, console_service=None) -> None:
        """初期化"""
        self.scene_file_name = "重要シーン.yaml"

        self.logger_service = logger_service
        self.console_service = console_service
    def initialize_scene_file(self, project_path: Path | str) -> bool:
        """シーンファイルを初期化"""
        try:
            scene_file = self.get_scene_file_path(project_path)

            # テンプレートファイルのパスを取得
            template_path = Path(__file__).parent.parent.parent.parent / "templates" / "重要シーンテンプレート.yaml"

            if template_path.exists():
                # テンプレートファイルをベースに使用
                f_content = template_path.read_text(encoding="utf-8")
                template_data: dict[str, Any] = yaml.safe_load(f_content) or {}

                # プロジェクト固有の情報で更新
                template_data.setdefault("metadata", {})
                template_data["metadata"]["project_name"] = Path(project_path).name if isinstance(project_path, str) else project_path.name
                template_data["metadata"]["created_at"] = "2025-01-20"

                # YAMLファイルとして保存
                with scene_file.open("w", encoding="utf-8") as f:
                    yaml.dump(template_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            else:
                # テンプレートが見つからない場合は基本構造を作成
                initial_data: dict[str, Any] = {
                    "metadata": {
                        "project_name": project_path.name,
                        "description": "重要シーンの設計と管理",
                        "created_at": "2025-01-20",
                    },
                    "scenes": {category.value: {} for category in SceneCategory},
                }

                # YAMLファイルとして保存
                with scene_file.open("w", encoding="utf-8") as f:
                    yaml.dump(initial_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            return True

        except Exception as e:
            # ファイルシステムエラーやパーミッションエラーをキャッチ
            self.console_service.print(f"シーンファイル初期化エラー: {e}")
            return False

    def get_scene_file_path(self, project_path: Path | str) -> Path:
        """シーンファイルのパスを取得"""
        path = Path(project_path) if isinstance(project_path, str) else project_path
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(path)
        return path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

    def scene_exists(self, project_path: Path | str, category: str, scene_id: str) -> bool:
        """シーンが存在するか確認"""
        try:
            scene_file = self.get_scene_file_path(project_path)
            if not scene_file.exists():
                return False

            with scene_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            scenes = data.get("scenes", {})
            category_scenes = scenes.get(category, {})
            return scene_id in category_scenes

        except (OSError, yaml.YAMLError) as e:
            # ファイル読み込みエラーやYAMLパースエラーをキャッチ
            self.console_service.print(f"シーン存在確認エラー: {e}")
            return False

    def add_scene(self, project_path: Path | str, category: str, scene_id: str, scene_data: dict[str, Any]) -> bool:
        """シーンを追加"""
        try:
            scene_file = self.get_scene_file_path(project_path)

            # 既存データを読み込み
            with scene_file.Path(encoding="utf-8").open() as f:
                data = yaml.safe_load(f)

            # シーンを追加
            if "scenes" not in data:
                data["scenes"] = {}
            if category not in data["scenes"]:
                data["scenes"][category] = {}

            data["scenes"][category][scene_id] = {
                "title": scene_data.get("title", ""),
                "description": scene_data.get("description", ""),
                "episodes": scene_data.get("episodes", []),
                "sensory_details": scene_data.get("sensory_details", {}),
                "emotional_arc": scene_data.get("emotional_arc"),
                "key_dialogues": scene_data.get("key_dialogues", []),
                "completion_status": scene_data.get("completion_status", "未実装"),
            }

            # 保存
            with scene_file.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            return True

        except (OSError, yaml.YAMLError) as e:
            # ファイル書き込みエラーやYAMLシリアライズエラーをキャッチ
            self.console_service.print(f"シーン追加エラー: {e}")
            return False

    def list_scenes(self, project_path: Path, category: str | None = None) -> list[SceneInfo]:
        """シーン一覧を取得"""
        try:
            scene_file = self.get_scene_file_path(project_path)
            if not scene_file.exists():
                return []

            with scene_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            scenes = []
            scenes_data: dict[str, Any] = data.get("scenes", {})

            for cat_name, cat_scenes in scenes_data.items():
                if category and cat_name != category:
                    continue

                for scene_id, scene_data in cat_scenes.items():
                    scenes.append(
                        SceneInfo(
                            scene_id=scene_id,
                            category=SceneCategory(cat_name),
                            title=scene_data.get("title", ""),
                            description=scene_data.get("description", ""),
                            episodes=scene_data.get("episodes", []),
                            sensory_details=scene_data.get("sensory_details", {}),
                            emotional_arc=scene_data.get("emotional_arc"),
                            key_dialogues=scene_data.get("key_dialogues", []),
                            completion_status=scene_data.get("completion_status"),
                        )
                    )

            return scenes

        except (OSError, yaml.YAMLError) as e:
            # ファイル読み込みエラーやYAMLパースエラーをキャッチ
            self.console_service.print(f"シーン一覧取得エラー: {e}")
            return []

    def get_scene(self, project_path: Path | str, category: str, scene_id: str) -> SceneInfo | None:
        """シーン詳細を取得"""
        try:
            scene_file = self.get_scene_file_path(project_path)
            if not scene_file.exists():
                return None

            with scene_file.Path(encoding="utf-8").open() as f:
                data = yaml.safe_load(f)

            scenes = data.get("scenes", {})
            category_scenes = scenes.get(category, {})

            if scene_id not in category_scenes:
                return None

            scene_data: dict[str, Any] = category_scenes[scene_id]
            return SceneInfo(
                scene_id=scene_id,
                category=SceneCategory(category),
                title=scene_data.get("title", ""),
                description=scene_data.get("description", ""),
                episodes=scene_data.get("episodes", []),
                sensory_details=scene_data.get("sensory_details", {}),
                emotional_arc=scene_data.get("emotional_arc"),
                key_dialogues=scene_data.get("key_dialogues", []),
                completion_status=scene_data.get("completion_status"),
            )

        except (OSError, yaml.YAMLError) as e:
            # ファイル読み込みエラーやYAMLパースエラーをキャッチ
            self.console_service.print(f"シーン詳細取得エラー: {e}")
            return None

    def _load_scene_data(self, scene_file: Path) -> dict[str, Any] | None:
        """シーンデータを読み込み"""
        try:
            with scene_file.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            self.console_service.print(f"シーンデータ読み込みエラー: {e}")
            return None

    def _validate_structure(self, data: dict[str, Any]) -> list[ValidationIssue]:
        """データ構造を検証"""
        issues: list[ValidationIssue] = []

        if "metadata" not in data:
            issues.append(
                ValidationIssue(severity="warning", category="metadata", message="メタデータが定義されていません")
            )

        if "scenes" not in data:
            issues.append(
                ValidationIssue(severity="error", category="structure", message="scenesセクションが存在しません")
            )

        return issues

    def _validate_scenes_content(self, scenes: dict[str, Any]) -> list[ValidationIssue]:
        """シーンコンテンツを検証"""
        issues: list[ValidationIssue] = []

        for category, category_scenes in scenes.items():
            # カテゴリーの妥当性チェック
            if not self._is_valid_category(category):
                issues.append(
                    ValidationIssue(severity="error", category="category", message=f"無効なカテゴリー: {category}")
                )

                continue

            # 各シーンの検証
            for scene_id, scene_data in category_scenes.items():
                issues.extend(self._validate_single_scene(scene_id, scene_data))

        return issues

    def _is_valid_category(self, category: str) -> bool:
        """カテゴリーが有効かチェック"""
        try:
            SceneCategory(category)
            return True
        except ValueError:
            return False

    def _validate_single_scene(self, scene_id: str, scene_data: dict[str, Any]) -> list[ValidationIssue]:
        """個別シーンを検証"""
        issues: list[ValidationIssue] = []

        # 必須フィールドチェック
        if not scene_data.get("title"):
            issues.append(
                ValidationIssue(severity="error", category="field", scene_id=scene_id, message="タイトルが未設定です")
            )

        if not scene_data.get("description"):
            issues.append(
                ValidationIssue(severity="warning", category="field", scene_id=scene_id, message="説明が未設定です")
            )

        # エピソード番号の妥当性チェック
        episodes = scene_data.get("episodes", [])
        for ep in episodes:
            if not isinstance(ep, int) or ep < 1:
                issues.append(
                    ValidationIssue(
                        severity="error", category="episode", scene_id=scene_id, message=f"無効なエピソード番号: {ep}"
                    )
                )

        return issues

    def validate_scenes(self, project_path: Path | str) -> list[ValidationIssue]:
        """シーンデータを検証"""
        issues: list[ValidationIssue] = []

        try:
            scene_file = self.get_scene_file_path(project_path)
            if not scene_file.exists():
                issues.append(
                    ValidationIssue(severity="error", category="file", message="重要シーンファイルが存在しません")
                )

                return issues

            data = self._load_scene_data(scene_file)
            if data is None:
                issues.append(
                    ValidationIssue(severity="error", category="yaml", message="YAMLファイルの読み込みに失敗しました")
                )

                return issues

            # 必須フィールドチェック
            issues.extend(self._validate_structure(data))
            if any(issue.severity == "error" for issue in issues):
                return issues

            # 各シーンの検証
            scenes = data.get("scenes", {})
            issues.extend(self._validate_scenes_content(scenes))

            return issues

        except yaml.YAMLError as e:
            issues.append(ValidationIssue(severity="error", category="yaml", message=f"YAMLパースエラー: {e}"))
            return issues
        except OSError as e:
            issues.append(ValidationIssue(severity="error", category="system", message=f"ファイルシステムエラー: {e}"))

            return issues

    def load_scenes(self, project_path: Path | str) -> list[Any]:
        """シーンデータを読み込み

        Args:
            project_path: プロジェクトパス

        Returns:
            シーンデータのリスト
        """
        try:
            scene_file = self.get_scene_file_path(project_path)
            if not scene_file.exists():
                return []

            with scene_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            scenes = []
            scenes_data: dict[str, Any] = data.get("scenes", {})

            for category_name, category_scenes in scenes_data.items():
                if isinstance(category_scenes, dict):
                    for scene_id, scene_data in category_scenes.items():
                        if isinstance(scene_data, dict):
                            # SceneExtractorで期待される形式に変換
                            scene = type(
                                "Scene",
                                (),
                                {
                                    "scene_id": scene_id,
                                    "title": scene_data.get("title", ""),
                                    "category": SceneCategory(category_name),
                                    "description": scene_data.get("description", ""),
                                    "importance": scene_data.get("importance", "medium"),
                                    "chapter": scene_data.get("chapter", 1),
                                    "episode_range": tuple(scene_data.get("episode_range", [1, 1])),
                                    "source": "existing_scenes",
                                },
                            )()
                            scenes.append(scene)

            return scenes

        except Exception as e:
            self.console_service.print(f"シーンデータ読み込みエラー: {e}")
            return []

    def save_scenes(self, project_path: Path, scenes: list[Any]) -> bool:
        """シーンデータを保存

        Args:
            project_path: プロジェクトパス
            scenes: 保存するシーンデータのリスト

        Returns:
            成功時True
        """
        try:
            scene_file = self.get_scene_file_path(project_path)

            # 既存データを読み込むか、新規作成
            if scene_file.exists():
                with scene_file.Path(encoding="utf-8").open() as f:
                    data = yaml.safe_load(f)
            else:
                data = {
                    "metadata": {
                        "project_name": project_path.name,
                        "description": "重要シーンの設計と管理",
                        "created_at": "2025-01-20",
                    },
                    "scenes": {},
                }

            # シーンをカテゴリ別に整理
            for scene in scenes:
                category = scene.category.value if hasattr(scene.category, "value") else str(scene.category)

                if category not in data["scenes"]:
                    data["scenes"][category] = {}

                # to_dict メソッドがあればそれを使用
                if hasattr(scene, "to_dict"):
                    scene_data: dict[str, Any] = scene.to_dict()
                else:
                    # なければ属性から辞書を作成
                    scene_data: dict[str, Any] = {
                        "title": scene.title,
                        "description": scene.description,
                        "importance": (
                            scene.importance.value if hasattr(scene.importance, "value") else str(scene.importance)
                        ),
                        "chapter": scene.chapter,
                        "episode_range": list(scene.episode_range) if hasattr(scene, "episode_range") else [1, 1],
                        "source": getattr(scene, "source", "unknown"),
                    }

                data["scenes"][category][scene.scene_id] = scene_data

            # ファイルに保存
            with scene_file.Path("w").open(encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            return True

        except Exception as e:
            self.console_service.print(f"シーンデータ保存エラー: {e}")
            return False
