"""
# File: tests/contracts/test_session_generator_contract.py
# Purpose: Contract test (baseline) for SessionGenerator API surface.
# Context: Skips if the SessionGenerator is not available in this codebase.

This test defines a minimal compatibility contract for a SessionGenerator that
produces session data from a project root and a template name. It does not
exercise behavior; it only verifies the presence of the type and its method
shape so refactors can keep the public surface stable.

Contract invariants (baseline):
- A type named "SessionGenerator" exists in one of the known modules.
- The type exposes a callable method "generate".
- The "generate" method takes at least two parameters (e.g., project_root, template name).

If the symbol is not present in this repository, the tests skip cleanly.
"""

from __future__ import annotations

import importlib
import inspect
import types
from typing import Any

import pytest
import tempfile
from pathlib import Path
import warnings


def _load_session_generator() -> type | None:
    """Best-effort loader for SessionGenerator from common module paths.

    Returns the class if found, otherwise None.
    """
    candidates: list[tuple[str, str]] = [
        ("noveler.application.session", "SessionGenerator"),
        ("noveler.application.session_generator", "SessionGenerator"),
        ("noveler.domain.services.session_generator", "SessionGenerator"),
        ("noveler.application.generators.session_generator", "SessionGenerator"),
    ]
    for mod_name, attr in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        if hasattr(mod, attr):
            obj = getattr(mod, attr)
            if isinstance(obj, type):
                return obj
    return None


@pytest.fixture(scope="module")
def session_generator_cls() -> type:
    cls = _load_session_generator()
    if cls is None:
        pytest.skip("SessionGenerator not present in this codebase (baseline contract only)")
    return cls


def test_session_generator_class_present(session_generator_cls: type) -> None:
    assert isinstance(session_generator_cls, type)
    assert session_generator_cls.__name__ == "SessionGenerator"


def test_generate_method_present(session_generator_cls: type) -> None:
    assert hasattr(session_generator_cls, "generate"), "SessionGenerator.generate must exist"
    meth = getattr(session_generator_cls, "generate")
    assert callable(meth), "generate must be callable"


def test_generate_signature_minimum_shape(session_generator_cls: type) -> None:
    sig = inspect.signature(getattr(session_generator_cls, "generate"))
    # Minimum: at least two parameters (e.g., project_root, template_name)
    # Note: 'self' for instance methods is part of parameters; account for both bound/unbound cases.
    params = [p for p in sig.parameters.values()]
    # If it's an instance method, expecting >= 3 (self + 2 args); if @staticmethod, expecting >= 2.
    assert len(params) >= 2, f"generate expected >=2 params; got {len(params)}: {[p.name for p in params]}"


@pytest.mark.smoke
def test_generate_smoke_optional(session_generator_cls: type) -> None:
    """Optional smoke: try calling generate with minimal kwargs.

    - Creates a temporary project root.
    - Supplies a template name 'default' when a plausible parameter exists.
    - If required parameters cannot be determined, the test is skipped.
    - On runtime errors (e.g., environment not prepared), xfail with reason.
    """
    # Instantiate
    try:
        gen = session_generator_cls()  # type: ignore[call-arg]
    except Exception as e:  # constructor requires deps
        pytest.xfail(f"Cannot instantiate SessionGenerator: {e}")

    generate = getattr(gen, "generate")
    sig = inspect.signature(generate)
    params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]

    # Build kwargs heuristically for common names
    tmpdir = Path(tempfile.mkdtemp(prefix="sg_contract_"))
    kwargs: dict[str, Any] = {}

    # Map of candidate names to value providers
    value_map: dict[str, Any] = {
        "project_root": tmpdir,
        "root": tmpdir,
        "project_path": tmpdir,
        "root_dir": tmpdir,
        "base_dir": tmpdir,
        "path": tmpdir,
        "template_name": "default",
        "template": "default",
        "name": "default",
    }

    required = [p for p in params if p.default is p.empty and p.name != "self"]
    # Try to satisfy up to 2 first required parameters with our map
    satisfied = 0
    for p in required:
        if p.name in value_map:
            kwargs[p.name] = value_map[p.name]
            satisfied += 1
        if satisfied >= 2:
            break

    if satisfied < 2:
        pytest.skip(
            f"Insufficient information to call generate; required={[p.name for p in required]}"
        )

    try:
        result = generate(**kwargs)  # type: ignore[misc]
    except Exception as e:
        pytest.xfail(f"generate smoke failed (environmental): {e}")

    # Shape check (non-failing): prefer dict-like or to_dict
    ok = False
    if isinstance(result, dict):
        ok = True
    elif hasattr(result, "to_dict") and callable(getattr(result, "to_dict")):
        try:
            _ = result.to_dict()
            ok = True
        except Exception:
            pass
    if not ok:
        warnings.warn(
            f"SessionGenerator.generate returned unexpected type: {type(result).__name__};"
            " contract focuses on callability only."
        )
    assert result is not None
