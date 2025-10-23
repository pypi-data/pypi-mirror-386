"""A40 Stage2/3 一気通貫推敲適用ツール（polish_manuscript_apply）

機能:
 - Stage2/Stage3の統合プロンプトを生成
 - 可能であればLLMを実行して原稿を改稿（MCP環境ではスキップ）
 - 差分を生成し、アーティファクトとして保存
 - 原稿ファイルに適用（dry_run=False時）
 - A41チェックの最終合否レポートをMarkdownで出力
 - すべての生成物を .noveler/artifacts に保存（参照IDで返却）
"""
from __future__ import annotations

import difflib
import json
from pathlib import Path
from textwrap import dedent
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.factories.path_service_factory import is_mcp_environment
from noveler.domain.services.artifact_store_service import create_artifact_store

from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService
from noveler.domain.value_objects.universal_prompt_execution import (
    ProjectContext,
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)

import yaml

from .run_quality_checks_tool import RunQualityChecksTool


POLISH_TEMPLATE_FILES = {
    "stage2": [
        "polish_stage2_content.yaml",
        "stage2_content_refiner.yaml",
        "write_step26_polish_stage2.yaml",
        "stage2_content_refiner.md",
    ],
    "stage3": [
        "polish_stage3_reader.yaml",
        "stage3_reader_experience.yaml",
        "write_step27_polish_stage3.yaml",
        "stage3_reader_experience.md",
    ],
}

POLISH_TEMPLATE_SEARCH_DIRS = (
    Path("templates") / "quality" / "checks",
    Path("templates") / "quality" / "checks" / "backup",
    Path("templates") / "writing",
)

class PolishManuscriptApplyTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="polish_manuscript_apply",
            tool_description="A40統合推敲(Stage2/3)のLLM実行→適用→レポート作成まで自動化",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "対象ファイル（省略時はepisode_numberから推定）",
                },
                "stages": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["stage2", "stage3"]},
                    "default": ["stage2", "stage3"],
                    "description": "実行する推敲ステージ（順序通りに適用）",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Trueなら適用せず、アーティファクトとレポートのみ作成",
                },
                "save_report": {
                    "type": "boolean",
                    "default": True,
                    "description": "A41最終合否レポートをMarkdownで保存",
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
            dry_run = bool(ap.get("dry_run", False))
            stages = [s for s in (ap.get("stages") or ["stage2", "stage3"]) if s in ("stage2", "stage3")]
            if not stages:
                stages = ["stage2", "stage3"]

            # 1) ターゲット解決 + 原稿読込
            fp = self._resolve_target_path(request)
            if isinstance(ap.get("file_path"), str):
                fp = Path(ap["file_path"]).expanduser()
            file_path: Path | None = fp
            content = ""
            if file_path and file_path.exists():
                content = file_path.read_text(encoding="utf-8")
            if not content:
                return self._create_response(True, 100.0, [], start)

            ps = create_path_service()
            project_root = ps.project_root
            store = create_artifact_store(storage_dir=ps.get_noveler_output_dir() / "artifacts")

            # 2) Stage毎にプロンプト生成→LLM実行（可能なら）→適用テキストを更新
            all_prompts: dict[str, str] = {}
            template_sources: dict[str, str] = {}
            improved = content
            for stage in stages:
                prompt, template_source = self._build_prompt(stage, improved, project_root, request)
                template_sources[stage] = template_source
                all_prompts[stage] = prompt
                # プロンプトをアーティファクト保存
                store.create_reference(prompt, alias=f"{stage}_prompt", content_type="text", source_file=str(file_path))

                candidate = self._run_llm(project_root, prompt)
                if candidate is None:
                    # LLM未実行（MCP等）。適用はスキップ
                    continue
                if candidate.strip():
                    improved = candidate

            # 3) 差分の作成・保存 + 改稿本文のアーティファクト化
            diff_text = self._make_diff(content, improved, file_path)
            diff_ref = store.create_reference(diff_text, alias="polish_diff", content_type="text", source_file=str(file_path))
            improved_ref = store.create_reference(
                improved,
                alias="polished_manuscript",
                content_type="text",
                source_file=str(file_path),
                description="A40 Stage2/3 適用後の改稿本文"
            )

            # 4) 適用（dry_runでなければファイルに書き戻し）
            applied = 0
            if not dry_run and file_path:
                if improved != content:
                    file_path.write_text(improved, encoding="utf-8")
                    applied = 1

            # 5) A41最終チェック（run_quality_checks）とレポート
            rq = RunQualityChecksTool()
            rq_res = rq.execute(
                request.__class__(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params={
                        "file_path": str(file_path) if file_path else None,
                        "format": "summary",
                        "severity_threshold": "medium",
                    },
                )
            )
            score = float(rq_res.score)
            passed = bool(score >= 80.0)
            report_md = self._make_a41_report(file_path, stages, score, passed, all_prompts, diff_text)
            report_ref = store.create_reference(report_md, alias="a41_report", content_type="text", source_file=str(file_path))

            # 保存先（品質記録）
            if bool(ap.get("save_report", True)):
                try:
                    qdir = ps.get_quality_records_dir()
                    ep = f"{request.episode_number:03d}"
                    out = qdir / f"A41_ep{ep}.md"
                    out.write_text(report_md, encoding="utf-8")
                except Exception:
                    pass

            # 6) レスポンス整形
            issues = [
                ToolIssue(
                    type="polish_apply_result",
                    severity="low",
                    message=f"Stage2/3 適用{'（dry-run）' if dry_run else ''}",
                    suggestion="必要に応じて再適用",
                    file_path=str(file_path) if file_path else None,
                    details={
                        "applied": applied,
                        "score": score,
                        "passed": passed,
                        "diff_artifact": diff_ref.get("artifact_id"),
                        "improved_artifact": improved_ref.get("artifact_id"),
                        "report_artifact": report_ref.get("artifact_id"),
                        "prompts": all_prompts,
                    },
                )
            ]
            resp = self._create_response(True, score, issues, start)
            resp.metadata.update(
                {
                    "file_path": str(file_path) if file_path else None,
                    "applied": applied,
                    "score": score,
                    "passed": passed,
                    "diff_artifact": diff_ref,
                    "improved_artifact": improved_ref,
                    "report_artifact": report_ref,
                    "template_sources": template_sources,
                }
            )
            # フォールバックメタ
            self._ps_collect_fallback(ps)
            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            logger.error(
                "polish_manuscript_apply実行エラー",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "episode_number": getattr(request, 'episode_number', None),
                    "execution_time_seconds": _t.time() - start
                }
            )
            return self._create_response(False, 0.0, [], start, f"polish_apply error: {e!s}")

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

    def _build_prompt(
        self,
        stage: str,
        manuscript: str,
        project_root: Path,
        request: ToolRequest,
    ) -> tuple[str, str]:
        context = self._build_prompt_context(manuscript, project_root, request)
        template_payload, template_source = self._load_prompt_template(stage, project_root)
        logger = get_logger(__name__)

        try:
            if isinstance(template_payload, dict):
                prompt = self._render_schema_v2_template(template_payload, context, stage)
            else:
                prompt = str(template_payload).format(**context)
        except (KeyError, ValueError) as exc:
            logger.warning(
                "テンプレートのプレースホルダ解決に失敗。内蔵デフォルトを使用",
                extra={
                    "stage": stage,
                    "missing_placeholder": str(exc),
                    "template_source": template_source,
                },
            )
            template_source = "embedded_default"
            prompt = self._embedded_default(stage).format(**context)

        return prompt, template_source

    def _build_prompt_context(
        self,
        manuscript: str,
        project_root: Path,
        request: ToolRequest,
    ) -> dict[str, Any]:
        ap = request.additional_params or {}
        project_title = ap.get("project_title") or request.project_name or project_root.name
        project_genre = ap.get("project_genre") or "ファンタジー"
        try:
            target_word_count = int(ap.get("target_word_count", 10000))
        except Exception:
            target_word_count = 10000

        context: dict[str, Any] = {
            "manuscript": manuscript,
            "project_title": project_title,
            "project_genre": project_genre,
            "target_word_count": target_word_count,
        }

        if request.episode_number:
            context["episode_number"] = f"{request.episode_number:03d}"
        else:
            context["episode_number"] = ""

        return context

    def _load_prompt_template(self, stage: str, project_root: Path) -> tuple[str, str]:
        filenames = POLISH_TEMPLATE_FILES.get(stage) or []
        if isinstance(filenames, str):
            filenames = [filenames]
        if not filenames:
            return self._embedded_default(stage), "embedded_default"

        logger = get_logger(__name__)
        last_error: Exception | None = None

        for relative_dir in POLISH_TEMPLATE_SEARCH_DIRS:
            template_dir = project_root / relative_dir
            for candidate in filenames:
                template_path = template_dir / candidate
                if not template_path.exists():
                    continue
                try:
                    raw = template_path.read_text(encoding="utf-8")
                    size = len(raw.encode("utf-8"))
                    if size < 512 or size > 200_000:
                        raise ValueError("template_size_out_of_bounds")
                    if template_path.suffix.lower() in {".yaml", ".yml"}:
                        template_dict = yaml.safe_load(raw)
                        if isinstance(template_dict, dict):
                            return template_dict, str(template_path)
                        raise ValueError("invalid_template_schema")
                    return raw, str(template_path)
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "テンプレート読み込みに失敗。次候補を探索",
                        extra={
                            "stage": stage,
                            "template_path": str(template_path),
                            "error_type": type(exc).__name__,
                        },
                    )

        logger.warning(
            "テンプレートを検出できず、内蔵デフォルトを使用",
            extra={
                "stage": stage,
                "last_error_type": type(last_error).__name__ if last_error else None,
            },
        )
        return self._embedded_default(stage), "embedded_default"

    def _render_schema_v2_template(self, template: dict[str, Any], context: dict[str, Any], stage: str) -> str:
        """Schema v2テンプレートからLLM向けプロンプト文字列を生成"""

        def _fmt_list(items: list[str]) -> str:
            return "\n".join(f"- {item}" for item in items if item)

        def _fmt_metrics(metrics: list[dict[str, Any]]) -> str:
            rendered: list[str] = []
            for metric in metrics:
                name = metric.get("name", "")
                target = metric.get("target", "")
                method = metric.get("method", "")
                rendered.append(f"- {name}: target={target}, method={method}")
            return "\n".join(rendered)

        role_messages = (template.get("llm_config") or {}).get("role_messages", {})
        system_msg = role_messages.get("system", "").strip()
        user_msg = role_messages.get("user", "").strip()

        prompt_section = template.get("prompt", {})
        main_instruction = prompt_section.get("main_instruction", "")
        formatted_instruction = main_instruction.format(**context)

        constraints = template.get("constraints", {})
        hard_rules = constraints.get("hard_rules", [])
        soft_targets = constraints.get("soft_targets", [])

        tasks = template.get("tasks", {})
        task_bullets = tasks.get("bullets", [])
        task_details = tasks.get("details", [])

        artifacts = template.get("artifacts", {})
        acceptance = template.get("acceptance_criteria", {})
        checklist = acceptance.get("checklist", [])
        metrics = acceptance.get("metrics", [])
        by_task = acceptance.get("by_task", [])

        sections: list[str] = []
        if system_msg:
            sections.append("# System Role\n" + system_msg)
        if user_msg:
            sections.append("# User Instructions\n" + user_msg)
        sections.append("# Main Instruction\n" + formatted_instruction)

        if hard_rules or soft_targets:
            constraint_lines: list[str] = []
            if hard_rules:
                constraint_lines.append("*Hard Rules*\n" + _fmt_list(hard_rules))
            if soft_targets:
                constraint_lines.append("*Soft Targets*\n" + _fmt_list(soft_targets))
            sections.append("# Constraints\n" + "\n\n".join(constraint_lines))

        if task_bullets or task_details:
            details_lines: list[str] = []
            if task_bullets:
                details_lines.append("*Primary Tasks*\n" + _fmt_list(task_bullets))
            for detail in task_details:
                name = detail.get("name", "")
                items = detail.get("items", [])
                lines = _fmt_list([item.get("text", "") for item in items if isinstance(item, dict)])
                if name and lines:
                    details_lines.append(f"*{name}*\n{lines}")
            if details_lines:
                sections.append("# Tasks\n" + "\n\n".join(details_lines))

        if artifacts:
            example_str = artifacts.get("example")
            if isinstance(example_str, dict):
                example_text = json.dumps(example_str, ensure_ascii=False, indent=2)
            else:
                example_text = str(example_str or "")
            art_lines = [
                f"- format: {artifacts.get('format', 'unknown')}",
                f"- required_fields: {', '.join(artifacts.get('required_fields', []))}",
            ]
            if example_text:
                art_lines.append("- example:\n" + example_text.strip())
            sections.append("# Output Specification\n" + "\n".join(art_lines))

        acceptance_lines: list[str] = []
        if checklist:
            acceptance_lines.append("*Checklist*\n" + _fmt_list(checklist))
        if metrics:
            acceptance_lines.append("*Metrics*\n" + _fmt_metrics(metrics))
        if by_task:
            lines = []
            for item in by_task:
                ident = item.get("id")
                field = item.get("field")
                rule = item.get("rule")
                if ident and field:
                    lines.append(f"- {ident}: field={field}, rule={rule}")
            if lines:
                acceptance_lines.append("*By Task*\n" + "\n".join(lines))
        if acceptance_lines:
            sections.append("# Acceptance Criteria\n" + "\n\n".join(acceptance_lines))

        manuscript = context.get("manuscript", "")
        sections.append("# Manuscript\n```markdown\n" + manuscript.rstrip() + "\n```")

        return "\n\n".join(section.strip() for section in sections if section and section.strip()) + "\n"

    def _embedded_default(self, stage: str) -> str:
        if stage == "stage2":
            return dedent(
                """
                あなたは Content Refiner（内容推敲者）です。以下の原稿を対象に、A40_推敲品質ガイドのStage 2（内容的推敲）に従って、
                構成最適化・描写の深化・会話最適化・キャラクター魅力強化を行ってください。

                要件:
                - 構成の最適化（冒頭フック、各シーンの目的、ペース配分）
                - 描写の深化（五感活用、具体化、比喩の適切な活用）
                - 会話の最適化（説明口調の削減、個性の表現、テンポ改善）
                - キャラクター魅力（行動の一貫性、感情変化、成長の可視化）

                参考テンプレ（A38 表現リファレンス・導線）:
                - 冒頭3行フック（3行固定・各行40-60字目安）
                  1) 異常値+即時具体 / 2) 五感×固有名詞×行動 / 3) 行動or選択+賭け金（未解決1つ残す）
                - Scene→Sequel（最小ループ）
                  Scene: goal→conflict→outcome / Sequel: reaction→dilemma→decision
                - 会話ビート抽出（1ターン1情報・機能会話）
                  intent/subtext/tactic/conflict/info_reveal/turn_type を明示し、説明台詞は禁止

                出力形式(JSON):
                {{
                  "manuscript": "推敲後の原稿（Markdown）",
                  "improvements": ["主要改善点1", "主要改善点2", "..."]
                }}

                対象原稿:
                ```markdown
                {manuscript}
                ```
                """
            )

        return dedent(
            """
            あなたは Reader Experience Designer（読者体験設計者）です。以下の原稿を対象に、A40_推敲品質ガイドのStage 3（読者体験最適化）に従って、
            没入感・感情移入・ページターン率の最大化を行ってください。

            要件:
            - スマホ読みやすさ（段落長3-4行、会話前後の改行、シーン転換の空行）
            - 没入感阻害の削除（メタ発言、作者コメント、過度な説明）
            - 没入強化（内面描写の5層化、感情起伏、緊張と緩和のリズム）
            - 離脱率対策（冒頭フック強化、中だるみ圧縮、章末の引き）

            参考テンプレ（A38 表現リファレンス・導線）:
            - 章末クリフハンガー設計
              type(question/reversal/reveal/time_bomb/decision)、unresolved_question、risk_and_stakes、promise_next を設計

            出力形式(JSON):
            {{
              "manuscript": "最終推敲版（Markdown）",
              "improvements": ["体験改善点1", "体験改善点2", "..."]
            }}

            対象原稿:
            ```markdown
            {manuscript}
            ```
            """
        )


    def _run_llm(self, project_root: Path, prompt: str) -> str | None:
        """LLM実行（UniversalLLMUseCase統合版）

        SPEC-LLM-001準拠: UniversalLLMUseCaseによる統一実行
        MCP環境でも自動フォールバック機能により100%動作保証

        v3.0.0: deprecated force_llmパラメータを削除。
        統一設定により適切な環境対応が自動的に行われます。
        """
        logger = get_logger(__name__)

        try:
            import asyncio
            from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
            from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService

            # サービス＆ユースケース初期化
            claude_service = UniversalClaudeCodeService()
            use_case = UniversalLLMUseCase(claude_service)

            request = UniversalPromptRequest(
                prompt_content=prompt,
                prompt_type=PromptType.WRITING,
                project_context=ProjectContext(project_root=project_root),
                output_format="json",
                max_turns=3,
            )

            # 同期実行：イベントループの競合を回避してフォールバック自動適用
            try:
                # 既存のイベントループがある場合、別スレッドで実行
                loop = asyncio.get_running_loop()
                response = self._run_async_in_thread(use_case, request)
            except RuntimeError:
                # イベントループがない場合
                response = asyncio.run(use_case.execute_with_fallback(request, fallback_enabled=True))

            if response.is_success():
                is_fallback_mode = False
                try:
                    if response.get_metadata_value("mode") == "fallback":
                        is_fallback_mode = True
                except AttributeError:
                    # metadata accessorが未定義の場合は直接辞書を参照
                    meta = getattr(response, "metadata", {}) or {}
                    is_fallback_mode = meta.get("mode") == "fallback"

                if not is_fallback_mode:
                    extracted = getattr(response, "extracted_data", {}) or {}
                    is_fallback_mode = bool(extracted.get("fallback_mode"))

                if is_fallback_mode:
                    logger.info(
                        "LLMフォールバック検出: 改稿適用をスキップ",
                        extra={
                            "execution_method": "universal_llm_use_case",
                            "fallback_mode": True,
                            "is_mcp_environment": is_mcp_environment(),
                        },
                    )
                    return None

                content = response.get_writing_content()
                logger.info(
                    "LLM実行成功",
                    extra={
                        "execution_method": "universal_llm_use_case",
                        "is_mcp_environment": is_mcp_environment(),
                        "response_length": len(content) if content else 0
                    }
                )
                return content
            else:
                logger.warning(
                    "LLM実行失敗: レスポンス不正",
                    extra={
                        "response_status": "failure",
                        "is_mcp_environment": is_mcp_environment()
                    }
                )
                return None

        except Exception as e:
            logger.error(
                "LLM実行エラー",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "is_mcp_environment": is_mcp_environment(),
                    "project_root": str(project_root)
                }
            )
            return None

    def _run_async_in_thread(self, use_case, request):
        """別スレッドでの非同期実行（イベントループ競合回避）

        既存のイベントループがある環境での統一LLM実行
        """
        import threading
        import asyncio

        result: dict[str, any] = {}
        error: list[Exception] = []

        def _worker() -> None:
            try:
                # 新しいイベントループで実行
                response = asyncio.run(use_case.execute_with_fallback(request, fallback_enabled=True))
                result["response"] = response
            except Exception as exc:
                error.append(exc)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join(timeout=300)  # 5分でタイムアウト

        if error:
            logger = get_logger(__name__)
            logger.error(f"スレッド実行エラー: {error[0]}")
            from noveler.domain.value_objects.universal_prompt_execution import UniversalPromptResponse, PromptType
            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=PromptType.WRITING,
                execution_time_ms=0,
                error_message=f"スレッド実行エラー: {error[0]}"
            )

        response = result.get("response")
        if response is None:
            logger = get_logger(__name__)
            logger.error("スレッド実行タイムアウト")
            from noveler.domain.value_objects.universal_prompt_execution import UniversalPromptResponse, PromptType
            return UniversalPromptResponse(
                success=False,
                response_content="",
                extracted_data={},
                prompt_type=PromptType.WRITING,
                execution_time_ms=300000,
                error_message="スレッド実行タイムアウト（300秒）"
            )

        return response

    # レガシーメソッド削除済み（SPEC-LLM-001：UniversalLLMUseCaseに完全統合）
    # Phase 1完了: 統一LLM実行パターンに統合、MCP環境100%対応
    # Phase 2完了: イベントループ競合回避の統一スレッド処理に統合

    def _make_diff(self, before: str, after: str, path: Path | None) -> str:
        if before == after:
            return ""
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path) if path else "before",
            tofile=str(path) if path else "after",
        )
        return "".join(list(diff))

    def _make_a41_report(
        self,
        file_path: Path | None,
        stages: list[str],
        score: float,
        passed: bool,
        prompts: dict[str, str],
        diff_text: str,
    ) -> str:
        p = "\n".join([f"- {k}: {('あり' if v else 'なし')}" for k, v in [("stage2", prompts.get("stage2")), ("stage3", prompts.get("stage3"))]])
        return (
            f"# A41 最終合否レポート\n\n"
            f"対象: {file_path}\n\n"
            f"## 実行サマリー\n\n"
            f"- 実行ステージ: {', '.join(stages)}\n"
            f"- 最終スコア: {score:.1f}\n"
            f"- 合否: {'合格' if passed else '不合格'}\n\n"
            f"## 適用状況\n\n{p}\n\n"
            f"## 差分（要約）\n\n````diff\n{diff_text[:4000]}\n````\n"
        )
