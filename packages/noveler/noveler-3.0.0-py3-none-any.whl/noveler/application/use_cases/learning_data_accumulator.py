"""学習データ蓄積ユースケース
品質チェック結果とアクセス分析データを統合して学習データを作成
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class LearningDataAccumulator(AbstractUseCase[dict, dict]):
    """学習データ蓄積ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        **kwargs) -> None:
        super().__init__(logger_service=logger_service, unit_of_work=unit_of_work, **kwargs)

        # 遅延初期化
        self._learning_repo = None
        self._style_service = None
        self._correlation_analyzer = None

    @property
    def learning_repo(self):
        """学習モデルリポジトリ取得"""
        if self._learning_repo is None:
            self._learning_repo = self.repository_factory.create_learning_model_repository()
        return self._learning_repo

    @property
    def style_service(self):
        """スタイルサービス取得"""
        if self._style_service is None:
            # 適切なサービスファクトリーから取得
            from noveler.domain.services.style_analysis_service import StyleAnalysisService
            self._style_service = StyleAnalysisService()
        return self._style_service

    @property
    def correlation_analyzer(self):
        """相関アナライザー取得"""
        if self._correlation_analyzer is None:
            # 適切なサービスファクトリーから取得
            from noveler.domain.services.correlation_analysis_service import CorrelationAnalysisService

            self._correlation_analyzer = CorrelationAnalysisService()
        return self._correlation_analyzer

    async def execute(self, request: dict) -> dict:
        """ユースケースを実行"""
        episode_number = request["episode_number"]
        quality_check_result = request["quality_check_result"]
        access_data: dict[str, Any] = request.get("access_data")
        episode_text = request.get("episode_text")
        return self.accumulate_episode_data(episode_number, quality_check_result, access_data, episode_text)

    def accumulate_episode_data(
        self,
        episode_number: int,
        quality_check_result: dict[str, Any],
        access_data: dict[str, Any] | None = None,
        episode_text: str | None = None,
    ) -> dict[str, Any]:
        """エピソードの学習データを蓄積"""

        # 既存の学習データを取得
        learning_data: dict[str, Any] = self.learning_repo.load_learning_data()

        # エピソードデータを構築
        episode_learning_data: dict[str, Any] = {
            "episode_number": episode_number,
            "timestamp": project_now().datetime.isoformat(),
            "quality_metrics": self._extract_quality_metrics(quality_check_result),
            "reader_metrics": self._extract_reader_metrics(access_data) if access_data else {},
            "style_features": {},
            "viewpoint_info": quality_check_result.get("viewpoint_info", {}),
        }

        # 文体特徴を抽出(テキストが提供された場合)
        if episode_text:
            style_features = self.style_service.extract_style_features(episode_text)
            episode_learning_data["style_features"] = style_features

        # 学習データに追加
        learning_data["episode_data"].append(episode_learning_data)
        learning_data["metadata"]["data_count"] = len(learning_data["episode_data"])
        learning_data["metadata"]["last_updated"] = project_now().datetime.isoformat()

        # 保存
        self.learning_repo.save_learning_data(learning_data)

        # 相関分析の実行(十分なデータがある場合)
        if learning_data["metadata"]["data_count"] >= 5:
            correlations = self._analyze_correlations(learning_data["episode_data"])
            learning_data["correlations"] = correlations
            self.learning_repo.save_learning_data(learning_data)

        return {
            "status": "success",
            "episode_number": episode_number,
            "data_count": learning_data["metadata"]["data_count"],
            "model_status": learning_data["metadata"]["model_status"],
        }

    def _extract_quality_metrics(self, quality_result: dict[str, Any]) -> dict[str, float]:
        """品質チェック結果から学習用メトリクスを抽出"""
        metrics = {}

        # 基本的な品質スコア
        if "total_score" in quality_result:
            metrics["total_quality_score"] = quality_result["total_score"]

        # 個別スコア
        if "scores" in quality_result:
            scores = quality_result["scores"]
            metrics["readability_score"] = scores.get("readability", 0)
            metrics["dialogue_ratio"] = scores.get("dialogue_ratio", 0)
            metrics["composition_score"] = scores.get("composition", 0)

        # 内面描写深度(視点情報連動システムから)
        if "adjusted_scores" in quality_result:
            metrics["narrative_depth"] = quality_result["adjusted_scores"].get("narrative_depth", 0)

        # エラー・警告数
        metrics["error_count"] = quality_result.get("error_count", 0)
        metrics["warning_count"] = quality_result.get("warning_count", 0)

        return metrics

    def _extract_reader_metrics(self, access_data: dict[str, Any]) -> dict[str, float]:
        """アクセス分析データから読者反応メトリクスを抽出"""
        metrics = {}

        # 基本的な閲覧データ
        metrics["total_views"] = access_data.get("views", {}).get("total", 0)
        metrics["last_30days_views"] = access_data.get("views", {}).get("last_30days", 0)
        metrics["unique_readers"] = access_data.get("unique_readers", 0)

        # 離脱率(提供されている場合)
        if "dropout_rate" in access_data:
            metrics["dropout_rate"] = access_data["dropout_rate"]
            metrics["retention_rate"] = 100 - access_data["dropout_rate"]

        # エンゲージメント指標(提供されている場合)
        if "completion_rate" in access_data:
            metrics["completion_rate"] = access_data["completion_rate"]

        return metrics

    def _analyze_correlations(self, episode_data_list: list[dict[str, Any]]) -> dict[str, Any]:
        """品質指標と読者反応の相関を分析"""
        quality_metrics = []
        reader_metrics = []

        for episode in episode_data_list:
            if episode["quality_metrics"] and episode["reader_metrics"]:
                quality_metrics.append(episode["quality_metrics"])
                reader_metrics.append(episode["reader_metrics"])

        if len(quality_metrics) < 5:
            return {}

        # 相関分析サービスを使用
        return self.correlation_analyzer.analyze_quality_reader_correlation(
            quality_metrics,
            reader_metrics,
        )


