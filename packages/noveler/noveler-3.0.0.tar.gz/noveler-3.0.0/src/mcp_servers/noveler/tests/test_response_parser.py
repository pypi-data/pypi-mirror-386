"""ResponseParserのユニットテスト

純粋関数によるレスポンス解析ロジックをテスト
"""


from mcp_servers.noveler.core.response_parser import ResponseParser


class TestResponseParser:
    """ResponseParserのテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.parser = ResponseParser()

    def test_parse_novel_output_success(self):
        """成功時のnovel出力解析テスト"""
        stdout = "Created: output.txt\n処理完了しました"
        stderr = ""
        return_code = 0

        result = self.parser.parse_novel_output(stdout, stderr, return_code)

        assert result["success"] is True
        assert result["return_code"] == 0
        assert result["raw_output"]["stdout"] == stdout
        assert result["raw_output"]["stderr"] == stderr
        assert "generated_files" in result
        assert "output.txt" in result["generated_files"]

    def test_parse_novel_output_error(self):
        """エラー時のnovel出力解析テスト"""
        stdout = ""
        stderr = "FileNotFoundError: File not found"
        return_code = 1

        result = self.parser.parse_novel_output(stdout, stderr, return_code)

        assert result["success"] is False
        assert result["return_code"] == 1
        assert result["error_type"] == "file_not_found"
        assert result["error_message"] == stderr.strip()

    def test_parse_status_output_success(self):
        """成功時のstatus出力解析テスト"""
        stdout = "Project: test_novel\nProgress: 5/10\nLast updated: 2025-01-01"
        stderr = ""
        return_code = 0

        result = self.parser.parse_status_output(stdout, stderr, return_code)

        assert result["success"] is True
        assert result["status"]["project"] == "test_novel"
        assert result["status"]["progress"]["current"] == 5
        assert result["status"]["progress"]["total"] == 10
        assert result["status"]["last_updated"] == "2025-01-01"

    def test_parse_check_output_grammar_success(self):
        """文法チェック成功時の出力解析テスト"""
        stdout = "Line 1: 誤字があります\n行 5: 文法エラーです"
        stderr = ""
        return_code = 0
        check_type = "grammar"

        result = self.parser.parse_check_output(stdout, stderr, return_code, check_type)

        assert result["success"] is True
        assert result["check_type"] == "grammar"
        assert len(result["check_results"]["issues"]) == 2
        assert result["check_results"]["issues"][0]["line"] == 1
        assert result["check_results"]["issues"][1]["line"] == 5

    def test_parse_check_output_readability_with_score(self):
        """可読性チェックのスコア解析テスト"""
        stdout = "Score: 75.5\nAverage sentence length: 20.3\nComplex word ratio: 0.15"
        stderr = ""
        return_code = 0
        check_type = "readability"

        result = self.parser.parse_check_output(stdout, stderr, return_code, check_type)

        assert result["success"] is True
        assert result["check_results"]["score"] == 75.5
        assert "metrics" in result["check_results"]

    def test_parse_error_output_with_traceback(self):
        """トレースバック付きエラー解析テスト"""
        stderr = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    raise ValueError("Test error")
ValueError: Test error"""

        error_info = self.parser._parse_error_output(stderr)

        assert error_info["error_type"] == "unknown"
        assert "traceback" in error_info
        assert "Traceback" in error_info["traceback"]
        assert "ValueError: Test error" in error_info["traceback"]

    def test_extract_json_response_valid_json(self):
        """有効なJSON抽出テスト"""
        text = 'Some text {"key": "value", "number": 42} more text'

        result = self.parser.extract_json_response(text)

        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_extract_json_response_complex_json(self):
        """複雑なJSON抽出テスト"""
        text = '''Output: {"results": [{"id": 1, "name": "test"}, {"id": 2, "name": "sample"}], "total": 2}'''

        result = self.parser.extract_json_response(text)

        assert result is not None
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["total"] == 2

    def test_extract_json_response_no_json(self):
        """JSON無しテキストの処理テスト"""
        text = "This is plain text without JSON data"

        result = self.parser.extract_json_response(text)

        assert result is None

    def test_extract_json_response_invalid_json(self):
        """無効なJSON処理テスト"""
        text = "Invalid JSON: {key: value, broken"

        result = self.parser.extract_json_response(text)

        assert result is None

    def test_validate_output_format_valid(self):
        """有効な解析結果形式検証テスト"""
        valid_result = {
            "success": True,
            "return_code": 0,
            "raw_output": {
                "stdout": "test output",
                "stderr": ""
            }
        }

        assert self.parser.validate_output_format(valid_result) is True

    def test_validate_output_format_missing_keys(self):
        """必須キー不足の形式検証テスト"""
        invalid_results = [
            {"return_code": 0, "raw_output": {"stdout": "", "stderr": ""}},  # success不足
            {"success": True, "raw_output": {"stdout": "", "stderr": ""}},  # return_code不足
            {"success": True, "return_code": 0},  # raw_output不足
            {"success": True, "return_code": 0, "raw_output": "invalid"},  # raw_output形式不正
            {"success": True, "return_code": 0, "raw_output": {"stderr": ""}},  # stdout不足
            {"success": True, "return_code": 0, "raw_output": {"stdout": ""}},  # stderr不足
        ]

        for invalid_result in invalid_results:
            assert self.parser.validate_output_format(invalid_result) is False

    def test_parse_success_output_file_generation(self):
        """ファイル生成情報解析テスト"""
        stdout_patterns = [
            "Created: chapter1.txt",
            "Generated: output.json",
            "Written to: final.md",
            "Saved: backup.zip"
        ]

        for stdout in stdout_patterns:
            result = self.parser._parse_success_output(stdout)
            assert "generated_files" in result
            assert len(result["generated_files"]) > 0

    def test_parse_success_output_status_detection(self):
        """ステータス検出テスト"""
        status_tests = [
            ("処理完了しました", "completed"),
            ("成功しました", "completed"),
            ("Success!", "completed"),
            ("処理中...", "processing"),
            ("Processing data", "processing")
        ]

        for stdout, expected_status in status_tests:
            result = self.parser._parse_success_output(stdout)
            if "status" in result:
                assert result["status"] == expected_status

    def test_parse_consistency_check(self):
        """一貫性チェック解析テスト"""
        stdout = "Inconsistency found: Character name mismatch at line 15\n不整合: 設定矛盾 25行目"

        result = self.parser._parse_consistency_check(stdout)

        assert "inconsistencies" in result
        assert len(result["inconsistencies"]) == 2
        assert result["inconsistencies"][0]["line"] == 15
        assert result["inconsistencies"][1]["line"] == 25

    def test_parse_generic_check_status(self):
        """汎用チェックステータス解析テスト"""
        test_cases = [
            ("Check passed successfully", "passed"),
            ("All tests OK", "passed"),
            ("成功", "passed"),
            ("Error detected in analysis", "failed"),
            ("Fail: Multiple issues found", "failed"),
            ("エラーが見つかりました", "failed"),
            ("Unknown result", "unknown")
        ]

        for stdout, expected_status in test_cases:
            result = self.parser._parse_generic_check(stdout)
            assert result["status"] == expected_status

    def test_response_parser_immutability(self):
        """ResponseParserの純粋関数性テスト（状態変更なし）"""
        stdout = "Test output"
        stderr = ""
        return_code = 0

        # 同じ入力で複数回呼び出し
        result1 = self.parser.parse_novel_output(stdout, stderr, return_code)
        result2 = self.parser.parse_novel_output(stdout, stderr, return_code)

        # 結果が同じであることを確認
        assert result1 == result2

    def test_error_type_classification(self):
        """エラータイプ分類テスト"""
        error_tests = [
            ("FileNotFoundError: No such file", "file_not_found"),
            ("PermissionError: Access denied", "permission_denied"),
            ("ValidationError: Invalid input", "validation_error"),
            ("JSONDecodeError: Invalid JSON", "json_decode_error"),
            ("SomeUnknownError: Mystery", "unknown")
        ]

        for stderr, expected_type in error_tests:
            error_info = self.parser._parse_error_output(stderr)
            assert error_info["error_type"] == expected_type

    def test_multiline_json_extraction(self):
        """複数行JSON抽出テスト"""
        text = '''Processing...
{
  "status": "success",
  "data": {
    "count": 10,
    "items": ["a", "b", "c"]
  }
}
Done.'''

        result = self.parser.extract_json_response(text)

        assert result is not None
        assert result["status"] == "success"
        assert result["data"]["count"] == 10
        assert len(result["data"]["items"]) == 3
