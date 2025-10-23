"""後方互換用 FiveStageExecutionService モジュール.

旧コードでは ``noveler.infrastructure.services.five_stage_execution_service`` から
サービスをインポートしていたため、現在の ``ManuscriptGenerationService`` を
再エクスポートして互換性を維持する。
"""

from __future__ import annotations

from noveler.infrastructure.services.manuscript_generation_service import ManuscriptGenerationService

# 旧名称との互換エイリアス
FiveStageExecutionService = ManuscriptGenerationService

__all__ = ["FiveStageExecutionService", "ManuscriptGenerationService"]
