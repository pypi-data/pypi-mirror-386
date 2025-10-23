#!/usr/bin/env python3

"""Application.use_cases.novel_creation_usecase
Where: Application use case orchestrating novel creation workflows.
What: Coordinates planning, drafting, and quality checks to produce complete novels.
Why: Provides a reusable entry point for novel creation without duplicating orchestration logic.
"""

from __future__ import annotations



import typing
from pathlib import Path
from typing import Any

from noveler.domain.entities.novel_project import NovelProject
from noveler.domain.value_objects.project_info import ProjectInfo


class NovelCreationRequest:
    """Input payload required to provision a new novel project.

    Attributes:
        project_name: Name of the project to be created.
        title: Title that will be associated with the project.
        author: Author credited for the work.
        genre: Genre classification for organisational purposes.
        description: Short description stored in the project metadata.
        project_path: Optional explicit path for the project root directory.
        target_word_count: Optional target word count for the project.
        additional_settings: Arbitrary keyword settings captured for later use.
    """

    def __init__(
        self,
        project_name: str,
        title: str,
        author: str,
        genre: str,
        description: str,
        project_path: Path | None = None,
        target_word_count: int | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.project_name = project_name
        self.title = title
        self.author = author
        self.genre = genre
        self.description = description
        self.project_path = project_path or Path.cwd() / project_name
        self.target_word_count = target_word_count
        self.additional_settings = kwargs


class NovelCreationResponse:
    """Outcome returned after attempting to create a novel project.

    Attributes:
        success: Indicates whether the creation workflow succeeded.
        project: Resulting `NovelProject` entity when creation was successful.
        error_message: Explanation in case the workflow failed.
        project_path: Path to the project directory when available.
    """

    def __init__(
        self,
        success: bool,
        project: NovelProject | None = None,
        error_message: str | None = None,
        project_path: Path | None = None,
    ) -> None:
        self.success = success
        self.project = project
        self.error_message = error_message
        self.project_path = project_path


class NovelCreationUsecase:
    """Coordinate the application workflow that provisions novel projects."""

    def __init__(
        self,
        project_repository: Any = None,  # Repository interface
        project_service: Any = None,  # Domain service interface
    ) -> None:
        self._project_repository = project_repository
        self.project_service = project_service

    def create_novel(self, project_name: str, author_name: str) -> bool:
        """Create a novel project using minimal metadata for quick provisioning.

        Args:
            project_name: Name of the project to provision.
            author_name: Author responsible for the project.

        Returns:
            bool: True when the project and supporting structure were created successfully.

        Raises:
            ValueError: If mandatory dependencies are missing or validation fails.
        """
        if not project_name or not project_name.strip():
            raise ValueError("プロジェクト名は必須です")
        if not author_name or not author_name.strip():
            raise ValueError("作者名は必須です")

        if self.project_service is None:
            raise ValueError("プロジェクトサービスが設定されていません")
        if self._project_repository is None:
            raise ValueError("プロジェクトリポジトリが設定されていません")

        if not self.project_service.validate_project_name(project_name):
            raise ValueError("不正なプロジェクト名です")

        exists_callable = getattr(self._project_repository, "exists", None)
        if callable(exists_callable) and exists_callable(project_name):
            raise ValueError("プロジェクトが既に存在します")

        project_path = self._extract_project_path(project_name, author_name)

        created = True
        create_callable = getattr(self._project_repository, "create_project", None)
        if callable(create_callable):
            try:
                created = create_callable(project_name, author_name)
            except TypeError as exc:
                if not self._is_signature_mismatch(exc):
                    raise
                created = create_callable(project_name)
        else:
            create_callable = getattr(self._project_repository, "create", None)
            if callable(create_callable):
                payload = {"author_name": author_name, "project_path": str(project_path)}
                created = create_callable(project_name, payload)

        if created is False:
            raise ValueError("プロジェクトの作成に失敗しました")

        initializer = getattr(self.project_service, "initialize_project_structure", None)
        if callable(initializer):
            init_result = initializer(project_path)
            if init_result is False:
                raise ValueError("プロジェクト構造の初期化に失敗しました")

        return True

    def execute(self, request: NovelCreationRequest) -> NovelCreationResponse:
        """Execute the full novel creation workflow.

        Args:
            request: Description of the project to be created.

        Returns:
            NovelCreationResponse: Result of the project creation attempt.
        """
        try:
            # バリデーション
            validation_result = self._validate_request(request)
            if not validation_result.success:
                return validation_result

            # プロジェクト情報作成
            project_info = ProjectInfo(
                name=request.project_name,
                root_path=request.project_path,
                config_path=request.project_path / "プロジェクト設定.yaml",
                title=request.title,
                author=request.author,
                genre=request.genre,
                description=request.description,
                target_word_count=request.target_word_count,
            )

            # プロジェクトエンティティ作成
            project = NovelProject(
                name=request.project_name,
                project_info=project_info,
                project_path=request.project_path,
            )

            # 追加設定があれば適用
            if request.additional_settings:
                project.update_configuration(request.additional_settings)

            # プロジェクトの保存（リポジトリが設定されている場合）
            if self._project_repository:
                save_success = self._project_repository.save(project)
                if not save_success:
                    return NovelCreationResponse(success=False, error_message="プロジェクトの保存に失敗しました")

            # プロジェクト構造の初期化（サービスが設定されている場合）
            if self.project_service:
                init_success = self.project_service.initialize_project_structure(request.project_path)
                if not init_success:
                    return NovelCreationResponse(success=False, error_message="プロジェクト構造の初期化に失敗しました")

            return NovelCreationResponse(
                success=True,
                project=project,
                project_path=request.project_path,
            )

        except Exception as e:
            return NovelCreationResponse(
                success=False, error_message=f"プロジェクト作成中にエラーが発生しました: {e!s}"
            )

    def _extract_project_path(self, project_name: str, author_name: str) -> Path:
        """Resolve the project path from the repository and normalise it.

        Args:
            project_name: Name of the project.
            author_name: Author used when deriving repository paths.

        Returns:
            Path: Normalised path for the project root.
        """
        path_getter = getattr(self._project_repository, "get_project_path", None)
        if callable(path_getter):
            try:
                candidate = path_getter(project_name, author_name)
            except TypeError as exc:
                if not self._is_signature_mismatch(exc):
                    raise
                candidate = path_getter(project_name)
            if candidate is not None:
                return Path(candidate)
        return Path(project_name)

    @staticmethod
    def _is_signature_mismatch(error: TypeError) -> bool:
        """Return whether a `TypeError` was triggered by a signature mismatch.

        Args:
            error: Error raised by a repository call.

        Returns:
            bool: True if the error indicates mismatched call signatures.
        """
        message = str(error)
        keywords = ["positional arguments", "positional argument", "keyword argument", "required positional argument", "unexpected keyword"]
        return any(keyword in message for keyword in keywords)

    def _validate_request(self, request: NovelCreationRequest) -> NovelCreationResponse:
        """Validate the incoming request before creating a project.

        Args:
            request: Request object to validate.

        Returns:
            NovelCreationResponse: Success response when validation passes or an error response.
        """
        # 必須フィールドのチェック
        if not request.project_name or not request.project_name.strip():
            return NovelCreationResponse(success=False, error_message="プロジェクト名は必須です")

        if not request.title or not request.title.strip():
            return NovelCreationResponse(success=False, error_message="タイトルは必須です")

        if not request.author or not request.author.strip():
            return NovelCreationResponse(success=False, error_message="作者名は必須です")

        # プロジェクト名のバリデーション（サービスが設定されている場合）
        if self.project_service:
            if not self.project_service.validate_project_name(request.project_name):
                return NovelCreationResponse(success=False, error_message="無効なプロジェクト名です")

        # プロジェクトの重複チェック（リポジトリが設定されている場合）
        if self._project_repository:
            if self._project_repository.exists(request.project_name):
                return NovelCreationResponse(success=False, error_message="同名のプロジェクトが既に存在します")

        return NovelCreationResponse(success=True)
