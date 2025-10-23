# File: tests/unit/hooks/test_halfwidth_checker.py
# Purpose: Unit tests for halfwidth alphanumeric checker script
# Context: Validates detection, conversion, and exclusion rules for Japanese text quality

import pytest
from pathlib import Path
import tempfile
import shutil
from scripts.hooks.halfwidth_checker import (
    Finding,
    is_japanese_context,
    mask_excluded_regions,
    scan_file,
    get_staged_files,
    HALFWIDTH_TO_FULLWIDTH,
)


class TestJapaneseContextDetection:
    """Test suite for Japanese context detection logic."""

    def test_japanese_context_hiragana(self):
        """Japanese context should be detected with Hiragana."""
        text = "これはa文字です"
        pos = text.index("a")
        assert is_japanese_context(text, pos, window=10) is True

    def test_japanese_context_katakana(self):
        """Japanese context should be detected with Katakana."""
        text = "カタカナ5文字"
        pos = text.index("5")
        assert is_japanese_context(text, pos, window=10) is True

    def test_japanese_context_kanji(self):
        """Japanese context should be detected with Kanji."""
        text = "漢字3個"
        pos = text.index("3")
        assert is_japanese_context(text, pos, window=10) is True

    def test_no_japanese_context_english_only(self):
        """No Japanese context should be detected in pure English text."""
        text = "This is version 3.14 release"
        pos = text.index("3")
        assert is_japanese_context(text, pos, window=10) is False

    def test_japanese_context_at_boundary(self):
        """Japanese context should be detected at text boundaries."""
        text = "日本語"
        # No halfwidth chars, but context detection should work
        assert is_japanese_context(text, 0, window=5) is True


class TestExclusionPatterns:
    """Test suite for exclusion pattern masking."""

    def test_mask_code_blocks(self):
        """Code blocks should be masked with spaces."""
        text = "テキスト\n```python\nprint('hello')\n```\n続き"
        masked = mask_excluded_regions(text)
        # Check that code block content is replaced with spaces
        assert "print" not in masked
        assert "hello" not in masked
        assert "テキスト" in masked
        assert "続き" in masked

    def test_mask_inline_code(self):
        """Inline code should be masked with spaces."""
        text = "これは`code123`です"
        masked = mask_excluded_regions(text)
        assert "code" not in masked
        assert "123" not in masked
        assert "これは" in masked

    def test_mask_urls(self):
        """URLs should be masked with spaces."""
        text = "参照: https://example.com/path123"
        masked = mask_excluded_regions(text)
        assert "example" not in masked
        assert "path123" not in masked
        assert "参照" in masked

    def test_mask_file_paths_windows(self):
        """Windows file paths should be masked."""
        text = "ファイル C:\\Users\\test\\file.txt を開く"
        masked = mask_excluded_regions(text)
        assert "Users" not in masked
        assert "test" not in masked
        assert "ファイル" in masked

    def test_mask_file_paths_unix(self):
        """Unix file paths should be masked."""
        text = "パス /usr/local/bin/python3 を使用"
        masked = mask_excluded_regions(text)
        assert "usr" not in masked
        assert "python" not in masked
        assert "パス" in masked

    def test_mask_version_numbers(self):
        """Version numbers should be masked."""
        text = "バージョン3.14.159をリリース"
        masked = mask_excluded_regions(text)
        # Version should be masked
        assert "3.14.159" not in masked
        assert "バージョン" in masked

    def test_mask_jira_ids(self):
        """JIRA IDs should be masked."""
        text = "課題PROJ-123を修正"
        masked = mask_excluded_regions(text)
        assert "PROJ-123" not in masked
        assert "課題" in masked

    def test_mask_units(self):
        """Measurement units should be masked."""
        text = "サイズ100px、時間500msです"
        masked = mask_excluded_regions(text)
        # Units should be masked
        assert "100px" not in masked
        assert "500ms" not in masked
        assert "サイズ" in masked


class TestFullwidthConversion:
    """Test suite for halfwidth to fullwidth character conversion."""

    def test_convert_digits(self):
        """Halfwidth digits should convert to fullwidth."""
        text = "0123456789"
        converted = text.translate(HALFWIDTH_TO_FULLWIDTH)
        assert converted == "０１２３４５６７８９"

    def test_convert_lowercase(self):
        """Halfwidth lowercase should convert to fullwidth."""
        text = "abcxyz"
        converted = text.translate(HALFWIDTH_TO_FULLWIDTH)
        assert converted == "ａｂｃｘｙｚ"

    def test_convert_uppercase(self):
        """Halfwidth uppercase should convert to fullwidth."""
        text = "ABCXYZ"
        converted = text.translate(HALFWIDTH_TO_FULLWIDTH)
        assert converted == "ＡＢＣＸＹＺ"

    def test_convert_mixed_text(self):
        """Mixed text should only convert alphanumerics."""
        text = "テキスト123ABC"
        converted = text.translate(HALFWIDTH_TO_FULLWIDTH)
        assert converted == "テキスト１２３ＡＢＣ"

    def test_no_conversion_japanese(self):
        """Japanese characters should remain unchanged."""
        text = "日本語テキスト"
        converted = text.translate(HALFWIDTH_TO_FULLWIDTH)
        assert converted == text


