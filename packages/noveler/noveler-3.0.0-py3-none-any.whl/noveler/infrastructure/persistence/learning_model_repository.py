"""学習モデルリポジトリ(インフラ層)"""

import json
import pickle
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class LearningModelRepository:
    """学習モデルリポジトリ実装"""

    def __init__(self, models_dir: Path | str | None = None, logger_service=None, console_service=None) -> None:
        """初期化

        Args:
            models_dir: モデル保存ディレクトリ(デフォルト: ./models)
        """
        if models_dir is None:
            models_dir = Path("./models")
        elif isinstance(models_dir, str):
            models_dir = Path(models_dir)
        self.models_dir = models_dir
        self.models_dir.mkdir(exist_ok=True)

        # メタデータディレクトリ
        self.metadata_dir = self.models_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)

        self.logger_service = logger_service
        self.console_service = console_service
    def has_trained_model(self, project_id: str) -> bool:
        """学習済みモデルが存在するか確認"""
        model_path = self.models_dir / f"{project_id}.pkl"
        metadata_path = self.metadata_dir / f"{project_id}_metadata.json"

        return model_path.exists() and metadata_path.exists()

    def load_model(self, project_id: str) -> object | None:
        """学習済みモデルを読み込み"""
        model_path = self.models_dir / f"{project_id}.pkl"

        if not model_path.exists():
            return None

        try:
            with Path(model_path).open("rb") as f:
                return pickle.load(f)
        except Exception as e:
            self.console_service.print(f"モデル読み込みエラー: {e}")
            return None

    def save_model(self, project_id: str, model: object, metadata: dict[str, str | int | float]) -> bool | None:
        """学習済みモデルを保存"""
        model_path = self.models_dir / f"{project_id}.pkl"
        metadata_path = self.metadata_dir / f"{project_id}_metadata.json"

        try:
            # モデル保存
            with Path(model_path).open("wb") as f:
                pickle.dump(model, f)

            # メタデータ保存
            metadata_with_timestamp = {
                **metadata,
                "saved_at": project_now().datetime.isoformat(),
                "model_file": str(model_path),
            }

            with Path(metadata_path).open("w", encoding="utf-8") as f:
                json.dump(metadata_with_timestamp, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            self.console_service.print(f"モデル保存エラー: {e}")
            return False

    def get_model_metadata(self, project_id: str) -> dict[str, str | int | float] | None:
        """モデルメタデータを取得"""
        metadata_path = self.metadata_dir / f"{project_id}_metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with Path(metadata_path).open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.console_service.print(f"メタデータ読み込みエラー: {e}")
            return None

    def predict_quality(self, model: object, features: dict[str, str | int | float]) -> float | None:
        """モデルを使用して品質を予測"""
        if model is None:
            return None

        try:
            # 特徴量の準備(プロジェクト依存の変換)
            feature_vector = self._prepare_features(features)

            # 予測実行
            prediction = model.predict([feature_vector])[0]

            # 予測値を0-5の範囲にクランプ
            return max(0.0, min(5.0, float(prediction)))

        except Exception as e:
            self.console_service.print(f"予測エラー: {e}")
            return None

    def _prepare_features(self, features: dict[str, Any]) -> list:
        """特徴量をモデル入力形式に変換"""
        # 基本的な特徴量の順序を定義
        feature_order = [
            "total_characters",
            "dialogue_ratio",
            "exclamation_count",
            "question_count",
            "paragraph_count",
            "sentence_count",
        ]

        feature_vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.0)
            feature_vector.append(float(value))

        return feature_vector

    def list_available_models(self) -> list:
        """利用可能なモデル一覧を取得"""
        model_files = list(self.models_dir.glob("*.pkl"))
        project_ids = []

        for model_file in model_files:
            project_id = model_file.stem
            if self.has_trained_model(project_id):
                project_ids.append(project_id)

        return project_ids
