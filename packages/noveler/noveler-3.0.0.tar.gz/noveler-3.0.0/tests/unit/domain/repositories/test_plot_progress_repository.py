"""PlotProgressRepositoryインターフェースのテスト
TDD: RED Phase - インターフェースを定義してテストから開始


仕様書: SPEC-UNIT-TEST
"""

from pathlib import Path

import pytest

from noveler.domain.repositories.plot_progress_repository import PlotProgressRepository
from noveler.domain.services.plot_progress_service import PlotProgressService


class TestPlotProgressRepository:
    """PlotProgressRepositoryインターフェースのテスト"""

    @pytest.mark.spec("SPEC-PLOT_PROGRESS_REPOSITORY-REPOSITORY_INTERFACE")
    def test_repository_interface_exists(self) -> None:
        """リポジトリインターフェースが存在する"""
        # インターフェースの存在確認
        assert hasattr(PlotProgressRepository, "read_file_content")
        assert hasattr(PlotProgressRepository, "parse_yaml_content")
        assert hasattr(PlotProgressRepository, "file_exists")
        assert hasattr(PlotProgressRepository, "list_files")

    @pytest.mark.spec("SPEC-PLOT_PROGRESS_REPOSITORY-MOCK_REPOSITORY_IMPL")
    def test_mock_repository_implementation(self) -> None:
        """モックリポジトリの実装テスト"""

        # インメモリ実装のテスト
        class InMemoryPlotProgressRepository(PlotProgressRepository):
            def __init__(self) -> None:
                self.files = {}

            def read_file_content(self, file_path: Path) -> str:
                str_path = str(file_path)
                if str_path not in self.files:
                    msg = f"File not found: {file_path}"
                    raise FileNotFoundError(msg)
                return str(self.files[str_path])

            def parse_yaml_content(self, content: str) -> dict[str, object]:
                # 簡易的なYAMLパース(テスト用)
                if not content.strip():
                    return {}
                if "invalid" in content:
                    msg = "Invalid YAML"
                    raise ValueError(msg)
                return {"parsed": True, "content": content}

            def file_exists(self, file_path: Path) -> bool:
                return str(file_path) in self.files

            def list_files(self, directory: Path, pattern: str) -> list[Path]:
                results = []
                dir_str = str(directory)
                for file_path in self.files:
                    if file_path.startswith(dir_str) and pattern in file_path:
                        results.append(Path(file_path))
                return results

            def add_test_file(self, file_path: str, content: str) -> None:
                """テスト用:ファイルを追加"""
                self.files[file_path] = content

        # リポジトリのテスト
        repo = InMemoryPlotProgressRepository()
        repo.add_test_file("/test/file.yaml", "test: content")

        # ファイル読み込みテスト
        content = repo.read_file_content(Path("/test/file.yaml"))
        assert content == "test: content"

        # YAML解析テスト
        parsed = repo.parse_yaml_content(content)
        assert parsed["parsed"] is True

        # ファイル存在確認テスト
        assert repo.file_exists(Path("/test/file.yaml"))
        assert not repo.file_exists(Path("/test/nonexistent.yaml"))

        # ファイル一覧テスト
        repo.add_test_file("/test/chapter1.yaml", "content1")
        repo.add_test_file("/test/chapter2.yaml", "content2")
        files = repo.list_files(Path("/test"), "chapter")
        assert len(files) == 2


class TestPlotProgressServiceWithRepository:
    """リポジトリを使用したPlotProgressServiceのテスト"""

    @pytest.mark.spec("SPEC-PLOT_PROGRESS_REPOSITORY-SERVICE_USES_REPOSIT")
    def test_service_uses_repository_instead_of_direct_io(self) -> None:
        """サービスがファイルI/Oの代わりにリポジトリを使用する"""

        # モックリポジトリ
        class MockRepository(PlotProgressRepository):
            def __init__(self) -> None:
                self.read_calls = []
                self.parse_calls = []

            def read_file_content(self, file_path: Path) -> str:
                self.read_calls.append(file_path)
                return "mock content"

            def parse_yaml_content(self, content: str) -> dict[str, object]:
                self.parse_calls.append(content)
                return {"mock": "data"}

            def file_exists(self, file_path: Path) -> bool:
                return True

            def list_files(self, directory: Path, pattern: str) -> list[Path]:
                return [directory / "mock_file.yaml"]

        # リポジトリを注入してサービスを作成
        repo = MockRepository()
        PlotProgressService(repository=repo)

        # メソッドを呼び出してリポジトリが使用されることを確認
        # (実装後にこのテストが通るようになる)
