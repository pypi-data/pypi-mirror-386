"""Universal Prompt Response

汎用プロンプト応答のデータ構造定義
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UniversalPromptResponse:
    """汎用プロンプト応答"""

    success: bool
    generated_prompt: str = ""
    saved_file_path: Path | None = None
    execution_time_ms: float = 0.0
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
