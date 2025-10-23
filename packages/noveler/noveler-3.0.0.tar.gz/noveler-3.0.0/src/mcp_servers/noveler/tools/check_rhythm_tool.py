"""check_rhythm ツールの実装

なろう小説想定の文章リズム検査（行幅/文長/会話比率/語尾反復/約物/読点密度）。
"""
from __future__ import annotations

import time
from typing import Any, Iterable
import hashlib
from pathlib import Path
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.domain.services.sentence_run_analysis_service import SentenceRunAnalysisService
from noveler.domain.services.dialogue_ratio_service import DialogueRatioService
from noveler.domain.services.ending_repetition_service import EndingRepetitionService
from noveler.domain.services.punctuation_style_service import PunctuationStyleService
from noveler.domain.services.comma_density_service import CommaDensityService

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger


class CheckRhythmTool(MCPToolBase):
    """文章リズムチェックツール"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="check_rhythm",
            tool_description="文章リズムチェック（行幅/文長連続/会話比率/語尾/約物/読点密度）",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
                "preset": {
                    "type": "string",
                    "enum": ["narou", "custom"],
                    "default": "narou",
                    "description": "閾値プリセット（narou推奨）",
                },
                "check_aspects": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "long_short_runs",
                            "dialogue_ratio",
                            "ending_repetition",
                            "punctuation_style",
                            "comma_density",
                        ],
                    },
                    "description": "実行するチェックの選択（未指定時は全て）",
                },
                "thresholds": {
                    "type": "object",
                    "description": "カスタム閾値（preset='custom'のとき適用）",
                    "properties": {
                        "long_sentence_length": {"type": "integer", "default": 45},
                        "long_run_threshold": {"type": "integer", "default": 3},
                        "short_sentence_length": {"type": "integer", "default": 10},
                        "short_run_threshold": {"type": "integer", "default": 5},
                        "dialogue_ratio_min": {"type": "number", "default": 0.4},
                        "dialogue_ratio_max": {"type": "number", "default": 0.75},
                        "comma_avg_min": {"type": "number", "default": 0.6},
                        "comma_avg_max": {"type": "number", "default": 1.6},
                        "comma_per_sentence_max": {"type": "integer", "default": 3},
                        "ending_repeat_threshold": {"type": "integer", "default": 4},
                    },
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start_time = time.time()
        logger.info("文章リズムチェック開始: エピソード%s", request.episode_number)

        try:
            self._validate_request(request)
            # 対象パスの解決と読み込み
            ap = request.additional_params or {}
            target_path = self._resolve_target_path(request)
            # content優先（B20: 重複I/O回避）。なければファイル読み込み
            if isinstance(ap.get("content"), str):
                content = ap.get("content") or ""
            else:
                if target_path and target_path.exists():
                    content = target_path.read_text(encoding="utf-8")
                else:
                    content = ""
            if not content:
                return self._create_response(True, 100.0, [], start_time)

            # 設定の読み込み（.novelerrc.* の defaults を優先し、引数で上書き）
            defaults = self._load_config_defaults()
            merged_params = {**defaults, **(request.additional_params or {})}
            cfg = self._resolve_thresholds(merged_params)
            aspects = self._resolve_aspects(request.additional_params or {})

            lines = content.split("\n")
            sentences, sentence_line_map = self._split_sentences_with_lines(lines)

            issues: list[ToolIssue] = []

            file_path_str = str(target_path) if target_path else None
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None

            if "long_short_runs" in aspects:
                issues.extend(self._check_consecutive_runs(sentences, sentence_line_map, cfg, lines, file_path_str, file_hash))

            if "dialogue_ratio" in aspects:
                issues.extend(self._check_dialogue_ratio(lines, cfg, file_path_str, file_hash))

            if "ending_repetition" in aspects:
                issues.extend(self._check_ending_repetition(sentences, sentence_line_map, cfg, lines, file_path_str, file_hash))

            if "punctuation_style" in aspects:
                issues.extend(self._check_punctuation_style(lines, file_path_str, file_hash))

            if "comma_density" in aspects:
                issues.extend(self._check_comma_density(sentences, sentence_line_map, cfg, lines, file_path_str, file_hash))

            score = self._calculate_score(issues)

            # 概要メトリクスを1件のsummary issueとして追加
            summary = self._summarize_metrics(lines, sentences, issues)
            issues.insert(
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
                    file_path=file_path_str,
                    reason_code="SUMMARY",
                    details=summary,
                ),
            )

            logger.info("文章リズムチェック完了: スコア=%.1f, 問題数=%d", score, len(issues))
            resp = self._create_response(True, score, issues, start_time, None)  # type: ignore[arg-type]
            # PathServiceのフォールバック可視化をメタに付加
            self._apply_fallback_metadata(resp)
            return resp

        except FileNotFoundError:
            return self._create_response(False, 0.0, [], start_time, "Episode file not found")
        except Exception as e:
            return self._create_response(False, 0.0, [], start_time, f"文章リズムチェックエラー: {e!s}")

    # ---- helpers ----

    def _resolve_thresholds(self, params: dict[str, Any]) -> dict[str, Any]:
        preset = (params.get("preset") or "narou").lower()
        defaults = {
            "preset": preset,
            "long_sentence_length": 45,
            "long_run_threshold": 3,
            "short_sentence_length": 10,
            "short_run_threshold": 5,
            "dialogue_ratio_min": 0.4,
            "dialogue_ratio_max": 0.75,
            "comma_avg_min": 0.6,
            "comma_avg_max": 1.6,
            "comma_per_sentence_max": 3,
            "ending_repeat_threshold": 4,
        }
        if preset == "custom":
            thresholds = params.get("thresholds") or {}
            defaults.update({k: thresholds.get(k, v) for k, v in defaults.items()})
        return defaults

    def _resolve_aspects(self, params: dict[str, Any]) -> set[str]:
        aspects = params.get("check_aspects")
        if not aspects:
            return {
                "long_short_runs",
                "dialogue_ratio",
                "ending_repetition",
                "punctuation_style",
                "comma_density",
            }
        return set(aspects)

    def _split_sentences_with_lines(self, lines: list[str]) -> tuple[list[str], list[int]]:
        sentences: list[str] = []
        line_map: list[int] = []
        for idx, line in enumerate(lines, 1):
            work = line.strip()
            if not work:
                continue
            parts = [p for p in work.split("。") if p.strip()]
            for p in parts:
                sentences.append(p)
                line_map.append(idx)
        return sentences, line_map

    # line width detection has been removed by policy; no replacement logic is provided.

    def _check_consecutive_runs(
        self,
        sentences: list[str],
        sentence_line_map: list[int],
        cfg: dict[str, Any],
        lines: list[str],
        file_path: str | None,
        file_hash: str | None,
    ) -> list[ToolIssue]:
        issues: list[ToolIssue] = []
        long_len = int(cfg["long_sentence_length"])  # type: ignore[arg-type]
        short_len = int(cfg["short_sentence_length"])  # type: ignore[arg-type]
        long_thr = int(cfg["long_run_threshold"])  # type: ignore[arg-type]
        short_thr = int(cfg["short_run_threshold"])  # type: ignore[arg-type]

        def classify(s: str) -> str:
            n = len(s)
            if n >= long_len:
                return "long"
            if n <= short_len:
                return "short"
            return "mid"

        runs = SentenceRunAnalysisService().find_consecutive_runs(
            sentences, long_len=long_len, short_len=short_len, long_thr=long_thr, short_thr=short_thr
        )
        for r in runs:
            sidx, eidx = r.start_sentence_index, r.end_sentence_index
            if r.kind == "long":
                sline = sentence_line_map[sidx]
                eline = sentence_line_map[eidx]
                block_text = "\n".join(lines[sline - 1 : eline])
                blk_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
                issue_id = hashlib.sha256(
                    f"{file_hash}:{'consecutive_long_sentences'}:{sline}-{eline}:{blk_hash}".encode("utf-8")
                ).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="consecutive_long_sentences",
                        severity="medium",
                        message=f"長文が{r.count}文連続しています（{sline}–{eline}行付近）",
                        line_number=sline,
                        suggestion="改行や句点の追加でリズムを整えてください",
                        end_line_number=eline,
                        file_path=file_path,
                        block_hash=blk_hash,
                        reason_code="CONSECUTIVE_LONG_SENTENCES",
                        details={"count": r.count, "threshold": long_thr, "start_line": sline, "end_line": eline},
                        issue_id=f"rhythm-{issue_id}",
                    )
                )
            if r.kind == "short":
                sline = sentence_line_map[sidx]
                eline = sentence_line_map[eidx]
                block_text = "\n".join(lines[sline - 1 : eline])
                blk_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
                issue_id = hashlib.sha256(
                    f"{file_hash}:{'consecutive_short_sentences'}:{sline}-{eline}:{blk_hash}".encode("utf-8")
                ).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="consecutive_short_sentences",
                        severity="low",
                        message=f"短文が{r.count}文連続しています（{sline}–{eline}行付近）",
                        line_number=sline,
                        suggestion="文の接続や描写追加で単調さを緩和してください",
                        end_line_number=eline,
                        file_path=file_path,
                        block_hash=blk_hash,
                        reason_code="CONSECUTIVE_SHORT_SENTENCES",
                        details={"count": r.count, "threshold": short_thr, "start_line": sline, "end_line": eline},
                        issue_id=f"rhythm-{issue_id}",
                    )
                )
        return issues

    def _check_dialogue_ratio(self, lines: list[str], cfg: dict[str, Any], file_path: str | None, file_hash: str | None) -> list[ToolIssue]:
        issues: list[ToolIssue] = []
        lo = float(cfg["dialogue_ratio_min"])  # type: ignore[arg-type]
        hi = float(cfg["dialogue_ratio_max"])  # type: ignore[arg-type]
        finding = DialogueRatioService().analyze(lines, min_ratio=lo, max_ratio=hi)
        if finding is None:
            return issues
        issue_id = hashlib.sha256(
            f"{file_hash}:{'dialogue_ratio_out_of_range'}:{finding.ratio:.4f}:{lo}-{hi}".encode("utf-8")
        ).hexdigest()[:12]
        issues.append(
            ToolIssue(
                type="dialogue_ratio_out_of_range",
                severity=finding.severity,
                message=f"会話比率が不均衡です（{finding.ratio*100:.1f}%、推奨{int(lo*100)}–{int(hi*100)}%）",
                suggestion="会話/地の文のバランスを調整してください",
                file_path=file_path,
                reason_code="DIALOGUE_RATIO_OUT_OF_RANGE",
                details={"ratio": finding.ratio, "min": lo, "max": hi},
                issue_id=f"rhythm-{issue_id}",
            )
        )
        return issues

    def _check_ending_repetition(
        self,
        sentences: list[str],
        sentence_line_map: list[int],
        cfg: dict[str, Any],
        lines: list[str],
        file_path: str | None,
        file_hash: str | None,
    ) -> list[ToolIssue]:
        issues: list[ToolIssue] = []
        thr = int(cfg["ending_repeat_threshold"])  # type: ignore[arg-type]
        findings = EndingRepetitionService().analyze(sentences, threshold=thr)
        for f in findings:
            sline = sentence_line_map[f.start_sentence_index]
            eline = sentence_line_map[f.end_sentence_index]
            block_text = "\n".join(lines[sline - 1 : eline])
            blk_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
            issue_id = hashlib.sha256(
                f"{file_hash}:{'ending_repetition'}:{sline}-{eline}:{blk_hash}".encode("utf-8")
            ).hexdigest()[:12]
            issues.append(
                ToolIssue(
                    type="ending_repetition",
                    severity="low",
                    message=f"同一語尾『{f.ending}。』が{f.count}連続（{sline}–{eline}行付近）",
                    line_number=sline,
                    suggestion="語尾バリエーション（〜か？/〜ね。/〜だろう など）を検討",
                    end_line_number=eline,
                    file_path=file_path,
                    block_hash=blk_hash,
                    reason_code="ENDING_REPETITION",
                    details={"ending": f.ending, "count": f.count, "threshold": thr, "start_line": sline, "end_line": eline},
                    issue_id=f"rhythm-{issue_id}",
                )
            )
        return issues

    def _check_punctuation_style(self, lines: list[str], file_path: str | None, file_hash: str | None) -> list[ToolIssue]:
        issues: list[ToolIssue] = []
        service = PunctuationStyleService()
        findings = service.analyze_lines(lines)
        for f in findings:
            line_text = lines[f.line_index - 1] if 0 < f.line_index <= len(lines) else ""
            ln_hash = hashlib.sha256(line_text.encode("utf-8")).hexdigest()
            if f.kind == "ellipsis_style":
                issue_id = hashlib.sha256(
                    f"{file_hash}:{'ellipsis_style'}:{f.line_index}:{ln_hash}".encode("utf-8")
                ).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="ellipsis_style",
                        severity="low",
                        message="三点リーダは『……』へ統一",
                        line_number=f.line_index,
                        suggestion="『...』『・・・』を『……』へ置換",
                        file_path=file_path,
                        line_hash=ln_hash,
                        reason_code="ELLIPSIS_STYLE",
                        details={"found": f.found},
                        issue_id=f"rhythm-{issue_id}",
                    )
                )
            elif f.kind == "ellipsis_odd_count":
                issue_id = hashlib.sha256(
                    f"{file_hash}:{'ellipsis_odd_count'}:{f.line_index}:{ln_hash}".encode("utf-8")
                ).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="ellipsis_odd_count",
                        severity="low",
                        message="『…』の数が奇数（『……』の偶数個で使用）",
                        line_number=f.line_index,
                        suggestion="『…』は2個単位で使用（例: 『……』）",
                        file_path=file_path,
                        line_hash=ln_hash,
                        reason_code="ELLIPSIS_ODD_COUNT",
                        details={"count": f.count},
                        issue_id=f"rhythm-{issue_id}",
                    )
                )
            elif f.kind == "dash_style":
                issue_id = hashlib.sha256(
                    f"{file_hash}:{'dash_style'}:{f.line_index}:{ln_hash}".encode("utf-8")
                ).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="dash_style",
                        severity="low",
                        message="ダッシュは『――』へ統一",
                        line_number=f.line_index,
                        suggestion="『—』『－』を『――』へ置換",
                        file_path=file_path,
                        line_hash=ln_hash,
                        reason_code="DASH_STYLE",
                        details={"found_dash": True},
                        issue_id=f"rhythm-{issue_id}",
                    )
                )
        return issues

    def _check_comma_density(
        self,
        sentences: list[str],
        sentence_line_map: list[int],
        cfg: dict[str, Any],
        lines: list[str],
        file_path: str | None,
        file_hash: str | None,
    ) -> list[ToolIssue]:
        issues: list[ToolIssue] = []
        avg_lo = float(cfg["comma_avg_min"])  # type: ignore[arg-type]
        avg_hi = float(cfg["comma_avg_max"])  # type: ignore[arg-type]
        per_max = int(cfg["comma_per_sentence_max"])  # type: ignore[arg-type]
        avg_finding, over = CommaDensityService().analyze(sentences, min_avg=avg_lo, max_avg=avg_hi, per_sentence_max=per_max)
        if avg_finding is not None:
            issue_id = hashlib.sha256(
                f"{file_hash}:{'comma_avg_out_of_range'}:{avg_finding.average:.4f}:{avg_lo}-{avg_hi}".encode("utf-8")
            ).hexdigest()[:12]
            issues.append(
                ToolIssue(
                    type="comma_avg_out_of_range",
                    severity="low",
                    message=f"読点密度が偏っています（平均{avg_finding.average:.2f}、推奨{avg_lo}–{avg_hi}）",
                    suggestion="文の構造を見直し、読点の過不足を調整",
                    file_path=file_path,
                    reason_code="COMMA_AVG_OUT_OF_RANGE",
                    details={"average": avg_finding.average, "min": avg_lo, "max": avg_hi},
                    issue_id=f"rhythm-{issue_id}",
                )
            )

        for ov in over:
            sline = sentence_line_map[ov.sentence_index]
            line_text = lines[sline - 1] if 0 < sline <= len(lines) else ""
            ln_hash = hashlib.sha256(line_text.strip().encode("utf-8")).hexdigest()
            issue_id = hashlib.sha256(
                f"{file_hash}:{'comma_overuse'}:{sline}:{ln_hash}".encode("utf-8")
            ).hexdigest()[:12]
            issues.append(
                ToolIssue(
                    type="comma_overuse",
                    severity="medium",
                    message=f"1文に読点が多すぎます（{ov.count}個 > {per_max}）",
                    line_number=sline,
                    suggestion="文を分割し、読みやすさを確保",
                    file_path=file_path,
                    line_hash=ln_hash,
                    reason_code="COMMA_OVERUSE",
                    details={"count": ov.count, "max": per_max},
                    issue_id=f"rhythm-{issue_id}",
                )
            )
        return issues

    def _calculate_score(self, issues: Iterable[ToolIssue]) -> float:
        penalty = 0
        for it in issues:
            if it.severity == "critical":
                penalty += 20
            elif it.severity == "high":
                penalty += 10
            elif it.severity == "medium":
                penalty += 5
            else:
                penalty += 2
        return max(0.0, 100.0 - float(penalty))

    def _summarize_metrics(self, lines: list[str], sentences: list[str], issues: list[ToolIssue]) -> dict[str, Any]:
        non_empty_lines = [ln for ln in lines if ln.strip()]
        dialogue_lines = [ln for ln in non_empty_lines if ("「" in ln and "」" in ln)]
        longest_line = max((len(ln.rstrip("\n")) for ln in non_empty_lines), default=0)
        return {
            "lines": len(non_empty_lines),
            "sentences": len(sentences),
            "dialogue_ratio": (len(dialogue_lines) / max(len(non_empty_lines), 1)) if non_empty_lines else 0.0,
            "longest_line": longest_line,
            "issue_count": len(issues),
            "issue_types": sorted({it.type for it in issues}),
        }

    def _resolve_target_path(self, request: ToolRequest):
        """入力からターゲットファイルパスを解決"""
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            target = Path(ap["file_path"]).expanduser()
            return target
        # episode_number から推定
        try:
            path_service = create_path_service()
            cache_service = get_file_cache_service()
            manuscript_dir = path_service.get_manuscript_dir()
            ep = cache_service.get_episode_file_cached(manuscript_dir, request.episode_number)
            # フォールバックイベント収集
            self._ps_collect_fallback(path_service)
            return ep
        except Exception:
            return None

    # ---- config helpers ----
    def _load_config_defaults(self) -> dict[str, Any]:
        """.novelerrc.* の defaults セクションを読み込み

        run_quality_checks と整合を取るため、check_rhythm 単体でも
        preset/custom thresholds を自動適用できるようにする。
        """
        try:
            import json as _json
            try:
                import yaml as _yaml  # type: ignore
            except Exception:  # pragma: no cover
                _yaml = None

            ps = create_path_service()
            root = ps.project_root
            # フォールバックイベント収集
            self._ps_collect_fallback(ps)

            for name in [".novelerrc.yaml", ".novelerrc.yml", ".novelerrc.json"]:
                p = root / name
                if not p.exists():
                    continue
                try:
                    if p.suffix in (".yaml", ".yml") and _yaml is not None:
                        data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                    else:
                        data = _json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if isinstance(data, dict) and "defaults" in data and isinstance(data["defaults"], dict):
                    return data["defaults"]
            return {}
        except Exception:
            return {}
