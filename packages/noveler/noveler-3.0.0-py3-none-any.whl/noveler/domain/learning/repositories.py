"""学習機能付き品質チェックドメイン - リポジトリインターフェース"""

from abc import ABC, abstractmethod
import functools
import inspect
from typing import Any

from noveler.domain.learning.entities import LearningQualityEvaluator, QualityLearningModel
from noveler.domain.learning.value_objects import WritingStyleProfile


def _ensure_public_identifier(entity: Any, public_attr: str) -> None:
    value = getattr(entity, public_attr, None)
    if isinstance(value, str) and value:
        return

    fallback = getattr(entity, f"_{public_attr}", None)
    if isinstance(fallback, str) and fallback:
        try:
            setattr(entity, public_attr, fallback)
        except AttributeError:
            try:
                entity.__dict__[public_attr] = fallback
            except Exception:
                pass


class QualityLearningRepository(ABC):
    """品質学習モデルリポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        method = cls.__dict__.get("save_model")
        if method is not None:
            cls.save_model = QualityLearningRepository._wrap_save_model(method)

    @staticmethod
    def _wrap_save_model(method):
        @functools.wraps(method)
        def wrapper(self, model: QualityLearningModel, *args, **kwargs):
            _ensure_public_identifier(model, "model_id")
            return method(self, model, *args, **kwargs)

        return wrapper

    @abstractmethod
    def save_model(self, model: QualityLearningModel) -> None:
        """学習モデル保存"""

    @abstractmethod
    def find_model_by_id(self, model_id: str) -> QualityLearningModel | None:
        """モデルID検索"""

    @abstractmethod
    def find_models_by_project(self, project_id: str) -> list[QualityLearningModel]:
        """プロジェクト別モデル取得"""

    @abstractmethod
    def save_learning_history(
        self, model_id: str, training_data: list[dict[str, Any]], accuracy: float
    ) -> None:
        """学習履歴保存"""

    @abstractmethod
    def get_learning_history(self, model_id: str) -> list[dict[str, Any]]:
        """学習履歴取得"""


class EpisodeAnalysisRepository(ABC):
    """エピソード分析データリポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        method = cls.__dict__.get("find_episodes_with_high_reader_rating")
        if method is not None:
            cls.find_episodes_with_high_reader_rating = EpisodeAnalysisRepository._wrap_high_reader_method(method)

    @staticmethod
    def _wrap_high_reader_method(method):
        signature = inspect.signature(method)
        params = list(signature.parameters.values())
        if len(params) < 3:
            return method
        alias_name = params[2].name
        if alias_name == "min_rating":
            return method

        @functools.wraps(method)
        def wrapper(self, project_id, *args, **kwargs):
            if "min_rating" in kwargs and alias_name not in kwargs:
                kwargs[alias_name] = kwargs.pop("min_rating")
            return method(self, project_id, *args, **kwargs)

        return wrapper

    @abstractmethod
    def save_episode_analysis(self, episode_id: str, analysis_data: dict[str, Any]) -> None:
        """エピソード分析データ保存"""

    @abstractmethod
    def find_episode_analysis(self, episode_id: str) -> dict[str, Any] | None:
        """エピソード分析データ取得"""

    @abstractmethod
    def find_project_episodes_analysis(self, project_id: str) -> list[dict[str, Any]]:
        """プロジェクト全エピソード分析データ取得"""

    @abstractmethod
    def find_episodes_by_quality_range(self, project_id: str, metric: str) -> list[dict[str, Any]]:
        """品質スコア範囲でエピソード検索"""

    @abstractmethod
    def find_episodes_with_high_reader_rating(self, project_id: str, min_rating: float) -> list[dict[str, Any]]:
        """高評価エピソード取得"""


