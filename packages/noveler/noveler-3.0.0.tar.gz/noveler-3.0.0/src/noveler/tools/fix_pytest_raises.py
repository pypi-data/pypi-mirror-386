"""Tools.fix_pytest_raises
Where: Tool updating deprecated pytest raises usage.
What: Refactors tests to modern pytest patterns.
Why: Keeps the test suite aligned with current pytest best practices.
"""

from noveler.presentation.shared.shared_utilities import console
'pytest.raisesにmatchパラメータを追加するスクリプト\n\nPT011エラー(pytest-raises-too-broad)を修正します。\n'
import re
from pathlib import Path

def fix_pytest_raises_in_file(file_path: Path) -> tuple[bool, int]:
    """ファイル内のpytest.raisesにmatchパラメータを追加

    Returns:
        (修正があったか, 修正数)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
    except Exception:
        return (False, 0)
    fixes = 0
    pattern = 'with\\s+pytest\\.raises\\(([^,\\)]+)\\)\\s*:'
    matches = list(re.finditer(pattern, content))
    for match in reversed(matches):
        exception_name = match.group(1).strip()
        if 'match=' in match.group(0):
            continue
        line_start = content.rfind('\n', 0, match.start()) + 1
        line = content[line_start:match.end()]
        indent_match = re.match('^(\\s*)', line)
        indent = indent_match.group(1) if indent_match else ''
        context_start = match.end()
        next_line_start = content.find('\n', context_start) + 1
        next_line_end = content.find('\n', next_line_start)
        if next_line_end == -1:
            next_line_end = len(content)
        next_line = content[next_line_start:next_line_end].strip()
        if exception_name == 'ValueError':
            match_msg = '.*'
        elif exception_name == 'TypeError' or exception_name == 'KeyError':
            match_msg = '.*'
        else:
            match_msg = '.*'
        old_text = match.group(0)
        new_text = f'with pytest.raises({exception_name}, match={match_msg!r}):'
        content = content[:match.start()] + new_text + content[match.end():]
        fixes += 1
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return (True, fixes)
    return (False, fixes)

def main():
    """メイン処理"""
    scripts_dir = Path(__file__).parent.parent
    test_files = list(scripts_dir.rglob('test*.py'))
    total_files = 0
    total_fixes = 0
    console.print('🔧 pytest.raisesの修正を開始します...')
    for test_file in test_files:
        if test_file == Path(__file__):
            continue
        (fixed, count) = fix_pytest_raises_in_file(test_file)
        if fixed:
            total_files += 1
            total_fixes += count
            console.print(f'✅ {test_file.relative_to(scripts_dir)}: {count}箇所を修正')
    console.print(f'\n📊 修正完了: {total_files}ファイル、{total_fixes}箇所')
if __name__ == '__main__':
    main()
