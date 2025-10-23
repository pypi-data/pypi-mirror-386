"""
YAMLベースの伏線管理リポジトリ実装
SPEC-FORESHADOWING-001準拠
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
from noveler.domain.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingCategory,
    ForeshadowingId,
    ForeshadowingStatus,
)
from noveler.domain.value_objects.project_time import project_now


# 一時的なモッククラス - 実際のForeshadowingクラス使用時は削除
class MockForeshadowing:
    def __init__(
        self,
        id: str,
        title: str,
        status: ForeshadowingStatus,
        importance: int,
        planting: dict[str, Any],
        resolution: dict[str, Any] | None,
        hints: list[str],
    ) -> None:
        self.id = id
        self.title = title
        self.status = status
        self.importance = importance
        self.planting = planting
        self.resolution = resolution
        self.hints = hints


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class MockStatus:
    def __init__(self, value: str, logger_service=None, console_service=None) -> None:
        self.value = value


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class MockPlanting:
    def __init__(self, episode: str, content: str, method: str, logger_service=None, console_service=None) -> None:
        self.episode = episode
        self.content = content
        self.method = method


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class MockResolution:
    def __init__(self, episode: str, content: str, method: str, logger_service=None, console_service=None) -> None:
        self.episode = episode
        self.content = content
        self.method = method


        # 一時的な実装 - 実際のクラスが利用可能になるまで使用
        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class PlantingInfo:
    def __init__(self, episode: str, chapter: int, method: str, content: str, subtlety_level: object, logger_service=None, console_service=None) -> None:
        self.episode = episode
        self.chapter = chapter
        self.method = method
        self.content = content
        self.subtlety_level = subtlety_level


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class ResolutionInfo:
    def __init__(self, episode: str, chapter: int, method: str, impact: str, logger_service=None, console_service=None) -> None:
        self.episode = episode
        self.chapter = chapter
        self.method = method
        self.impact = impact


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class Hint:
    def __init__(self, episode: str, content: str, subtlety: object, logger_service=None, console_service=None) -> None:
        self.episode = episode
        self.content = content
        self.subtlety = subtlety


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class SubtletyLevel:
    def __init__(self, value: str, logger_service=None, console_service=None) -> None:
        self.value = value


        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
class ReaderReaction:
    def __init__(self, on_planting: str, on_hints: str, on_resolution: str, logger_service=None, console_service=None) -> None:
        self.on_planting = on_planting
        self.on_hints = on_hints
        self.on_resolution = on_resolution


        from noveler.domain.value_objects.project_time import ProjectTimezone

        # JSTタイムゾーン
        ProjectTimezone.jst().timezone


class YamlForeshadowingRepository(ForeshadowingRepository):
    """YAML形式で伏線を管理するリポジトリ実装"""

    def __init__(self, template_path: str | Path | None = None, logger_service=None, console_service=None) -> None:
        """
        Args:
            template_path: テンプレートファイルのパス(省略時はデフォルト)
        """
        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
        if template_path:
            self.template_path = template_path
        else:
            # デフォルトのテンプレートパス
            self.template_path = Path(__file__).parent.parent.parent.parent / "templates" / "伏線管理テンプレート.yaml"

        # サービスは初期化時に設定される
        # self.logger_service = logger_service
        # self.console_service = console_service
    def load_all(self, project_root: str | Path) -> list[Foreshadowing]:
        """すべての伏線を読み込む"""
        file_path = self._get_file_path(project_root)

        if not file_path.exists():
            msg = f"伏線管理ファイルが見つかりません: {file_path}"
            raise FileNotFoundError(msg)

        with Path(file_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "foreshadowing" not in data:
            return []

        foreshadowings = []
        for foreshadowing_id, foreshadowing_data in data["foreshadowing"].items():
            foreshadowing = self._yaml_to_domain(foreshadowing_id, foreshadowing_data)
            if foreshadowing:
                foreshadowings.append(foreshadowing)

        return foreshadowings

    def save_all(self, foreshadowings: list[Foreshadowing], project_root: str | Path) -> None:
        """すべての伏線を保存する"""
        file_path = self._get_file_path(project_root)

        # ディレクトリを作成
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 既存データを読み込む(メタデータ等を保持するため)
        if file_path.exists():
            with Path(file_path).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            # テンプレートから基本構造を作成
            data = self._load_template_structure()

        # メタデータを更新
        data["metadata"]["total_foreshadowing"] = len(foreshadowings)
        data["metadata"]["last_updated"] = project_now().datetime.isoformat()

        # 伏線データを更新
        data["foreshadowing"] = {}
        for foreshadowing in foreshadowings:
            yaml_data: dict[str, Any] = self._domain_to_yaml(foreshadowing)
            data["foreshadowing"][foreshadowing.id.value] = yaml_data

        # 章別サマリーを更新
        data["chapter_summary"] = self._create_chapter_summary(foreshadowings)

        # ファイルに保存
        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def find_by_id(self, foreshadowing_id: ForeshadowingId, project_root: str | Path) -> Foreshadowing | None:
        """IDで伏線を検索する"""
        foreshadowings = self.load_all(project_root)
        for foreshadowing in foreshadowings:
            if foreshadowing.id.value == foreshadowing_id.value:
                return foreshadowing
        return None

    def exists(self, project_root: str | Path) -> bool:
        """伏線管理ファイルが存在するか確認"""
        file_path = self._get_file_path(project_root)
        return file_path.exists()

    def create_from_template(self, project_root: str | Path) -> None:
        """テンプレートから伏線管理ファイルを作成"""
        file_path = self._get_file_path(project_root)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # テンプレートを読み込む
        if self.template_path.exists():
            with Path(self.template_path).open(encoding="utf-8") as f:
                template_data: dict[str, Any] = yaml.safe_load(f)
        else:
            # テンプレートが見つからない場合は最小構造を作成
            template_data: dict[str, Any] = self._create_minimal_template()

        # プロジェクト名を設定
        template_data["metadata"]["project_name"] = project_root.name
        template_data["metadata"]["last_updated"] = project_now().datetime.isoformat()

        # ファイルに保存
        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(template_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def _get_file_path(self, project_root: str | Path) -> Path:
        """伏線管理ファイルのパスを取得"""
        root_path = Path(project_root) if isinstance(project_root, str) else project_root
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(root_path)
        return path_service.get_foreshadowing_file()

    def _yaml_to_domain(self, foreshadowing_id: str, data: dict[str, Any]) -> Foreshadowing | None:
        """YAMLデータをドメインオブジェクトに変換"""
        try:
            # 必須フィールドの確認
            if not all(key in data for key in ["title", "category", "description", "importance"]):
                return None

            # PlantingInfo
            planting_data: dict[str, Any] = data.get("planting", {})
            planting = PlantingInfo(
                episode=planting_data.get("episode", "第001話"),
                chapter=planting_data.get("chapter", 1),
                method=planting_data.get("method", ""),
                content=planting_data.get("content", ""),
                subtlety_level=SubtletyLevel(planting_data.get("subtlety_level", "medium")),
            )

            # ResolutionInfo
            resolution_data: dict[str, Any] = data.get("resolution", {})
            resolution = ResolutionInfo(
                episode=resolution_data.get("episode", "第030話"),
                chapter=resolution_data.get("chapter", 3),
                method=resolution_data.get("method", ""),
                impact=resolution_data.get("impact", ""),
            )

            # Hints
            hints = []
            if "hints" in data:
                for hint_data in data["hints"]:
                    hint = Hint(
                        episode=hint_data.get("episode", ""),
                        content=hint_data.get("content", ""),
                        subtlety=SubtletyLevel(hint_data.get("subtlety", "medium")),
                    )

                    hints.append(hint)

            # ReaderReaction
            reader_reaction = None
            if "expected_reader_reaction" in data:
                reaction_data: dict[str, Any] = data["expected_reader_reaction"]
                reader_reaction = ReaderReaction(
                    on_planting=reaction_data.get("on_planting", ""),
                    on_hints=reaction_data.get("on_hints", ""),
                    on_resolution=reaction_data.get("on_resolution", ""),
                )

            return Foreshadowing(
                id=ForeshadowingId(foreshadowing_id),
                title=data["title"],
                category=ForeshadowingCategory(data["category"]),
                description=data["description"],
                importance=data["importance"],
                planting=planting,
                resolution=resolution,
                status=ForeshadowingStatus(data.get("status", "planned")),
                related_scene_ids=data.get("related_scenes"),
                hints=hints if hints else None,
                notes=data.get("notes"),
                expected_reader_reaction=reader_reaction,
            )

        except Exception as e:
            self.console_service.print(f"伏線データの変換エラー ({foreshadowing_id}): {e}")
            return None

    def _domain_to_yaml(self, foreshadowing: Foreshadowing) -> dict[str, Any]:
        """ドメインオブジェクトをYAMLデータに変換"""
        data = {
            "title": foreshadowing.title,
            "category": foreshadowing.category.value,
            "description": foreshadowing.description,
            "importance": foreshadowing.importance,
            "planting": {
                "episode": foreshadowing.planting.episode,
                "chapter": foreshadowing.planting.chapter,
                "method": foreshadowing.planting.method,
                "content": foreshadowing.planting.content,
                "subtlety_level": foreshadowing.planting.subtlety_level.value,
            },
            "resolution": {
                "episode": foreshadowing.resolution.episode,
                "chapter": foreshadowing.resolution.chapter,
                "method": foreshadowing.resolution.method,
                "impact": foreshadowing.resolution.impact,
            },
            "status": foreshadowing.status.value,
        }

        # オプショナルフィールド
        if foreshadowing.related_scene_ids:
            data["related_scenes"] = foreshadowing.related_scene_ids

        if foreshadowing.hints:
            data["hints"] = [
                {"episode": hint.episode, "content": hint.content, "subtlety": hint.subtlety.value}
                for hint in foreshadowing.hints
            ]

        if foreshadowing.notes:
            data["notes"] = foreshadowing.notes

        if foreshadowing.expected_reader_reaction:
            data["expected_reader_reaction"] = {
                "on_planting": foreshadowing.expected_reader_reaction.on_planting,
                "on_hints": foreshadowing.expected_reader_reaction.on_hints,
                "on_resolution": foreshadowing.expected_reader_reaction.on_resolution,
            }

        return data

    def _create_chapter_summary(self, foreshadowings: list[Foreshadowing]) -> dict[int, dict[str, Any]]:
        """章別の伏線サマリーを作成"""
        summary = {}

        for foreshadowing in foreshadowings:
            # 仕込み章
            planting_chapter = foreshadowing.planting.chapter
            if planting_chapter not in summary:
                summary[planting_chapter] = {"planted": [], "resolved": [], "notes": ""}
            summary[planting_chapter]["planted"].append(foreshadowing.id.value)

            # 回収章
            resolution_chapter = foreshadowing.resolution.chapter
            if resolution_chapter not in summary:
                summary[resolution_chapter] = {"planted": [], "resolved": [], "notes": ""}
            summary[resolution_chapter]["resolved"].append(foreshadowing.id.value)

        return summary

    def _load_template_structure(self) -> dict[str, Any]:
        """テンプレートの基本構造を読み込む"""
        if self.template_path.exists():
            with Path(self.template_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            return self._create_minimal_template()

    def _create_minimal_template(self) -> dict[str, Any]:
        """最小限のテンプレート構造を作成"""
        return {
            "metadata": {"project_name": "", "total_foreshadowing": 0, "last_updated": "", "version": "1.0"},
            "categories": {
                "main": "メインプロット関連",
                "character": "キャラクター関連",
                "worldbuilding": "世界観・設定関連",
                "mystery": "謎・ミステリー関連",
                "emotional": "感情的伏線",
                "thematic": "テーマ的伏線",
            },
            "foreshadowing": {},
            "relationships": [],
            "chapter_summary": {},
            "writing_checklist": {
                "planting": [
                    "自然な流れで仕込めているか",
                    "読者に違和感を与えていないか",
                    "後から読み返した時に「なるほど」と思えるか",
                ],
                "hints": ["ヒントの量は適切か(多すぎず少なすぎず)", "段階的に情報開示できているか"],
                "resolution": ["十分なインパクトがあるか", "論理的に納得できる展開か", "感情的な満足感を与えられるか"],
            },
            "analytics": {
                "average_planting_to_resolution_distance": 0,
                "foreshadowing_density_by_chapter": {},
                "resolution_satisfaction_score": 0,
            },
        }