class ReaderFeedbackRepository(ABC):
    """読者反応データリポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    @abstractmethod
    def save_reader_feedback(self, episode_id: str, feedback_data: dict[str, Any]) -> None:
        """読者反応データ保存"""

    @abstractmethod
    def find_feedback_by_episode(self, episode_id: str) -> list[dict[str, Any]]:
        """エピソード別反応データ取得"""

    @abstractmethod
    def find_feedback_by_project(self, project_id: str) -> list[dict[str, Any]]:
        """プロジェクト別反応データ取得"""

    @abstractmethod
    def find_feedback_by_date_range(self, project_id: str, start_date: str) -> list[dict[str, Any]]:
        """期間別反応データ取得"""

    @abstractmethod
    def calculate_average_rating(self, project_id: str) -> float:
        """プロジェクト平均評価計算"""

    @abstractmethod
    def find_trending_episodes(self, project_id: str, days: int) -> list[dict[str, Any]]:
        """トレンドエピソード取得"""


class WritingStyleProfileRepository(ABC):
    """文体プロファイルリポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        method = cls.__dict__.get("find_similar_profiles")
        if method is not None:
            cls.find_similar_profiles = WritingStyleProfileRepository._wrap_similarity_method(method)

    @staticmethod
    def _wrap_similarity_method(method):
        signature = inspect.signature(method)
        params = list(signature.parameters.values())
        if len(params) < 3:
            return method
        alias_name = params[2].name
        if alias_name == "similarity_threshold":
            return method

        @functools.wraps(method)
        def wrapper(self, reference_profile, *args, **kwargs):
            if "similarity_threshold" in kwargs and alias_name not in kwargs:
                kwargs[alias_name] = kwargs.pop("similarity_threshold")
            return method(self, reference_profile, *args, **kwargs)

        return wrapper

    @abstractmethod
    def save_profile(self, profile: WritingStyleProfile) -> None:
        """文体プロファイル保存"""

    @abstractmethod
    def find_profile_by_id(self, profile_id: str) -> WritingStyleProfile | None:
        """プロファイルID検索"""

    @abstractmethod
    def find_profiles_by_project(self, project_id: str) -> list[WritingStyleProfile]:
        """プロジェクト別プロファイル取得"""

    @abstractmethod
    def find_similar_profiles(
        self, reference_profile: WritingStyleProfile, similarity_threshold: float
    ) -> list[WritingStyleProfile]:
        """類似プロファイル検索"""

    @abstractmethod
    def update_profile(self, profile: WritingStyleProfile) -> None:
        """プロファイル更新"""

    @abstractmethod
    def find_profiles_by_confidence(self, min_confidence: float) -> list[WritingStyleProfile]:
        """信頼度別プロファイル取得"""


class LearningEvaluatorRepository(ABC):
    """学習評価器リポジトリインターフェース

    ドメイン層で定義、インフラ層で実装
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        method = cls.__dict__.get("save_evaluator")
        if method is not None:
            cls.save_evaluator = LearningEvaluatorRepository._wrap_save_evaluator(method)

    @staticmethod
    def _wrap_save_evaluator(method):
        @functools.wraps(method)
        def wrapper(self, evaluator: LearningQualityEvaluator, *args, **kwargs):
            _ensure_public_identifier(evaluator, "evaluator_id")
            return method(self, evaluator, *args, **kwargs)

        return wrapper

    @abstractmethod
    def save_evaluator(self, evaluator: LearningQualityEvaluator) -> None:
        """学習評価器保存"""

    @abstractmethod
    def find_evaluator_by_id(self, evaluator_id: str) -> LearningQualityEvaluator | None:
        """評価器ID検索"""

    @abstractmethod
    def find_evaluator_by_project(self, project_id: str) -> LearningQualityEvaluator | None:
        """プロジェクト別評価器取得"""

    @abstractmethod
    def save_evaluation_result(self, evaluator_id: str, episode_id: str) -> None:
        """評価結果保存"""

    @abstractmethod
    def find_evaluation_history(self, evaluator_id: str, limit: int) -> list[dict[str, Any]]:
        """評価履歴取得"""

    @abstractmethod
    def find_evaluation_improvements(self, evaluator_id: str, days: int) -> list[dict[str, Any]]:
        """評価改善履歴取得"""
