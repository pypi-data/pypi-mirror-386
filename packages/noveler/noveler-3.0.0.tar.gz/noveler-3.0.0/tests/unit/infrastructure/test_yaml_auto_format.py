"""YAML自動整形機能のテスト

TDDアプローチでYAML保存時の自動整形・検証機能をテストする


仕様書: SPEC-INFRASTRUCTURE
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.infrastructure.utils.yaml_utils import YAMLHandler
from noveler.presentation.shared.shared_utilities import get_common_path_service


from noveler.presentation.shared import shared_utilities as shared_utils

class TestYAMLAutoFormat:
    """YAML自動整形機能のテスト"""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """テスト用プロジェクトディレクトリ"""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        original_service = getattr(shared_utils, "_common_path_service", None)
        shared_utils._common_path_service = None

        path_service = get_common_path_service(project_dir)
        management_dir = path_service.get_management_dir()
        manuscript_dir = path_service.get_manuscript_dir()
        management_dir.mkdir(parents=True, exist_ok=True)
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        try:
            yield project_dir
        finally:
            shared_utils._common_path_service = original_service

    def test_yaml_episode_repository_save_with_formatter(self, temp_project_dir: Path) -> None:
        """YamlEpisodeRepositoryの_save_episode_management()がYAML整形機能を使用することを確認"""
        # テストファイルパス
        path_service = get_common_path_service()
        management_file = temp_project_dir / str(path_service.get_management_dir()) / "話数管理.yaml"

        # テストコード(_save_episode_management メソッドをシミュレート)
        test_code = f"""
import sys
from pathlib import Path

sys.path.insert(0, r"{Path(__file__).parent.parent.parent.parent}")

from noveler.infrastructure.utils.yaml_utils import YAMLHandler

# テストデータ
data = {{
    "episodes": [{{
        "number": 1,
        "title": "第1話",
        "status": "執筆済み",
        "word_count": 5000
    }}]
}}

# 保存パス
path = Path(r"{management_file}")

# YAMLHandlerを使用して保存(use_formatter=True)
YAMLHandler.save_yaml(path, data, use_formatter=True)
"""

        # 一時ファイルにテストコードを書き込んで実行
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            temp_script = f.name

        try:
            #  # Moved to top-level
            result = subprocess.run([sys.executable, temp_script], check=False, capture_output=True, text=True)

            # エラーがないことを確認
            assert result.returncode == 0, f"Error: {result.stderr}"

            # ファイルが作成されたことを確認
            assert management_file.exists()

            # YAMLとして読み込めることを確認
            loaded_data = YAMLHandler.load_yaml(management_file)
            assert loaded_data["episodes"][0]["title"] == "第1話"

        finally:
            # 一時ファイルを削除
            Path(temp_script).unlink(missing_ok=True)

    def test_yaml_quality_record_repository_save_with_formatter(self, temp_project_dir: Path) -> None:
        """YamlQualityRecordRepositoryのsave()がYAML整形機能を使用することを確認"""
        # テストファイルパス
        path_service = get_common_path_service()
        quality_file = temp_project_dir / str(path_service.get_management_dir()) / "品質記録.yaml"

        # テストコード
        test_code = f"""
import sys
from pathlib import Path

sys.path.insert(0, r"{Path(__file__).parent.parent.parent.parent}")

from noveler.infrastructure.utils.yaml_utils import YAMLHandler

# テストデータ
data = {{
    "metadata": {{
        "project_name": "test_project",
        "last_updated": "2024-01-20T10:00:00"
    }},
    "quality_checks": [{{
        "episode_number": 1,
        "check_date": "2024-01-20T10:00:00",
        "overall_score": 85.0
    }}]
}}

# 保存パス
path = Path(r"{quality_file}")

