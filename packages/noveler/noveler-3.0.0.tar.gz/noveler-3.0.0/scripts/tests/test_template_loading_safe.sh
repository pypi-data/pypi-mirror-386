#!/bin/bash
# test_template_loading_safe.sh

# 環境変数で副作用抑制
export NOVELER_ENV=ci
export NOVELER_DRY_RUN=1

echo "Testing template loading after migration..."

# 1. ProgressiveTaskManager（出力検証のみ）
echo "Testing ProgressiveTaskManager..."
python3 -c "
import os
os.environ['NOVELER_ENV'] = 'ci'
from pathlib import Path
try:
    from noveler.domain.services.progressive_task_manager import ProgressiveTaskManager
    mgr = ProgressiveTaskManager(Path('.'), 1)
    template = mgr._load_prompt_template(0)
    print('OK' if template else 'FAIL')
except Exception as e:
    print(f'ERROR: {e}')
" | grep -q "OK" && echo "✅ ProgressiveTaskManager: OK" || echo "❌ ProgressiveTaskManager: FAIL"

# 2. ProgressiveCheckManager
echo "Testing ProgressiveCheckManager..."
python3 -c "
import os
os.environ['NOVELER_ENV'] = 'ci'
from pathlib import Path
try:
    from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager
    mgr = ProgressiveCheckManager(Path('.'), 1)
    template = mgr._load_prompt_template(1)
    print('OK' if template else 'FAIL')
except Exception as e:
    print(f'ERROR: {e}')
" | grep -q "OK" && echo "✅ ProgressiveCheckManager: OK" || echo "❌ ProgressiveCheckManager: FAIL"

# 3. ProgressiveWriteManager
echo "Testing ProgressiveWriteManager..."
python3 -c "
import os
os.environ['NOVELER_ENV'] = 'ci'
from pathlib import Path
try:
    from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager
    mgr = ProgressiveWriteManager(Path('.'), 1)
    template = mgr._load_prompt_template(0)
    print('OK' if template else 'FAIL')
except Exception as e:
    print(f'ERROR: {e}')
" | grep -q "OK" && echo "✅ ProgressiveWriteManager: OK" || echo "❌ ProgressiveWriteManager: FAIL"

# 4. YamlClaudeQualityPromptRepository
echo "Testing YamlClaudeQualityPromptRepository..."
python3 -c "
import os
os.environ['NOVELER_ENV'] = 'ci'
from pathlib import Path
try:
    from noveler.infrastructure.repositories.yaml_claude_quality_prompt_repository import YamlClaudeQualityPromptRepository
    repo = YamlClaudeQualityPromptRepository(Path('.'))
    mapping = repo._get_template_mapping()
    print('OK' if len(mapping) > 0 else 'FAIL')
except Exception as e:
    print(f'ERROR: {e}')
" | grep -q "OK" && echo "✅ YamlClaudeQualityPromptRepository: OK" || echo "❌ YamlClaudeQualityPromptRepository: FAIL"

echo "Template loading tests completed!"
