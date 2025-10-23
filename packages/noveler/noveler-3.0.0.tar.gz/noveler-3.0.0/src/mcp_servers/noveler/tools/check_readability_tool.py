# File: src/mcp_servers/noveler/tools/check_readability_tool.py
# Purpose: Implement the "check_readability" MCP tool that evaluates manuscript
#          readability and returns findings and a score.
# Context: Part of the Noveler MCP tool suite. Uses domain readability
#          services and infrastructure path/cache services. No side effects at
#          import time; work happens during execute().
"""check_readability ツールの実装

SPEC-MCP-001: MCP Server Granular Microservice Architecture
"""
import hashlib
import re
import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import MCPToolBase, ToolIssue, ToolRequest, ToolResponse
from noveler.domain.services.readability_analysis_service import ReadabilityAnalysisService
from noveler.domain.value_objects.readability_finding import ReadabilityFinding
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.logging.unified_logger import get_logger


class CheckReadabilityTool(MCPToolBase):
    """読みやすさチェックツール

    文章の読みやすさを評価し、改善点を提案する。
    - 文の長さ
    - 語彙の複雑さ
    - 読みやすさスコア
    """

    def __init__(self) -> None:
        super().__init__(
            tool_name="check_readability",
            tool_description="読みやすさチェック（文の長さ、難解語彙）"
        )
        self._analysis_service = ReadabilityAnalysisService()

    def get_input_schema(self) -> dict[str, Any]:
        """入力スキーマを返す"""
        schema = self._get_common_input_schema()

        # readability特有のパラメータを追加
        schema["properties"].update({
            "file_path": {
                "type": "string",
                "description": "直接ファイルパス指定（episode_numberより優先）",
            },
            "exclude_dialogue_lines": {
                "type": "boolean",
                "default": False,
                "description": "会話行（「…」/『…』）を文長チェックから除外する",
            },
            "check_aspects": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["sentence_length", "vocabulary_complexity", "readability_score"]
                },
                "description": "チェック観点の絞り込み（省略時は全て）"
            }
        })

        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        """読みやすさチェックを実行"""
        # 統一ロギングシステムを使用
        logger = get_logger(__name__)

        start_time = time.time()
        logger.info("読みやすさチェック開始: エピソード%s", request.episode_number)

        try:
            self._validate_request(request)

            # エピソードファイルの読み込み + パス/ハッシュ
            episode_content, file_path, file_hash = self._resolve_episode_content(request)
            if not episode_content:
                # 空のエピソードの場合は満点を返す
                logger.info("エピソード%s は空のため、満点を返却", request.episode_number)
                return self._create_response(True, 100.0, [], start_time)

            # チェック観点の決定
            check_aspects = self._get_check_aspects(request)
            logger.debug("チェック観点: %s", check_aspects)

            # 読みやすさ分析の実行
            analysis_result = self._analysis_service.analyze(
                episode_content, aspects=check_aspects,
                exclude_dialogue_lines=bool((request.additional_params or {}).get("exclude_dialogue_lines", False))
            )
            issues = self._convert_findings(
                analysis_result.issues,
                episode_content.split("\n"),
                file_path,
                file_hash,
            )
            score = analysis_result.score

            logger.info("読みやすさチェック完了: スコア=%.1f, 問題数=%d", score, len(issues))
            resp = self._create_response(True, score, issues, start_time)
            if file_path:
                resp.metadata["file_path"] = str(file_path)
            if file_hash:
                resp.metadata["file_hash"] = file_hash
            if analysis_result.average_sentence_length is not None:
                resp.metadata["average_sentence_length"] = analysis_result.average_sentence_length
            # PathServiceのフォールバック可視化
            self._apply_fallback_metadata(resp)
            return resp

        except FileNotFoundError:
            # より詳細なエラー情報を提供
            available_episodes = self._get_available_episodes()
            if available_episodes:
                error_msg = f"Episode {request.episode_number} not found. Available episodes: {', '.join(map(str, available_episodes))}"
            else:
                error_msg = f"Episode {request.episode_number} not found. No episodes are currently available in the manuscript directory."

            logger.warning(error_msg)
            return self._create_response(False, 0.0, [], start_time, error_msg)
        except Exception as e:
            error_msg = f"読みやすさチェックエラー: {e!s}"
            logger.exception(error_msg)
            return self._create_response(False, 0.0, [], start_time, error_msg)

    def _load_episode_content(self, episode_number: int, project_name: str | None) -> str:
        """エピソードファイルの内容を読み込み（基底クラスの共通実装を使用）"""
        return super()._load_episode_content(episode_number, project_name)

    def _get_check_aspects(self, request: ToolRequest) -> list[str]:
        """チェック観点を決定"""
        if request.additional_params and "check_aspects" in request.additional_params:
            return request.additional_params["check_aspects"]

        # デフォルトは全ての観点をチェック
        return ["sentence_length", "vocabulary_complexity", "readability_score"]

    def _get_available_episodes(self) -> list[int]:
        """利用可能なエピソード番号のリストを取得"""
        try:
            path_service = create_path_service()
            get_file_cache_service()
            manuscript_dir = path_service.get_manuscript_dir()

            # エピソードファイルのパターンで検索
            episode_numbers = []

            if manuscript_dir.exists():
                for file_path in manuscript_dir.glob("第*話_*.md"):
                    match = re.search(r"第(\d+)話_", file_path.name)
                    if match:
                        episode_numbers.append(int(match.group(1)))

            return sorted(episode_numbers)
        except Exception:
            return []

    def _convert_findings(
        self,
        findings: list[ReadabilityFinding],
        lines: list[str],
        file_path: Path | None,
        file_hash: str | None,
    ) -> list[ToolIssue]:
        reason_map = {
            "long_sentence": "LONG_SENTENCE",
            "complex_vocabulary": "COMPLEX_VOCABULARY",
            "high_average_sentence_length": "HIGH_AVG_SENTENCE_LENGTH",
        }

        tool_issues: list[ToolIssue] = []
        for finding in findings:
            ln_hash = None
            if finding.line_number and 1 <= finding.line_number <= len(lines):
                line_text = lines[finding.line_number - 1].strip()
                ln_hash = hashlib.sha256(line_text.encode("utf-8")).hexdigest()
            base = f"{file_hash}:{finding.issue_type}:{finding.line_number}:{ln_hash or ''}"
            iid = hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]
            tool_issues.append(
                ToolIssue(
                    type=finding.issue_type,
                    severity=finding.severity,
                    message=finding.message,
                    line_number=finding.line_number,
                    suggestion=finding.suggestion,
                    file_path=str(file_path) if file_path else None,
                    line_hash=ln_hash,
                    reason_code=reason_map.get(finding.issue_type, finding.issue_type.upper()),
                    issue_id=f"readability-{iid}",
                )
                )
        return tool_issues

    def _resolve_episode_content(self, request: ToolRequest) -> tuple[str, Path | None, str | None]:
        ap = request.additional_params or {}
        file_path: Path | None = None

        if isinstance(ap.get("content"), str):
            content = ap.get("content") or ""
            if isinstance(ap.get("file_path"), str):
                candidate = Path(ap["file_path"]).expanduser()
                file_path = candidate if candidate.exists() else None
        elif isinstance(ap.get("file_path"), str):
            candidate = Path(ap["file_path"]).expanduser()
            file_path = candidate if candidate.exists() else None
            content = candidate.read_text(encoding="utf-8") if candidate.exists() else ""
        else:
            content = self._load_episode_content(request.episode_number, request.project_name)
            try:
                path_service = create_path_service()
                cache_service = get_file_cache_service()
                manuscript_dir = path_service.get_manuscript_dir()
                file_path = cache_service.get_episode_file_cached(manuscript_dir, request.episode_number)
                self._ps_collect_fallback(path_service)
            except Exception:
                file_path = None

        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None
        return content, file_path, file_hash
