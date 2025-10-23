"""Universal Prompt Request

汎用プロンプト要求のデータ構造定義
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UniversalPromptRequest:
    """汎用プロンプト要求"""

    episode_number: int
    project_root: Path
    prompt_type: str = "standard"
    context_data: dict[str, Any] = field(default_factory=dict)
    target_stage: str | None = None
    save_prompt: bool = True
    debug_mode: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
