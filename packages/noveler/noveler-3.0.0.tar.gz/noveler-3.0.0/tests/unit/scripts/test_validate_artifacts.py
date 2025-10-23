# File: tests/unit/scripts/test_validate_artifacts.py
# Purpose: Verify scripts/validate_artifacts.py evaluates acceptance criteria fixtures.
# Context: Guards regressions in artifact validation logic used by CI.

from __future__ import annotations

from pathlib import Path
import textwrap

from scripts import validate_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]


def _entry(name: str, template: str, artifact: str) -> validate_artifacts.EvaluationEntry:
    return validate_artifacts.EvaluationEntry(
        name=name,
        template_path=REPO_ROOT / template,
        artifact_path=REPO_ROOT / artifact,
        variables={},
        use_example=False,
    )


def test_validate_step06_logic_verification_fixture() -> None:
    entry = _entry(
        "step06_logic_verification",
        "templates/writing/write_step06_logic_verification.yaml",
        "docs/examples/acceptance/write_step06_logic_verification.yaml",
    )
    result = validate_artifacts.evaluate_acceptance(entry)
    assert result.success
    assert all(item["status"] != "fail" for item in result.by_task)
    assert all(item["status"] != "fail" for item in result.checklist)


def test_validate_step16_quality_check_fixture() -> None:
    entry = _entry(
        "step16_quality_check",
        "templates/writing/write_step16_quality_check.yaml",
        "docs/examples/acceptance/write_step16_quality_check.yaml",
    )
    result = validate_artifacts.evaluate_acceptance(entry)
    assert result.success
    # Metrics should pass the defined thresholds
    failing_metrics = [metric for metric in result.metrics if metric["status"] == "fail"]
    assert not failing_metrics
    verdict_item = next(item for item in result.checklist if "verdict" in item["item"])
    assert verdict_item["status"] == "pass"


def test_extract_markdown_meta_block() -> None:
    markdown = textwrap.dedent(
        """
        <!--
        meta:
          version: 1
          by_task:
            integrate.section_balance:
              status: pass
              notes:
                - ratio_ok
        -->
        # 第001話

        本文...
        """
    )

    meta = validate_artifacts.extract_markdown_meta(markdown)
    assert meta["meta"]["version"] == 1
    status = meta["meta"]["by_task"]["integrate.section_balance"]["status"]
    assert status == "pass"


def test_load_artifact_returns_meta_for_markdown(tmp_path: Path) -> None:
    artifact = tmp_path / "draft.md"
    artifact.write_text(
        textwrap.dedent(
            """
            <!--
            meta:
              by_task:
                style.hook:
                  status: pass
                  notes: []
            -->
            # 第001話
            本文...
            """
        ),
        encoding="utf-8",
    )

    template = {"artifacts": {"format": "md"}}
    data, text, fmt = validate_artifacts.load_artifact(template, artifact, {}, False)

    assert fmt == "md"
    assert text.lstrip().startswith("<!--")
    assert data["meta"]["by_task"]["style.hook"]["status"] == "pass"
