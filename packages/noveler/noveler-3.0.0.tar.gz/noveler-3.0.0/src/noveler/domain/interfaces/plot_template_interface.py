#!/usr/bin/env python3
"""プロットテンプレートインターフェース

プロットテンプレート機能のドメインインターフェース定義。
DDD準拠でApplication層からInfrastructure層への抽象化層を提供。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TemplateData:
    """テンプレートデータ"""

    template_id: str
    template_content: str
    parameters: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class TemplateResult:
    """テンプレート処理結果"""

    success: bool
    generated_content: str | None = None
    template_used: str | None = None
    error_message: str | None = None
    processing_time_ms: int | None = None


class PlotTemplateInterface(ABC):
    """プロットテンプレート操作のドメインインターフェース

    DDD準拠: Application層がInfrastructure層の具体実装に直接依存せずに
    テンプレート機能を利用するための抽象化層。
    """

    @abstractmethod
    def generate_from_template(self, template_id: str, parameters: dict[str, Any]) -> TemplateResult:
        """テンプレートからプロット生成

        Args:
            template_id: テンプレート識別子
            parameters: テンプレートパラメータ

        Returns:
            TemplateResult: 生成結果
        """

    @abstractmethod
    def get_available_templates(self) -> list[str]:
        """利用可能なテンプレート一覧取得

        Returns:
            利用可能なテンプレートID一覧
        """

    @abstractmethod
    def validate_template_parameters(self, template_id: str, parameters: dict[str, Any]) -> bool:
        """テンプレートパラメータの妥当性検証

        Args:
            template_id: テンプレート識別子
            parameters: 検証対象パラメータ

        Returns:
            妥当性検証結果
        """
