"""感情表現MCPツール基底クラス

SPEC-A38-EMOTION-001準拠：
- 五層感情表現システム対応
- JSON応答による95%トークン削減
- 独立実行可能性保証
- 統一エラーハンドリング
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class EmotionLayer(Enum):
    """五層感情表現システムの層定義"""
    PHYSICAL = "physical"      # 身体層：体温、震え、姿勢
    VISCERAL = "visceral"      # 内臓層：胃のもたれ、息苦しさ
    CARDIAC = "cardiac"        # 心拍呼吸層：動悸、呼吸の乱れ
    NEURAL = "neural"          # 神経歪み層：思考の混乱、集中力低下
    METAPHORICAL = "metaphorical"  # 比喩層：抽象的表現、詩的比喩


class EmotionIntensity(Enum):
    """感情強度レベル"""
    MINIMAL = 1
    LOW = 3
    MODERATE = 5
    HIGH = 7
    EXTREME = 10


@dataclass
class EmotionToolInput:
    """感情表現ツール共通入力データ構造"""
    text: str
    emotion_layer: EmotionLayer | None = None
    intensity: EmotionIntensity | None = None
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class EmotionToolOutput:
    """感情表現ツール共通出力データ構造"""
    success: bool
    tool_name: str
    score: float | None = None
    analysis: dict[str, Any] | None = None
    suggestions: list[str] | None = None
    issues: list[str] | None = None
    metadata: dict[str, Any] | None = None
    error_message: str | None = None


class BaseEmotionTool(ABC):
    """感情表現MCPツール基底クラス

    すべての感情表現ツールが継承すべき基底クラス。
    共通のインターフェース、エラーハンドリング、ログ機能を提供。
    """

    def __init__(self, tool_name: str) -> None:
        """ツール初期化

        Args:
            tool_name: ツール識別名
        """
        self.tool_name = tool_name
        self.logger = get_logger(f"emotion_tools.{tool_name}")
        self._initialize_tool()

    def _initialize_tool(self) -> None:
        """ツール固有の初期化処理（オーバーライド可能）"""

    @abstractmethod
    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """ツールの主要処理を実行

        Args:
            input_data: 入力データ

        Returns:
            処理結果
        """

    def validate_input(self, input_data: EmotionToolInput) -> bool:
        """入力データの妥当性検証

        Args:
            input_data: 検証対象の入力データ

        Returns:
            妥当性（True: 有効, False: 無効）
        """
        if not input_data.text or not input_data.text.strip():
            self.logger.warning(f"{self.tool_name}: 空のテキスト入力")
            return False
        return True

    def create_success_output(
        self,
        score: float | None = None,
        analysis: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> EmotionToolOutput:
        """成功レスポンス生成

        Args:
            score: 評価スコア
            analysis: 分析結果
            suggestions: 改善提案
            metadata: 追加メタデータ

        Returns:
            成功レスポンス
        """
        return EmotionToolOutput(
            success=True,
            tool_name=self.tool_name,
            score=score,
            analysis=analysis or {},
            suggestions=suggestions or [],
            metadata=metadata or {}
        )

    def create_error_output(
        self,
        error_message: str,
        issues: list[str] | None = None
    ) -> EmotionToolOutput:
        """エラーレスポンス生成

        Args:
            error_message: エラーメッセージ
            issues: 問題リスト

        Returns:
            エラーレスポンス
        """
        self.logger.error(f"{self.tool_name}: {error_message}")
        return EmotionToolOutput(
            success=False,
            tool_name=self.tool_name,
            error_message=error_message,
            issues=issues or []
        )

    async def safe_execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """安全な実行ラッパー

        エラーハンドリングと共通処理を含む実行メソッド。

        Args:
            input_data: 入力データ

        Returns:
            処理結果（エラー時も含む）
        """
        try:
            # 入力検証
            if not self.validate_input(input_data):
                return self.create_error_output(
                    "無効な入力データ",
                    ["テキストが空または無効です"]
                )

            self.logger.info(f"{self.tool_name}: 実行開始")

            # 主要処理実行
            result = await self.execute(input_data)

            self.logger.info(f"{self.tool_name}: 実行完了")
            return result

        except Exception as e:
            return self.create_error_output(
                f"実行時エラー: {e!s}",
                [f"例外: {type(e).__name__}"]
            )

    def get_tool_info(self) -> dict[str, Any]:
        """ツール情報取得

        Returns:
            ツール基本情報
        """
        return {
            "name": self.tool_name,
            "version": "1.0.0",
            "spec": "SPEC-A38-EMOTION-001",
            "supported_layers": [layer.value for layer in EmotionLayer],
            "supported_intensities": [intensity.value for intensity in EmotionIntensity]
        }
