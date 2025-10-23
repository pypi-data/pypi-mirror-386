"""Text analysis use case.

Implements the Unicode character count analysis workflow (SPEC-COUNT-001) at the application layer.
"""

from dataclasses import dataclass
from pathlib import Path

from noveler.application.base.abstract_use_case import AbstractUseCase

# Import moved to top-level
from noveler.domain.services.text_analysis_service import TextAnalysisService
from noveler.domain.value_objects.text_analysis_result import TextAnalysisResult


@dataclass
class TextAnalysisRequest:
    """Request payload describing how to analyze text.

    Attributes:
        file_path: Optional path to the file to analyze.
        text: Inline text content to analyze when no file is provided.
        target_id: Optional hashed identifier to filter the result.
        warn_long_line: Threshold triggering long line warnings.
        warn_long_sentence: Threshold triggering long sentence warnings.
    """
    file_path: str | None = None
    text: str | None = None
    target_id: str | None = None  # 特定箇所のハッシュID
    warn_long_line: int = 40
    warn_long_sentence: int = 100

@dataclass
class TextAnalysisResponse:
    """Response payload returned after text analysis.

    Attributes:
        success: Indicates whether the analysis succeeded.
        result: Rich analysis data structure.
        error_message: Error description when analysis fails.
    """
    success: bool
    result: TextAnalysisResult | None = None
    error_message: str | None = None

class TextAnalysisUseCase(AbstractUseCase[TextAnalysisRequest, TextAnalysisResponse]):
    """Manage IO and delegate text analysis to the functional core service."""

    def __init__(self) -> None:
        self._service = TextAnalysisService()

    async def execute(self, request: TextAnalysisRequest) -> TextAnalysisResponse:
        """Execute the text analysis workflow.

        Args:
            request: Text analysis request payload.

        Returns:
            TextAnalysisResponse: Analysis result or error response.
        """
        try:
            # Retrieve text from request or file
            text = await self._get_text(request)

            if not text:
                return TextAnalysisResponse(
                    success=False,
                    error_message="テキストが空です"
                )

            # 純粋関数での分析
            result = self._service.analyze_text(
                text=text,
                warn_long_line=request.warn_long_line,
                warn_long_sentence=request.warn_long_sentence
            )

            # 特定箇所の指定がある場合はフィルタリング
            if request.target_id:
                filtered_result = self._filter_by_target_id(result, request.target_id)
                return TextAnalysisResponse(
                    success=True,
                    result=filtered_result
                )

            return TextAnalysisResponse(
                success=True,
                result=result
            )

        except Exception as e:
            return TextAnalysisResponse(
                success=False,
                error_message=f"分析エラー: {e!s}"
            )

    async def _get_text(self, request: TextAnalysisRequest) -> str:
        """Retrieve text content either from inline payload or disk."""
        if request.text is not None:
            return request.text

        if request.file_path:
            try:
                file_path = Path(request.file_path)
                if not file_path.exists():
                    msg = f"ファイルが見つかりません: {request.file_path}"
                    raise FileNotFoundError(msg)

                # ファイル読み込み（副作用）
                with file_path.open(encoding="utf-8") as f:
                    return f.read()

            except Exception as e:
                msg = f"ファイル読み込みエラー: {e!s}"
                raise ValueError(msg)

        msg = "text または file_path のいずれかが必要です"
        raise ValueError(msg)

    def _filter_by_target_id(
        self,
        result: TextAnalysisResult,
        target_id: str
    ) -> TextAnalysisResult:
        """Filter the analysis result to include only the matching identifier."""
        # 該当する行を検索
        target_line = result.get_line_by_id(target_id)
        if target_line:
            return TextAnalysisResult(
                total_characters=target_line.char_count,
                total_lines=1,
                total_sentences=0,
                total_paragraphs=0,
                breakdown=result.breakdown,
                lines=[target_line],
                sentences=[],
                paragraphs=[],
                quality_warnings=[]
            )

        # 該当する文を検索
        target_sentence = result.get_sentence_by_id(target_id)
        if target_sentence:
            return TextAnalysisResult(
                total_characters=target_sentence.char_count,
                total_lines=0,
                total_sentences=1,
                total_paragraphs=0,
                breakdown=result.breakdown,
                lines=[],
                sentences=[target_sentence],
                paragraphs=[],
                quality_warnings=[]
            )

        # 見つからない場合は空の結果
        return TextAnalysisResult(
            total_characters=0,
            total_lines=0,
            total_sentences=0,
            total_paragraphs=0,
            breakdown=result.breakdown,
            lines=[],
            sentences=[],
            paragraphs=[],
            quality_warnings=[]
        )
