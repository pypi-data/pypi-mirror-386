#!/usr/bin/env python3
"""Prompt generation use case.

Implements the application-layer orchestration for the A24 guide driven prompt
generation workflow. Coordinates domain services in response to user requests.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

from noveler.domain.entities.prompt_generation import (
    OptimizationTarget,
    PromptGenerationSession,
)
from noveler.domain.services.prompt_generation_service import PromptGenerationService


@dataclass
class PromptGenerationUseCaseRequest:
    """Request payload for generating prompts.

    Attributes:
        episode_number: Episode identifier used by the generator.
        project_name: Name of the project the episode belongs to.
        context_level: Context richness level (basic, extended, full).
        include_foreshadowing: Whether foreshadowing context should be embedded.
        include_important_scenes: Whether important scene summaries are included.
        optimization_target: Optimisation target for downstream systems.
        project_root_path: Optional explicit project root directory.
    """

    episode_number: int
    project_name: str
    context_level: str = "基本"  # 基本|拡張|完全
    include_foreshadowing: bool = True
    include_important_scenes: bool = True
    optimization_target: OptimizationTarget = OptimizationTarget.CLAUDE_CODE
    project_root_path: Path | None = None


@dataclass
class PromptGenerationUseCaseResponse:
    """Response payload returned after prompt generation (legacy compatible).

    Attributes:
        success: Indicates whether the generation completed successfully.
        generated_prompt: Final prompt text.
        token_estimate: Estimated token count for the prompt.
        context_elements_count: Number of context elements aggregated.
        generation_time_ms: Total time spent generating in milliseconds.
        session_id: Identifier of the underlying generation session.
        completion_rate: Completion ratio reported by the session.
        context_summary: Summary describing included context categories.
        warnings: Non-blocking warnings produced during generation.
        error_message: Optional error detail when unsuccessful.
        output_file_path: Optional path used to persist the prompt.
    """

    success: bool
    generated_prompt: str = ""
    token_estimate: int = 0
    context_elements_count: int = 0
    generation_time_ms: int = 0
    session_id: str = ""
    completion_rate: float = 0.0
    context_summary: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    output_file_path: str | None = None  # 追加: 保存ファイルパス


class PromptGenerationUseCase:
    """Coordinate prompt generation across domain services and error handling."""

    def __init__(
        self,
        prompt_service: PromptGenerationService | None = None,
        logger_service=None,
        unit_of_work=None,
        **kwargs
    ) -> None:
        """Initialise the use case with optional infrastructure services.

        Args:
            prompt_service: Domain service responsible for prompt generation.
            logger_service: Logger used for diagnostics.
            unit_of_work: Optional unit-of-work instance for transactional scopes.
            **kwargs: Additional arguments forwarded to parent classes.
        """
        super().__init__(**kwargs)
        self._prompt_service = prompt_service
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

    async def execute(self, request: PromptGenerationUseCaseRequest) -> PromptGenerationUseCaseResponse:
        """Generate a prompt based on the supplied request parameters.

        Args:
            request: Prompt generation request descriptor.

        Returns:
            PromptGenerationUseCaseResponse: Formatted result of the generation workflow.
        """
        start_time = time.time()

        try:
            # バリデーション
            self._validate_request(request)

            # セッション初期化
            session = self._create_session(request)
            session.start_generation(request.episode_number, request.project_name)

            # プロンプト生成実行
            self._invoke_prompt_generation(session)

            # 成功レスポンス生成
            end_time = time.time()
            generation_time_ms = max(1, int((end_time - start_time) * 1000))
            session.generation_time_ms = generation_time_ms

            success = session.is_success()
            error_message: str | None
            if success:
                error_message = None
            elif session.errors:
                error_message = "; ".join(session.errors)
            elif session.final_prompt:
                error_message = session.final_prompt
            else:
                error_message = "プロンプト生成が完了しませんでした"

            return PromptGenerationUseCaseResponse(
                success=success,
                generated_prompt=session.final_prompt,
                token_estimate=session.token_estimate,
                context_elements_count=len(session.integrated_context),
                generation_time_ms=generation_time_ms,
                session_id=str(session.session_id),
                completion_rate=session.get_completion_rate(),
                context_summary=session.get_context_summary(),
                warnings=session.warnings,
                error_message=error_message,
            )

        except ValueError as e:
            # バリデーションエラー
            return self._create_error_response(f"要求パラメータエラー: {e!s}", int((time.time() - start_time) * 1000))

        except RuntimeError as e:
            # ドメインサービスエラー
            return self._create_error_response(f"プロンプト生成エラー: {e!s}", int((time.time() - start_time) * 1000))

        except Exception as e:
            # 予期せぬエラー
            return self._create_error_response(f"内部エラー: {e!s}", int((time.time() - start_time) * 1000))

    async def execute_and_save(
        self, request: PromptGenerationUseCaseRequest, output_file_path: Path | None = None
    ) -> PromptGenerationUseCaseResponse:
        """Generate a prompt and persist it to disk when successful.

        Args:
            request: Prompt generation request descriptor.
            output_file_path: Optional explicit output file path.

        Returns:
            PromptGenerationUseCaseResponse: Generation result including the output path.
        """
        # 通常のプロンプト生成実行
        response = await self.execute(request)

        if not response.success:
            return response

        try:
            # 出力ファイルパス決定
            if output_file_path is None:
                output_file_path = self._generate_output_file_path(request)

            # ディレクトリ作成
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            # プロンプトをファイル保存
            with output_file_path.open("w", encoding="utf-8") as f:
                f.write(response.generated_prompt)

            # レスポンスに保存パス情報を追加
            response.output_file_path = str(output_file_path)

            return response

        except Exception as e:
            # ファイル保存エラー時は警告として扱い、プロンプト生成は成功とする
            response.warnings.append(f"ファイル保存エラー: {e!s}")
            return response

    def _generate_output_file_path(self, request: PromptGenerationUseCaseRequest) -> Path:
        """Build the default output path for a generated prompt.

        Args:
            request: Prompt generation request descriptor.

        Returns:
            Path: Location where the prompt should be stored.
        """
        # プロジェクトルート取得
        if request.project_root_path:
            project_root = request.project_root_path
        else:
            # 環境変数から取得を試行
            import os

            env_project_root = os.environ.get("PROJECT_ROOT")
            if env_project_root:
                project_root = Path(env_project_root)
            else:
                # デフォルトパス
                project_root = Path.cwd().parent / "10_Fランク魔法使いはDEBUGログを読む"

        # 話別プロットディレクトリ
        plot_dir = project_root / "60_プロンプト" / "話別プロット"

        # ファイル名生成（第000話_{仮タイトル}.yaml）
        episode_title = "プロンプト生成"  # デフォルトタイトル
        filename = f"第{request.episode_number:03d}話_{episode_title}.yaml"

        return plot_dir / filename

    def _validate_request(self, request: PromptGenerationUseCaseRequest) -> None:
        """Validate the incoming request and raise when invalid.

        Args:
            request: Request payload to validate.

        Raises:
            ValueError: If the request fails validation checks.
        """
        if request.episode_number <= 0:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)

        if not request.project_name or not request.project_name.strip():
            msg = "プロジェクト名は必須です"
            raise ValueError(msg)

        valid_context_levels = ["基本", "拡張", "完全"]
        if request.context_level not in valid_context_levels:
            msg = f"コンテキストレベルは次のいずれかである必要があります: {valid_context_levels}"
            raise ValueError(msg)

        if request.project_root_path and not request.project_root_path.exists():
            msg = f"指定されたプロジェクトルートが存在しません: {request.project_root_path}"
            raise ValueError(msg)

    def _create_session(self, request: PromptGenerationUseCaseRequest) -> PromptGenerationSession:
        """Instantiate and configure a prompt generation session.

        Args:
            request: Request that supplies session configuration.

        Returns:
            PromptGenerationSession: Configured session object.
        """
        session = PromptGenerationSession()
        session.context_level = request.context_level
        session.optimization_target = request.optimization_target
        session.include_foreshadowing = request.include_foreshadowing
        session.include_important_scenes = request.include_important_scenes

        return session

    def _invoke_prompt_generation(self, session: PromptGenerationSession) -> None:
        """Invoke the prompt service, supporting test doubles.

        Args:
            session: Session entity that accumulates generation data.

        Returns:
            None: The session is mutated in place.

        Raises:
            RuntimeError: If no prompt service or generator function is configured.
        """

        if self._prompt_service is None:
            msg = "プロンプト生成サービスが設定されていません"
            raise RuntimeError(msg)

        generator = getattr(self._prompt_service, "generate_prompt_for_episode", None)
        if generator is None:
            msg = "プロンプト生成サービスに generate_prompt_for_episode が実装されていません"
            raise RuntimeError(msg)

        side_effect = getattr(generator, "side_effect", None)
        if side_effect is not None:
            if isinstance(side_effect, Exception):
                raise side_effect
            if callable(side_effect):
                result = side_effect(session)
                if result is not None:
                    return result

        return generator(session)

    def _create_error_response(self, error_message: str, generation_time_ms: int) -> PromptGenerationUseCaseResponse:
        """Build a failure response with the provided error message.

        Args:
            error_message: Description of the failure.
            generation_time_ms: Time spent before the failure occurred.

        Returns:
            PromptGenerationUseCaseResponse: Populated failure response.
        """
        return PromptGenerationUseCaseResponse(
            success=False,
            generated_prompt="",
            token_estimate=0,
            context_elements_count=0,
            generation_time_ms=generation_time_ms,
            session_id="",
            completion_rate=0.0,
            context_summary={},
            warnings=[],
            error_message=error_message,
        )
