import re
from tests.helpers import create_test_progressive_check_manager
import shutil
from pathlib import Path

import pytest

from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    source = Path(__file__).with_name("sample_project")
    destination = tmp_path / "project"
    shutil.copytree(source, destination)
    return destination


def test_generate_enhanced_instruction_matches_golden(sample_project: Path) -> None:
    manager = create_test_progressive_check_manager(project_root=str(sample_project), episode_number=1)
    manager.prompt_templates_dir = sample_project / "templates"
    current_task = manager._get_task_by_id(manager.tasks_config["tasks"], 1)
    assert current_task is not None
    instruction = manager._generate_enhanced_llm_instruction(current_task, [current_task])

    golden_path = Path(__file__).with_name("golden_step01_instruction.txt")
    expected = golden_path.read_text(encoding="utf-8")

    # タイムスタンプ部分（EP001_YYYYMMDDHHMMSS）を正規化して比較
    normalized_instruction = re.sub(r'EP001_\d{12}', 'EP001_NORMALIZED', instruction)
    normalized_expected = re.sub(r'EP001_\d{12}', 'EP001_NORMALIZED', expected)

    assert normalized_instruction == normalized_expected
