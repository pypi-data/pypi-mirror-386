#!/usr/bin/env python3
"""汎用プロンプト実行関連バリューオブジェクト

仕様書: SPEC-CLAUDE-CODE-002
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service

# TODO: DDD準拠のためドメインサービス経由でパス取得に改善予定


class PromptType(Enum):
    """プロンプト種別列挙型

    REQ-2.1: プロンプト種別の明確な定義
    """

    WRITING = "writing"
    PLOT = "plot"
    QUALITY_CHECK = "quality_check"


@dataclass
class ProjectContext:
    """プロジェクトコンテキスト

    プロンプト実行に必要なプロジェクト固有情報を保持
    """

    project_root: Path
    project_name: str | None = None
    additional_context_files: list[Path] | None = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.additional_context_files is None:
            self.additional_context_files = []

        if not self.project_root.exists():
            msg = f"Project root does not exist: {self.project_root}"
            raise ValueError(msg)

        if self.project_name is None:
            self.project_name = self.project_root.name


@dataclass
class UniversalPromptRequest:
    """汎用プロンプト実行リクエスト

    REQ-2.1: 統一されたプロンプト実行リクエスト構造
    """

    prompt_content: str
    prompt_type: PromptType
    project_context: ProjectContext
    type_specific_config: dict[str, Any] | None = None
    output_format: str = "json"
    max_turns: int = 3

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.type_specific_config is None:
            self.type_specific_config = {}

        # バリデーション
        if not self.prompt_content.strip():
            msg = "prompt_content must not be empty"
            raise ValueError(msg)

        if self.max_turns <= 0:
            msg = "max_turns must be positive"
            raise ValueError(msg)

        if self.output_format not in ["json", "text", "stream-json"]:
            msg = f"Unsupported output_format: {self.output_format}"
            raise ValueError(msg)

    def get_context_files(self) -> list[Path]:
        """コンテキストファイル一覧取得"""
        context_files = [self.project_context.project_root]
        context_files.extend(self.project_context.additional_context_files)

        # 種別固有のコンテキストファイル追加
        # TODO: DDD準拠のためドメインサービス経由でパス取得に改善予定
        # TODO: F821修正 - path_service未定義のため一時的にコメントアウト
        # DDD準拠のためドメインサービス経由でパス取得機能は別途実装予定
        # if self.prompt_type == PromptType.WRITING:
        #     # 執筆時は原稿ディレクトリを追加
        #     # B20準拠: Path ServiceはDI注入されたものを使用
        #     # path_service = self._path_service
        #     manuscript_dir = path_service.get_manuscript_dir(self.project_context.project_root)
        #     if manuscript_dir.exists():
        #         context_files.append(manuscript_dir)
        #
        # elif self.prompt_type == PromptType.PLOT:
        #     # プロット作成時はプロット・原稿ディレクトリを追加
        #     # B20準拠: Path ServiceはDI注入されたものを使用
        #     # path_service = self._path_service
        #     plot_dir = path_service.get_plot_dir(self.project_context.project_root)
        #     if plot_dir.exists():
        #         context_files.append(plot_dir)

        return context_files


@dataclass
class UniversalPromptResponse:
    """汎用プロンプト実行レスポンス

    REQ-3.1: 統一されたプロンプト実行レスポンス構造
    """

    success: bool
    response_content: str
    extracted_data: dict[str, Any]
    prompt_type: PromptType
    execution_time_ms: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.metadata is None:
            self.metadata = {}

    def is_success(self) -> bool:
        """実行成功判定"""
        return self.success and not self.error_message

    def has_extracted_data(self) -> bool:
        """抽出データ存在判定"""
        return bool(self.extracted_data)

    def get_writing_content(self) -> str | None:
        """執筆結果抽出

        REQ-3.2: 種別固有の結果抽出メソッド
        """
        if self.prompt_type != PromptType.WRITING:
            return None

        if not self.has_extracted_data():
            return self.response_content

        # 執筆内容の一般的なキー名での検索
        writing_keys = ["manuscript", "content", "writing", "text", "output"]
        for key in writing_keys:
            if key in self.extracted_data:
                return self.extracted_data[key]

        return self.response_content

    def get_plot_content(self) -> dict[str, Any] | None:
        """プロット結果抽出

        REQ-3.2: 種別固有の結果抽出メソッド
        """
        if self.prompt_type != PromptType.PLOT:
            return None

        if not self.has_extracted_data():
            return None

        # プロット情報の一般的なキー名での検索
        plot_keys = ["plot", "episode_plot", "scenes", "structure", "outline"]
        for key in plot_keys:
            if key in self.extracted_data:
                return self.extracted_data[key]

        return self.extracted_data

    def get_quality_assessment(self) -> dict[str, Any] | None:
        """品質評価結果抽出

        REQ-3.3: 品質評価・メタデータ管理機能
        """
        if self.prompt_type != PromptType.QUALITY_CHECK:
            return None

        if not self.has_extracted_data():
            return None

        # 品質評価の一般的なキー名での検索
        quality_keys = ["quality", "assessment", "evaluation", "score", "analysis"]
        for key in quality_keys:
            if key in self.extracted_data:
                return self.extracted_data[key]

        return self.extracted_data

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """メタデータ値取得"""
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """メタデータ値設定"""
        self.metadata[key] = value
