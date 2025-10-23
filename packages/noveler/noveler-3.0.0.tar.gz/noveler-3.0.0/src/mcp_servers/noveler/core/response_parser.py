"""Parse command outputs produced by the ``noveler`` CLI.

The parser implements pure string-processing utilities so that tests can
validate the behaviour without invoking subprocesses.
"""

import json
import re
from typing import Any


class ResponseParser:
    """Parse stdout/stderr emitted by the ``noveler`` command set."""

    def parse_novel_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int
    ) -> dict[str, Any]:
        """Parse the generic ``noveler`` CLI response.

        Args:
            stdout (str): Captured standard output.
            stderr (str): Captured error output.
            return_code (int): Process return code.

        Returns:
            dict[str, Any]: Normalised payload including success flag,
            original output, and parsed metadata.
        """
        result = {
            "success": return_code == 0,
            "return_code": return_code,
            "raw_output": {
                "stdout": stdout,
                "stderr": stderr
            }
        }

        if return_code == 0:
            # 成功時の出力解析
            result.update(self._parse_success_output(stdout))
        else:
            # エラー時の出力解析
            result.update(self._parse_error_output(stderr))

        return result

    def parse_status_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int
    ) -> dict[str, Any]:
        """Parse ``noveler status`` output.

        Args:
            stdout (str): Captured standard output.
            stderr (str): Captured error output.
            return_code (int): Process return code.

        Returns:
            dict[str, Any]: Parsed payload including the extracted status
            summary.
        """
        result = {
            "success": return_code == 0,
            "return_code": return_code,
            "raw_output": {
                "stdout": stdout,
                "stderr": stderr
            }
        }

        if return_code == 0:
            # statusコマンド特有の出力解析
            status_info = self._extract_status_info(stdout)
            result["status"] = status_info
        else:
            result.update(self._parse_error_output(stderr))

        return result

    def parse_check_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        check_type: str
    ) -> dict[str, Any]:
        """Parse ``noveler check`` output.

        Args:
            stdout (str): Captured standard output.
            stderr (str): Captured error output.
            return_code (int): Process return code.
            check_type (str): Name of the executed check.

        Returns:
            dict[str, Any]: Parsed payload including structured check results.
        """
        result = {
            "success": return_code == 0,
            "return_code": return_code,
            "check_type": check_type,
            "raw_output": {
                "stdout": stdout,
                "stderr": stderr
            }
        }

        if return_code == 0:
            # チェック結果の解析
            check_results = self._extract_check_results(stdout, check_type)
            result["check_results"] = check_results
        else:
            result.update(self._parse_error_output(stderr))

        return result

    def _parse_success_output(self, stdout: str) -> dict[str, Any]:
        """Parse success output and extract structured metadata.

        Args:
            stdout (str): Captured standard output.

        Returns:
            dict[str, Any]: Parsed metadata such as generated files and JSON
            payloads.
        """
        output_info = {}

        # ファイル生成情報を抽出
        file_patterns = [
            r"Created: (.+)",
            r"Generated: (.+)",
            r"Written to: (.+)",
            r"Saved: (.+)"
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, stdout)
            if matches:
                output_info["generated_files"] = matches
                break

        # プロセス情報を抽出
        if "完了" in stdout or "成功" in stdout or "Success" in stdout:
            output_info["status"] = "completed"
        elif "処理中" in stdout or "Processing" in stdout:
            output_info["status"] = "processing"

        # JSONレスポンスが含まれている場合
        json_match = re.search(r"\{.*\}", stdout, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                output_info["json_response"] = json_data
            except json.JSONDecodeError:
                pass

        return output_info

    def _parse_error_output(self, stderr: str) -> dict[str, Any]:
        """Parse error output and categorise the failure type.

        Args:
            stderr (str): Captured error output.

        Returns:
            dict[str, Any]: Parsed error metadata including type, message,
            and traceback information if available.
        """
        error_info = {}

        # エラーメッセージの分類
        if "FileNotFoundError" in stderr:
            error_info["error_type"] = "file_not_found"
        elif "PermissionError" in stderr:
            error_info["error_type"] = "permission_denied"
        elif "ValidationError" in stderr:
            error_info["error_type"] = "validation_error"
        elif "JSONDecodeError" in stderr:
            error_info["error_type"] = "json_decode_error"
        else:
            error_info["error_type"] = "unknown"

        # エラーメッセージの抽出
        error_info["error_message"] = stderr.strip()

        # トレースバック情報の抽出
        if "Traceback" in stderr:
            traceback_lines = []
            lines = stderr.split("\n")
            in_traceback = False

            for line in lines:
                if "Traceback" in line:
                    in_traceback = True
                if in_traceback:
                    traceback_lines.append(line)

            error_info["traceback"] = "\n".join(traceback_lines)

        return error_info

    def _extract_status_info(self, stdout: str) -> dict[str, Any]:
        """status情報を抽出

        Args:
            stdout: 標準出力文字列

        Returns:
            ステータス情報
        """
        status_info = {}

        # プロジェクト情報
        project_match = re.search(r"Project: (.+)", stdout)
        if project_match:
            status_info["project"] = project_match.group(1).strip()

        # 進捗情報
        progress_match = re.search(r"Progress: (\d+)/(\d+)", stdout)
        if progress_match:
            status_info["progress"] = {
                "current": int(progress_match.group(1)),
                "total": int(progress_match.group(2))
            }

        # 最終更新
        update_match = re.search(r"Last updated: (.+)", stdout)
        if update_match:
            status_info["last_updated"] = update_match.group(1).strip()

        return status_info

    def _extract_check_results(self, stdout: str, check_type: str) -> dict[str, Any]:
        """チェック結果を抽出

        Args:
            stdout: 標準出力文字列
            check_type: チェック種別

        Returns:
            チェック結果
        """
        check_results = {
            "check_type": check_type,
            "issues": [],
            "score": None,
            "summary": ""
        }

        # 文法チェック特有の処理
        if check_type == "grammar":
            check_results.update(self._parse_grammar_check(stdout))
        elif check_type == "readability":
            check_results.update(self._parse_readability_check(stdout))
        elif check_type == "consistency":
            check_results.update(self._parse_consistency_check(stdout))
        else:
            # 汎用的なチェック結果解析
            check_results.update(self._parse_generic_check(stdout))

        return check_results

    def _parse_grammar_check(self, stdout: str) -> dict[str, Any]:
        """文法チェック結果を解析"""
        results = {"issues": []}

        # エラーパターンの抽出
        error_patterns = [
            r"Line (\d+): (.+)",
            r"行 (\d+): (.+)",
            r"(\d+)行目: (.+)"
        ]

        for pattern in error_patterns:
            matches = re.findall(pattern, stdout)
            for match in matches:
                results["issues"].append({
                    "line": int(match[0]),
                    "message": match[1].strip()
                })

        return results

    def _parse_readability_check(self, stdout: str) -> dict[str, Any]:
        """可読性チェック結果を解析"""
        results = {}

        # スコアの抽出
        score_match = re.search(r"Score: (\d+(?:\.\d+)?)", stdout)
        if score_match:
            results["score"] = float(score_match.group(1))

        # 可読性指標の抽出
        metrics_patterns = [
            r"Average sentence length: (\d+(?:\.\d+)?)",
            r"Complex word ratio: (\d+(?:\.\d+)?)",
            r"平均文長: (\d+(?:\.\d+)?)",
            r"複雑語比率: (\d+(?:\.\d+)?)"
        ]

        metrics = {}
        for pattern in metrics_patterns:
            match = re.search(pattern, stdout)
            if match:
                key = pattern.split(":")[0].replace('r"', "").replace("\\", "")
                metrics[key] = float(match.group(1))

        if metrics:
            results["metrics"] = metrics

        return results

    def _parse_consistency_check(self, stdout: str) -> dict[str, Any]:
        """一貫性チェック結果を解析"""
        results = {"inconsistencies": []}

        # 不整合パターンの抽出
        inconsistency_patterns = [
            r"Inconsistency found: (.+) at line (\d+)",
            r"不整合: (.+) (\d+)行目"
        ]

        for pattern in inconsistency_patterns:
            matches = re.findall(pattern, stdout)
            for match in matches:
                results["inconsistencies"].append({
                    "message": match[0].strip(),
                    "line": int(match[1])
                })

        return results

    def _parse_generic_check(self, stdout: str) -> dict[str, Any]:
        """汎用的なチェック結果を解析"""
        results = {}

        # 基本的なパターン抽出（大文字小文字を考慮）
        stdout_lower = stdout.lower()
        if ("ok" in stdout_lower or "pass" in stdout_lower or "success" in stdout_lower or
            "成功" in stdout or "完了" in stdout):
            results["status"] = "passed"
        elif ("error" in stdout_lower or "fail" in stdout_lower or
              "エラー" in stdout or "失敗" in stdout):
            results["status"] = "failed"
        else:
            results["status"] = "unknown"

        # サマリーの抽出
        summary_match = re.search(r"Summary: (.+)", stdout)
        if summary_match:
            results["summary"] = summary_match.group(1).strip()

        return results

    def extract_json_response(self, text: str) -> dict[str, Any] | None:
        """テキストからJSONレスポンスを抽出

        Args:
            text: 解析対象のテキスト

        Returns:
            抽出されたJSONデータまたはNone
        """
        # JSON形式のデータを探す
        json_patterns = [
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",  # 単純なJSON
            r"\{.*?\}",  # 非貪欲マッチ
            r"\{[\s\S]*\}"  # 改行を含む
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        return None

    def validate_output_format(self, parsed_result: dict[str, Any]) -> bool:
        """解析結果の形式を検証

        Args:
            parsed_result: 解析結果

        Returns:
            形式が正しい場合True
        """
        required_keys = ["success", "return_code", "raw_output"]

        for key in required_keys:
            if key not in parsed_result:
                return False

        # raw_outputの形式チェック
        if not isinstance(parsed_result["raw_output"], dict):
            return False

        if "stdout" not in parsed_result["raw_output"]:
            return False

        return "stderr" in parsed_result["raw_output"]
