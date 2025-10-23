# File: tests/unit/domain/test_domain_dependency_guards.py
# Purpose: Guard the domain layer against forbidden dependencies (rich/presentation)
# Context: Runs in pytest session scope with lightweight, cache-aware scanning

"""Domain dependency guard tests.

Verifies that domain modules avoid importing UI-centric helpers (rich console,
presentation shared utilities).  Designed to be xdist-friendly by caching scan
results and only parsing modules that contain candidate import strings.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

import pytest


DOMAIN_ROOT = Path("src/noveler/domain")
_CACHE_KEY_META = "domain_dependency_scan/meta_v1"
_CACHE_KEY_RESULTS = "domain_dependency_scan/results_v1"
_CANDIDATE_PATTERN = re.compile(
    r"\b(?:from|import)\s+(rich|noveler\.presentation\.shared\.shared_utilities)"
)


@pytest.fixture(scope="session")
def _domain_dependency_scan(request: pytest.FixtureRequest) -> dict[str, tuple[str, ...]]:
    """Collect domain-layer import usage once per session with caching.

    This fixture keeps only offending module paths (strings) so that multiple
    xdist workers do not retain full AST objects in memory.  Results are cached
    via pytest's config cache and invalidated whenever the domain module set
    changes (based on file path, mtime, and size hash).
    """

    module_paths = sorted(_iter_python_files(DOMAIN_ROOT))
    meta_signature = _compute_meta_signature(module_paths)
    cache = request.config.cache

    cached_meta = cache.get(_CACHE_KEY_META, None)
    if cached_meta == meta_signature:
        cached_results = cache.get(_CACHE_KEY_RESULTS, None)
        if cached_results:
            decoded = {key: tuple(value) for key, value in cached_results.items()}
            return decoded

    scan_results = _scan_domain_dependencies(module_paths)
    cache.set(_CACHE_KEY_META, meta_signature)
    cache.set(_CACHE_KEY_RESULTS, {k: list(v) for k, v in scan_results.items()})
    return scan_results


def _compute_meta_signature(module_paths: Iterable[Path]) -> str:
    digest = hashlib.sha1()
    for path in module_paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        payload = json.dumps(
            {
                "path": str(path),
                "mtime": int(stat.st_mtime),
                "size": stat.st_size,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        digest.update(payload)
    return digest.hexdigest()


def _scan_domain_dependencies(module_paths: Iterable[Path]) -> dict[str, tuple[str, ...]]:
    rich_offenders: list[str] = []
    presentation_offenders: list[str] = []

    for module_path in module_paths:
        try:
            source = module_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if not _CANDIDATE_PATTERN.search(source):
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        has_rich = False
        has_presentation = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root == "rich":
                        has_rich = True
                    if alias.name == "noveler.presentation.shared.shared_utilities":
                        has_presentation = True
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root == "rich":
                    has_rich = True
                if node.module == "noveler.presentation.shared.shared_utilities":
                    has_presentation = True

            if has_rich and has_presentation:
                break

        rel_path = str(module_path)
        if has_rich:
            rich_offenders.append(rel_path)
        if has_presentation and module_path.name != "domain_console.py":
            presentation_offenders.append(rel_path)

    return {
        "rich": tuple(rich_offenders),
        "presentation": tuple(presentation_offenders),
    }


def _iter_python_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.py") if path.is_file()]


def test_domain_avoids_rich_imports(_domain_dependency_scan: dict[str, tuple[str, ...]]) -> None:
    assert list(_domain_dependency_scan["rich"]) == []


def test_domain_avoids_presentation_shared_utilities(
    _domain_dependency_scan: dict[str, tuple[str, ...]]
) -> None:
    assert list(_domain_dependency_scan["presentation"]) == []