class TestScanFile:
    """Test suite for file scanning logic."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)

    def test_scan_file_with_violations(self, temp_dir):
        """File with halfwidth chars in Japanese context should report findings."""
        test_file = temp_dir / "test.md"
        test_file.write_text("これは3個のa文字です", encoding="utf-8")

        findings, _ = scan_file(test_file, fix=False)
        assert len(findings) == 2  # "3" and "a"
        assert findings[0].char in ["3", "a"]
        assert findings[0].line_num == 1

    def test_scan_file_no_violations(self, temp_dir):
        """File without violations should report no findings."""
        test_file = temp_dir / "test.md"
        test_file.write_text("これは全角３個のａ文字です", encoding="utf-8")

        findings, _ = scan_file(test_file, fix=False)
        assert len(findings) == 0

    def test_scan_file_with_exclusions(self, temp_dir):
        """Halfwidth chars in excluded regions should not be reported."""
        test_file = temp_dir / "test.md"
        content = """
日本語テキスト

```python
code = "abc123"
```

続きの日本語
"""
        test_file.write_text(content, encoding="utf-8")

        findings, _ = scan_file(test_file, fix=False)
        # "abc123" should be excluded (inside code block)
        assert len(findings) == 0

    def test_scan_file_with_fix(self, temp_dir):
        """Fix mode should convert halfwidth to fullwidth."""
        test_file = temp_dir / "test.md"
        test_file.write_text("これは3個のa文字です", encoding="utf-8")

        findings, fixed_content = scan_file(test_file, fix=True)
        assert len(findings) == 2
        assert fixed_content is not None
        assert "３" in fixed_content
        assert "ａ" in fixed_content
        assert "3" not in fixed_content
        assert "a" not in fixed_content

    def test_scan_file_code_block_preserved(self, temp_dir):
        """Fix mode should preserve code blocks unchanged."""
        test_file = temp_dir / "test.md"
        content = "これは`code123`インラインコードです"
        test_file.write_text(content, encoding="utf-8")

        findings, fixed_content = scan_file(test_file, fix=False)
        # code123 should be excluded, no findings
        assert len(findings) == 0
        assert "code123" in test_file.read_text(encoding="utf-8")

    def test_scan_file_encoding_error(self, temp_dir):
        """Non-UTF8 files should be skipped with error."""
        test_file = temp_dir / "test.txt"
        # Write binary content that's invalid UTF-8
        test_file.write_bytes(b"\xff\xfe invalid utf8")

        findings, _ = scan_file(test_file, fix=False)
        # Should return empty findings on encoding error
        assert len(findings) == 0

    def test_scan_file_url_preserved(self, temp_dir):
        """URLs should be excluded from detection."""
        test_file = temp_dir / "test.md"
        test_file.write_text("参照: https://example.com/abc123", encoding="utf-8")

        findings, _ = scan_file(test_file, fix=False)
        # URL content should be excluded
        assert len(findings) == 0

    def test_scan_file_path_preserved(self, temp_dir):
        """File paths should be excluded from detection."""
        test_file = temp_dir / "test.md"
        test_file.write_text("ファイル C:\\path\\file123.txt を開く", encoding="utf-8")

        findings, _ = scan_file(test_file, fix=False)
        # Path content should be excluded
        assert len(findings) == 0


class TestGetStagedFiles:
    """Test suite for git staged file detection."""

    def test_get_staged_files_empty(self, monkeypatch):
        """No staged files should return empty list."""
        # Mock subprocess to return empty output
        import subprocess

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = ""

            return Result()

        monkeypatch.setattr(subprocess, "run", mock_run)
        files = get_staged_files(["*.md"])
        assert len(files) == 0

    def test_get_staged_files_with_patterns(self, monkeypatch):
        """Staged files matching patterns should be returned."""
        import subprocess

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = "docs/test.md\nREADME.md\nsrc/code.py\n"

            return Result()

        monkeypatch.setattr(subprocess, "run", mock_run)
        files = get_staged_files(["*.md", "docs/**/*.md"])
        # Should match .md files
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)


class TestFindingDataclass:
    """Test suite for Finding dataclass."""

    def test_finding_creation(self):
        """Finding should be created with correct attributes."""
        finding = Finding(
            file=Path("test.md"), line_num=10, col=5, char="a",
            context="これはa文字", suggestion="ａ"
        )
        assert finding.file == Path("test.md")
        assert finding.line_num == 10
        assert finding.col == 5
        assert finding.char == "a"
        assert finding.context == "これはa文字"
        assert finding.suggestion == "ａ"

    def test_finding_str_representation(self):
        """Finding should have readable string representation."""
        finding = Finding(
            file=Path("test.md"), line_num=10, col=5, char="a",
            context="これはa文字", suggestion="ａ"
        )
        # Should contain key information
        assert "test.md" in str(finding)


class TestMainFunction:
    """Test suite for main() CLI entry point."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)

    def test_main_no_files(self, temp_dir, monkeypatch, capsys):
        """Main should exit 0 when no files to check."""
        from scripts.hooks.halfwidth_checker import main

        monkeypatch.chdir(temp_dir)
        exit_code = main(["--patterns", "*.md"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "No files to check" in captured.out

    def test_main_with_findings_warn_mode(self, temp_dir, monkeypatch, capsys):
        """Main should exit 0 in warn mode even with findings."""
        from scripts.hooks.halfwidth_checker import main

        test_file = temp_dir / "test.md"
        test_file.write_text("これは3個のa文字です", encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        exit_code = main(["test.md"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Found 2 halfwidth character(s)" in captured.out

    def test_main_with_findings_fail_mode(self, temp_dir, monkeypatch, capsys):
        """Main should exit 1 in fail mode with findings."""
        from scripts.hooks.halfwidth_checker import main

        test_file = temp_dir / "test.md"
        test_file.write_text("これは3個です", encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        exit_code = main(["--fail", "test.md"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Found 1 halfwidth character(s)" in captured.out

    def test_main_with_fix(self, temp_dir, monkeypatch, capsys):
        """Main should fix files when --fix specified."""
        from scripts.hooks.halfwidth_checker import main

        test_file = temp_dir / "test.md"
        test_file.write_text("これは3個です", encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        exit_code = main(["--fix", "test.md"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Auto-fixed 1 file(s)" in captured.out

        # Verify fix was applied
        fixed_content = test_file.read_text(encoding="utf-8")
        assert "３" in fixed_content
        assert "3" not in fixed_content

    def test_main_ok_no_violations(self, temp_dir, monkeypatch, capsys):
        """Main should report OK when no violations."""
        from scripts.hooks.halfwidth_checker import main

        test_file = temp_dir / "test.md"
        test_file.write_text("これは全角３個です", encoding="utf-8")

        monkeypatch.chdir(temp_dir)
        exit_code = main(["test.md"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "OK (no halfwidth in Japanese context)" in captured.out

    def test_main_staged_no_files(self, temp_dir, monkeypatch, capsys):
        """Main should exit 0 when no staged files match."""
        from scripts.hooks.halfwidth_checker import main
        import subprocess

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = ""
            return Result()

        monkeypatch.setattr(subprocess, "run", mock_run)
        monkeypatch.chdir(temp_dir)

        exit_code = main(["--staged", "--patterns", "*.md"])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "No staged files matching patterns" in captured.out


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)

    def test_end_to_end_detection_and_fix(self, temp_dir):
        """Complete workflow: detect violations and apply fixes."""
        test_file = temp_dir / "document.md"
        original_content = """これは3個のa文字です。

```python
# Code should be preserved
version = "1.2.3"
```

参照: https://example.com/api/v2

ファイルパス: /usr/local/bin/python3

バージョン4.5.6をリリース
"""
        test_file.write_text(original_content, encoding="utf-8")

        # Phase 1: Detection
        findings, _ = scan_file(test_file, fix=False)
        # Should detect "3" and "a" in Japanese context
        # Code block, URL, path, version should be excluded
        assert len(findings) == 2

        # Phase 2: Fix
        findings, fixed_content = scan_file(test_file, fix=True)
        assert fixed_content is not None

        # Verify fixes applied
        assert "３個のａ文字" in fixed_content

        # Verify exclusions preserved
        assert 'version = "1.2.3"' in fixed_content
        assert "https://example.com/api/v2" in fixed_content
        assert "/usr/local/bin/python3" in fixed_content

    def test_multiple_files_batch_processing(self, temp_dir):
        """Multiple files should be processed correctly."""
        files = {
            "file1.md": "日本語1個",
            "file2.md": "テキストa文字",
            "file3.md": "全角３のみ",
        }

        for name, content in files.items():
            (temp_dir / name).write_text(content, encoding="utf-8")

        results = {}
        for path in temp_dir.glob("*.md"):
            findings, _ = scan_file(path, fix=False)
            results[path.name] = len(findings)

        # file1: 1 violation ("1")
        # file2: 1 violation ("a")
        # file3: 0 violations (already fullwidth)
        assert results["file1.md"] == 1
        assert results["file2.md"] == 1
        assert results["file3.md"] == 0
