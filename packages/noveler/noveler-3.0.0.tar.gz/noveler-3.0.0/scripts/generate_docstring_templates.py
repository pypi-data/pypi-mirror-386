#!/usr/bin/env python3
# File: scripts/generate_docstring_templates.py
# Purpose: Generate compliant docstring templates for Python modules/classes/functions.
# Context: Supports mass-fixing docstring compliance issues identified by comment_header_audit.py.

"""
Automated docstring template generator for AGENTS.md compliance.

Purpose:
    Generate standardized docstring templates that include all required sections:
    - Purpose
    - Args (if applicable)
    - Returns (if applicable)
    - Raises (if applicable)
    - Side Effects

Args:
    file_path: Path to Python file to analyze
    --fix: Apply generated templates directly to file (default: dry-run)

Returns:
    Exit code 0 on success, 1 on failure

Side Effects:
    - Reads Python files via AST parsing
    - Optionally modifies files in-place when --fix is specified
    - Prints generated templates to stdout
"""

import ast
import sys
from pathlib import Path
from typing import List, Optional


def find_project_root(start_path: Path) -> Path:
    """Find project root by looking for .git directory.

    Purpose:
        Locate the project root directory for reliable path resolution
        from any working directory.

    Args:
        start_path: Path to start searching from (typically __file__).

    Returns:
        Path to project root (contains .git directory).
        Falls back to Path.cwd() if .git not found.

    Side Effects:
        None - read-only filesystem traversal.
    """
    current = start_path.resolve()
    while current.parent != current:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback if .git directory not found
    return Path.cwd()


# Global project root for path resolution
PROJECT_ROOT = find_project_root(Path(__file__).parent.parent)


def generate_module_header(file_path: Path) -> str:
    """
    Generate compliant module header comment.

    Purpose:
        Create the required '# File: ...' header with Purpose and Context sections.

    Args:
        file_path: Path to the module file

    Returns:
        Multi-line header comment string

    Side Effects:
        None (pure function)
    """
    rel_path = file_path.relative_to(PROJECT_ROOT)

    return f"""# File: {rel_path}
# Purpose: [TODO: Describe module's responsibility and why it exists]
# Context: [TODO: Note key dependencies, domain constraints, or consumers]
"""

def generate_function_docstring(node: ast.FunctionDef) -> str:
    """
    Generate compliant function/method docstring template.

    Purpose:
        Create docstring with all required sections based on function signature.

    Args:
        node: AST FunctionDef node to analyze

    Returns:
        Multi-line docstring template string

    Side Effects:
        None (pure function)
    """
    # Analyze function signature
    has_args = bool([arg for arg in node.args.args if arg.arg not in {"self", "cls"}])
    has_returns = any(isinstance(child, ast.Return) and child.value is not None
                     for child in ast.walk(node))
    has_raises = any(isinstance(child, ast.Raise) for child in ast.walk(node))

    lines = [
        '"""',
        '[TODO: Brief description of function purpose]',
        '',
        'Purpose:',
        '    [TODO: What this function is responsible for]',
        '',
    ]

    if has_args:
        lines.extend([
            'Args:',
            '    [TODO: Document each parameter]',
            '',
        ])

    if has_returns:
        lines.extend([
            'Returns:',
            '    [TODO: Describe return value and meaning]',
            '',
        ])

    if has_raises:
        lines.extend([
            'Raises:',
            '    [TODO: Document intentionally raised exceptions]',
            '',
        ])

    lines.extend([
        'Side Effects:',
        '    [TODO: Document I/O, state changes, or emitted events, or write "None"]',
        '"""',
    ])

    return '\n    '.join(lines)

def generate_class_docstring(node: ast.ClassDef) -> str:
    """
    Generate compliant class docstring template.

    Purpose:
        Create class docstring with required sections.

    Args:
        node: AST ClassDef node to analyze

    Returns:
        Multi-line docstring template string

    Side Effects:
        None (pure function)
    """
    lines = [
        '"""',
        '[TODO: Brief description of class purpose]',
        '',
        'Purpose:',
        '    [TODO: What this class is responsible for]',
        '',
        'Side Effects:',
        '    [TODO: Document state management or external interactions, or write "None"]',
        '"""',
    ]

    return '\n    '.join(lines)

def analyze_file(file_path: Path) -> None:
    """
    Analyze Python file and generate docstring templates for violations.

    Purpose:
        Parse file via AST and identify missing/incomplete docstrings,
        then print compliant templates to stdout.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        None (prints to stdout)

    Side Effects:
        - Reads file from disk
        - Prints analysis results to stdout
    """
    print(f"\n{'=' * 80}")
    print(f"File: {file_path}")
    print('=' * 80)

    text = file_path.read_text(encoding='utf-8')

    # Check header comment
    if not text.startswith('# File:') and not text.startswith('#!/usr/bin/env'):
        print("\n[MISSING] Module header comment:")
        print(generate_module_header(file_path))

    # Parse AST
    try:
        tree = ast.parse(text, filename=str(file_path))
    except SyntaxError as e:
        print(f"\n[ERROR] Syntax error prevents analysis: {e}")
        return

    # Check module docstring
    module_doc = ast.get_docstring(tree)
    if not module_doc or 'Purpose:' not in module_doc:
        print("\n[MISSING/INCOMPLETE] Module docstring:")
        print('"""')
        print('[TODO: Module description]')
        print('')
        print('Purpose:')
        print('    [TODO: Describe module responsibility]')
        print('')
        print('Side Effects:')
        print('    [TODO: Document side effects or write "None"]')
        print('"""')

    # Check classes and functions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if not doc or 'Purpose:' not in doc:
                print(f"\n[MISSING/INCOMPLETE] Class '{node.name}' docstring (line {node.lineno}):")
                print(generate_class_docstring(node))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if not doc or 'Purpose:' not in doc:
                print(f"\n[MISSING/INCOMPLETE] Function '{node.name}' docstring (line {node.lineno}):")
                print(generate_function_docstring(node))

def main(args: Optional[List[str]] = None) -> int:
    """
    Entry point for docstring template generator.

    Purpose:
        Parse command-line arguments and process target files.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 = success, 1 = error)

    Side Effects:
        - Reads files from disk
        - Prints to stdout
        - Modifies files when --fix is specified (not yet implemented)
    """
    args = args or sys.argv[1:]

    if not args:
        print("Usage: python generate_docstring_templates.py <file.py> [<file2.py> ...]")
        print("       python generate_docstring_templates.py --top-violations N")
        return 1

    if args[0] == '--top-violations':
        # TODO: Integrate with audit script to process top N violators
        print("[ERROR] --top-violations not yet implemented")
        return 1

    # Process specified files
    for arg in args:
        file_path = Path(arg)
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            continue

        if not file_path.suffix == '.py':
            print(f"[SKIP] Not a Python file: {file_path}")
            continue

        analyze_file(file_path)

    return 0

if __name__ == '__main__':
    sys.exit(main())
