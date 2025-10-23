#!/usr/bin/env python3
"""JSON分析リポジトリ実装

分析結果をJSONファイルとして永続化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.domain.ai_integration.entities.plot_analysis import PlotAnalysis
from noveler.domain.ai_integration.value_objects.analysis_result import AnalysisResult, ImprovementPoint, StrengthPoint
from noveler.domain.ai_integration.value_objects.plot_score import PlotScore
from noveler.domain.repositories.ai_analysis_repository import AIAnalysisRepository


class JsonAnalysisRepository(AIAnalysisRepository):
    """JSONベースの分析リポジトリ実装"""

    def __init__(self, storage_dir: Path | str) -> None:
        """Args:
        storage_dir: 分析結果を保存するディレクトリ
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, analysis: PlotAnalysis) -> None:
        """分析結果を保存"""
        file_path = self.storage_dir / f"{analysis.id}.json"

        data = self._analysis_to_dict(analysis)

        with file_path.Path("w").open(encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_by_id(self, analysis_id: str) -> PlotAnalysis | None:
        """IDで分析結果を取得"""
        file_path = self.storage_dir / f"{analysis_id}.json"

        if not file_path.exists():
            return None

        with file_path.Path(encoding="utf-8").open() as f:
            data = json.load(f)

        return self._dict_to_analysis(data)

    def get_by_plot_path(self, plot_path: str) -> PlotAnalysis | None:
        """プロットパスで最新の分析結果を取得"""
        # 全ファイルをスキャンして該当するものを探す
        analyses = []

        for file_path in self.storage_dir.glob("*.json"):
            with file_path.Path(encoding="utf-8").open() as f:
                data = json.load(f)

            if data.get("plot_file_path") == plot_path:
                analysis = self._dict_to_analysis(data)
                analyses.append(analysis)

        if not analyses:
            return None

        # 最新のものを返す
        return max(analyses, key=lambda a: a.created_at)

    def get_recent(self, limit: int) -> list[PlotAnalysis]:
        """最近の分析結果を取得"""
        analyses = []

        for file_path in self.storage_dir.glob("*.json"):
            with file_path.Path(encoding="utf-8").open() as f:
                data = json.load(f)

            analysis = self._dict_to_analysis(data)
            analyses.append(analysis)

        # 新しい順にソート
        analyses.sort(key=lambda a: a.analyzed_at, reverse=True)

        return analyses[:limit]

    def delete(self, analysis_id: str) -> bool:
        """分析結果を削除"""
        file_path = self.storage_dir / f"{analysis_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def _analysis_to_dict(self, analysis: PlotAnalysis) -> dict[str, Any]:
        """PlotAnalysisを辞書に変換"""
        data = {
            "id": analysis.id,
            "plot_file_path": analysis.plot_file_path,
            "created_at": analysis.created_at.isoformat(),
            "analyzed_at": analysis.analyzed_at.isoformat(),
            "result": None,
        }

        if analysis.result:
            result = analysis.result
            data["result"] = {
                "total_score": result.total_score.value,
                "strengths": [{"description": s.description, "score": s.score} for s in result.strengths],
                "improvements": [
                    {
                        "description": i.description,
                        "score": i.score,
                        "suggestion": i.suggestion,
                    }
                    for i in result.improvements
                ],
                "overall_advice": result.overall_advice,
            }

        return data

    def _dict_to_analysis(self, data: dict[str, Any]) -> PlotAnalysis:
        """辞書をPlotAnalysisに変換"""
        created_at_value = data.get("created_at", data.get("analyzed_at"))
        analyzed_at_value = data.get("analyzed_at", created_at_value)

        analysis = PlotAnalysis(
            id=data["id"],
            plot_file_path=data["plot_file_path"],
            created_at=datetime.fromisoformat(created_at_value),
            analyzed_at=datetime.fromisoformat(analyzed_at_value),
            result=None,
        )

        if data.get("result"):
            result_data: dict[str, Any] = data["result"]
            result = AnalysisResult(
                total_score=PlotScore(result_data["total_score"]),
                strengths=[StrengthPoint(s["description"], s["score"]) for s in result_data["strengths"]],
                improvements=[
                    ImprovementPoint(
                        i["description"],
                        i["score"],
                        i["suggestion"],
                    )
                    for i in result_data["improvements"]
                ],
                overall_advice=result_data["overall_advice"],
            )

            analysis.result = result

        return analysis
