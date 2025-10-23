"""check_grammar ツールの実装

SPEC-MCP-001: MCP Server Granular Microservice Architecture
"""
import hashlib
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from mcp_servers.noveler.domain.entities.mcp_tool_base import MCPToolBase, ToolIssue, ToolRequest, ToolResponse
from noveler.domain.services.grammar_analysis_service import GrammarAnalysisService
from noveler.domain.value_objects.grammar_finding import GrammarFinding
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.logging.unified_logger import get_logger


class CheckGrammarTool(MCPToolBase):
    """文法チェックツール

    文法・誤字脱字を検出し、修正提案を行う。
    - 誤字脱字
    - 助詞の誤用
    - 表記揺れ
    - 句読点の使い方
    """

    def __init__(self) -> None:
        super().__init__(
            tool_name="check_grammar",
            tool_description="文法・誤字脱字チェック"
        )
        self._analysis_service = GrammarAnalysisService()

    def get_input_schema(self) -> dict[str, Any]:
        """入力スキーマを返す"""
        schema = self._get_common_input_schema()

        # grammar特有のパラメータを追加
        schema["properties"].update({
            "file_path": {
                "type": "string",
                "description": "直接ファイルパス指定（episode_numberより優先）",
            },
            "check_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["typo", "particle_error", "notation_inconsistency", "punctuation"]
                },
                "description": "チェックする文法問題のタイプ（省略時は全て）"
            }
        })

        return schema

    def execute(self, request: ToolRequest | Dict[str, Any]) -> ToolResponse | dict[str, Any]:
        """文法チェックを実行

        レガシー互換性のため、辞書形式で渡されたリクエストも受け付け、
        その場合は辞書形式のレスポンスを返す。
        """
        expects_dict = isinstance(request, dict)
        tool_request = self._coerce_request(request)

        # 統一ロギングシステムを使用
        logger = get_logger(__name__)

        start_time = time.time()
        logger.info("文法チェック開始: エピソード%s", tool_request.episode_number)

        try:
            self._validate_request(tool_request)

            # 直接ファイル指定があれば優先 + パス/ハッシュ
            episode_content, file_path, file_hash = self._resolve_episode_content(tool_request)
            if not episode_content:
                # 空のエピソードの場合は満点を返す
                logger.info("エピソード%sは空のため、満点を返却", tool_request.episode_number)
                response = self._create_response(True, 100.0, [], start_time)
                return self._finalize_response(response, expects_dict)

            # チェックタイプの決定
            check_types = self._get_check_types(tool_request)
            logger.debug("チェックタイプ: %s", check_types)

            analysis_result = self._analysis_service.analyze(episode_content, check_types=check_types)
            issues = self._convert_findings(
                analysis_result.issues,
                episode_content.split("\n"),
                file_path,
                file_hash,
            )
            score = analysis_result.score

            logger.info("文法チェック完了: スコア=%.1f, 問題数=%d", score, len(issues))
            resp = self._create_response(True, score, issues, start_time)
            if file_path:
                resp.metadata["file_path"] = str(file_path)
            if file_hash:
                resp.metadata["file_hash"] = file_hash
            # PathServiceのフォールバック可視化
            self._apply_fallback_metadata(resp)
            return self._finalize_response(resp, expects_dict)

        except FileNotFoundError as e:
            error_msg = f"Episode {tool_request.episode_number} not found"
            logger.exception(error_msg)
            raise ValueError(error_msg) from e
        except Exception:
            logger.exception("文法チェックエラー")
            response = self._create_response(False, 0.0, [], start_time)
            return self._finalize_response(response, expects_dict)

    def _load_episode_content(self, episode_number: int, project_name: str | None) -> str:
        """エピソードファイルの内容を読み込み（基底クラスの共通実装を使用）"""
        return super()._load_episode_content(episode_number, project_name)

    def _get_check_types(self, request: ToolRequest) -> list[str]:
        """チェックタイプを決定"""
        if request.additional_params and "check_types" in request.additional_params:
            return request.additional_params["check_types"]

        # デフォルトは全てのタイプをチェック
        return ["typo", "particle_error", "notation_inconsistency", "punctuation"]

    def _convert_findings(
        self,
        findings: list[GrammarFinding],
        lines: list[str],
        file_path: Path | None,
        file_hash: str | None,
    ) -> list[ToolIssue]:
        reason_map = {
            "typo": "TYPO",
            "particle_error": "PARTICLE_ERROR",
            "notation_inconsistency": "NOTATION_INCONSISTENCY",
            "punctuation": "GRAMMAR_PUNCTUATION",
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
                    issue_id=f"grammar-{iid}",
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
            try:
                content = self._load_episode_content(request.episode_number, request.project_name)
            except FileNotFoundError:
                content = ""
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

    def _coerce_request(self, request: ToolRequest | Dict[str, Any]) -> ToolRequest:
        if isinstance(request, ToolRequest):
            return request
        if isinstance(request, dict):
            episode_number = int(request.get("episode_number", 0) or 0)
            project_name = request.get("project_name")
            additional_params = {
                key: value
                for key, value in request.items()
                if key not in {"episode_number", "project_name"}
            }
            return ToolRequest(
                episode_number=episode_number,
                project_name=project_name,
                additional_params=additional_params or None,
            )
        msg = f"Unsupported request type: {type(request)!r}"
        raise TypeError(msg)

    def _finalize_response(self, response: ToolResponse, as_dict: bool) -> ToolResponse | dict[str, Any]:
        if not as_dict:
            return response

        data = asdict(response)
        data.setdefault("issues", [])
        data.setdefault("metadata", {})
        return data
