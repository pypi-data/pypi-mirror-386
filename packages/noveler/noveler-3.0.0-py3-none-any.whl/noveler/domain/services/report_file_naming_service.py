# File: src/noveler/domain/services/report_file_naming_service.py
# Purpose: Domain service providing unified filename generation logic
# Context: Enforces consistent naming conventions across all report generation

import re
from datetime import datetime
from pathlib import Path

from noveler.domain.value_objects.report_file_name_config import ReportFileNameConfig


class ReportFileNamingService:
    """ドメインサービス: レポートファイル名生成の統一ロジック

    Purpose:
        統一された命名規則でファイル名を生成・検証・解析する。
        フォーマット: episode_{episode:03d}_{report_type}[_{timestamp}][_{version}].{ext}

    Preconditions:
        ReportFileNameConfig が有効な値で初期化されていること。

    Side Effects:
        なし（純粋関数として実装）
    """

    @staticmethod
    def generate_filename(config: ReportFileNameConfig) -> str:
        """統一された命名規則でファイル名を生成

        Args:
            config: ファイル名生成設定

        Returns:
            生成されたファイル名（例: "episode_001_A41.md"）

        Raises:
            ValueError: config のバリデーションに失敗した場合
        """
        # エピソード番号を3桁ゼロ埋めでフォーマット
        parts = [f"episode_{config.episode_number:03d}", config.report_type]

        # オプション: タイムスタンプを追加
        if config.include_timestamp:
            ts = datetime.now().strftime(config.timestamp_format)
            parts.append(ts)

        # オプション: バージョンを追加
        if config.version:
            parts.append(config.version)

        # パーツをアンダースコアで連結し、拡張子を追加
        filename = "_".join(parts)
        return f"{filename}.{config.extension}"

    @staticmethod
    def parse_filename(filename: str) -> dict[str, str | int | None]:
        """ファイル名から各要素を抽出

        Args:
            filename: パース対象のファイル名（例: "episode_001_A41.md"）

        Returns:
            抽出された要素の辞書:
                - episode_number: int
                - report_type: str
                - extension: str
                - timestamp: str | None
                - version: str | None

        Raises:
            ValueError: ファイル名が命名規則に準拠していない場合

        Notes:
            Timestampとversionの区別規則:
            - Timestamp: YYYYMMDD_HHMMSS 形式（16文字、アンダースコア含む）
            - Version: それ以外の文字列（v1, v2, initial, final など）
        """
        # エピソード番号、レポートタイプ、拡張子は必須
        # タイムスタンプ（YYYYMMDD_HHMMSS）とバージョンはオプション
        base_pattern = r"^episode_(\d{3})_([^_.]+)"
        extension_pattern = r"\.([\w]+)$"
        
        # タイムスタンプパターン（厳密な形式チェック）
        timestamp_pattern = r"_(\d{8}_\d{6})"
        
        # バージョンパターン（タイムスタンプ以外の文字列）
        version_pattern = r"_([^_]+)"
        
        # 完全な正規表現パターンを構築
        # Format: episode_{episode:03d}_{report_type}[_{timestamp}][_{version}].{ext}
        # タイムスタンプが存在する場合、それはバージョンより前に配置される
        full_pattern = (
            base_pattern +
            f"(?:{timestamp_pattern})?" +  # オプショナルなタイムスタンプ
            f"(?:{version_pattern})?" +    # オプショナルなバージョン
            extension_pattern
        )
        
        match = re.match(full_pattern, filename)

        if not match:
            raise ValueError(
                f"Filename '{filename}' does not match naming convention: "
                f"episode_{{episode:03d}}_{{report_type}}[_{{timestamp}}][_{{version}}].{{ext}}"
            )

        episode_number = int(match.group(1))
        report_type = match.group(2)
        timestamp = match.group(3) if len(match.groups()) >= 3 else None
        version = match.group(4) if len(match.groups()) >= 4 else None
        extension = match.group(5) if len(match.groups()) >= 5 else None

        # タイムスタンプ形式のバリデーション
        if timestamp:
            # YYYYMMDD_HHMMSS形式を厳密にチェック
            if not re.match(r"^\d{8}_\d{6}$", timestamp):
                # タイムスタンプ形式でない場合はバージョンとして扱う
                version = timestamp
                timestamp = None

        return {
            "episode_number": episode_number,
            "report_type": report_type,
            "extension": extension,
            "timestamp": timestamp,
            "version": version,
        }

    @staticmethod
    def validate_filename(filename: str) -> bool:
        """ファイル名が命名規則に準拠しているかチェック

        Args:
            filename: 検証対象のファイル名

        Returns:
            準拠している場合 True、そうでない場合 False
        """
        try:
            ReportFileNamingService.parse_filename(filename)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_sorting_order(filenames: list[str]) -> bool:
        """ファイル名リストが自然順序でソートされているかチェック

        Args:
            filenames: 検証対象のファイル名リスト

        Returns:
            ソート済みの場合 True、そうでない場合 False

        Purpose:
            命名規則がアルファベット順ソートで自然な順序を保つことを検証。
            episode_001, episode_002, ..., episode_010, ... の順序を確認。
        """
        return filenames == sorted(filenames)

    @staticmethod
    def extract_episode_number(filepath: Path) -> int | None:
        """ファイルパスからエピソード番号を抽出

        Args:
            filepath: ファイルパス（PathまたはPath互換オブジェクト）

        Returns:
            エピソード番号（抽出できない場合はNone）

        Purpose:
            既存ファイルから episode_number を取得し、次のエピソード番号を決定する。
        """
        try:
            parsed = ReportFileNamingService.parse_filename(filepath.name)
            return parsed["episode_number"]
        except (ValueError, AttributeError):
            return None
