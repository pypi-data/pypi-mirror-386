#!/usr/bin/env python3
"""Plot adherence validation use case.

Implements SPEC-PLOT-ADHERENCE-001 to validate manuscripts against plot requirements and integrate
with the TenStageEpisodeWriting workflow.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.application.services.llm_plot_adherence_evaluator import (
    LLMAdherenceConfig,
    LLMPlotAdherenceEvaluator,
)
from noveler.application.validators.evidence_verifier import EvidenceVerifier
from noveler.application.validators.plot_adherence_validator import PlotAdherenceValidator
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

# Per B20/B30 quality guidelines, use the unified logger service (no fallback).
from noveler.presentation.shared.shared_utilities import get_logger


@dataclass
class PlotAdherenceRequest:
    """Input payload for plot adherence validation.

    Attributes:
        episode_number: Episode identifier to validate.
        manuscript_content: Manuscript text being evaluated.
        project_root: Root directory of the project.
        include_suggestions: Whether improvement suggestions should be returned.
        minimum_score_threshold: Minimum adherence score required to pass.
    """

    episode_number: int
    manuscript_content: str
    project_root: Path
    include_suggestions: bool = True
    minimum_score_threshold: float = 95.0


@dataclass
class PlotAdherenceResponse:
    """Result payload produced by the plot adherence validation.

    Attributes:
        success: Indicates whether validation completed successfully.
        adherence_score: Overall adherence score assigned to the manuscript.
        plot_elements_checked: Number of plot elements evaluated.
        missing_elements: Elements that were not found in the manuscript.
        suggestions: Improvement suggestions produced by the validation.
        validation_result: Raw validation structure for downstream consumers.
        error_message: Error message when validation fails.
        llm_used: Flag indicating whether LLM assistance was used.
        llm_score: Score provided by the LLM, when available.
        override_applied: Indicates if LLM feedback altered the final outcome.
        override_reason: Reason describing why an override was applied.
    """

    success: bool
    adherence_score: float
    plot_elements_checked: int
    missing_elements: list[str]
    suggestions: list[str]
    validation_result: Any = None
    error_message: str = ""
    # Additional metadata
    llm_used: bool = False
    llm_score: float | None = None
    override_applied: bool = False
    override_reason: str = ""

    def is_acceptable_quality(self) -> bool:
        """Return whether the adherence score meets the quality threshold."""
        return self.adherence_score >= 95.0

    def get_quality_summary(self) -> str:
        """Return a human-readable summary of the adherence result."""
        if self.adherence_score >= 95.0:
            return f"✅ 優秀 (準拠率: {self.adherence_score:.1f}%)"
        if self.adherence_score >= 80.0:
            return f"⚠️ 要改善 (準拠率: {self.adherence_score:.1f}%)"
        return f"❌ 修正必須 (準拠率: {self.adherence_score:.1f}%)"


class ValidatePlotAdherenceUseCase(AbstractUseCase[PlotAdherenceRequest, PlotAdherenceResponse]):
    """Coordinate local and LLM-assisted plot adherence validation."""

    def __init__(
        self, logger_service: object | None = None, unit_of_work: object | None = None, **kwargs: object
    ) -> None:
        super().__init__(logger_service=logger_service, unit_of_work=unit_of_work, **kwargs)
        self.logger = get_logger(__name__)

    async def execute(self, request: PlotAdherenceRequest) -> PlotAdherenceResponse:  # noqa: C901, PLR0912, PLR0915
        """Run local and LLM-assisted plot adherence validation.

        Args:
            request: Plot adherence validation request payload.

        Returns:
            PlotAdherenceResponse: Validation result translated for callers.
        """
        try:
            self.logger.info("プロット準拠検証開始 - 第%03d話", request.episode_number)

            # 1) Local validation (official evaluation)
            local_result = await self._run_local_validation(
                request.project_root, request.episode_number, request.manuscript_content
            )

            response = PlotAdherenceResponse(
                success=True,
                adherence_score=local_result["score"],
                plot_elements_checked=local_result["total_elements"],
                missing_elements=local_result["missing_elements"],
                suggestions=(local_result["suggestions"] if request.include_suggestions else []),
                validation_result=local_result.get("raw"),
            )

            # 2) Optional LLM-assisted validation (gated evaluation)
            cfg = get_configuration_manager()
            use_llm = bool(cfg.get_default_setting("plot_adherence", "use_llm", True))
            mode = (cfg.get_default_setting("plot_adherence", "mode", "gated") or "gated").strip().lower()
            band_val = cfg.get_default_setting("plot_adherence", "threshold_band", 5.0)
            try:
                threshold_band = float(band_val) if band_val is not None else 5.0
            except Exception:
                threshold_band = 5.0
            override_policy = (
                (cfg.get_default_setting("plot_adherence", "override_policy", "fail_only") or "fail_only")
                .strip()
                .lower()
            )
            temp_val = cfg.get_default_setting("plot_adherence", "llm_temperature", 0.1)
            try:
                temperature = float(temp_val) if temp_val is not None else 0.1
            except Exception:
                temperature = 0.1

            should_call_llm = False
            local_score = float(response.adherence_score)
            threshold = float(request.minimum_score_threshold)
            if use_llm:
                if mode == "strict":
                    should_call_llm = True
                elif mode == "gated":
                    if abs(local_score - threshold) <= threshold_band or len(response.missing_elements) > 0:
                        should_call_llm = True
                elif mode == "fast":
                    should_call_llm = False

            if should_call_llm:
                # Retrieve chunk/cache/evidence settings for the LLM evaluation
                chunk_cfg = cfg.get_default_setting("plot_adherence", "chunk", {}) or {}
                cache_cfg = cfg.get_default_setting("plot_adherence", "cache", {}) or {}
                evidence_cfg = cfg.get_default_setting("plot_adherence", "evidence", {}) or {}
                min_verified_ratio = 0.0
                try:
                    mvr = evidence_cfg.get("min_verified_ratio")
                    min_verified_ratio = float(mvr) if mvr is not None else 0.0
                except Exception:
                    min_verified_ratio = 0.0

                # Chunking configuration
                chunk_enabled = bool(chunk_cfg.get("enabled", True))
                chunk_size = int(chunk_cfg.get("size_chars", 3500) or 3500)
                chunk_overlap = int(chunk_cfg.get("overlap_chars", 400) or 400)

                # Derive cache key from manuscript, episode, and configuration fingerprint
                fingerprint_data = {
                    "mode": mode,
                    "threshold_band": threshold_band,
                    "temperature": temperature,
                    "chunk": {
                        "enabled": chunk_enabled,
                        "size": chunk_size,
                        "overlap": chunk_overlap,
                    },
                    "override_policy": override_policy,
                }
                cache_key_src = (
                    f"EP{request.episode_number}|" + request.manuscript_content + "|" + json.dumps(fingerprint_data, sort_keys=True)
                )
                key_hash = hashlib.sha256(cache_key_src.encode("utf-8")).hexdigest()[:16]
                ps = create_path_service(request.project_root)
                cache_dir = ps.get_noveler_output_dir() / "checks" / "cache" / "plot_adherence"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path = cache_dir / f"EP{request.episode_number:03d}_{key_hash}.json"

                llm_data: dict[str, Any]
                loaded_from_cache = False
                if bool(cache_cfg.get("enabled", True)) and cache_path.exists():
                    try:
                        with cache_path.open("r", encoding="utf-8") as f:
                            llm_data = json.load(f)
                        loaded_from_cache = True
                    except Exception:
                        llm_data = {}
                        loaded_from_cache = False
                else:
                    llm_data = {}

                if not llm_data:
                    # Execute LLM evaluation (chunk analysis with aggregation)
                    llm_config = LLMAdherenceConfig(mode=mode, temperature=temperature)
                    llm_eval = LLMPlotAdherenceEvaluator(llm_config)
                    project_name = request.project_root.name

                    chunks: list[tuple[int, str]]
                    if chunk_enabled and len(request.manuscript_content) > chunk_size:
                        chunks = self._split_chunks(request.manuscript_content, chunk_size, chunk_overlap)
                    else:
                        chunks = [(0, request.manuscript_content)]

                    chunk_results: list[dict[str, Any]] = []
                    for offset, text in chunks:
                        result = await llm_eval.evaluate(
                            episode_number=request.episode_number,
                            manuscript_content=text,
                            project_root=request.project_root,
                            project_name=project_name,
                        )
                        # Adjust evidence offsets from chunk-local coordinates to manuscript-global coordinates
                        ev_list = []
                        for ev in result.get("evidence", []) or []:
                            try:
                                st = ev.get("start")
                                en = ev.get("end")
                                ev = dict(ev)
                                if isinstance(st, (int, float)):
                                    ev["start"] = int(st) + offset
                                if isinstance(en, (int, float)):
                                    ev["end"] = int(en) + offset
                            except Exception:
                                pass
                            ev_list.append(ev)
                        result["evidence"] = ev_list
                        result["_chunk"] = {"offset": offset, "length": len(text)}
                        chunk_results.append(result)

                    llm_data = self._aggregate_chunk_results(chunk_results)

                    # Persist evaluation cache if enabled
                    if bool(cache_cfg.get("enabled", True)):
                        try:
                            with cache_path.open("w", encoding="utf-8") as f:
                                json.dump(
                                    {
                                        **llm_data,
                                        "_meta": {
                                            "hash": key_hash,
                                            "episode": request.episode_number,
                                            "created": True,
                                        },
                                    },
                                    f,
                                    ensure_ascii=False,
                                    indent=2,
                                )
                        except Exception:
                            self.logger.debug("LLMキャッシュの保存に失敗しました", exc_info=True)

                response.llm_used = True
                try:
                    response.llm_score = float(llm_data.get("score")) if llm_data.get("score") is not None else None
                except Exception:
                    response.llm_score = None

                # Verify evidence to gate LLM advice
                verified_ratio = 0.0
                try:
                    verifier = EvidenceVerifier()
                    ver = verifier.verify(request.manuscript_content, llm_data.get("evidence", []))
                    verified_ratio = ver.ratio()
                except Exception:
                    self.logger.debug("LLMエビデンス検証に失敗しました", exc_info=True)

                # 3) Apply override policy when the LLM identifies critical failures
                if override_policy in ("fail_only", "any") and verified_ratio >= min_verified_ratio:
                    llm_missing = llm_data.get("missing_elements") or []
                    llm_score_effective = response.llm_score if response.llm_score is not None else local_score
                    if (llm_missing and local_score >= threshold) or (llm_score_effective < threshold <= local_score):
                        response.override_applied = True
                        response.override_reason = "llm_detected_missing_or_low_score"
                        # スコアはローカルを維持。助言はマージ。
                        llm_suggestions = llm_data.get("suggestions") or []
                        if request.include_suggestions and llm_suggestions:
                            response.suggestions.extend([s for s in llm_suggestions if s not in response.suggestions])

            # Log the final quality summary
            self.logger.info("プロット準拠検証完了 - %s", response.get_quality_summary())

            return response

        except Exception:
            self.logger.exception("プロット準拠検証エラー")
            return PlotAdherenceResponse(
                success=False,
                adherence_score=0.0,
                plot_elements_checked=0,
                missing_elements=[],
                suggestions=[],
                error_message="プロット準拠検証エラー",
            )

    def generate_adherence_report(self, response: PlotAdherenceResponse) -> str:
        """Build a formatted report describing the adherence outcome.

        Args:
            response: Validation response payload.

        Returns:
            str: Human-readable report.
        """
        if not response.success:
            return f"❌ プロット準拠検証失敗: {response.error_message}"

        report_lines = [
            "📊 プロット準拠検証レポート",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"✅ {response.get_quality_summary()}",
            f"📋 検証要素数: {response.plot_elements_checked}個",
            "",
        ]

        if response.missing_elements:
            report_lines.extend(["⚠️ 不足要素:", *[f"  - {element}" for element in response.missing_elements], ""])

        if response.suggestions:
            report_lines.extend(["💡 改善提案:", *[f"  - {suggestion}" for suggestion in response.suggestions], ""])

        if response.llm_used:
            report_lines.append("🧠 LLM補助: 有効")
            if response.llm_score is not None:
                report_lines.append(f"  - LLMスコア: {response.llm_score:.1f}")
            if response.override_applied:
                report_lines.append(f"  - 公式判定: ローカル維持（Fail強化: {response.override_reason}）")

        return "\n".join(report_lines)

    # ===== Internal implementation (local validation) =====
    async def _run_local_validation(self, project_root: Path, episode_number: int, manuscript: str) -> dict[str, Any]:
        """Run the local (official) plot adherence validation."""
        validator = PlotAdherenceValidator()
        plot_data = self._load_episode_plot_data(project_root, episode_number)
        validation_result = await validator.validate_adherence(
            episode_number=episode_number,
            manuscript_content=manuscript,
            plot_data=plot_data,
            project_root=project_root,
        )
        return {
            "score": float(
                validation_result.adherence_score.total_score
                if hasattr(validation_result.adherence_score, "total_score")
                else validation_result.adherence_score
            ),
            "total_elements": getattr(validation_result.adherence_score, "total_count", 0),
            "missing_elements": getattr(validation_result, "missing_elements", []) or [],
            "suggestions": getattr(validation_result, "improvement_suggestions", []) or [],
            "raw": validation_result,
        }

    def _load_episode_plot_data(self, project_root: Path, episode_number: int) -> dict[str, Any]:
        """Load episode plot data from YAML files with a fallback."""
        try:
            ps = create_path_service(project_root)
            ep_dir = ps.get_episode_plots_dir()
            import re

            pattern = re.compile(rf"^第{episode_number:03d}話_.*\.yaml$")
            candidates = [p for p in ep_dir.glob("*.yaml") if pattern.match(p.name)]
            if candidates:
                import yaml

                with candidates[0].open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return {
                    "key_events": data.get("key_events", []) or [],
                    "character_development": data.get("character_development", []) or [],
                    "world_building": data.get("world_building", []) or [],
                    "foreshadowing": data.get("foreshadowing", []) or [],
                }
        except Exception:
            self.logger.debug("話別プロットの読込に失敗しました（フォールバック適用）", exc_info=True)

        # Fallback default plot requirements (simplified)
        return {
            "key_events": ["序盤の事件", "中盤の転換", "終盤の決着"],
            "character_development": ["主人公の変化"],
            "world_building": ["舞台の描写"],
            "foreshadowing": ["後の展開の示唆"],
        }

    # ===== Internal implementation (LLM assistance) =====
    def _split_chunks(self, text: str, size: int, overlap: int) -> list[tuple[int, str]]:
        """Split text into overlapping chunks returning pairs of (offset, chunk)."""
        if size <= 0:
            return [(0, text)]
        res: list[tuple[int, str]] = []
        n = len(text)
        i = 0
        step = max(1, size - max(0, overlap))
        while i < n:
            chunk = text[i : i + size]
            if not chunk:
                break
            res.append((i, chunk))
            if i + size >= n:
                break
            i += step
        return res

    def _aggregate_chunk_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate chunk-level LLM evaluation results into a single structure."""
        missing: list[str] = []
        evidence: list[dict[str, Any]] = []
        suggestions: list[str] = []

        # Aggregate the maximum score observed for each plot element
        per_element_max: dict[str, float] = {}
        per_element_seen = False

        # Fallback aggregation: chunk-length weighted average
        total_weight = 0
        score_sum = 0.0

        for r in results:
            # Scores per plot element
            scores_by_element = r.get("scores_by_element") or {}
            if isinstance(scores_by_element, dict) and scores_by_element:
                per_element_seen = True
                for elem, val in scores_by_element.items():
                    try:
                        fval = float(val)
                    except Exception:
                        continue
                    if elem not in per_element_max or fval > per_element_max[elem]:
                        per_element_max[elem] = fval

            # Fallback aggregation using chunk-length weighted average
            ch = r.get("_chunk") or {}
            w = int(ch.get("length", 0) or 0)
            s = r.get("score")
            if s is not None and w > 0:
                try:
                    score_sum += float(s) * w
                    total_weight += w
                except Exception:
                    pass

            # Normalize and deduplicate missing elements
            for e in r.get("missing_elements", []) or []:
                e_norm = str(e).strip()
                if e_norm and e_norm not in missing:
                    missing.append(e_norm)
            # Combine evidence entries; duplicates are handled later during verification
            for ev in r.get("evidence", []) or []:
                evidence.append(ev)
            # Merge suggestions, ensuring uniqueness
            for s in r.get("suggestions", []) or []:
                s_norm = str(s).strip()
                if s_norm and s_norm not in suggestions:
                    suggestions.append(s_norm)

        # Determine aggregated score
        agg_score: float | None
        if per_element_seen and per_element_max:
            # Compute an equal-weight average (weights could be configurable in the future)
            try:
                agg_score = sum(per_element_max.values()) / max(1, len(per_element_max))
            except Exception:
                agg_score = None
        else:
            agg_score = (score_sum / total_weight) if total_weight > 0 else None

        return {
            "score": agg_score,
            "scores_by_element": per_element_max if per_element_max else None,
            "missing_elements": missing,
            "evidence": evidence,
            "suggestions": suggestions,
        }
