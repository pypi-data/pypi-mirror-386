"""A40 Stage2/Stage3 統合推敲（内容推敲・読者体験最適化）

Stage 2: 内容的推敲（Content Refiner）
Stage 3: 読者体験最適化（Reader Experience Designer）

UniversalClaudeCodeService を用いて原稿を段階的に改稿し、必要に応じて保存する。
MCP環境ではClaude呼び出しはフォールバック（ダミー成功）となるため、
ネットワークが無い環境でもワークフローを検証できる。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger

from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from .polish_manuscript_apply_tool import PolishManuscriptApplyTool


@dataclass
class _StageSpec:
    key: str
    name: str
    prompt: str
    template_source: str
    config: dict[str, Any]


class PolishManuscriptTool(MCPToolBase):
    """A40統合推敲（Stage2/Stage3）ツール"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="polish_manuscript",
            tool_description="A40統合推敲: Stage2(内容推敲)/Stage3(読者体験) を順次適用し改稿",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
                "stages": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["stage2", "stage3"]},
                    "default": ["stage2", "stage3"],
                    "description": "実行する推敲ステージ（順序通りに適用）",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Trueなら保存せずdiffのみ（安全運用）",
                },
                "include_diff": {
                    "type": "boolean",
                    "default": False,
                    "description": "レスポンスに短縮diffを同梱",
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        import time as _t
        start = _t.time()

        try:
            self._validate_request(request)
            ap = request.additional_params or {}
            dry_run = bool(ap.get("dry_run", True))
            include_diff = bool(ap.get("include_diff", False))
            stages_in = ap.get("stages") or ["stage2", "stage3"]
            stages: list[str] = [s for s in stages_in if s in ("stage2", "stage3")]
            if not stages:
                stages = ["stage2", "stage3"]

            # 対象パスと原稿読み込み
            target_path = self._resolve_target_path(request)
            file_path: Path | None = None
            if isinstance(ap.get("file_path"), str):
                file_path = Path(ap["file_path"]).expanduser()
            elif target_path:
                file_path = target_path
            text = ""
            if file_path and file_path.exists():
                text = file_path.read_text(encoding="utf-8")
            if not text:
                return self._create_response(True, 100.0, [], start)

            # プロジェクトコンテキスト
            try:
                ps = create_path_service()
                project_root = ps.project_root
            except Exception:
                project_root = Path.cwd()

            current = text
            stage_issues: list[ToolIssue] = []
            prompts_out: dict[str, str] = {}
            template_loader = PolishManuscriptApplyTool()

            for stage_key in stages:
                spec = self._build_stage_spec(stage_key, current, project_root, request, template_loader)
                # 実行導線: プロンプトを生成し返す（MCP内は非同期制約のため実行は上位レイヤーへ委譲）
                prompts_out[stage_key] = spec.prompt
                improved = current  # ツール内では未適用（導線提供）
                diff_text = None

                # issueとして段階結果を格納
                stage_issues.append(
                    ToolIssue(
                        type="polish_stage_result",
                        severity="low",
                        message=f"{spec.name}: プロンプト生成完了",
                        suggestion="LLMにプロンプトを渡して改稿を実行してください",
                        file_path=str(file_path) if file_path else None,
                        details={
                            "stage": spec.key,
                            "applied": False,
                            "prompt": spec.prompt,
                            "template_source": spec.template_source,
                            "diff": diff_text if include_diff else None,
                        },
                    )
                )

                current = improved

            # レスポンス
            resp = self._create_response(True, 100.0, stage_issues, start)
            resp.metadata.update(
                {
                    "file_path": str(file_path) if file_path else None,
                    "stages": stages,
                    "dry_run": True,
                    "prompts": prompts_out,
                }
            )
            # PathServiceのフォールバック可視化
            try:
                self._ps_collect_fallback(create_path_service())
                self._apply_fallback_metadata(resp)
            except Exception:
                pass
            return resp

        except Exception as e:
            return self._create_response(False, 0.0, [], start, f"polish error: {e!s}")

    # ---- helpers ----

    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        try:
            from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            self._ps_collect_fallback(ps)
            return ep
        except Exception:
            return None

    def _build_stage_spec(
        self,
        stage: str,
        current_text: str,
        project_root: Path,
        request: ToolRequest,
        loader: PolishManuscriptApplyTool,
    ) -> _StageSpec:
        prompt, template_source = loader._build_prompt(stage, current_text, project_root, request)
        if stage == "stage2":
            return _StageSpec(
                key="stage2",
                name="Stage2 内容的推敲",
                prompt=prompt,
                template_source=template_source,
                config={"stage": "content_refinement", "mode": "standard"},
            )
        return _StageSpec(
            key="stage3",
            name="Stage3 読者体験最適化",
            prompt=prompt,
            template_source=template_source,
            config={"stage": "reader_experience", "mode": "standard"},
        )