# YAMLHandlerを使用して保存
YAMLHandler.save_yaml(path, data, use_formatter=True)
"""

        # 一時ファイルにテストコードを書き込んで実行
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            temp_script = f.name

        try:
            #  # Moved to top-level
            result = subprocess.run([sys.executable, temp_script], check=False, capture_output=True, text=True)

            # エラーがないことを確認
            assert result.returncode == 0, f"Error: {result.stderr}"

            # ファイルが作成されたことを確認
            assert quality_file.exists()

            # YAMLとして読み込めることを確認
            loaded_data = YAMLHandler.load_yaml(quality_file)
            assert loaded_data["metadata"]["project_name"] == "test_project"

        finally:
            # 一時ファイルを削除
            Path(temp_script).unlink(missing_ok=True)

    def test_yaml_formatter_integration(self, temp_project_dir: Path) -> None:
        """YAML整形機能の統合テスト"""
        # 不正な形式のYAMLデータ
        bad_yaml = {
            "episodes": {
                "ep1": {
                    "title": "テスト",  # 余分なスペース
                    "status": "draft",
                    "word_count": 5000,  # 余分なスペース
                }
            }
        }

        # ファイルパス
        test_file = temp_project_dir / "test.yaml"

        # ruamel.yamlがインストールされている場合のみテスト
        try:
            from noveler.infrastructure.utils.yaml_formatter import YAMLFormatter

            HAS_FORMATTER = True
            _ = YAMLFormatter  # 未使用インポート警告を回避
        except ImportError:
            HAS_FORMATTER = False

        if HAS_FORMATTER:
            # 整形付き保存
            YAMLHandler.save_yaml(test_file, bad_yaml, use_formatter=True)

            # ファイルが整形されたことを確認
            with open(test_file, encoding="utf-8") as f:
                content = f.read()

            # 正しいインデントと余分なスペースが削除されていることを確認
            assert "title: テスト" in content  # 余分なスペースなし
            assert "word_count: 5000" in content  # 余分なスペースなし

            # YAMLとして読み込めることを確認
            loaded_data = YAMLHandler.load_yaml(test_file)
            assert loaded_data["episodes"]["ep1"]["title"] == "テスト"
            assert loaded_data["episodes"]["ep1"]["word_count"] == 5000
        else:
            # フォーマッターがない場合も正常に保存できることを確認
            YAMLHandler.save_yaml(test_file, bad_yaml, use_formatter=False)
            assert test_file.exists()

    def test_fallback_on_formatter_error(self, temp_project_dir: Path) -> None:
        """整形エラー時のフォールバックテスト"""
        test_file = temp_project_dir / "test.yaml"
        test_data = {"key": "value"}

        # YAMLFormatterがエラーを起こすようにモック
        with patch("noveler.infrastructure.utils.yaml_utils.YAMLFormatter") as mock_formatter:
            mock_formatter_instance = Mock()
            mock_formatter_instance.save_yaml.side_effect = Exception("整形エラー")
            mock_formatter.return_value = mock_formatter_instance

            # エラーが起きても保存が成功することを確認
            YAMLHandler.save_yaml(test_file, test_data, use_formatter=True)
            assert test_file.exists()

            # 通常のyaml.dumpで保存されたことを確認
            with open(test_file, encoding="utf-8") as f:
                loaded_data = yaml.safe_load(f)
            assert loaded_data == test_data

    def test_preserve_comments_and_order(self, temp_project_dir: Path) -> None:
        """コメントと順序の保持テスト"""
        # ruamel.yamlがインストールされている場合のみテスト
        try:
            from noveler.infrastructure.utils.yaml_formatter import YAMLFormatter
        except ImportError:
            pytest.skip("ruamel.yaml not installed")

        # コメント付きYAMLファイルを作成
        test_file = temp_project_dir / "test_with_comments.yaml"
        yaml_content = """# プロジェクト設定
metadata:
  project_name: テストプロジェクト  # プロジェクト名
  version: 1.0.0
  # 最終更新日時
  last_updated: 2024-01-20

# エピソード情報
episodes:
  ep1:
    title: 第1話
    status: 執筆済み
"""

        # ファイルに書き込み
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # YAMLFormatterで読み込み・保存
        formatter = YAMLFormatter()
        data = formatter.load_yaml(test_file)
        success, messages = formatter.save_yaml(test_file, data)

        assert success

        # コメントが保持されていることを確認
        with open(test_file, encoding="utf-8") as f:
            saved_content = f.read()

        assert "# プロジェクト設定" in saved_content
        assert "# プロジェクト名" in saved_content
        assert "# 最終更新日時" in saved_content
        assert "# エピソード情報" in saved_content
