# アーキテクチャ違反詳細レポート

**生成日時:** 2025-08-13
**対象:** CODEMAP.yaml/CODEMAP_dependencies.yaml 検証結果

## 🔴 重大な違反: Application → Presentation 依存

### 違反の概要
Application層（ユースケース）がPresentation層（共通ユーティリティ）に依存している違反が検出されました。
これはDDDのクリーンアーキテクチャ原則に反します。

### 違反箇所一覧

#### Console使用違反
```python
# ❌ 違反: Application層でPresentation層のconsoleを直接使用
from noveler.presentation.shared.shared_utilities import console
```

**影響ファイル:**
1. `scripts.application.use_cases.claude_quality_check_use_case` (line 217)
2. `scripts.application.use_cases.enhanced_integrated_writing_use_case` (line 329)
3. `scripts.application.use_cases.five_stage_writing_use_case` (line 405)

#### PathService使用違反
```python
# ❌ 違反: Application層でPresentation層のPathServiceを直接使用
from noveler.presentation.shared.shared_utilities import get_common_path_service
```

**影響ファイル:**
1. `scripts.application.use_cases.a31_complete_check_use_case` (line 63)
2. `scripts.application.use_cases.auto_chaining_plot_generation_use_case` (line 115)
3. `scripts.application.use_cases.claude_quality_check_use_case` (line 218)
4. `scripts.application.use_cases.enhanced_integrated_writing_use_case` (line 330)
5. `scripts.application.use_cases.episode_prompt_save_use_case` (line 349)
6. `scripts.application.use_cases.five_stage_writing_use_case` (line 415)

## 🔍 根本原因分析

### 1. 設計上の問題
- **共通コンポーネントの配置ミス**: ConsoleやPathServiceがPresentation層に配置
- **依存性注入の不足**: ユースケースが直接インフラ層のサービスに依存

### 2. アーキテクチャ原則違反
```
❌ 現状: Application → Presentation (違反)
✅ 正解: Application → Domain ← Infrastructure
```

## 🛠️ 修正方針

### A. 即時修正（最小侵襲）
1. **依存性注入パターン適用**
   ```python
   # Before (違反)
   from noveler.presentation.shared.shared_utilities import console

   # After (修正)
   class SomeUseCase:
       def __init__(self, console_service: IConsoleService):
           self.console = console_service
   ```

2. **インターフェース定義**
   ```python
   # scripts/domain/interfaces/i_console_service.py
   from abc import ABC, abstractmethod

   class IConsoleService(ABC):
       @abstractmethod
       def print(self, message: str) -> None:
           pass
   ```

### B. 構造修正（推奨）
1. **共通サービスの再配置**
   ```
   scripts/infrastructure/shared/
   ├── console_service.py      # ConsoleService実装
   ├── path_service.py         # PathService実装
   └── configuration_service.py # ConfigurationService実装
   ```

2. **Factory パターン適用**
   ```python
   # scripts/infrastructure/factories/shared_service_factory.py
   def get_console_service() -> IConsoleService:
       return ConsoleService()
   ```

## 🚨 影響度評価

### 現状リスク
- **保守性**: 高リスク（層間依存の混乱）
- **テスタビリティ**: 中リスク（モック化困難）
- **機能性**: 低リスク（現在は動作中）

### 修正優先度
1. **高優先**: Console使用違反（3件）- 出力制御への影響
2. **中優先**: PathService違反（6件）- パス管理への影響

## ✅ 検証手順

### 1. 修正前テスト
```bash
# 現在の動作確認
python -m pytest scripts/tests/ -v
# 注: 現行は `/bin/test` / `scripts/run_pytest.py` 推奨
```

### 2. 段階的修正
```bash
# 1ファイルずつ修正・テスト
python -m pytest scripts/tests/test_specific_use_case.py -v
# 注: 現行は `/bin/test` / `scripts/run_pytest.py` 推奨
```

### 3. アーキテクチャ違反再チェック
```bash
python scripts/tools/dependency_analyzer.py --detect-circular
```

## 🔧 自動修正スクリプト（提案）

```python
#!/usr/bin/env python3
"""
Application層からPresentation層への違反を自動修正
"""

import re
from pathlib import Path

def fix_console_violations():
    """Console違反の修正"""
    pattern = r"from scripts\.presentation\.cli\.shared_utilities import console"
    replacement = "# TODO: Inject console service via dependency injection"

def fix_path_service_violations():
    """PathService違反の修正"""
    pattern = r"from scripts\.presentation\.cli\.shared_utilities import get_common_path_service"
    replacement = "# TODO: Inject path service via dependency injection"
```

## 📋 次のアクション

1. **即時**: Console違反3件の修正
2. **短期**: PathService違反6件の修正
3. **中期**: 共通サービスのInfrastructure層への移行
4. **長期**: 依存性注入フレームワークの導入検討

---
**注意**: このレポートは自動生成されたアーキテクチャ分析結果です。修正前には必ず既存テストの実行を推奨します。
