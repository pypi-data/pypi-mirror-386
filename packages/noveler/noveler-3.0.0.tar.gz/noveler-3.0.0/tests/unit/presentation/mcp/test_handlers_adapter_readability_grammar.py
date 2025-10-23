"""Tests.unit.presentation.mcp.test_handlers_adapter_readability_grammar
Where: Automated test module.
What: Thin adapter tests for readability/grammar handlers.
Why: Guards behaviour as we extract handlers from main.py.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp.adapters.handlers import (
    check_readability,
    check_grammar,
)


@pytest.mark.asyncio
async def test_check_readability_adapter_runs() -> None:
    res = await check_readability({"episode_number": 1})
    assert isinstance(res, dict)
    assert "success" in res and "issues" in res


@pytest.mark.asyncio
async def test_check_grammar_adapter_runs() -> None:
    res = await check_grammar({"episode_number": 1})
    assert isinstance(res, dict)
    assert "success" in res and "issues" in res



import pytest
from noveler.presentation.mcp.adapters.handlers import check_readability as _check

@pytest.mark.asyncio
async def test_check_readability_exclude_dialogue_lines():
    # 長文だが会話で始まり複数行に継続する場合、除外フラグがあれば文長指摘が抑制されること
    content = (
        "\n".join([
            "「これは非常に長く、続いていく会話のサンプルです。実際には80字を超えるようなテキストが入ると想定します。この行は開き括弧のみで開始します",
            "そして次の行でも会話が継続します」",
            "地の文 これは短い。",
        ])
    )
    res = await _check({
        "episode_number": 1,
        "content": content,
        "exclude_dialogue_lines": True,
        "check_aspects": ["sentence_length"],
    })
    assert res.get("success", False) is True
    # issues が空、もしくは会話行に対する long_sentence が含まれないことを確認
    issues = res.get("issues", [])
    assert all(i.get("type") != "long_sentence" for i in issues)
