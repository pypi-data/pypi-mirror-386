# File: tests/unit/infrastructure/adapters/test_path_service_report_filename.py
# Purpose: Integration tests for report filename generation via PathService
# Context: Validates that PathServiceAdapter correctly delegates to ReportFileNamingService

from pathlib import Path

import pytest

from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter


class TestPathServiceReportFilenameGeneration:
    """PathServiceAdapter経由のレポートファイル名生成テスト"""

    @pytest.fixture
    def path_service(self, tmp_path: Path) -> PathServiceAdapter:
        """PathServiceAdapterインスタンス"""
        return PathServiceAdapter(project_root=tmp_path)

    def test_basic_report_filename_generation(
        self, path_service: PathServiceAdapter
    ) -> None:
        """基本的なレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=1, report_type="A41", extension="md"
        )
        assert filename == "episode_001_A41.md"

    def test_report_filename_with_json_extension(
        self, path_service: PathServiceAdapter
    ) -> None:
        """JSON拡張子でのレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=42, report_type="quality", extension="json"
        )
        assert filename == "episode_042_quality.json"

    def test_report_filename_with_yaml_extension(
        self, path_service: PathServiceAdapter
    ) -> None:
        """YAML拡張子でのレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=999, report_type="backup", extension="yaml"
        )
        assert filename == "episode_999_backup.yaml"

    def test_report_filename_with_version(
        self, path_service: PathServiceAdapter
    ) -> None:
        """バージョン付きレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=1, report_type="A41", extension="md", version="v2"
        )
        assert filename == "episode_001_A41_v2.md"

    def test_report_filename_with_timestamp(
        self, path_service: PathServiceAdapter
    ) -> None:
        """タイムスタンプ付きレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=1,
            report_type="backup",
            extension="yaml",
            include_timestamp=True,
        )
        # タイムスタンプの正確な値は予測不可能
        assert filename.startswith("episode_001_backup_")
        assert filename.endswith(".yaml")

    def test_report_filename_with_timestamp_and_version(
        self, path_service: PathServiceAdapter
    ) -> None:
        """タイムスタンプとバージョン付きレポートファイル名生成"""
        filename = path_service.generate_report_filename(
            episode_number=5,
            report_type="quality",
            extension="json",
            include_timestamp=True,
            version="v3",
        )
        assert filename.startswith("episode_005_quality_")
        assert "_v3.json" in filename

    def test_report_filename_sorting_consistency(
        self, path_service: PathServiceAdapter
    ) -> None:
        """複数エピソードのレポートファイル名がソート可能"""
        filenames = [
            path_service.generate_report_filename(i, "A41", "md")
            for i in [1, 2, 10, 100, 999]
        ]

        # 自然順序でソート
        assert filenames == sorted(filenames)
        assert filenames[0] == "episode_001_A41.md"
        assert filenames[1] == "episode_002_A41.md"
        assert filenames[2] == "episode_010_A41.md"
        assert filenames[3] == "episode_100_A41.md"
        assert filenames[4] == "episode_999_A41.md"

    def test_report_filename_invalid_episode_number_too_low(
        self, path_service: PathServiceAdapter
    ) -> None:
        """エピソード番号が範囲外（下限）でエラー"""
        with pytest.raises(ValueError, match="must be between 1 and 999"):
            path_service.generate_report_filename(
                episode_number=0, report_type="A41", extension="md"
            )

    def test_report_filename_invalid_episode_number_too_high(
        self, path_service: PathServiceAdapter
    ) -> None:
        """エピソード番号が範囲外（上限）でエラー"""
        with pytest.raises(ValueError, match="must be between 1 and 999"):
            path_service.generate_report_filename(
                episode_number=1000, report_type="A41", extension="md"
            )

    def test_full_path_generation_with_reports_dir(
        self, path_service: PathServiceAdapter
    ) -> None:
        """reportsディレクトリと組み合わせた完全パス生成"""
        reports_dir = path_service.get_reports_dir()
        quality_dir = reports_dir / "quality"
        quality_dir.mkdir(parents=True, exist_ok=True)

        filename = path_service.generate_report_filename(
            episode_number=1, report_type="A41", extension="md"
        )

        full_path = quality_dir / filename
        # パスの末尾部分を検証（プラットフォーム独立）
        assert full_path.name == "episode_001_A41.md"
        assert full_path.parent.name == "quality"

    def test_different_report_types(
        self, path_service: PathServiceAdapter
    ) -> None:
        """異なるレポートタイプでのファイル名生成"""
        report_types = ["A41", "quality", "backup", "summary", "analysis"]

        for report_type in report_types:
            filename = path_service.generate_report_filename(
                episode_number=1, report_type=report_type, extension="md"
            )
            assert filename == f"episode_001_{report_type}.md"
