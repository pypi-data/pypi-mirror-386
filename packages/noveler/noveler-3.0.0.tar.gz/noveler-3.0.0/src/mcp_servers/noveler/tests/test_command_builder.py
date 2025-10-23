"""CommandBuilderのユニットテスト

純粋関数によるコマンド構築ロジックをテスト
"""

from pathlib import Path

from mcp_servers.noveler.core.command_builder import CommandBuilder


class TestCommandBuilder:
    """CommandBuilderのテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.builder = CommandBuilder()

    def test_build_novel_command_basic(self):
        """基本的なnovelコマンド構築テスト"""
        command = "write 1"
        options = {}

        cmd_parts, working_dir = self.builder.build_novel_command(command, options)

        assert len(cmd_parts) >= 3
        assert cmd_parts[-2:] == ["write", "1"]
        assert isinstance(working_dir, Path)
        assert working_dir.is_absolute()

    def test_build_novel_command_with_options(self):
        """オプション付きnovelコマンド構築テスト"""
        command = "write 1"
        options = {
            "force": True,
            "output": "test.txt",
            "verbose": False,
            "count": 10
        }

        cmd_parts, working_dir = self.builder.build_novel_command(command, options)

        # ブール値Trueオプションの確認
        assert "--force" in cmd_parts

        # 値付きオプションの確認
        assert "--output" in cmd_parts
        assert "test.txt" in cmd_parts

        # ブール値Falseオプションは含まれない
        assert "--verbose" not in cmd_parts

        # 数値オプションの確認
        assert "--count" in cmd_parts
        assert "10" in cmd_parts

    def test_build_novel_command_with_project_root(self):
        """プロジェクトルート指定時のコマンド構築テスト"""
        command = "check 2"
        options = {}
        project_root = "/tmp/test_project"

        cmd_parts, working_dir = self.builder.build_novel_command(
            command, options, project_root
        )

        assert cmd_parts[-2:] == ["check", "2"]
        assert working_dir == Path(project_root).absolute()

    def test_build_status_command(self):
        """statusコマンド構築テスト"""
        cmd_parts, working_dir = self.builder.build_status_command()

        assert cmd_parts[-1] == "status"
        assert isinstance(working_dir, Path)

    def test_build_status_command_with_project_root(self):
        """プロジェクトルート指定時のstatusコマンド構築テスト"""
        project_root = "/tmp/test_status"

        cmd_parts, working_dir = self.builder.build_status_command(project_root)

        assert cmd_parts[-1] == "status"
        assert working_dir == Path(project_root).absolute()

    def test_build_check_command_basic(self):
        """基本的なcheckコマンド構築テスト"""
        check_type = "grammar"

        cmd_parts, working_dir = self.builder.build_check_command(check_type)

        assert cmd_parts[-2:] == ["check", "grammar"]
        assert isinstance(working_dir, Path)

    def test_build_check_command_with_file(self):
        """ファイル指定時のcheckコマンド構築テスト"""
        check_type = "readability"
        file_path = "test.txt"

        cmd_parts, working_dir = self.builder.build_check_command(
            check_type, file_path
        )

        assert cmd_parts[-3:] == ["check", "readability", "test.txt"]

    def test_build_check_command_with_options(self):
        """オプション付きcheckコマンド構築テスト"""
        check_type = "consistency"
        file_path = "novel.txt"
        options = {
            "strict": True,
            "threshold": 0.8,
            "format": "json"
        }

        cmd_parts, working_dir = self.builder.build_check_command(
            check_type, file_path, options
        )

        assert "check" in cmd_parts
        assert "consistency" in cmd_parts
        assert "novel.txt" in cmd_parts
        assert "--strict" in cmd_parts
        assert "--threshold" in cmd_parts
        assert "0.8" in cmd_parts
        assert "--format" in cmd_parts
        assert "json" in cmd_parts

    def test_validate_command_valid_commands(self):
        """有効なコマンドの検証テスト"""
        valid_commands = [
            "write 1",
            "check grammar test.txt",
            "status",
            "plot 5",
            "analyze output.json",
            "backup project"
        ]

        for command in valid_commands:
            assert self.builder.validate_command(command) is True

    def test_validate_command_invalid_commands(self):
        """無効なコマンドの検証テスト"""
        invalid_commands = [
            "",
            "   ",
            "invalid_command 1",
            "rm -rf /",
            "exec malicious_code"
        ]

        for command in invalid_commands:
            assert self.builder.validate_command(command) is False

    def test_build_environment_vars_without_project_root(self):
        """プロジェクトルートなしの環境変数構築テスト"""
        env_vars = self.builder.build_environment_vars()

        assert isinstance(env_vars, dict)
        # プロジェクトルートが指定されていない場合は空辞書
        assert len(env_vars) == 0

    def test_build_environment_vars_with_project_root(self):
        """プロジェクトルート指定時の環境変数構築テスト"""
        project_root = "/tmp/test_env"

        env_vars = self.builder.build_environment_vars(project_root)

        assert isinstance(env_vars, dict)
        assert "PROJECTS_ROOT" in env_vars
        assert "PROJECT_ROOT" in env_vars

        expected_path = str(Path(project_root).absolute())
        assert env_vars["PROJECTS_ROOT"] == expected_path
        assert env_vars["PROJECT_ROOT"] == expected_path

    def test_get_noveler_command_path_development(self):
        """開発環境でのnovelerコマンドパス取得テスト"""
        # distディレクトリが存在しない場合のテスト
        builder = CommandBuilder(base_dir=Path("/tmp/test_no_dist"))

        noveler_path = builder._get_noveler_command_path()

        expected_path = Path("/tmp/test_no_dist/bin/noveler-dev")
        assert noveler_path == expected_path

    def test_get_noveler_command_path_production(self, tmp_path):
        """本番環境でのnovelerコマンドパス取得テスト"""
        # distディレクトリを作成
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        builder = CommandBuilder(base_dir=tmp_path)

        noveler_path = builder._get_noveler_command_path()

        expected_path = tmp_path / "bin" / "noveler"
        assert noveler_path == expected_path

    def test_command_builder_immutability(self):
        """CommandBuilderの純粋関数性テスト（状態変更なし）"""
        command = "write 1"
        options = {"force": True}

        # 同じ入力で複数回呼び出し
        result1 = self.builder.build_novel_command(command, options)
        result2 = self.builder.build_novel_command(command, options)

        # 結果が同じであることを確認
        assert result1[0] == result2[0]  # コマンド配列
        assert result1[1] == result2[1]  # 作業ディレクトリ

    def test_option_handling_edge_cases(self):
        """オプション処理のエッジケーステスト"""
        command = "write 1"
        options = {
            "none_value": None,
            "empty_string": "",
            "zero": 0,
            "false": False,
            "true": True
        }

        cmd_parts, _ = self.builder.build_novel_command(command, options)

        # None値は無視される
        assert "--none_value" not in cmd_parts

        # 空文字列は含まれる
        assert "--empty_string" in cmd_parts
        assert "" in cmd_parts

        # 0は含まれる
        assert "--zero" in cmd_parts
        assert "0" in cmd_parts

        # Falseは無視される
        assert "--false" not in cmd_parts

        # Trueはフラグとして含まれる
        assert "--true" in cmd_parts

    def test_complex_command_parsing(self):
        """複雑なコマンド解析テスト"""
        command = "write 1 --additional-flag"
        options = {"output": "test.txt"}

        cmd_parts, _ = self.builder.build_novel_command(command, options)

        # コマンド部分の解析確認
        assert "write" in cmd_parts
        assert "1" in cmd_parts
        assert "--additional-flag" in cmd_parts

        # オプション部分の追加確認
        assert "--output" in cmd_parts
        assert "test.txt" in cmd_parts
