"""fix_quality_issues ツールの実装

安全な自動修正（約物統一・安全整形）を行い、dry_runでdiffを返す。
対象の選択はreason_codes/issue_idsで制御可能。
"""
from __future__ import annotations

import difflib
import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
try:
    from noveler.infrastructure.nlp.morphological_analyzer import create_analyzer as _create_analyzer
    _MORPH_AVAILABLE = True
except Exception:  # pragma: no cover
    _create_analyzer = None
    _MORPH_AVAILABLE = False

from .run_quality_checks_tool import RunQualityChecksTool


SAFE_REASON_CODES = {
    "ELLIPSIS_STYLE",
    "ELLIPSIS_ODD_COUNT",
    "DASH_STYLE",
    # 追加: 文の連結/分割（安全範囲）
    "CONSECUTIVE_SHORT_SENTENCES",
    "CONSECUTIVE_LONG_SENTENCES",
    "LONG_SENTENCE",
    "COMMA_OVERUSE",
    "TRAILING_SPACES",
    "DOUBLE_SPACES",
    "TAB_FOUND",
    # style（安全範囲）
    "EMPTY_LINE_RUNS",
    # grammar（安全範囲）
    "GRAMMAR_PUNCTUATION",
    # FULLWIDTH_SPACE は危険度があるため自動修正対象から除外（通知のみ）
}


BOUNDARY_HIGH_SURFACES = {
    "ます",
    "ました",
    "ません",
    "です",
    "でした",
    "だった",
    "だ",
    "する",
    "した",
    "できる",
    "できた",
    "なる",
    "なった",
    "たい",
    "ない",
}

BOUNDARY_MEDIUM_SURFACES = {
    "て",
    "ので",
    "から",
    "そして",
    "しかし",
    "だから",
    "それで",
}

BOUNDARY_LOW_SURFACES = {
    "に",
    "で",
    "を",
    "が",
    "の",
}

FALLBACK_ENDINGS = (
    "ます",
    "ました",
    "ません",
    "です",
    "でした",
    "だった",
    "だ",
    "する",
    "した",
    "できる",
    "できた",
    "なる",
    "なった",
    "ている",
    "ていた",
    "ており",
    "たい",
    "ない",
)


@dataclass
class FixResult:
    original_text: str
    fixed_text: str
    applied: int
    skipped: int
    notes: list[str]


