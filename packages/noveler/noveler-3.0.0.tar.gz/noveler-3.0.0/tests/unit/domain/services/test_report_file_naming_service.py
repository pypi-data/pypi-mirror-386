# File: tests/unit/domain/services/test_report_file_naming_service.py
# Purpose: Unit tests for ReportFileNamingService domain service
# Context: Validates filename generation, parsing, and validation logic

from pathlib import Path

import pytest

from noveler.domain.services.report_file_naming_service import ReportFileNamingService
from noveler.domain.value_objects.report_file_name_config import ReportFileNameConfig


class TestReportFileNameConfig:
    """ReportFileNameConfig 値オブジェクトのテスト"""

    def test_basic_creation(self) -> None:
        """基本的な生成が成功する"""
        config = ReportFileNameConfig(
            episode_number=1, report_type="A41", extension="md"
        )
        assert config.episode_number == 1
        assert config.report_type == "A41"
        assert config.extension == "md"
        assert config.include_timestamp is False
        assert config.version is None

    def test_with_timestamp(self) -> None:
        """タイムスタンプ付き設定の生成"""
        config = ReportFileNameConfig(
            episode_number=1,
            report_type="quality",
            extension="json",
            include_timestamp=True,
        )
        assert config.include_timestamp is True
        assert config.timestamp_format == "%Y%m%d_%H%M%S"

    def test_with_version(self) -> None:
        """バージョン付き設定の生成"""
        config = ReportFileNameConfig(
            episode_number=1, report_type="backup", extension="yaml", version="v1"
        )
        assert config.version == "v1"

    def test_episode_number_validation_too_low(self) -> None:
        """エピソード番号が範囲外（下限）でエラー"""
        with pytest.raises(ValueError, match="must be between 1 and 999"):
            ReportFileNameConfig(episode_number=0, report_type="A41", extension="md")

    def test_episode_number_validation_too_high(self) -> None:
        """エピソード番号が範囲外（上限）でエラー"""
        with pytest.raises(ValueError, match="must be between 1 and 999"):
            ReportFileNameConfig(
                episode_number=1000, report_type="A41", extension="md"
            )

    def test_immutability(self) -> None:
        """設定は不変である"""
        config = ReportFileNameConfig(
            episode_number=1, report_type="A41", extension="md"
        )
        with pytest.raises(AttributeError):
            config.episode_number = 2  # type: ignore[misc]


