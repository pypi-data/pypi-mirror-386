# File: src/noveler/domain/value_objects/report_file_name_config.py
# Purpose: Immutable configuration for report filename generation
# Context: Used by ReportFileNamingService to generate standardized filenames

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportFileNameConfig:
    """レポートファイル名生成の設定（不変）

    Purpose:
        統一されたファイル名生成のための設定を保持する値オブジェクト。
        不変性を保証し、命名規則の一貫性を確保する。

    Attributes:
        episode_number: エピソード番号（1-999）
        report_type: レポートタイプ（例: "A41", "quality", "backup"）
        extension: ファイル拡張子（例: "md", "yaml", "json"）
        include_timestamp: タイムスタンプをファイル名に含めるか
        timestamp_format: タイムスタンプのフォーマット（デフォルト: "%Y%m%d_%H%M%S"）
        version: バージョン文字列（オプション）

    Raises:
        ValueError: episode_number が範囲外の場合
    """

    episode_number: int
    report_type: str
    extension: str
    include_timestamp: bool = False
    timestamp_format: str = "%Y%m%d_%H%M%S"
    version: str | None = None

    def __post_init__(self) -> None:
        """バリデーション: エピソード番号が有効範囲内かチェック

        Side Effects:
            episode_number が 1-999 の範囲外の場合、ValueError を送出
        """
        if not 1 <= self.episode_number <= 999:
            raise ValueError(
                f"episode_number must be between 1 and 999, got {self.episode_number}"
            )