class FixQualityIssuesTool(MCPToolBase):
    """安全オートフィクス（約物統一・安全整形）"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="fix_quality_issues",
            tool_description="安全オートフィクス（三点リーダ/ダッシュ統一などの安全整形）",
        )
        # 形態素・分割ルール設定（.novelerrc から反映）
        self._morph_settings: dict[str, Any] = {}

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
                "output_path": {
                    "type": "string",
                    "description": "dry_run=false時の書き出し先（省略時は上書き）",
                },
                "reason_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "適用する修正の種類（省略時は安全な既定セット）",
                },
                "issue_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "指定されたissue_idに一致する箇所のみ修正",
                },
                "include_style": {
                    "type": "boolean",
                    "default": True,
                    "description": "検出段階でstyleも含める（EMPTY_LINE_RUNS/スペース系など）",
                },
                "include_grammar": {
                    "type": "boolean",
                    "default": True,
                    "description": "検出段階でgrammarも含める（句読点重複など）",
                },
                # 行幅/自動改行に関する設定は撤廃
                "max_sentence_length": {
                    "type": "integer",
                    "default": 45,
                    "description": "長文分割の目標文長（文字数）",
                },
                "short_sentence_length": {
                    "type": "integer",
                    "default": 10,
                    "description": "短文連結の対象閾値（文字数以下）",
                },
                "enable_sentence_split": {
                    "type": "boolean",
                    "default": True,
                    "description": "長文分割を有効化",
                },
                "enable_sentence_merge": {
                    "type": "boolean",
                    "default": True,
                    "description": "短文連結を有効化",
                },
                "max_commas_per_sentence": {
                    "type": "integer",
                    "default": 3,
                    "description": "1文あたり許容する読点の最大数（超過分割）",
                },
                "max_merges_per_line": {
                    "type": "integer",
                    "default": 2,
                    "description": "1行あたりの最大連結回数",
                },
                "max_splits_per_line": {
                    "type": "integer",
                    "default": 2,
                    "description": "1行あたりの最大分割回数",
                },
                "skip_dialogue_lines": {
                    "type": "boolean",
                    "default": True,
                    "description": "台詞行（「…」を含む）は分割・連結をスキップ",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Trueで差分のみ返却。Falseでファイルに適用",
                },
                # B20: レスポンス軽量化オプション
                "include_diff": {
                    "type": "boolean",
                    "default": False,
                    "description": "Trueでdiffを返却（大規模化するため既定はFalse）",
                },
                "max_diff_lines": {
                    "type": "integer",
                    "default": 400,
                    "description": "diffの最大行数（include_diff=Trueのとき有効）",
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start = time.time()

        # 外部境界: MCPツール実行開始
        logger.info(
            "fix_quality_issues実行開始",
            extra={
                "tool": "fix_quality_issues",
                "episode_number": request.episode_number,
                "project_name": request.project_name,
                "request_id": getattr(request, 'request_id', 'unknown')
            }
        )

        try:
            self._validate_request(request)
            base_ap = request.additional_params or {}
            cfg = self._load_config_overrides()
            ap = {**cfg.get("defaults", {}), **base_ap}
            # Merge nested additional_params for compatibility with callers that
            # pass options under arguments["additional_params"].
            nested_ap = base_ap.get("additional_params") if isinstance(base_ap, dict) else None
            if isinstance(nested_ap, dict):
                ap.update(nested_ap)
            self._morph_settings = cfg.get("morphology", {})

            target_path = self._resolve_target_path(request)
            logger.debug(
                "ファイルパス解決結果",
                extra={
                    "file_path": str(target_path) if target_path else None,
                    "exists": target_path.exists() if target_path else False
                }
            )

            if not target_path or not target_path.exists():
                logger.warning(
                    "対象ファイルが見つからない",
                    extra={"file_path": str(target_path) if target_path else None}
                )
                return self._create_response(False, 0.0, [], start, "Target file not found")

            text = target_path.read_text(encoding="utf-8")
            lines = text.split("\n")
            file_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

            logger.info(
                "ファイル読み込み完了",
                extra={
                    "content_length": len(text),
                    "line_count": len(lines),
                    "file_hash": file_hash[:8] + "..." if file_hash else None
                }
            )

            reason_codes = set(ap.get("reason_codes") or SAFE_REASON_CODES)
            issue_ids = set(ap.get("issue_ids") or [])
            dry_run = bool(ap.get("dry_run", True))
            include_style = bool(ap.get("include_style", True))
            include_grammar = bool(ap.get("include_grammar", True))

            logger.info(
                "品質修正実行設定",
                extra={
                    "reason_codes": sorted(reason_codes),
                    "issue_ids_count": len(issue_ids),
                    "dry_run": dry_run,
                    "include_style": include_style,
                    "include_grammar": include_grammar
                }
            )

            # 検出再実行（対象行/範囲の特定）
            # 既定で rhythm/readability に加えて style/grammar も含める（安全修正に限定）
            _aspects = ["rhythm", "readability"]
            if include_style:
                _aspects.append("style")
            if include_grammar:
                _aspects.append("grammar")
            detect_req = ToolRequest(
                episode_number=request.episode_number,
                project_name=request.project_name,
                additional_params={
                    **ap,
                    "file_path": str(target_path),
                    "aspects": _aspects,
                    "severity_threshold": "low",
                },
            )
            logger.debug("品質チェック実行（修正対象特定）")
            quality_check_start = time.time()
            detect_res = RunQualityChecksTool().execute(detect_req)
            quality_check_time = time.time() - quality_check_start

            logger.debug(
                "品質チェック完了",
                extra={
                    "execution_time_seconds": quality_check_time,
                    "issues_detected": len(detect_res.issues)
                }
            )

            applicable = [i for i in detect_res.issues if i.type != "summary_metrics"]
            applicable = [i for i in applicable if (getattr(i, "reason_code", i.type) in reason_codes)]
            if issue_ids:
                applicable = [i for i in applicable if getattr(i, "issue_id", None) in issue_ids]

            logger.info(
                "修正対象フィルタリング完了",
                extra={
                    "total_issues": len(detect_res.issues),
                    "applicable_issues": len(applicable),
                    "filtered_by_reason_codes": len(reason_codes) > 0,
                    "filtered_by_issue_ids": len(issue_ids) > 0
                }
            )

            logger.debug("修正処理開始")
            fix_start = time.time()
            fix_result = self._apply_fixes(
                lines,
                applicable,
                # 行幅関連の自動改行は撤廃
                max_sentence_length=int(
                    ap.get(
                        "max_sentence_length",
                        cfg.get("sentence_split", {}).get("target_len", 45),
                    )
                ),
                short_sentence_length=int(
                    ap.get(
                        "short_sentence_length",
                        cfg.get("sentence_merge", {}).get("short_len", 10),
                    )
                ),
                max_commas_per_sentence=int(ap.get("max_commas_per_sentence", 3)),
                enable_sentence_split=bool(ap.get("enable_sentence_split", True)),
                enable_sentence_merge=bool(ap.get("enable_sentence_merge", True)),
                max_merges_per_line=int(
                    ap.get(
                        "max_merges_per_line",
                        cfg.get("sentence_merge", {}).get("max_merges_per_line", 2),
                    )
                ),
                max_splits_per_line=int(
                    ap.get(
                        "max_splits_per_line",
                        cfg.get("sentence_split", {}).get("max_splits_per_line", 2),
                    )
                ),
                skip_dialogue_lines=bool(
                    ap.get(
                        "skip_dialogue_lines",
                        cfg.get("sentence_merge", {}).get("skip_dialogue_lines", True),
                    )
                ),
                cfg=cfg,
            )
            fix_time = time.time() - fix_start

            logger.info(
                "修正処理完了",
                extra={
                    "execution_time_seconds": fix_time,
                    "applied_fixes": fix_result.applied,
                    "skipped_fixes": fix_result.skipped,
                    "notes_count": len(fix_result.notes)
                }
            )

            # 結果をまとめる
            # diffは既定では返さない（トークン節約）。必要時のみ限定返却
            include_diff = bool(ap.get("include_diff", False))
            diff = None
            if include_diff:
                raw = self._make_diff(text, fix_result.fixed_text, target_path)
                max_lines = int(ap.get("max_diff_lines", 400))
                if isinstance(raw, str) and max_lines > 0:
                    lines_lim = raw.splitlines()
                    if len(lines_lim) > max_lines:
                        head = "\n".join(lines_lim[: max_lines // 2])
                        tail = "\n".join(lines_lim[-(max_lines - max_lines // 2) :])
                        diff = head + "\n... (truncated) ...\n" + tail
                    else:
                        diff = raw
                else:
                    diff = raw
            issues = [
                ToolIssue(
                    type="auto_fix_summary",
                    severity="low",
                    message=f"修正:{fix_result.applied}件 / スキップ:{fix_result.skipped}件",
                    suggestion="dry_run=falseで適用可能",
                    file_path=str(target_path),
                    details={
                        "reason_codes": sorted(reason_codes),
                        "issue_ids": sorted(issue_ids) if issue_ids else None,
                        "notes": fix_result.notes,
                        "diff": diff,
                    },
                )
            ]

            written_to = None
            if not dry_run:
                logger.debug("ファイル書き込み開始")
                out = ap.get("output_path")
                if isinstance(out, str) and out:
                    dest = Path(out)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(fix_result.fixed_text, encoding="utf-8")
                    written_to = str(dest)
                    logger.info(
                        "修正結果を別ファイルに保存",
                        extra={"output_path": written_to}
                    )
                else:
                    # 変更が無い場合でも上書きしてパスを返す（E2E検証用）
                    target_path.write_text(fix_result.fixed_text, encoding="utf-8")
                    written_to = str(target_path)
                    logger.info(
                        "修正結果を元ファイルに上書き保存",
                        extra={"file_path": written_to}
                    )

            execution_time = time.time() - start
            logger.info(
                "fix_quality_issues実行完了",
                extra={
                    "execution_time_seconds": execution_time,
                    "total_applied": fix_result.applied,
                    "total_skipped": fix_result.skipped,
                    "dry_run": dry_run,
                    "written_to": written_to
                }
            )

            resp = self._create_response(True, 100.0, issues, start)
            resp.metadata.update(
                {
                    "file_path": str(target_path),
                    "file_hash_before": file_hash,
                    "file_hash_after": hashlib.sha256(fix_result.fixed_text.encode("utf-8")).hexdigest(),
                    "applied": fix_result.applied,
                    "skipped": fix_result.skipped,
                    "dry_run": dry_run,
                    "written_to": written_to,
                    "diff_included": include_diff,
                }
            )
            # PathServiceのフォールバック可視化
            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            logger.error(
                "fix_quality_issues実行エラー",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "episode_number": request.episode_number,
                    "project_name": request.project_name,
                    "execution_time_seconds": time.time() - start
                }
            )
            return self._create_response(False, 0.0, [], start, f"オートフィクスエラー: {e!s}")

    # ---- helpers ----

    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        try:
            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            # PathServiceのフォールバックイベントを収集
            self._ps_collect_fallback(ps)
            return ep
        except Exception:
            return None

    def _apply_fixes(
        self,
        lines: list[str],
        issues: Iterable[ToolIssue],
        *,
        max_sentence_length: int,
        short_sentence_length: int,
        max_commas_per_sentence: int,
        enable_sentence_split: bool,
        enable_sentence_merge: bool,
        max_merges_per_line: int,
        max_splits_per_line: int,
        skip_dialogue_lines: bool,
        cfg: dict[str, Any] | None = None,
    ) -> FixResult:
        logger = get_logger(__name__)
        logger.debug(
            "修正処理パラメータ",
            extra={
                "max_sentence_length": max_sentence_length,
                "short_sentence_length": short_sentence_length,
                "max_commas_per_sentence": max_commas_per_sentence,
                "enable_sentence_split": enable_sentence_split,
                "enable_sentence_merge": enable_sentence_merge,
                "skip_dialogue_lines": skip_dialogue_lines
            }
        )
        # index対象を作る（行単位／範囲単位）
        line_targets = set()
        range_targets: list[tuple[int, int]] = []
        ellipsis_lines = set()
        dash_lines = set()
        # width_lines は撤廃（行幅による改行は行わない）
        split_lines = set()
        merge_lines = set()
        comma_overuse_lines = set()
        trailing_space_lines = set()
        double_space_lines = set()
        tab_lines = set()
        grammar_punct_lines = set()

        for i in issues:
            ln = i.line_number or 0
            if i.reason_code == "ELLIPSIS_STYLE" or i.reason_code == "ELLIPSIS_ODD_COUNT":
                ellipsis_lines.add(ln)
            elif i.reason_code == "DASH_STYLE":
                dash_lines.add(ln)
            # LINE_WIDTH_OVERFLOW は撤廃対象（スキップ）
            elif i.reason_code == "LINE_WIDTH_OVERFLOW":
                continue
            elif i.reason_code in ("CONSECUTIVE_LONG_SENTENCES", "LONG_SENTENCE"):
                if i.end_line_number:
                    for lno in range(ln, i.end_line_number + 1):
                        split_lines.add(lno)
                else:
                    split_lines.add(ln)
            elif i.reason_code == "CONSECUTIVE_SHORT_SENTENCES":
                if i.end_line_number:
                    for lno in range(ln, i.end_line_number + 1):
                        merge_lines.add(lno)
                else:
                    merge_lines.add(ln)
            elif i.reason_code == "COMMA_OVERUSE":
                comma_overuse_lines.add(ln)
            elif i.reason_code == "TRAILING_SPACES":
                trailing_space_lines.add(ln)
            elif i.reason_code == "DOUBLE_SPACES":
                double_space_lines.add(ln)
            elif i.reason_code == "TAB_FOUND":
                tab_lines.add(ln)
            elif i.reason_code == "GRAMMAR_PUNCTUATION":
                grammar_punct_lines.add(ln)
            # 範囲系は今回は対象外（将来拡張）

        original_text = "\n".join(lines)
        fixed_lines = list(lines)
        applied = 0
        skipped = 0
        notes: list[str] = []

        # 0) A40 Stage1 安全正規化（全行に対して無害適用）
        logger.debug("A40 Stage1安全正規化開始")
        #    - 半角!/? → 全角（！/？）
        #    - 会話文末の句点削除（行末の『」。』→『」』）
        #    - 閉じ括弧直前の空白削除（… ）」 → …」）
        # 設定読込（未指定時は既定True）
        stage1_cfg = cfg.get("stage1", {}) if isinstance((cfg or {}).get("stage1", {}), dict) else {}
        indent_cfg = stage1_cfg.get("indent", {}) if isinstance(stage1_cfg.get("indent", {}), dict) else {}
        indent_enable = bool(indent_cfg.get("enable", True))
        indent_style = str(indent_cfg.get("style", "fullwidth"))
        indent_count = int(indent_cfg.get("count", 1))
        skip_dialogue_indent = bool(indent_cfg.get("skip_dialogue", False))
        skip_markdown_blocks = bool(indent_cfg.get("skip_markdown_blocks", True))
        punct_cfg = stage1_cfg.get("punctuation", {}) if isinstance(stage1_cfg.get("punctuation", {}), dict) else {}
        exq_space_enable = bool(punct_cfg.get("exclamation_question_fullwidth_space", True))

        in_code_block = False
        for idx in range(1, len(fixed_lines) + 1):
            s = fixed_lines[idx - 1]
            before = s
            # コードブロック判定
            if s.strip().startswith("```"):
                in_code_block = not in_code_block
                fixed_lines[idx - 1] = s
                continue
            if in_code_block and skip_markdown_blocks:
                continue

            # 半角記号の全角統一
            s = s.replace("!", "！").replace("?", "？")

            # 感嘆符・疑問符の後に全角スペース（直後が空白や終端・句読点・閉じ括弧でない場合）
            if exq_space_enable:
                # 末尾や閉じ記号・空白の直前では付与しない
                s = re.sub(r"([！？])(?![ 　』」）】、。！？\n]|$)", r"\1　", s)

            # 行末の会話文末句点削除
            s = re.sub(r"」。\s*$", "」", s)
            # 閉じ括弧直前の空白削除（全体）
            s = re.sub(r"\s+([」』）】])", r"\1", s)

            # 段落頭の字下げ統一
            if indent_enable:
                # 見出し/箇条書き/引用/表などは対象外
                stripped = s.lstrip(" 　")
                if s.strip() and not s.lstrip().startswith(("#", ">", "|")):
                    is_list = bool(re.match(r"^\s*([-*+]\s|\d+[\.)]\s)", s))
                    is_code_fence = s.strip().startswith("```")
                    if not is_list and not is_code_fence:
                        # 会話行の字下げをスキップする設定
                        if not (skip_dialogue_indent and stripped.startswith(("「", "『"))):
                            indent_prefix = ("　" * max(0, indent_count)) if indent_style == "fullwidth" else (" " * max(0, indent_count * 2))
                            # 既存の先頭全角/半角スペースは除去してから付与
                            s = indent_prefix + stripped

            if s != before:
                fixed_lines[idx - 1] = s
                applied += 1
                notes.append(f"A40 normalization applied at line {idx}")
                logger.debug(
                    "A40正規化適用",
                    extra={"line_number": idx, "type": "normalization"}
                )

        # 1) 三点リーダ統一 + 奇数個調整
        if ellipsis_lines:
            logger.debug(
                "三点リーダ統一処理開始",
                extra={"target_lines": len(ellipsis_lines)}
            )
        for ln in sorted(ellipsis_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            src = fixed_lines[ln - 1]
            before = src
            # ... / ・・・ -> ……
            src = src.replace("...", "……").replace("・・・", "……")
            # 連続する「…」を偶数化
            def evenize(match: re.Match[str]) -> str:
                n = len(match.group(0))
                m = n + (n % 2)
                return "…" * m
            src = re.sub(r"…+", evenize, src)
            if src != before:
                fixed_lines[ln - 1] = src
                applied += 1
                notes.append(f"ELLIPSIS normalized at line {ln}")
                logger.debug(
                    "三点リーダ正規化適用",
                    extra={"line_number": ln, "before": before, "after": src}
                )

        # 2) ダッシュ統一
        if dash_lines:
            logger.debug(
                "ダッシュ統一処理開始",
                extra={"target_lines": len(dash_lines)}
            )
        for ln in sorted(dash_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            s = fixed_lines[ln - 1]
            before = s
            # 既存の『――』は維持しつつ、単体の—/－を『――』に
            # 一旦プレースホルダで既存の『――』を保護
            placeholder = "__EMDASH_PAIR__"
            s = s.replace("――", placeholder)
            s = s.replace("—", "――").replace("－", "――")
            s = s.replace(placeholder, "――")
            if s != before:
                fixed_lines[ln - 1] = s
                applied += 1
                notes.append(f"DASH normalized at line {ln}")
                logger.debug(
                    "ダッシュ正規化適用",
                    extra={"line_number": ln, "before": before, "after": s}
                )

        # 3) 句読点重複の正規化（grammar: punctuation）
        if grammar_punct_lines:
            logger.debug(
                "句読点重複正規化処理開始",
                extra={"target_lines": len(grammar_punct_lines)}
            )
        for ln in sorted(grammar_punct_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            s = fixed_lines[ln - 1]
            if skip_dialogue_lines and ("「" in s and "」" in s):
                continue
            before = s
            s = re.sub(r"、{2,}", "、", s)
            s = re.sub(r"。{2,}", "。", s)
            if s != before:
                fixed_lines[ln - 1] = s
                applied += 1
                notes.append(f"Normalized punctuation duplicates at line {ln}")
                logger.debug(
                    "句読点重複正規化適用",
                    extra={"line_number": ln, "before": before, "after": s}
                )

        # 3.5) 行幅改行は撤廃（日本語文への自動改行は行わない）

        # 4) 長文分割
        if enable_sentence_split:
            logger.debug(
                "長文分割処理開始",
                extra={
                    "target_lines": len(split_lines),
                    "max_sentence_length": max_sentence_length
                }
            )
            # grammarの句読点不足で長大な行も対象に追加
            extra_split_lines = set()
            for ln in sorted(grammar_punct_lines):
                if 1 <= ln <= len(fixed_lines):
                    s = fixed_lines[ln - 1]
                    if ("、" not in s and "。" not in s) and len(s) > max_sentence_length:
                        extra_split_lines.add(ln)
            for ln in sorted(split_lines | extra_split_lines):
                if not (1 <= ln <= len(fixed_lines)):
                    skipped += 1
                    continue
                s = fixed_lines[ln - 1]
                if skip_dialogue_lines and ("「" in s and "」" in s):
                    continue
                before = s
                s, cnt = self._split_long_sentences_in_line(
                    s, target_len=max_sentence_length, max_splits=max_splits_per_line
                )
                if s != before and cnt > 0:
                    fixed_lines[ln - 1] = s
                    applied += cnt
                    notes.append(f"Split long sentence at line {ln} x{cnt}")
                    logger.debug(
                        "長文分割適用",
                        extra={"line_number": ln, "split_count": cnt}
                    )

        # 5) 短文連結
        if enable_sentence_merge:
            logger.debug(
                "短文連結処理開始",
                extra={
                    "target_lines": len(merge_lines),
                    "short_sentence_length": short_sentence_length
                }
            )
            for ln in sorted(merge_lines):
                if not (1 <= ln <= len(fixed_lines)):
                    skipped += 1
                    continue
                s = fixed_lines[ln - 1]
                if skip_dialogue_lines and ("「" in s and "」" in s):
                    continue
                before = s
                s, cnt = self._merge_short_sentences_in_line(
                    s,
                    short_len=short_sentence_length,
                    max_merges=max_merges_per_line,
                )
                if s != before and cnt > 0:
                    fixed_lines[ln - 1] = s
                    applied += cnt
                    notes.append(f"Merged short sentences at line {ln} x{cnt}")
                    logger.debug(
                        "短文連結適用",
                        extra={"line_number": ln, "merge_count": cnt}
                    )

        # 6) 読点過多の安全分割
        if comma_overuse_lines:
            logger.debug(
                "読点過多分割処理開始",
                extra={
                    "target_lines": len(comma_overuse_lines),
                    "max_commas_per_sentence": max_commas_per_sentence
                }
            )
        for ln in sorted(comma_overuse_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            s = fixed_lines[ln - 1]
            if skip_dialogue_lines and ("「" in s and "」" in s):
                continue
            before = s
            s, cnt = self._split_comma_overuse(s, max_commas_per_sentence)
            if s != before and cnt > 0:
                fixed_lines[ln - 1] = s
                applied += cnt
                notes.append(f"Split comma overuse at line {ln} x{cnt}")
                logger.debug(
                    "読点過多分割適用",
                    extra={"line_number": ln, "split_count": cnt}
                )

        # 7) 末尾空白除去
        if trailing_space_lines:
            logger.debug(
                "末尾空白除去処理開始",
                extra={"target_lines": len(trailing_space_lines)}
            )
        for ln in sorted(trailing_space_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            s = fixed_lines[ln - 1]
            ns = re.sub(r"\s+$", "", s)
            if ns != s:
                fixed_lines[ln - 1] = ns
                applied += 1
                notes.append(f"Trimmed trailing spaces at line {ln}")
                logger.debug(
                    "末尾空白除去適用",
                    extra={"line_number": ln}
                )

        # 8) タブ→空白、連続半角スペース圧縮
        if tab_lines or double_space_lines:
            logger.debug(
                "タブ・スペース正規化処理開始",
                extra={
                    "tab_lines": len(tab_lines),
                    "double_space_lines": len(double_space_lines)
                }
            )
        for ln in sorted(tab_lines | double_space_lines):
            if not (1 <= ln <= len(fixed_lines)):
                skipped += 1
                continue
            s = fixed_lines[ln - 1]
            before = s
            s = s.replace("\t", "  ")  # タブを2スペースに
            s = re.sub(r" {2,}", " ", s)  # 連続半角スペースを1に
            if s != before:
                fixed_lines[ln - 1] = s
                applied += 1
                notes.append(f"Normalized spaces/tabs at line {ln}")
                logger.debug(
                    "タブ・スペース正規化適用",
                    extra={"line_number": ln, "before": before, "after": s}
                )

        # 9) 連続空行の圧縮（全体パス）
        # EMPTY_LINE_RUNS が1件でもあれば実施
        if any(i.reason_code == "EMPTY_LINE_RUNS" for i in issues):
            logger.debug("連続空行圧縮処理開始")
            compacted: list[str] = []
            blank_seen = False
            for line in fixed_lines:
                if line.strip() == "":
                    if not blank_seen:
                        compacted.append("")
                        blank_seen = True
                else:
                    compacted.append(line)
                    blank_seen = False
            if compacted != fixed_lines:
                fixed_lines[:] = compacted
                notes.append("Compacted empty line runs")
                logger.debug(
                    "連続空行圧縮適用",
                    extra={
                        "before_lines": len(fixed_lines),
                        "after_lines": len(compacted)
                    }
                )

        fixed_text = "\n".join(fixed_lines)

        logger.info(
            "修正処理完了",
            extra={
                "total_applied": applied,
                "total_skipped": skipped,
                "notes_count": len(notes),
                "content_changed": original_text != fixed_text
            }
        )

        return FixResult(original_text, fixed_text, applied, skipped, notes)

    def _wrap_japanese_line(self, s: str, max_width: int) -> str:
        # DDD: ドメインサービスへ委譲
        from noveler.domain.services.text_wrapping_service import wrap_japanese_line
        return wrap_japanese_line(s, max_width)

    def _split_long_sentences_in_line(
        self, s: str, *, target_len: int, max_splits: int
    ) -> tuple[str, int]:
        analyzer = None
        if _MORPH_AVAILABLE:
            try:
                candidate = _create_analyzer()
                if candidate is not None and getattr(candidate, "initialized", False):
                    analyzer = candidate
            except Exception:
                analyzer = None

        parts = s.split("。")
        new_parts = []
        split_count = 0
        for p in parts:
            p = p.strip()
            if not p:
                continue
            cur = p
            local_splits = 0
            while len(cur) > target_len and local_splits < max_splits:
                cut_pos = self._find_split_position(cur, target_len, analyzer)
                if not isinstance(cut_pos, int):
                    cut_pos = target_len
                cut_pos = max(1, min(len(cur) - 1, cut_pos))
                left = cur[:cut_pos].rstrip("、")
                right = cur[cut_pos:].lstrip()
                if not left or not right:
                    # これ以上安全に分割できない場合は中断
                    break
                new_parts.append(left)
                cur = right
                local_splits += 1
                split_count += 1
            if cur:
                new_parts.append(cur)
        if not new_parts:
            return s, 0
        fixed = "。".join(new_parts)
        if s.endswith("。"):
            fixed += "。"
        return fixed, split_count

    def _find_split_position(self, cur: str, target_len: int, analyzer: Any | None) -> int:
        candidates: list[tuple[float, int]] = []
        length = len(cur)
        if analyzer is not None:
            try:
                tokens = analyzer.analyze(cur)
            except Exception:
                tokens = []
            acc = 0
            for idx, token in enumerate(tokens):
                surface = getattr(token, "surface", "")
                pos = getattr(token, "part_of_speech", getattr(token, "pos", ""))
                pos_head = pos.split(",")[0] if isinstance(pos, str) else str(pos)
                acc += len(surface)
                if acc <= 0 or acc >= length:
                    continue
                score = self._score_morph_boundary(surface, pos_head, tokens, idx)
                if score <= 0:
                    continue
                distance = abs(acc - target_len) / max(length, 1)
                adjusted = score - (distance * 0.8)
                if adjusted > 0:
                    candidates.append((adjusted, acc))
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1]
        return self._fallback_split_position(cur, target_len)

    def _score_morph_boundary(
        self,
        surface: str,
        pos_head: str,
        tokens: list[Any],
        idx: int,
    ) -> float:
        token = surface.strip()
        if not token:
            return 0.0
        if token in BOUNDARY_LOW_SURFACES:
            # 極力避ける（他候補が無い場合のみ採用される程度のスコア）
            base = 0.2
        elif token in BOUNDARY_HIGH_SURFACES or pos_head == "助動詞":
            base = 3.0
        elif token in BOUNDARY_MEDIUM_SURFACES or pos_head == "接続詞":
            base = 2.0
        elif pos_head == "助詞":
            if token in {"て", "ので", "から"}:
                base = 1.5
            else:
                base = 0.8
        elif pos_head == "動詞" and token.endswith(("た", "る", "す")):
            base = 1.2
        else:
            base = 0.0

        if base <= 0:
            return 0.0

        prefer_pos = set(self._morph_settings.get("sentence_split", {}).get("use_pos", []))
        if prefer_pos and pos_head in prefer_pos:
            base = max(base, 2.5)

        # 次の語が接続詞の場合は文の切れ目になりやすいので加点
        if idx + 1 < len(tokens):
            next_surface = getattr(tokens[idx + 1], "surface", "")
            next_pos = getattr(tokens[idx + 1], "part_of_speech", getattr(tokens[idx + 1], "pos", ""))
            next_head = next_pos.split(",")[0] if isinstance(next_pos, str) else str(next_pos)
            if next_head == "接続詞" or next_surface in {"そして", "しかし", "でも"}:
                base += 0.7

        return base

    def _fallback_split_position(self, cur: str, target_len: int) -> int:
        length = len(cur)
        if length <= 1:
            return max(0, length - 1)

        window = max(10, target_len // 2)
        start_back = max(0, target_len - window)
        start_forward = min(length, target_len + window)

        # 読点があればそこを優先（元実装との互換）
        for idx in range(target_len, start_back - 1, -1):
            if idx < length and cur[idx] == "、":
                return idx + 1
        for idx in range(target_len, start_forward):
            if idx < length and cur[idx] == "、":
                return idx + 1

        # 文末候補の語尾パターンを探索
        for idx in range(target_len, start_back - 1, -1):
            prefix = cur[:idx]
            for ending in FALLBACK_ENDINGS:
                if prefix.endswith(ending):
                    return idx

        # 最終手段: 目標長付近でカット（極力中央寄せ）
        suggested = max(target_len, max(5, target_len // 2))
        return min(max(suggested, 1), length - 1)

    def _merge_short_sentences_in_line(
        self, s: str, *, short_len: int, max_merges: int
    ) -> tuple[str, int]:
        # 連続する短文（短文。短文。）を「、」で連結（最大回数）
        parts = [p for p in s.split("。") if p is not None]
        if len(parts) <= 1:
            return s, 0
        merged: list[str] = []
        merges = 0
        i = 0
        while i < len(parts):
            cur = parts[i].strip()
            if not cur:
                i += 1
                continue
            if i + 1 < len(parts) and merges < max_merges:
                nxt = parts[i + 1].strip()
                # どちらも短く、次が台詞開始等でない
                if len(cur) <= short_len and len(nxt) <= short_len and not nxt.startswith("「"):
                    merged.append(cur + "、" + nxt)
                    merges += 1
                    i += 2
                    continue
            merged.append(cur)
            i += 1
        out = "。".join([m for m in merged if m])
        if s.endswith("。") and not out.endswith("。"):
            out += "。"
        return out, merges

    def _split_by_punct(self, cur: str, target_len: int) -> tuple[tuple[str, str], int]:
        # 近傍の読点で分割（なければ固定長）
        idx = -1
        start = max(0, int(len(cur) * 2 / 3) - 1)
        for i in range(start, max(-1, start - 30), -1):
            if cur[i] == "、":
                idx = i
                break
        if idx == -1:
            for i in range(start, min(len(cur), start + 30)):
                if cur[i] == "、":
                    idx = i
                    break
        if idx == -1:
            idx = target_len
        left = cur[: idx + 1].rstrip("、")
        right = cur[idx + 1 :].lstrip()
        return (left, right), 1

    def _split_comma_overuse(self, s: str, max_commas: int) -> tuple[str, int]:
        # 「。」で区切り、各文内の読点がmaxを超える場合に複数回分割
        segs = s.split("。")
        out_segs = []
        splits = 0
        for seg in segs:
            cur = seg.strip()
            if not cur:
                continue
            while cur.count("、") > max_commas:
                (left, right), add = self._split_by_punct(cur, max(1, len(cur)//2))
                out_segs.append(left)
                cur = right
                splits += add
            if cur:
                out_segs.append(cur)
        if not out_segs:
            return s, 0
        out = "。".join(out_segs)
        if s.endswith("。") and not out.endswith("。"):
            out += "。"
        return out, splits

    def _make_diff(self, before: str, after: str, path: Path) -> str:
        if before == after:
            return ""
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
        return "".join(diff)

    def _load_config_overrides(self) -> dict[str, Any]:
        """.novelerrc から fix_quality_issues 関連既定値を読み込み

        期待キー:
        - sentence_split: { use_pos: [...], max_splits_per_line: int, target_len: int }
        - sentence_merge: { short_len: int, max_merges_per_line: int, skip_dialogue_lines: bool }
        - line_wrap: { enabled: bool, max_line_width: int }  # 廃止
        - morphology: { sentence_split: { use_pos: [...] } }
        - stage1:
            indent: { enable: bool, style: "fullwidth"|"spaces", count: int, skip_dialogue: bool, skip_markdown_blocks: bool }
            punctuation: { exclamation_question_fullwidth_space: bool }
        互換: fix_quality_issues セクション配下にも同キーを許容
        """
        out: dict[str, Any] = {"defaults": {}, "sentence_split": {}, "sentence_merge": {}, "morphology": {}, "stage1": {}}
        try:
            ps = create_path_service()
            root = ps.project_root
            import json as _json
            try:
                import yaml as _yaml
            except Exception:  # pragma: no cover
                _yaml = None

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
                if not isinstance(data, dict):
                    continue
                fx = data.get("fix_quality_issues", {}) if isinstance(data.get("fix_quality_issues", {}), dict) else {}
                # top-level
                out["sentence_split"].update({k: v for k, v in (data.get("sentence_split", {}) or {}).items() if v is not None})
                out["sentence_merge"].update({k: v for k, v in (data.get("sentence_merge", {}) or {}).items() if v is not None})
                # 行幅/自動改行設定は読み込まない
                out["morphology"].update({k: v for k, v in (data.get("morphology", {}) or {}).items() if v is not None})
                # nested
                out["sentence_split"].update({k: v for k, v in (fx.get("sentence_split", {}) or {}).items() if v is not None})
                out["sentence_merge"].update({k: v for k, v in (fx.get("sentence_merge", {}) or {}).items() if v is not None})
                # 行幅/自動改行設定は読み込まない
                out["morphology"].update({k: v for k, v in (fx.get("morphology", {}) or {}).items() if v is not None})
                out["stage1"].update({k: v for k, v in (data.get("stage1", {}) or {}).items() if v is not None})
                out["stage1"].update({k: v for k, v in (fx.get("stage1", {}) or {}).items() if v is not None})

            # defaults へミラー（従来パラメータ名に合わせる）
            if "target_len" in out["sentence_split"]:
                out["defaults"]["max_sentence_length"] = out["sentence_split"]["target_len"]
            if "max_splits_per_line" in out["sentence_split"]:
                out["defaults"]["max_splits_per_line"] = out["sentence_split"]["max_splits_per_line"]
            if "short_len" in out["sentence_merge"]:
                out["defaults"]["short_sentence_length"] = out["sentence_merge"]["short_len"]
            if "max_merges_per_line" in out["sentence_merge"]:
                out["defaults"]["max_merges_per_line"] = out["sentence_merge"]["max_merges_per_line"]
            if "skip_dialogue_lines" in out["sentence_merge"]:
                out["defaults"]["skip_dialogue_lines"] = out["sentence_merge"]["skip_dialogue_lines"]
            # 行幅/自動改行設定はdefaultsへもミラーしない
            # 既定（stage1）
            if "indent" not in out["stage1"]:
                out["stage1"]["indent"] = {}
            if "punctuation" not in out["stage1"]:
                out["stage1"]["punctuation"] = {}
            out["stage1"]["indent"].setdefault("enable", True)
            out["stage1"]["indent"].setdefault("style", "fullwidth")
            out["stage1"]["indent"].setdefault("count", 1)
            out["stage1"]["indent"].setdefault("skip_dialogue", False)
            out["stage1"]["indent"].setdefault("skip_markdown_blocks", True)
            out["stage1"]["punctuation"].setdefault("exclamation_question_fullwidth_space", True)
            return out
        except Exception:
            return out
