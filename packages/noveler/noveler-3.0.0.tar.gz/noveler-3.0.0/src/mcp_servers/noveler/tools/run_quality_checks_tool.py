"""run_quality_checks ツールの実装

複数アスペクト（リズム/読みやすさ/文法）の統合チェックを実行し、
安定識別子・ハッシュ・理由コードを付与した統一スキーマで返す。

B20補足: ページネーション(page/page_size)、フォーマットsummary、
安全な既定上限(200件)およびNDJSONのページ範囲限定同梱に対応。
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Iterable

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
import json as _json
try:
    import yaml as _yaml
except Exception:  # pragma: no cover
    _yaml = None

from .check_rhythm_tool import CheckRhythmTool
from .check_readability_tool import CheckReadabilityTool
from .check_grammar_tool import CheckGrammarTool
from .check_style_tool import CheckStyleTool


class RunQualityChecksTool(MCPToolBase):
    """統合品質チェックツール"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="run_quality_checks",
            tool_description="統合品質チェック（rhythm/readability/grammar）",
        )
        # フォールバックイベントは基底クラスの共通バッファを使用

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
                "aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["rhythm", "readability", "grammar", "style"],
                    "description": "実行するアスペクト（例: rhythm/readability/grammar）",
                },
                "exclude_dialogue_lines": {
                    "type": "boolean",
                    "default": False,
                    "description": "readability の文長チェックから会話行（「…」/『…』）を除外",
                },
                "preset": {
                    "type": "string",
                    "enum": ["narou", "custom"],
                    "default": "narou",
                    "description": "閾値プリセット（rhythmで使用）",
                },
                "thresholds": {
                    "type": "object",
                    "description": "カスタム閾値（preset='custom'時）",
                },
                "severity_threshold": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "low",
                    "description": "この重要度未満の問題を除外",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "ndjson", "summary"],
                    "default": "json",
                    "description": "出力フォーマット（summaryは要約のみ、ndjsonは同梱メタにページ分のみ）",
                },
                "weights": {
                    "type": "object",
                    "description": "アスペクト重み（例: {rhythm:0.35, readability:0.35, grammar:0.2, style:0.1}）。指定時は重み付き平均で総合スコア算出",
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "reason_codes": {"type": "array", "items": {"type": "string"}},
                        "types": {"type": "array", "items": {"type": "string"}},
                        "text_contains": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "description": "追加フィルタ（理由コード/タイプ/部分一致/件数制限）",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["line_number", "severity", "reason_code", "type"],
                    "description": "ソートキー",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "asc",
                    "description": "ソート順",
                },
                # 追加: ページネーション（B20: 段階的取得）
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "取得ページ（1始まり）。page_size指定時に有効",
                },
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 2000,
                    "description": "1ページあたりの件数（指定がなければ既定の安全上限を適用）",
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start = time.time()

        # 外部境界: MCPツール実行開始
        logger.info(
            "run_quality_checks実行開始",
            extra={
                "tool": "run_quality_checks",
                "episode_number": request.episode_number,
                "project_name": request.project_name,
                "request_id": getattr(request, 'request_id', 'unknown')
            }
        )

        try:
            self._validate_request(request)
            # 設定ロード（.novelerrc / ignore）
            base_ap = request.additional_params or {}
            cfg = self._load_config_overrides()
            ap = {**cfg.get("defaults", {}), **base_ap}

            # 対象ファイルと内容
            file_path = self._resolve_target_path(request)

            logger.debug(
                "ファイルパス解決結果",
                extra={
                    "file_path": str(file_path) if file_path else None,
                    "exists": file_path.exists() if file_path else False
                }
            )

            # ファイルが存在しない場合はエラーを返す
            if not file_path or not file_path.exists():
                logger.warning(
                    "ファイルが存在しないまたはパスが無効",
                    extra={"file_path": str(file_path) if file_path else None}
                )
                error_msg = f"ファイルが見つかりません: {file_path}。A38パターンを参照してください。"
                response = self._create_response(False, 0.0, [], start, error_message=error_msg)
                response.metadata["file_path"] = str(file_path) if file_path else None
                return response

            try:
                from noveler.infrastructure.caching.file_cache_service import read_text_cached
                text = read_text_cached(file_path)
                logger.debug("ファイル読み込み成功（キャッシュ使用）")
            except Exception as e:
                text = file_path.read_text(encoding="utf-8")
                logger.warning(
                    "キャッシュ読み込み失敗、直接読み込みでフォールバック",
                    extra={"cache_error": str(e)}
                )

            lines = text.split("\n") if text else []
            file_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None

            logger.info(
                "ファイル解析完了",
                extra={
                    "content_length": len(text),
                    "line_count": len(lines),
                    "file_hash": file_hash[:8] + "..." if file_hash else None
                }
            )

            aspects = set(ap.get("aspects") or ["rhythm", "readability", "grammar", "style"])
            all_issues: list[ToolIssue] = []
            aspect_scores: dict[str, float] = {}

            logger.info(
                "品質チェック実行設定",
                extra={
                    "aspects": list(aspects),
                    "severity_threshold": ap.get("severity_threshold", "low"),
                    "format": ap.get("format", "json"),
                    "preset": ap.get("preset", "narou")
                }
            )

            # rhythm
            if "rhythm" in aspects:
                logger.debug("rhythmチェック開始")
                rhythm_start = time.time()

                rhythm_req = ToolRequest(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params={
                        **ap,
                        "file_path": str(file_path) if file_path else ap.get("file_path"),
                        "content": text,
                    },
                )
                rhythm_tool = CheckRhythmTool()
                rhythm_res = rhythm_tool.execute(rhythm_req)
                rhythm_time = time.time() - rhythm_start

                aspect_scores["rhythm"] = rhythm_res.score
                rhythm_issues = self._normalize_issues(
                    rhythm_res.issues, lines, file_path, file_hash, source_aspect="rhythm"
                )
                all_issues.extend(rhythm_issues)

                logger.info(
                    "rhythmチェック完了",
                    extra={
                        "score": rhythm_res.score,
                        "issues_count": len(rhythm_issues),
                        "execution_time_seconds": rhythm_time
                    }
                )

            # readability
            if "readability" in aspects:
                logger.debug("readabilityチェック開始")
                read_start = time.time()

                read_req = ToolRequest(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params={
                        **({"check_aspects": [
                            "sentence_length",
                            "vocabulary_complexity",
                            "readability_score",
                        ]}),
                        "file_path": str(file_path) if file_path else ap.get("file_path"),
                        "content": text,
                        "exclude_dialogue_lines": ap.get("exclude_dialogue_lines", False),
                    },
                )
                read_tool = CheckReadabilityTool()
                read_res = read_tool.execute(read_req)
                read_time = time.time() - read_start

                aspect_scores["readability"] = read_res.score
                read_issues = self._normalize_issues(
                    read_res.issues, lines, file_path, file_hash, source_aspect="readability"
                )
                all_issues.extend(read_issues)

                logger.info(
                    "readabilityチェック完了",
                    extra={
                        "score": read_res.score,
                        "issues_count": len(read_issues),
                        "execution_time_seconds": read_time,
                        "exclude_dialogue": ap.get("exclude_dialogue_lines", False)
                    }
                )

            # grammar
            if "grammar" in aspects:
                logger.debug("grammarチェック開始")
                gram_start = time.time()

                gram_req = ToolRequest(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params={
                        "file_path": str(file_path) if file_path else ap.get("file_path"),
                        "content": text,
                    },
                )
                gram_tool = CheckGrammarTool()
                gram_res = gram_tool.execute(gram_req)
                gram_time = time.time() - gram_start

                aspect_scores["grammar"] = gram_res.score
                gram_issues = self._normalize_issues(
                    gram_res.issues, lines, file_path, file_hash, source_aspect="grammar"
                )
                all_issues.extend(gram_issues)

                logger.info(
                    "grammarチェック完了",
                    extra={
                        "score": gram_res.score,
                        "issues_count": len(gram_issues),
                        "execution_time_seconds": gram_time
                    }
                )

            # style
            if "style" in aspects:
                logger.debug("styleチェック開始")
                style_start = time.time()

                sty_req = ToolRequest(
                    episode_number=request.episode_number,
                    project_name=request.project_name,
                    additional_params={
                        "file_path": str(file_path) if file_path else ap.get("file_path"),
                        "content": text,
                    },
                )
                sty_tool = CheckStyleTool()
                sty_res = sty_tool.execute(sty_req)
                style_time = time.time() - style_start

                aspect_scores["style"] = sty_res.score
                style_issues = self._normalize_issues(
                    sty_res.issues, lines, file_path, file_hash, source_aspect="style"
                )
                all_issues.extend(style_issues)

                logger.info(
                    "styleチェック完了",
                    extra={
                        "score": sty_res.score,
                        "issues_count": len(style_issues),
                        "execution_time_seconds": style_time
                    }
                )

            # 既知抑止（ignore）
            ignore = cfg.get("ignore", {})
            ignore_ids = set(ignore.get("issue_ids") or [])
            ignore_codes = set(ignore.get("reason_codes") or [])

            # severity filter
            logger.debug(
                "フィルタリング開始",
                extra={
                    "total_raw_issues": len(all_issues),
                    "ignore_ids_count": len(ignore_ids),
                    "ignore_codes_count": len(ignore_codes)
                }
            )

            sev_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            thr = sev_order.get(str(ap.get("severity_threshold", "low")).lower(), 1)
            filtered = [
                i
                for i in all_issues
                if (sev_order.get(i.severity, 1) >= thr)
                and (getattr(i, "issue_id", None) not in ignore_ids)
                and (getattr(i, "reason_code", i.type) not in ignore_codes)
            ]

            logger.debug(
                "重要度フィルタ適用後",
                extra={
                    "severity_threshold": ap.get("severity_threshold", "low"),
                    "filtered_count": len(filtered)
                }
            )

            # additional filters
            flt = ap.get("filters") or {}
            rcodes = set(flt.get("reason_codes") or [])
            if rcodes:
                filtered = [i for i in filtered if (getattr(i, "reason_code", i.type) in rcodes)]
            tps = set(flt.get("types") or [])
            if tps:
                filtered = [i for i in filtered if i.type in tps]
            contains = flt.get("text_contains")
            if isinstance(contains, str) and contains:
                filtered = [i for i in filtered if contains in (i.message or "")]

            # 重複抑止（同一箇所・同一理由を集約）
            filtered = self._deduplicate_issues(filtered)

            # sorting
            sort_by = ap.get("sort_by")
            sort_order = str(ap.get("sort_order", "asc"))
            reverse = sort_order == "desc"
            if sort_by == "line_number":
                filtered.sort(key=lambda i: (i.line_number if i.line_number is not None else 10**9), reverse=reverse)
            elif sort_by == "severity":
                filtered.sort(key=lambda i: sev_order.get(i.severity, 0), reverse=reverse)
            elif sort_by == "reason_code":
                filtered.sort(key=lambda i: getattr(i, "reason_code", i.type) or "", reverse=reverse)
            elif sort_by == "type":
                filtered.sort(key=lambda i: i.type or "", reverse=reverse)

            # limit（明示指定）
            limit = flt.get("limit")
            # ページネーション（page_size優先）
            page = ap.get("page")
            page_size = ap.get("page_size")
            total_issues = len(filtered)
            pagination_applied = False
            if isinstance(page_size, int) and page_size > 0:
                p = int(page) if isinstance(page, int) and page >= 1 else 1
                start_idx = (p - 1) * page_size
                end_idx = max(start_idx, min(start_idx + page_size, total_issues))
                filtered = filtered[start_idx:end_idx]
                pagination_applied = True
            elif isinstance(limit, int) and limit > 0:
                filtered = filtered[:limit]
            else:
                # 既定の安全上限（レスポンス肥大化防止）
                DEFAULT_MAX = 200
                if len(filtered) > DEFAULT_MAX:
                    filtered = filtered[:DEFAULT_MAX]
                    pagination_applied = True
                    page = 1
                    page_size = DEFAULT_MAX

            # スコアは既定で各アスペクトの最小値。weights指定時は重み付き平均
            score_method = "min"
            overall_score = min(aspect_scores.values()) if aspect_scores else 100.0
            weights = ap.get("weights") if isinstance(ap.get("weights"), dict) else None
            if weights and aspect_scores:
                total_w = 0.0
                acc = 0.0
                for k, v in aspect_scores.items():
                    w = float(weights.get(k, 0.0))
                    if w <= 0:
                        continue
                    acc += w * float(v)
                    total_w += w
                if total_w > 0:
                    overall_score = acc / total_w
                    score_method = "weighted_average"

            # 先頭にサマリーを追加
            summary = self._make_summary(lines, filtered)
            filtered.insert(
                0,
                ToolIssue(
                    type="summary_metrics",
                    severity="low",
                    message=(
                        f"行数:{summary['lines']} / 文数:{summary['sentences']} / 会話比率:{summary['dialogue_ratio']*100:.1f}% / "
                        f"最長行:{summary['longest_line']} / 問題:{summary['issue_count']}"
                    ),
                    line_number=None,
                    suggestion=None,
                    file_path=str(file_path) if file_path else None,
                    reason_code="SUMMARY",
                    details={"metrics": summary, "aspect_scores": aspect_scores},
                ),
            )

            # format==summary の場合は要約のみ返す（問題詳細は省略）
            fmt = str(ap.get("format", "json"))
            if fmt == "summary":
                issues_out = [
                    ToolIssue(
                        type="summary_metrics",
                        severity="low",
                        message=(
                            f"行数:{summary['lines']} / 文数:{summary['sentences']} / 会話比率:{summary['dialogue_ratio']*100:.1f}% / "
                            f"最長行:{summary['longest_line']} / 問題:{summary['issue_count']}"
                        ),
                        line_number=None,
                        suggestion=None,
                        file_path=str(file_path) if file_path else None,
                        reason_code="SUMMARY",
                        details={"metrics": summary, "aspect_scores": aspect_scores},
                    )
                ]
            else:
                issues_out = filtered

            execution_time = time.time() - start

            logger.info(
                "run_quality_checks実行完了",
                extra={
                    "execution_time_seconds": execution_time,
                    "overall_score": overall_score,
                    "aspect_scores": aspect_scores,
                    "total_issues_found": total_issues,
                    "returned_issues": len(issues_out),
                    "score_method": score_method,
                    "aspects_executed": list(aspects)
                }
            )

            resp = self._create_response(True, overall_score, issues_out, start)
            # 追加メタ
            resp.metadata.update(
                {
                    "file_path": str(file_path) if file_path else None,
                    "file_hash": file_hash,
                    "aspect_scores": aspect_scores,
                    "total_issues": total_issues,
                    "returned_issues": len(issues_out),
                    "score_method": score_method,
                }
            )
            if pagination_applied:
                resp.metadata.update(
                    {
                        "pagination": {
                            "page": int(page) if isinstance(page, int) and page >= 1 else 1,
                            "page_size": int(page_size) if isinstance(page_size, int) and page_size > 0 else len(issues_out),
                            "total": int(total_issues),
                        },
                        "truncated": True,
                    }
                )
            # Gate B (Quality Thresholds) evaluation
            gate_thresholds = ap.get("gate_thresholds", {})
            gate_b_pass = True
            gate_b_evaluation = {}

            if gate_thresholds:
                for aspect_name, threshold in gate_thresholds.items():
                    score = aspect_scores.get(aspect_name, 0.0)
                    aspect_pass = score >= threshold
                    gate_b_pass = gate_b_pass and aspect_pass

                    gate_b_evaluation[aspect_name] = {
                        "required": threshold,
                        "actual": score,
                        "pass": aspect_pass,
                    }

            resp.metadata["gate_b_pass"] = gate_b_pass
            resp.metadata["gate_b_evaluation"] = gate_b_evaluation
            resp.metadata["gate_b_should_fail"] = not gate_b_pass

            # Gate C (Editorial Checklist) evaluation - conditional
            gate_c_result = None
            if ap.get("enable_gate_c"):
                gate_c_result = self._check_gate_c_status(ap)  # Pass additional_params to _check_gate_c_status
                if gate_c_result:
                    resp.metadata["gate_c_pass"] = gate_c_result.get("gate_c_pass")
                    resp.metadata["gate_c_should_fail"] = gate_c_result.get("gate_c_should_fail", False)
                    resp.metadata["gate_c_counts"] = gate_c_result.get("gate_c_counts", {})
                    resp.metadata["gate_c_counts_by_status"] = gate_c_result.get("gate_c_counts_by_status", {})
                    if "gate_c_error" in gate_c_result:
                        resp.metadata["gate_c_error"] = gate_c_result["gate_c_error"]
            else:
                resp.metadata["gate_c_pass"] = None
                resp.metadata["gate_c_should_fail"] = False

            # Aggregate should_fail across all gates
            should_fail = resp.metadata.get("gate_b_should_fail", False) or resp.metadata.get("gate_c_should_fail", False)
            resp.metadata["should_fail"] = should_fail

            # fail_on条件評価
            fail_meta = self._evaluate_fail_on(ap.get("fail_on"), filtered, overall_score, sev_order)
            if fail_meta:
                # Preserve gate failures when merging fail_on results
                fail_on_should_fail = fail_meta.get("should_fail", False)
                resp.metadata.update(fail_meta)
                resp.metadata["should_fail"] = should_fail or fail_on_should_fail
            # ndjson出力要求があればメタに同梱
            if fmt == "ndjson":
                def issue_to_dict(it):
                    return {
                        "type": it.type,
                        "severity": it.severity,
                        "message": it.message,
                        "line_number": it.line_number,
                        "end_line_number": getattr(it, "end_line_number", None),
                        "file_path": getattr(it, "file_path", None) or (str(file_path) if file_path else None),
                        "line_hash": getattr(it, "line_hash", None),
                        "block_hash": getattr(it, "block_hash", None),
                        "reason_code": getattr(it, "reason_code", None),
                        "details": getattr(it, "details", None),
                        "issue_id": getattr(it, "issue_id", None),
                    }
                # 注意: ndjsonはページ・上限適用後の範囲のみを同梱（全件はページングで取得）
                ndjson = "\n".join(_json.dumps(issue_to_dict(i), ensure_ascii=False) for i in issues_out) + ("\n" if issues_out else "")
                resp.metadata["ndjson"] = ndjson
                resp.metadata["ndjson_count"] = len(issues_out)
            # PathServiceのフォールバック可視化をメタに付加（共通ヘルパ）
            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            logger.error(
                "run_quality_checks実行エラー",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "episode_number": request.episode_number,
                    "project_name": request.project_name,
                    "execution_time_seconds": time.time() - start
                }
            )
            return self._create_response(False, 0.0, [], start, f"統合チェックエラー: {e!s}")

    # ---- helpers ----

    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        # episodeから推定
        try:
            from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            # フォールバックイベント収集（共通ヘルパ）
            self._ps_collect_fallback(ps)
            return ep
        except Exception:
            return None

    def _normalize_issues(
        self,
        issues: Iterable[ToolIssue],
        lines: list[str],
        file_path: Path | None,
        file_hash: str | None,
        *,
        source_aspect: str | None = None,
    ) -> list[ToolIssue]:
        """不足フィールド（reason_code/line_hash/issue_id等）を補完"""
        out: list[ToolIssue] = []
        for it in issues:
            if it.type == "summary_metrics":
                # 内部ツールのサマリーは統合側で再生成するため除外
                continue
            reason = it.reason_code or self._infer_reason_code(it.type)
            line_hash = it.line_hash
            if line_hash is None and it.line_number and 1 <= it.line_number <= len(lines):
                line_text = lines[it.line_number - 1].strip()
                line_hash = hashlib.sha256(line_text.encode("utf-8")).hexdigest()

            # 範囲のハッシュ（無ければスキップ）
            block_hash = it.block_hash
            if block_hash is None and it.line_number and it.end_line_number and 1 <= it.line_number <= len(lines):
                s = it.line_number - 1
                e = min(it.end_line_number, len(lines))
                block_text = "\n".join(lines[s:e])
                block_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()

            issue_id = it.issue_id
            if issue_id is None:
                base = f"{file_hash}:{it.type}:{it.line_number}:{line_hash or ''}:{(block_hash or '')}"
                issue_id = hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]
                issue_id = f"quality-{issue_id}"

            # detailsへソースアスペクトを記録（重複集約時の情報源）
            det = getattr(it, "details", None)
            if source_aspect:
                try:
                    if det is None:
                        det = {"source_aspect": source_aspect}
                    elif isinstance(det, dict):
                        if "aspects" in det and isinstance(det["aspects"], list):
                            if source_aspect not in det["aspects"]:
                                det["aspects"].append(source_aspect)
                        elif "source_aspect" in det and det["source_aspect"] != source_aspect:
                            prev = det.pop("source_aspect")
                            det["aspects"] = sorted(set([prev, source_aspect]))
                        else:
                            det["source_aspect"] = source_aspect
                except Exception:
                    pass

            out.append(
                ToolIssue(
                    type=it.type,
                    severity=it.severity,
                    message=it.message,
                    line_number=it.line_number,
                    suggestion=it.suggestion,
                    end_line_number=getattr(it, "end_line_number", None),
                    file_path=str(file_path) if file_path else getattr(it, "file_path", None),
                    line_hash=line_hash,
                    block_hash=block_hash,
                    reason_code=reason,
                    details=det,
                    issue_id=issue_id,
                )
            )
        return out

    def _deduplicate_issues(self, issues: list[ToolIssue]) -> list[ToolIssue]:
        """同一箇所・同一理由の問題を集約し、severityは最大を採用する。

        キー: (reason_code/type, line_hash or block_hash or span, file_path)
        details.aspects に検出元アスペクトを集合で記録。
        """
        if not issues:
            return issues
        sev_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        merged: dict[tuple, ToolIssue] = {}
        for it in issues:
            key = (
                getattr(it, "reason_code", None) or it.type,
                getattr(it, "line_hash", None) or getattr(it, "block_hash", None) or f"L{getattr(it,'line_number',None)}-{getattr(it,'end_line_number',None)}",
                getattr(it, "file_path", None),
            )
            if key not in merged:
                # details正規化: aspects集合
                det = getattr(it, "details", None)
                if isinstance(det, dict):
                    aspects = set()
                    if "aspects" in det and isinstance(det["aspects"], list):
                        aspects.update(det["aspects"])
                    if "source_aspect" in det:
                        aspects.add(det.get("source_aspect"))  # type: ignore[arg-type]
                        det.pop("source_aspect", None)
                    if aspects:
                        det["aspects"] = sorted(a for a in aspects if a)
                merged[key] = it
            else:
                cur = merged[key]
                # 最大severityを採用
                try:
                    if sev_rank.get(it.severity, 0) > sev_rank.get(cur.severity, 0):
                        cur = ToolIssue(
                            type=cur.type,
                            severity=it.severity,
                            message=cur.message,
                            line_number=cur.line_number,
                            suggestion=cur.suggestion,
                            end_line_number=getattr(cur, "end_line_number", None),
                            file_path=getattr(cur, "file_path", None),
                            line_hash=getattr(cur, "line_hash", None),
                            block_hash=getattr(cur, "block_hash", None),
                            reason_code=getattr(cur, "reason_code", None),
                            details=getattr(cur, "details", None),
                            issue_id=getattr(cur, "issue_id", None),
                        )
                        merged[key] = cur
                except Exception:
                    pass
                # details.aspects を統合
                try:
                    d1 = getattr(merged[key], "details", None)
                    d2 = getattr(it, "details", None)
                    aspects = set()
                    if isinstance(d1, dict) and "aspects" in d1 and isinstance(d1["aspects"], list):
                        aspects.update(d1["aspects"])
                    if isinstance(d1, dict) and "source_aspect" in d1:
                        aspects.add(d1.get("source_aspect"))  # type: ignore[arg-type]
                        d1.pop("source_aspect", None)
                    if isinstance(d2, dict) and "aspects" in d2 and isinstance(d2["aspects"], list):
                        aspects.update(d2["aspects"])
                    if isinstance(d2, dict) and "source_aspect" in d2:
                        aspects.add(d2.get("source_aspect"))  # type: ignore[arg-type]
                    if not isinstance(d1, dict):
                        d1 = {}
                    if aspects:
                        d1["aspects"] = sorted(a for a in aspects if a)
                    merged[key] = ToolIssue(
                        type=getattr(merged[key], "type"),
                        severity=getattr(merged[key], "severity"),
                        message=getattr(merged[key], "message"),
                        line_number=getattr(merged[key], "line_number"),
                        suggestion=getattr(merged[key], "suggestion"),
                        end_line_number=getattr(merged[key], "end_line_number", None),
                        file_path=getattr(merged[key], "file_path", None),
                        line_hash=getattr(merged[key], "line_hash", None),
                        block_hash=getattr(merged[key], "block_hash", None),
                        reason_code=getattr(merged[key], "reason_code", None),
                        details=d1,
                        issue_id=getattr(merged[key], "issue_id", None),
                    )
                except Exception:
                    pass
        return list(merged.values())

    def _infer_reason_code(self, typ: str) -> str:
        mapping = {
            # rhythm
            "consecutive_long_sentences": "CONSECUTIVE_LONG_SENTENCES",
            "consecutive_short_sentences": "CONSECUTIVE_SHORT_SENTENCES",
            "dialogue_ratio_out_of_range": "DIALOGUE_RATIO_OUT_OF_RANGE",
            "ending_repetition": "ENDING_REPETITION",
            "ellipsis_style": "ELLIPSIS_STYLE",
            "ellipsis_odd_count": "ELLIPSIS_ODD_COUNT",
            "dash_style": "DASH_STYLE",
            "comma_avg_out_of_range": "COMMA_AVG_OUT_OF_RANGE",
            "comma_overuse": "COMMA_OVERUSE",
            # readability
            "long_sentence": "LONG_SENTENCE",
            "complex_vocabulary": "COMPLEX_VOCABULARY",
            "high_average_sentence_length": "HIGH_AVG_SENTENCE_LENGTH",
            # grammar
            "typo": "TYPO",
            "particle_error": "PARTICLE_ERROR",
            "notation_inconsistency": "NOTATION_INCONSISTENCY",
            "punctuation": "GRAMMAR_PUNCTUATION",
            # summary
            "summary_metrics": "SUMMARY",
        }
        return mapping.get(typ, typ.upper())

    def _make_summary(self, lines: list[str], issues: list[ToolIssue]) -> dict[str, Any]:
        # 文数と会話比率のみ簡易算出
        text = "\n".join(lines)
        sentences = [s for s in text.replace("\n", "").split("。") if s.strip()]
        non_empty = [ln for ln in lines if ln.strip()]
        dialogue_lines = [ln for ln in non_empty if ("「" in ln and "」" in ln)]
        longest_line = max((len(ln.rstrip("\n")) for ln in non_empty), default=0)
        return {
            "lines": len(non_empty),
            "sentences": len(sentences),
            "dialogue_ratio": (len(dialogue_lines) / max(len(non_empty), 1)) if non_empty else 0.0,
            "longest_line": longest_line,
            "issue_count": len(issues),
            "issue_types": sorted({it.type for it in issues}),
        }

    def _load_config_overrides(self) -> dict[str, Any]:
        """プロジェクト設定（.novelerrc.* と .noveler/quality_ignore.json）を読み込み"""
        try:
            ps = create_path_service()
            root = ps.project_root
            # フォールバックイベント収集（共通ヘルパ）
            self._ps_collect_fallback(ps)
            # .novelerrc（yaml/json）
            cfg: dict[str, Any] = {"defaults": {}, "ignore": {}}
            for name in [".novelerrc.yaml", ".novelerrc.yml", ".novelerrc.json"]:
                p = root / name
                if p.exists():
                    try:
                        if p.suffix in (".yaml", ".yml") and _yaml is not None:
                            data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                        else:
                            data = _json.loads(p.read_text(encoding="utf-8"))
                        # 期待キー: defaults(aspects/preset/thresholds...), ignore(issue_ids/reason_codes)
                        if isinstance(data, dict):
                            cfg["defaults"].update(data.get("defaults", {}))
                            if "ignore" in data and isinstance(data["ignore"], dict):
                                cfg["ignore"].update(data["ignore"])
                    except Exception:
                        continue
            # quality_ignore.json（優先）
            ign = root / ".noveler" / "quality_ignore.json"
            if ign.exists():
                try:
                    data = _json.loads(ign.read_text(encoding="utf-8")) or {}
                    if isinstance(data, dict):
                        cfg["ignore"].update(data)
                except Exception:
                    pass
            return cfg
        except Exception:
            return {"defaults": {}, "ignore": {}}

    def _evaluate_fail_on(self, fail_on: Any, issues: list[ToolIssue], score: float, sev_order: dict[str, int]) -> dict[str, Any] | None:
        if not isinstance(fail_on, dict):
            return None
        violations: list[str] = []
        # score_below
        sb = fail_on.get("score_below")
        if isinstance(sb, (int, float)) and score < sb:
            violations.append(f"score<{sb}")
        # severity_at_least
        sal = fail_on.get("severity_at_least")
        if isinstance(sal, str):
            thr = sev_order.get(sal.lower(), 999)
            if any(sev_order.get(i.severity, 0) >= thr for i in issues):
                violations.append(f"severity>={sal}")
        # reason_codes
        rcs = set(fail_on.get("reason_codes") or [])
        if rcs:
            if any(getattr(i, "reason_code", i.type) in rcs for i in issues):
                violations.append("reason_codes")
        # max_issue_count
        mic = fail_on.get("max_issue_count")
        if isinstance(mic, int) and len(issues) > mic:
            violations.append(f"issues>{mic}")
        return {"should_fail": bool(violations), "violations": violations} if violations else {"should_fail": False}

    def _check_gate_c_status(self, additional_params: dict | None = None) -> dict:
        """
        Editorial checklist の Gate C 評価を行う

        Args:
            additional_params: Request parameters potentially containing editorial_report path

        Returns:
            dict with keys:
            - gate_c_pass: bool or None
            - gate_c_should_fail: bool
            - gate_c_counts: dict with total, pass, note, todo, unknown, checked, unchecked
            - gate_c_counts_by_status: dict with PASS, NOTE, TODO, UNKNOWN counts
            - (optional) gate_c_error: str if evaluation failed
        """
        import subprocess
        from pathlib import Path

        result = {
            "gate_c_pass": True,
            "gate_c_should_fail": False,
            "gate_c_counts": {
                "total": 0,
                "pass": 0,
                "note": 0,
                "todo": 0,
                "unknown": 0,
                "checked": 0,
                "unchecked": 0,
            },
            "gate_c_counts_by_status": {"PASS": 0, "NOTE": 0, "TODO": 0, "UNKNOWN": 0},
        }

        # Get editorial_report path from additional_params
        ap = additional_params or {}
        editorial_report_path = ap.get("editorial_report")
        if not editorial_report_path:
            # No editorial report specified, return neutral (pass) result
            return result

        # Verify file exists
        report_path = Path(editorial_report_path)
        if not report_path.exists():
            result["gate_c_error"] = f"Editorial report not found: {editorial_report_path}"
            return result

        try:
            # Call editorial_checklist_evaluator script
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service
            path_service = create_path_service()
            evaluator_path = path_service.project_root / "scripts" / "tools" / "editorial_checklist_evaluator.py"

            if not evaluator_path.exists():
                result["gate_c_error"] = f"Editorial evaluator script not found: {evaluator_path}"
                return result

            proc = subprocess.run(
                ["python", str(evaluator_path), "--file", str(report_path), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # editorial_checklist_evaluator.py returns 0 (pass) or 2 (fail)
            if proc.returncode in (0, 2):
                try:
                    import json
                    output = json.loads(proc.stdout)
                    # Map subprocess output to gate_c_counts
                    counts = output.get("counts", {})
                    result["gate_c_counts"] = {
                        "total": output.get("total_items", 0),
                        "pass": counts.get("PASS", 0),
                        "note": counts.get("NOTE", 0),
                        "todo": counts.get("TODO", 0),
                        "unknown": counts.get("UNKNOWN", 0),
                        "checked": sum(counts.values()),
                        "unchecked": 0,
                    }
                    result["gate_c_counts_by_status"] = counts

                    # Determine gate_c_pass based on subprocess result
                    gate_c_pass = output.get("pass", True)
                    result["gate_c_pass"] = gate_c_pass
                    result["gate_c_should_fail"] = not gate_c_pass

                except Exception as e:
                    result["gate_c_error"] = f"Failed to parse evaluator output: {e}"
            else:
                # Non-zero exit code means evaluator failed or returned non-JSON output
                result["gate_c_error"] = f"Editorial evaluator failed with code {proc.returncode}: {proc.stderr}"

        except subprocess.TimeoutExpired:
            result["gate_c_error"] = "Editorial checklist evaluator timed out"
        except Exception as e:
            result["gate_c_error"] = str(e)

        return result
