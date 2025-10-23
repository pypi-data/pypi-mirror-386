#!/usr/bin/env python3
"""シーン管理DTO群

シーン管理ユースケースのリクエスト・レスポンスオブジェクト定義。
アプリケーション層のデータ転送オブジェクト(DTO)として分離。
"""

from dataclasses import dataclass, field
from pathlib import Path

from noveler.domain.entities.scene_management_entities import SceneCategory, SceneInfo, ValidationIssue


@dataclass
class SceneInitRequest:
    """シーン初期化リクエスト"""

    project_name: str
    project_directory: str


@dataclass
class SceneInitResponse:
    """シーン初期化レスポンス"""

    success: bool
    scene_file_path: Path | None = None
    message: str = ""


@dataclass
class SceneAddRequest:
    """シーン追加リクエスト"""

    project_name: str
    project_directory: str
    category: SceneCategory
    scene_id: str
    title: str
    description: str
    episodes: list[int] = field(default_factory=list)
    sensory_details: dict[str, str] = field(default_factory=dict)


@dataclass
class SceneAddResponse:
    """シーン追加レスポンス"""

    success: bool
    scene_id: str
    category: SceneCategory
    message: str = ""


@dataclass
class SceneListRequest:
    """シーン一覧リクエスト"""

    project_name: str
    project_directory: str
    category: SceneCategory | None = None


@dataclass
class SceneListResponse:
    """シーン一覧レスポンス"""

    success: bool
    scenes: list[SceneInfo] = field(default_factory=list)
    total_by_category: dict[SceneCategory, int] = field(default_factory=dict)
    message: str = ""


@dataclass
class SceneShowRequest:
    """シーン詳細リクエスト"""

    project_name: str
    project_directory: str
    category: SceneCategory
    scene_id: str


@dataclass
class SceneShowResponse:
    """シーン詳細レスポンス"""

    success: bool
    scene: SceneInfo | None = None
    message: str = ""


@dataclass
class SceneChecklistRequest:
    """シーンチェックリストリクエスト"""

    project_name: str
    project_directory: str
    output_format: str = "markdown"
    output_path: str | None = None


@dataclass
class SceneChecklistResponse:
    """シーンチェックリストレスポンス"""

    success: bool
    checklist_content: str = ""
    total_scenes: int = 0
    completed_scenes: int = 0
    output_path: Path | None = None
    message: str = ""


@dataclass
class SceneValidateRequest:
    """シーン検証リクエスト"""

    project_name: str
    project_directory: str


@dataclass
class SceneValidateResponse:
    """シーン検証レスポンス"""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    message: str = ""
