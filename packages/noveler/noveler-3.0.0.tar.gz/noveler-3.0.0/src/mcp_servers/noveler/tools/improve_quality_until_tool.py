"""improve_quality_until ツールの実装

各評価項目ごとに「自動修正→再評価」を反復し、合格(既定80点)で次の項目へ進む。
レスポンスはハッシュ/ID中心で、本文やdiffは既定で含めない（B20準拠・軽量）。
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger

from .run_quality_checks_tool import RunQualityChecksTool
from .fix_quality_issues_tool import FixQualityIssuesTool


DEFAULT_ASPECTS = ["rhythm", "readability", "grammar"]

# 各アスペクトに対して安全な自動修正対象（B20方針）
SAFE_REASON_CODES_BY_ASPECT: dict[str, list[str]] = {
    "rhythm": [
        "ELLIPSIS_STYLE",
        "ELLIPSIS_ODD_COUNT",
        "DASH_STYLE",
        "CONSECUTIVE_SHORT_SENTENCES",
        "CONSECUTIVE_LONG_SENTENCES",
        "LONG_SENTENCE",
        "COMMA_OVERUSE",
        "TRAILING_SPACES",
        "DOUBLE_SPACES",
        "TAB_FOUND",
        "EMPTY_LINE_RUNS",
    ],
    "readability": [
        "LONG_SENTENCE",
        "CONSECUTIVE_SHORT_SENTENCES",
        "COMMA_OVERUSE",
    ],
    "grammar": [
        "GRAMMAR_PUNCTUATION",
    ],
}

# 後方互換のための理由コード同義語マップ
# LLMが短縮名や概念名で渡しても安全に受け入れる
REASON_CODE_SYNONYMS: dict[str, str] = {
    # 読点過多（代表）
    "COMMA_OVERUSED": "COMMA_OVERUSE",
    # 長短文連続（代表）
    "CONSECUTIVE_LONG": "CONSECUTIVE_LONG_SENTENCES",
    "CONSECUTIVE_SHORT": "CONSECUTIVE_SHORT_SENTENCES",
    # 三点リーダ/ダッシュ（代表）
    "ELLIPSIS": "ELLIPSIS_STYLE",
    "DASH": "DASH_STYLE",
}


class ImproveQualityUntilTool(MCPToolBase):
    """各評価項目を合格まで自動改善するオーケストレーター"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="improve_quality_until",
            tool_description="各項目を合格(80点)まで反復改善し、順次次項目へ進む",
        )

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
                    "default": DEFAULT_ASPECTS,
                    "description": "評価順序（例: rhythm→readability→grammar）",
                },
                "severity_threshold": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "medium",
                    "description": "この重要度未満を除外（軽量化・ノイズ抑制）",
                },
                "target_score": {
                    "type": "number",
                    "default": 80,
                    "description": "合格スコア（既定80）",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 3,
                    "description": "各アスペクトの最大反復回数",
                },
                "min_delta": {
                    "type": "number",
                    "default": 0.5,
                    "description": "改善幅がこの値未満なら早期停止",
                },
                "page_size": {
                    "type": "integer",
                    "default": 100,
                    "description": "詳細取得時の1ページ件数（内部用）",
                },
                "include_diff": {
                    "type": "boolean",
                    "default": False,
                    "description": "オートフィクス時に短縮diffを同梱（既定False）",
                },
                # 後方互換: 配列（全アスペクト共通）も受理
                "reason_codes": {
                    "oneOf": [
                        {
                            "type": "object",
                            "description": "アスペクト別の適用理由コード上書き（{aspect: string[]}）",
                            "additionalProperties": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        {
                            "type": "array",
                            "description": "全アスペクトに共通で適用する理由コード配列（後方互換）",
                            "items": {"type": "string"},
                        },
                    ],
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start = time.time()

        # 外部境界: MCPツール実行開始
        logger.info(
            "improve_quality_until実行開始",
            extra={
                "tool": "improve_quality_until",
                "episode_number": request.episode_number,
                "project_name": request.project_name,
                "request_id": getattr(request, 'request_id', 'unknown')
            }
        )

        try:
            self._validate_request(request)
            ap = request.additional_params or {}

            target_path = self._resolve_target_path(request)
            file_path_str = str(target_path) if target_path else ap.get("file_path")
            text_hash = None

            logger.debug(
                "ファイルパス解決結果",
                extra={
                    "file_path": file_path_str,
                    "exists": target_path.exists() if target_path else False
                }
            )

            if file_path_str:
                try:
                    p = Path(file_path_str)
                    if p.exists():
                        text_content = p.read_text(encoding="utf-8")
                        text_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
                        logger.info(
                            "対象ファイル読み込み完了",
                            extra={
                                "content_length": len(text_content),
                                "file_hash": text_hash[:8] + "..." if text_hash else None
                            }
                        )
                except Exception as e:
                    logger.warning(
                        "ファイル読み込みエラー",
                        extra={"file_path": file_path_str, "error": str(e)}
                    )

            aspects = list(ap.get("aspects") or DEFAULT_ASPECTS)
            severity = str(ap.get("severity_threshold", "medium")).lower()
            target = float(ap.get("target_score", 80))
            max_iter = int(ap.get("max_iterations", 3))
            min_delta = float(ap.get("min_delta", 0.5))
            include_diff = bool(ap.get("include_diff", False))
            page_size = int(ap.get("page_size", 100))

            logger.info(
                "品質改善実行設定",
                extra={
                    "aspects": aspects,
                    "severity_threshold": severity,
                    "target_score": target,
                    "max_iterations": max_iter,
                    "min_delta": min_delta,
                    "include_diff": include_diff
                }
            )
            # reason_codes は後方互換で dict か list を許容する
            raw_rc = ap.get("reason_codes")
            if isinstance(raw_rc, dict):
                custom_rc: dict[str, list[str]] = {k: list(v) for k, v in raw_rc.items() if isinstance(v, (list, tuple))}
                rc_kind = "object"
            elif isinstance(raw_rc, (list, tuple)):
                # 配列が来た場合は、全アスペクトに同一配列を適用
                custom_rc = {a: list(raw_rc) for a in DEFAULT_ASPECTS}
                rc_kind = "array"
            else:
                custom_rc = {}
                rc_kind = "none"

            # 許容される理由コード集合（fix_quality_issuesの安全セットと一致させる）
            try:
                # 循環参照を避けるためローカルimport
                from .fix_quality_issues_tool import SAFE_REASON_CODES as _FX_SAFE
                allowed_codes: set[str] = set(_FX_SAFE)
            except Exception:
                # フォールバック: 既知の安全集合から構築
                allowed_codes = set()
                for _v in SAFE_REASON_CODES_BY_ASPECT.values():
                    allowed_codes.update(_v)

            # 正規化ユーティリティ
            def _normalize_codes(values: list[str]) -> tuple[list[str], list[str]]:
                normalized: list[str] = []
                ignored: list[str] = []
                for raw in values:
                    if not isinstance(raw, str):
                        continue
                    key = raw.strip().upper()
                    key = REASON_CODE_SYNONYMS.get(key, key)
                    # 非自動修正系の概念ラベルを受けた場合も弾く
                    if key in allowed_codes:
                        normalized.append(key)
                    else:
                        ignored.append(raw)
                # 重複除去をしつつ順序維持
                seen: set[str] = set()
                deduped: list[str] = []
                for c in normalized:
                    if c not in seen:
                        seen.add(c)
                        deduped.append(c)
                return deduped, ignored

            aspect_results: list[ToolIssue] = []
            overall_min_score: float | None = None

            normalization_ignored_total: list[str] = []

            logger.info(
                "アスペクト別品質改善開始",
                extra={
                    "total_aspects": len(aspects),
                    "aspects_order": aspects
                }
            )

            for aspect_idx, aspect in enumerate(aspects, 1):
                logger.info(
                    f"アスペクト処理開始 ({aspect_idx}/{len(aspects)})",
                    extra={"aspect": aspect, "position": aspect_idx}
                )
                # 1) 現状サマリー（軽量）
                logger.debug(f"{aspect}の初期スコア評価開始")
                initial_check_start = time.time()
                cur_score = self._check_summary(request, file_path_str, aspect, severity)
                initial_check_time = time.time() - initial_check_start
                initial_score = cur_score
                applied_total = 0
                it = 0

                logger.info(
                    f"{aspect}初期評価完了",
                    extra={
                        "aspect": aspect,
                        "initial_score": initial_score,
                        "target_score": target,
                        "needs_improvement": initial_score < target,
                        "evaluation_time_seconds": initial_check_time
                    }
                )

                # 2) 反復（合格or上限まで）
                if cur_score < target:
                    logger.info(
                        f"{aspect}改善反復処理開始",
                        extra={
                            "aspect": aspect,
                            "current_score": cur_score,
                            "target_score": target,
                            "max_iterations": max_iter
                        }
                    )
                else:
                    logger.info(
                        f"{aspect}は既に合格スコア",
                        extra={"aspect": aspect, "score": cur_score, "target": target}
                    )

                while cur_score < target and it < max_iter:
                    it += 1
                    iteration_start = time.time()

                    logger.debug(
                        f"{aspect}反復{it}回目開始",
                        extra={
                            "aspect": aspect,
                            "iteration": it,
                            "current_score": cur_score
                        }
                    )
                    # 適用理由コード選択
                    reason_codes_raw = custom_rc.get(aspect) if isinstance(custom_rc, dict) else None
                    if not reason_codes_raw:
                        reason_codes_raw = SAFE_REASON_CODES_BY_ASPECT.get(aspect, [])
                    reason_codes, ignored_codes = _normalize_codes(list(reason_codes_raw))
                    if ignored_codes:
                        normalization_ignored_total.extend([f"{aspect}:{c}" for c in ignored_codes])
                    # 正常化後に何も残らなければ、安全集合で代替
                    if not reason_codes:
                        reason_codes = list(SAFE_REASON_CODES_BY_ASPECT.get(aspect, []))

                    logger.debug(f"{aspect}修正処理実行（理由コード: {len(reason_codes)}個）")
                    fix_start = time.time()
                    applied = self._apply_fixes(
                        request,
                        file_path_str,
                        reason_codes,
                        include_diff=include_diff,
                    )
                    fix_time = time.time() - fix_start
                    applied_total += max(0, applied)

                    logger.debug(
                        f"{aspect}修正処理完了",
                        extra={
                            "aspect": aspect,
                            "iteration": it,
                            "applied_fixes": applied,
                            "fix_time_seconds": fix_time,
                            "reason_codes": reason_codes
                        }
                    )

                    # 再評価
                    logger.debug(f"{aspect}再評価開始")
                    re_eval_start = time.time()
                    new_score = self._check_summary(request, file_path_str, aspect, severity)
                    re_eval_time = time.time() - re_eval_start
                    iteration_time = time.time() - iteration_start

                    score_delta = new_score - cur_score
                    early_stop = new_score <= cur_score or abs(score_delta) < min_delta

                    logger.info(
                        f"{aspect}反復{it}回目完了",
                        extra={
                            "aspect": aspect,
                            "iteration": it,
                            "score_before": cur_score,
                            "score_after": new_score,
                            "score_delta": score_delta,
                            "applied_fixes": applied,
                            "early_stop": early_stop,
                            "min_delta_threshold": min_delta,
                            "iteration_time_seconds": iteration_time,
                            "evaluation_time_seconds": re_eval_time
                        }
                    )

                    if early_stop:
                        logger.info(
                            f"{aspect}改善停止（効果不十分）",
                            extra={
                                "aspect": aspect,
                                "reason": "score_delta_insufficient" if abs(score_delta) < min_delta else "score_degraded",
                                "score_delta": score_delta,
                                "min_delta": min_delta
                            }
                        )
                        cur_score = new_score
                        break
                    cur_score = new_score

                # アスペクト処理完了ログ
                aspect_passed = cur_score >= target
                logger.info(
                    f"{aspect}処理完了",
                    extra={
                        "aspect": aspect,
                        "initial_score": initial_score,
                        "final_score": cur_score,
                        "score_improvement": cur_score - initial_score,
                        "iterations_used": it,
                        "total_applied_fixes": applied_total,
                        "passed": aspect_passed,
                        "target_score": target
                    }
                )

                # 結果をIssue（軽量）に格納
                aspect_results.append(
                    ToolIssue(
                        type="aspect_result",
                        severity="low",
                        message=f"{aspect}: {cur_score:.1f}点",
                        details={
                            "aspect": aspect,
                            "initial_score": initial_score,
                            "final_score": cur_score,
                            "iterations": it,
                            "applied": applied_total,
                            "passed": aspect_passed,
                        },
                    )
                )

                overall_min_score = cur_score if overall_min_score is None else min(overall_min_score, cur_score)

            # 最終サマリー（全アスペクト最小をscoreに採用）
            final_score = overall_min_score if overall_min_score is not None else 100.0
            execution_time = time.time() - start

            passed_aspects = [r for r in aspect_results if r.details.get("passed", False)]
            total_applied = sum(r.details.get("applied", 0) for r in aspect_results)

            logger.info(
                "improve_quality_until実行完了",
                extra={
                    "execution_time_seconds": execution_time,
                    "final_score": final_score,
                    "target_score": target,
                    "overall_passed": final_score >= target,
                    "processed_aspects": len(aspects),
                    "passed_aspects": len(passed_aspects),
                    "total_applied_fixes": total_applied,
                    "ignored_reason_codes": len(normalization_ignored_total)
                }
            )
            resp = self._create_response(True, float(final_score), aspect_results, start)
            resp.metadata.update(
                {
                    "file_path": file_path_str,
                    "file_hash": text_hash,
                    "target_score": target,
                    "severity_threshold": severity,
                    "reason_codes_input_kind": rc_kind,
                    "ignored_reason_codes": normalization_ignored_total or None,
                }
            )
            return resp

        except Exception as e:
            logger.error(
                "improve_quality_until実行エラー",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "episode_number": request.episode_number,
                    "project_name": request.project_name,
                    "execution_time_seconds": time.time() - start
                }
            )
            return self._create_response(False, 0.0, [], start, f"improve_quality_until error: {e!s}")

    # ---- helpers ----

    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        try:
            from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            return ep
        except Exception:
            return None

    def _check_summary(self, request: ToolRequest, file_path: str | None, aspect: str, severity: str) -> float:
        logger = get_logger(__name__)
        logger.debug(
            "品質チェック実行（要約モード）",
            extra={
                "aspect": aspect,
                "severity_threshold": severity,
                "file_path": file_path
            }
        )

        chk = RunQualityChecksTool()
        req = ToolRequest(
            episode_number=request.episode_number,
            project_name=request.project_name,
            additional_params={
                "file_path": file_path,
                "aspects": [aspect],
                "severity_threshold": severity,
                "format": "summary",
            },
        )
        res = chk.execute(req)

        logger.debug(
            "品質チェック完了",
            extra={
                "aspect": aspect,
                "score": res.score,
                "success": res.success
            }
        )

        return float(res.score)

    def _apply_fixes(
        self,
        request: ToolRequest,
        file_path: str | None,
        reason_codes: list[str],
        *,
        include_diff: bool,
    ) -> int:
        logger = get_logger(__name__)
        logger.debug(
            "品質修正実行",
            extra={
                "file_path": file_path,
                "reason_codes": reason_codes,
                "reason_codes_count": len(reason_codes),
                "include_diff": include_diff
            }
        )

        fixer = FixQualityIssuesTool()
        req = ToolRequest(
            episode_number=request.episode_number,
            project_name=request.project_name,
            additional_params={
                "file_path": file_path,
                "reason_codes": reason_codes,
                "dry_run": False,
                "include_diff": bool(include_diff),
                # diffは必要時のみ、短縮はツール側設定に従う
            },
        )
        res = fixer.execute(req)

        try:
            applied = int(res.metadata.get("applied", 0))
            logger.debug(
                "品質修正完了",
                extra={
                    "applied_fixes": applied,
                    "success": res.success,
                    "reason_codes": reason_codes
                }
            )
            return applied
        except Exception as e:
            logger.warning(
                "品質修正結果解析エラー",
                extra={
                    "error": str(e),
                    "reason_codes": reason_codes
                }
            )
            return 0