class BatchLearningDataProcessor:
    """既存データの一括処理"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        accumulator = None,
        **kwargs) -> None:
        self.accumulator = accumulator

    def process_existing_data(
        self,
        quality_records_path: Path | str,
        access_data_path: Path | str,
        episode_texts_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        """既存の品質記録とアクセスデータから学習データを生成"""

        processed_count = 0
        errors: list[Any] = []

        # 品質記録を読み込み
        with Path(quality_records_path).open(encoding="utf-8") as f:
            quality_data: dict[str, Any] = yaml.safe_load(f)

        # アクセスデータを読み込み
        with Path(access_data_path).open(encoding="utf-8") as f:
            access_data: dict[str, Any] = yaml.safe_load(f)

        # エピソードごとに処理
        for episode_key, episode_access in access_data.get("episodes", {}).items():
            result = self._process_episode_safely(episode_key, episode_access, quality_data, episode_texts_dir)

            if result["success"]:
                processed_count += 1
            else:
                errors.append({"episode": episode_key, "error": result["error"]})

        return {
            "processed_count": processed_count,
            "errors": errors,
            "status": "completed" if not errors else "partial",
        }

    def _find_quality_data(self, _quality_data: dict[str, Any], _episode_num: int) -> dict[str, Any] | None:
        """品質データから特定エピソードの結果を検索"""
        # 実装は品質記録の構造に依存
        # ここでは簡略化
        return None

    def _process_episode_safely(
        self, episode_key: str, episode_access: dict, quality_data: dict, episode_texts_dir: Path
    ) -> dict:
        """単一エピソードを安全に処理"""
        try:
            # エピソード番号を抽出
            episode_num = int(episode_key.replace("ep", ""))

            # 対応する品質データを探す
            quality_result = self._find_quality_data(quality_data, episode_num)

            # エピソードテキストを読み込み(存在する場合)
            episode_text = self._read_episode_text(episode_texts_dir, episode_num)

            # 学習データとして蓄積
            self.accumulator.accumulate_episode_data(
                episode_number=episode_num,
                quality_check_result=quality_result or {},
                access_data=episode_access,
                episode_text=episode_text,
            )

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_episode_text(self, texts_dir: Path, episode_num: int) -> str | None:
        """エピソードテキストを読み込み"""
        file_pattern = f"第{episode_num:03d}話*.md"
        files = list(texts_dir.glob(file_pattern))

        if files:
            with Path(files[0]).open(encoding="utf-8") as f:
                return f.read()

        return None