class TestReportFileNamingService:
    """ReportFileNamingService ドメインサービスのテスト"""

    @pytest.fixture
    def service(self) -> ReportFileNamingService:
        """サービスインスタンス"""
        return ReportFileNamingService()

    def test_basic_filename_generation(
        self, service: ReportFileNamingService
    ) -> None:
        """基本的なファイル名生成"""
        config = ReportFileNameConfig(episode_number=1, report_type="A41", extension="md")
        filename = service.generate_filename(config)
        assert filename == "episode_001_A41.md"

    def test_filename_with_double_digit_episode(
        self, service: ReportFileNamingService
    ) -> None:
        """2桁エピソード番号でのファイル名生成"""
        config = ReportFileNameConfig(
            episode_number=42, report_type="quality", extension="json"
        )
        filename = service.generate_filename(config)
        assert filename == "episode_042_quality.json"

    def test_filename_with_triple_digit_episode(
        self, service: ReportFileNamingService
    ) -> None:
        """3桁エピソード番号でのファイル名生成"""
        config = ReportFileNameConfig(
            episode_number=999, report_type="backup", extension="yaml"
        )
        filename = service.generate_filename(config)
        assert filename == "episode_999_backup.yaml"

    def test_filename_with_version(self, service: ReportFileNamingService) -> None:
        """バージョン付きファイル名生成"""
        config = ReportFileNameConfig(
            episode_number=1, report_type="A41", extension="md", version="v2"
        )
        filename = service.generate_filename(config)
        assert filename == "episode_001_A41_v2.md"

    def test_filename_with_timestamp(self, service: ReportFileNamingService) -> None:
        """タイムスタンプ付きファイル名生成"""
        config = ReportFileNameConfig(
            episode_number=1,
            report_type="backup",
            extension="yaml",
            include_timestamp=True,
        )
        filename = service.generate_filename(config)
        # タイムスタンプの正確な値は予測不可能なので、パターンマッチング
        assert filename.startswith("episode_001_backup_")
        assert filename.endswith(".yaml")
        # タイムスタンプフォーマット: YYYYMMDD_HHMMSS (アンダースコアで分割される)
        # 例: episode_001_backup_20251013_123456.yaml
        parts = filename.split("_")
        assert len(parts) == 5  # episode, 001, backup, YYYYMMDD, HHMMSS.yaml
        # YYYYMMDD部分の検証
        assert len(parts[3]) == 8  # YYYYMMDD = 8 chars
        # HHMMSS.yaml部分の検証
        timestamp_time_with_ext = parts[4]
        timestamp_time = timestamp_time_with_ext.replace(".yaml", "")
        assert len(timestamp_time) == 6  # HHMMSS = 6 chars

    def test_filename_with_timestamp_and_version(
        self, service: ReportFileNamingService
    ) -> None:
        """タイムスタンプとバージョン両方付きファイル名生成"""
        config = ReportFileNameConfig(
            episode_number=5,
            report_type="quality",
            extension="json",
            include_timestamp=True,
            version="v3",
        )
        filename = service.generate_filename(config)
        assert filename.startswith("episode_005_quality_")
        assert "_v3.json" in filename

    def test_sorting_order(self, service: ReportFileNamingService) -> None:
        """ソート順序の検証"""
        configs = [
            ReportFileNameConfig(i, "A41", "md") for i in [1, 2, 10, 100, 999]
        ]
        filenames = [service.generate_filename(c) for c in configs]

        # 自然順序でソート
        assert filenames == sorted(filenames)
        assert filenames[0] == "episode_001_A41.md"
        assert filenames[1] == "episode_002_A41.md"
        assert filenames[2] == "episode_010_A41.md"
        assert filenames[3] == "episode_100_A41.md"
        assert filenames[4] == "episode_999_A41.md"

    def test_parse_basic_filename(self, service: ReportFileNamingService) -> None:
        """基本的なファイル名のパース"""
        parsed = service.parse_filename("episode_001_A41.md")
        assert parsed["episode_number"] == 1
        assert parsed["report_type"] == "A41"
        assert parsed["extension"] == "md"
        assert parsed["timestamp"] is None
        assert parsed["version"] is None

    def test_parse_filename_with_version(
        self, service: ReportFileNamingService
    ) -> None:
        """バージョン付きファイル名のパース"""
        parsed = service.parse_filename("episode_042_quality_v2.json")
        assert parsed["episode_number"] == 42
        assert parsed["report_type"] == "quality"
        assert parsed["extension"] == "json"
        assert parsed["version"] == "v2"

    def test_parse_filename_with_timestamp(
        self, service: ReportFileNamingService
    ) -> None:
        """タイムスタンプ付きファイル名のパース"""
        parsed = service.parse_filename("episode_010_backup_20250113_143052.yaml")
        assert parsed["episode_number"] == 10
        assert parsed["report_type"] == "backup"
        assert parsed["extension"] == "yaml"
        assert parsed["timestamp"] == "20250113_143052"

    def test_parse_filename_with_timestamp_and_version(
        self, service: ReportFileNamingService
    ) -> None:
        """タイムスタンプとバージョン付きファイル名のパース"""
        parsed = service.parse_filename(
            "episode_005_quality_20250113_143052_v3.json"
        )
        assert parsed["episode_number"] == 5
        assert parsed["report_type"] == "quality"
        assert parsed["timestamp"] == "20250113_143052"
        assert parsed["version"] == "v3"
        assert parsed["extension"] == "json"

    def test_parse_invalid_filename_format(
        self, service: ReportFileNamingService
    ) -> None:
        """無効なフォーマットでエラー"""
        with pytest.raises(ValueError, match="does not match naming convention"):
            service.parse_filename("invalid_filename.md")

    def test_parse_legacy_filename_format(
        self, service: ReportFileNamingService
    ) -> None:
        """レガシー形式（A41_ep001.md）ではエラー"""
        with pytest.raises(ValueError, match="does not match naming convention"):
            service.parse_filename("A41_ep001.md")

    def test_validate_valid_filename(self, service: ReportFileNamingService) -> None:
        """有効なファイル名の検証"""
        assert service.validate_filename("episode_001_A41.md") is True
        assert service.validate_filename("episode_042_quality_v2.json") is True
        assert (
            service.validate_filename("episode_010_backup_20250113_143052.yaml")
            is True
        )

    def test_validate_invalid_filename(self, service: ReportFileNamingService) -> None:
        """無効なファイル名の検証"""
        assert service.validate_filename("invalid.md") is False
        assert service.validate_filename("A41_ep001.md") is False
        assert service.validate_filename("episode_1_A41.md") is False  # ゼロ埋めなし

    def test_validate_sorting_order_success(
        self, service: ReportFileNamingService
    ) -> None:
        """ソート順序の検証（成功）"""
        filenames = [
            "episode_001_A41.md",
            "episode_002_A41.md",
            "episode_010_A41.md",
            "episode_100_A41.md",
        ]
        assert service.validate_sorting_order(filenames) is True

    def test_validate_sorting_order_failure(
        self, service: ReportFileNamingService
    ) -> None:
        """ソート順序の検証（失敗）"""
        filenames = [
            "episode_001_A41.md",
            "episode_010_A41.md",
            "episode_002_A41.md",  # 順序不正
        ]
        assert service.validate_sorting_order(filenames) is False

    def test_extract_episode_number_from_path(
        self, service: ReportFileNamingService
    ) -> None:
        """ファイルパスからエピソード番号を抽出"""
        path = Path("reports/quality/episode_042_A41.md")
        episode = service.extract_episode_number(path)
        assert episode == 42

    def test_extract_episode_number_from_invalid_path(
        self, service: ReportFileNamingService
    ) -> None:
        """無効なファイルパスからの抽出はNone"""
        path = Path("reports/quality/legacy_A41_ep1.md")
        episode = service.extract_episode_number(path)
        assert episode is None
