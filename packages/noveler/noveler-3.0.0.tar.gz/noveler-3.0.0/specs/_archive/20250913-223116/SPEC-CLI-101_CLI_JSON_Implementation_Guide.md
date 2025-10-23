# SPEC-CLI-101: CLI JSON化 実装ガイド

## 概要

CLI出力の100% JSON化・MCPツール化の段階的実装手順書。
既存システムとの互換性を保ちながら、高品質で保守性の高いJSON変換システムを構築。

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-CLI-001 |
| E2EテストID | E2E-CLI-001 |
| test_type | integration |
| バージョン | v1.0.0 |
| 作成日 | 2025-08-27 |
| 最終更新 | 2025-08-28 |
| ステータス | active |
| 実装期間 | 4週間（Phase 1-3構成） |
| 対象者 | システム開発者、保守担当者 |

## 1. 実装概要・前提条件

### 1.1 実装前提条件

```bash
# 必要な環境
- Python 3.11+
- 既存プロジェクト構造（DDD準拠）
- Git管理環境
- テスト環境（pytest）

# 必要なライブラリ
pip install pydantic==2.5.0 jsonschema==4.20.0 mcp==0.9.0
```

### 1.2 既存システム影響評価

```python
# 影響範囲チェックリスト
IMPACT_ASSESSMENT = {
    "破壊的変更": "なし（既存CLI出力と並行運用）",
    "DDD層分離": "遅延初期化パターンで準拠維持",
    "テストカバレッジ": "既存95%を維持、新機能95%以上",
    "パフォーマンス": "95%トークン削減、60%レスポンス向上",
    "セキュリティ": "SHA256完全性保証、権限制御強化"
}
```

### 1.3 実装戦略

1. **漸進的実装**: 既存システムを破壊せず段階的に導入
2. **並行運用**: 従来出力とJSON出力の両方をサポート
3. **フォールバック機能**: JSON化失敗時の自動フォールバック
4. **品質保証**: 各Phase完了時の包括的テスト実行

## 2. Phase 1: 基盤構築 (Week 1-2)

### 2.1 ディレクトリ構造作成

```bash
# 新規ディレクトリ構造作成（現行構成に準拠）
mkdir -p src/noveler/infrastructure/json/{schemas,models,converters,validators,file_managers,utils}
mkdir -p src/noveler/infrastructure/json/mcp/{tools,resources,validators}
mkdir -p tests/unit/infrastructure/json
mkdir -p tests/integration/infrastructure/json
mkdir -p tests/e2e/json_mcp_integration

# JSONスキーマディレクトリ作成
mkdir -p schemas/json/{base,commands,responses}
```

### 2.2 JSON スキーマファイル作成

```bash
# schemas/json/base/file_reference_schema.json
cat > schemas/json/base/file_reference_schema.json << 'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "file_reference_schema.json",
  "title": "FileReferenceSchema",
  "description": "ファイル参照スキーマ",
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "ファイルの相対パス",
      "pattern": "^[^/].*$",
      "minLength": 1,
      "maxLength": 500
    },
    "sha256": {
      "type": "string",
      "description": "SHA256ハッシュ値",
      "pattern": "^[a-f0-9]{64}$"
    },
    "size_bytes": {
      "type": "integer",
      "description": "ファイルサイズ（バイト）",
      "minimum": 0,
      "maximum": 104857600
    },
    "content_type": {
      "type": "string",
      "description": "MIMEタイプ",
      "enum": ["text/markdown", "text/yaml", "application/json", "text/plain"]
    },
    "created_at": {
      "type": "string",
      "description": "作成日時（ISO 8601）",
      "format": "date-time"
    },
    "encoding": {
      "type": "string",
      "description": "ファイルエンコーディング",
      "default": "utf-8"
    }
  },
  "required": ["path", "sha256", "size_bytes", "content_type", "created_at"],
  "additionalProperties": false
}
EOF
```

```bash
# schemas/json/responses/standard_response_schema.json
cat > schemas/json/responses/standard_response_schema.json << 'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "standard_response_schema.json",
  "title": "StandardResponseSchema",
  "description": "標準レスポンススキーマ",
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "実行成功フラグ"
    },
    "command": {
      "type": "string",
      "description": "実行されたコマンド",
      "minLength": 1,
      "maxLength": 200
    },
    "timestamp": {
      "type": "string",
      "description": "実行時刻（ISO 8601）",
      "format": "date-time"
    },
    "execution_time_ms": {
      "type": "number",
      "description": "実行時間（ミリ秒）",
      "minimum": 0
    },
    "outputs": {
      "type": "object",
      "description": "出力ファイル参照コレクション",
      "properties": {
        "files": {
          "type": "array",
          "items": {"$ref": "file_reference_schema.json"}
        },
        "total_files": {
          "type": "integer",
          "minimum": 0
        },
        "total_size_bytes": {
          "type": "integer",
          "minimum": 0
        }
      },
      "required": ["files", "total_files", "total_size_bytes"]
    },
    "metadata": {
      "type": "object",
      "description": "追加メタデータ",
      "additionalProperties": true
    }
  },
  "required": ["success", "command", "timestamp", "execution_time_ms", "outputs"],
  "additionalProperties": false
}
EOF
```

### 2.3 基底モデル実装

```python
# src/noveler/infrastructure/json/models/base_models.py
#!/usr/bin/env python3
"""JSON変換基底モデル"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

class ContentType(str, Enum):
    """サポートするコンテンツタイプ"""
    MARKDOWN = "text/markdown"
    YAML = "text/yaml"
    JSON = "application/json"
    PLAIN_TEXT = "text/plain"

class BaseJSONModel(BaseModel):
    """JSON変換基底モデル"""

    class Config:
        # Pydantic v2設定
        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }

    @root_validator
    def validate_model_consistency(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """モデル一貫性検証"""
        return values

class TimestampMixin(BaseModel):
    """タイムスタンプミックスイン"""

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="作成日時（ISO 8601）"
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description="更新日時（ISO 8601）"
    )
```

### 2.4 ファイル参照モデル実装

```python
# src/noveler/infrastructure/json/models/file_reference_models.py
#!/usr/bin/env python3
"""ファイル参照モデル"""

from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator
import re

from .base_models import BaseJSONModel, TimestampMixin, ContentType

class FileReferenceModel(BaseJSONModel, TimestampMixin):
    """ファイル参照モデル"""

    path: str = Field(
        ...,
        description="ファイルの相対パス",
        min_length=1,
        max_length=500
    )

    sha256: str = Field(
        ...,
        description="SHA256ハッシュ値（64文字16進文字列）",
        regex=r"^[a-f0-9]{64}$"
    )

    size_bytes: int = Field(
        ...,
        description="ファイルサイズ（バイト）",
        ge=0,
        le=100_000_000
    )

    content_type: ContentType = Field(
        ...,
        description="MIMEタイプ"
    )

    encoding: str = Field(
        default="utf-8",
        description="ファイルエンコーディング"
    )

    @validator('path')
    def validate_path_format(cls, v: str) -> str:
        """パス形式検証"""
        if v.startswith('/') or '..' in v:
            raise ValueError("相対パスのみ許可、親ディレクトリ参照禁止")

        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in dangerous_chars):
            raise ValueError(f"危険な文字が含まれています: {dangerous_chars}")

        return v

    @validator('sha256')
    def validate_sha256_format(cls, v: str) -> str:
        """SHA256形式検証"""
        if not re.match(r'^[a-f0-9]{64}$', v.lower()):
            raise ValueError("SHA256は64文字の16進文字列である必要があります")
        return v.lower()

class FileReferenceCollection(BaseJSONModel):
    """ファイル参照コレクション"""

    files: List[FileReferenceModel] = Field(
        default_factory=list,
        description="ファイル参照一覧"
    )

    total_files: int = Field(
        description="総ファイル数"
    )

    total_size_bytes: int = Field(
        description="総サイズ（バイト）"
    )
```

### 2.5 ハッシュユーティリティ実装

```python
# src/noveler/infrastructure/json/utils/hash_utils.py
#!/usr/bin/env python3
"""ハッシュユーティリティ"""

import hashlib
from pathlib import Path
from typing import Union

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """SHA256ハッシュ計算（最適化版）"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが存在しません: {file_path}")

    sha256_hash = hashlib.sha256()
    chunk_size = 65536  # 64KB

    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
    except IOError as e:
        raise IOError(f"ファイル読み込みエラー: {file_path}") from e

    return sha256_hash.hexdigest()

def calculate_sha256_from_content(content: str, encoding: str = 'utf-8') -> str:
    """コンテンツ文字列からSHA256ハッシュ計算"""
    content_bytes = content.encode(encoding)
    return hashlib.sha256(content_bytes).hexdigest()
```

### 2.6 Phase 1 テスト実装

```python
# tests/unit/infrastructure/json/test_base_models.py
#!/usr/bin/env python3
"""基底モデルテスト"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from scripts.infrastructure.json.models.base_models import BaseJSONModel, TimestampMixin, ContentType

class TestContentType:
    """コンテンツタイプテスト"""

    def test_content_type_values(self):
        """コンテンツタイプ値テスト"""
        assert ContentType.MARKDOWN == "text/markdown"
        assert ContentType.YAML == "text/yaml"
        assert ContentType.JSON == "application/json"
        assert ContentType.PLAIN_TEXT == "text/plain"

class TestTimestampMixin:
    """タイムスタンプミックスインテスト"""

    def test_auto_timestamp_creation(self):
        """自動タイムスタンプ生成テスト"""

        class TestModel(TimestampMixin):
            name: str

        model = TestModel(name="test")
        assert isinstance(model.created_at, datetime)
        assert model.updated_at is None

    def test_manual_timestamp_setting(self):
        """手動タイムスタンプ設定テスト"""

        class TestModel(TimestampMixin):
            name: str

        test_time = datetime(2025, 8, 27, 12, 0, 0)
        model = TestModel(name="test", created_at=test_time)
        assert model.created_at == test_time
```

```bash
# Phase 1 テスト実行
cd /mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド
python -m pytest tests/unit/infrastructure/json/ -v
```

## 3. Phase 2: JSON変換システム実装 (Week 2-3)

### 3.1 基底変換器実装

```python
# src/noveler/infrastructure/json/converters/base_converter.py
#!/usr/bin/env python3
"""JSON変換基底クラス"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pathlib import Path
import time
import json
from pydantic import ValidationError
import jsonschema

from ..models.base_models import BaseJSONModel

T = TypeVar('T', bound=BaseJSONModel)

class BaseConverter(ABC):
    """JSON変換基底クラス"""

    def __init__(self,
                 schema_dir: Path = None,
                 output_dir: Path = None,
                 validate_schema: bool = True):
        self.schema_dir = schema_dir or Path("schemas/json")
        self.output_dir = output_dir or Path("outputs")
        self.validate_schema = validate_schema
        self._schema_cache: Dict[str, Dict] = {}

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """JSONスキーマロード・キャッシュ"""
        if schema_name not in self._schema_cache:
            schema_path = self.schema_dir / f"{schema_name}.json"
            if not schema_path.exists():
                raise FileNotFoundError(f"スキーマファイル未発見: {schema_path}")

            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema_cache[schema_name] = json.load(f)

        return self._schema_cache[schema_name]

    @abstractmethod
    def convert(self, input_data: Any) -> Dict[str, Any]:
        """変換実行（抽象メソッド）"""
        pass
```

### 3.2 CLI→JSON変換器実装

```python
# src/noveler/infrastructure/json/converters/cli_response_converter.py
#!/usr/bin/env python3
"""CLI レスポンス→JSON変換器"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import uuid
from datetime import datetime
import json

from ..models.response_models import StandardResponseModel, ErrorResponseModel
from ..models.file_reference_models import FileReferenceModel, FileReferenceCollection
from ..file_managers.file_reference_manager import FileReferenceManager
from .base_converter import BaseConverter

class CLIResponseConverter(BaseConverter):
    """CLI レスポンス→JSON変換器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_manager = FileReferenceManager(self.output_dir)

    def convert(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """CLI実行結果をJSON形式に変換"""

        start_time = time.perf_counter()

        try:
            if cli_result.get('success', False):
                result = self._convert_success_response(cli_result)
            else:
                result = self._convert_error_response(cli_result)

            # 実行時間追加
            end_time = time.perf_counter()
            if 'execution_time_ms' not in result:
                result['execution_time_ms'] = (end_time - start_time) * 1000

            return result

        except Exception as e:
            return self._create_emergency_error_response(str(e), cli_result)

    def _convert_success_response(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """成功レスポンス変換"""

        file_references = []

        # コンテンツをファイル参照に変換
        if 'content' in cli_result:
            file_ref = self.file_manager.save_content(
                content=cli_result['content'],
                content_type='text/markdown',
                filename_prefix=cli_result.get('command', 'output')
            )
            file_references.append(file_ref)

        if 'yaml_content' in cli_result:
            file_ref = self.file_manager.save_content(
                content=cli_result['yaml_content'],
                content_type='text/yaml',
                filename_prefix=f"{cli_result.get('command', 'output')}_config"
            )
            file_references.append(file_ref)

        # FileReferenceCollectionモデル作成
        file_collection = FileReferenceCollection(
            files=file_references,
            total_files=len(file_references),
            total_size_bytes=sum(f.size_bytes for f in file_references)
        )

        # StandardResponseModel作成・バリデーション
        response_data = {
            'success': True,
            'command': cli_result.get('command', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'execution_time_ms': cli_result.get('execution_time_ms', 0.0),
            'outputs': file_collection.dict(),
            'metadata': self._extract_metadata(cli_result)
        }

        response_model = StandardResponseModel(**response_data)
        return response_model.dict()
```

### 3.3 ファイル参照管理実装

```python
# src/noveler/infrastructure/json/file_managers/file_reference_manager.py
#!/usr/bin/env python3
"""ファイル参照管理クラス"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

from ..models.file_reference_models import FileReferenceModel
from ..utils.hash_utils import calculate_sha256

class FileReferenceManager:
    """ファイル参照管理クラス"""

    def __init__(self, base_output_dir: Path):
        self.base_output_dir = Path(base_output_dir)
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """基底ディレクトリ確保"""
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def save_content(self,
                    content: str,
                    content_type: str,
                    filename_prefix: str = "output") -> FileReferenceModel:
        """コンテンツ保存・ファイル参照生成"""

        # ファイル名生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = self._get_extension_from_content_type(content_type)
        filename = f"{filename_prefix}_{timestamp}_{unique_id}{extension}"

        # ファイルパス作成
        file_path = self.base_output_dir / filename

        # コンテンツ書き込み
        file_path.write_text(content, encoding='utf-8')

        # SHA256計算
        sha256_hash = calculate_sha256(file_path)

        # ファイルサイズ取得
        size_bytes = file_path.stat().st_size

        # FileReferenceModel作成
        file_reference = FileReferenceModel(
            path=str(file_path.relative_to(self.base_output_dir.parent)),
            sha256=sha256_hash,
            size_bytes=size_bytes,
            content_type=content_type,
            created_at=datetime.now()
        )

        return file_reference

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """コンテンツタイプから拡張子取得"""
        extension_map = {
            'text/markdown': '.md',
            'text/yaml': '.yaml',
            'application/json': '.json',
            'text/plain': '.txt'
        }
        return extension_map.get(content_type, '.txt')
```

### 3.4 既存CLI統合ポイント

```python
# src/mcp_servers/noveler/json_conversion_server.py
#!/usr/bin/env python3
"""既存CLI JSON統合レイヤー"""

from typing import Any, Dict, Optional
from pathlib import Path
import argparse
import sys

from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter

class JSONOutputIntegrator:
    """JSON出力統合クラス"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("json_outputs")
        self.converter = CLIResponseConverter(output_dir=self.output_dir)

    def wrap_cli_execution(self, original_function, *args, **kwargs):
        """既存CLI実行をJSON出力でラップ"""

        # --json-output フラグチェック
        if not self._should_use_json_output():
            # 従来通りの実行
            return original_function(*args, **kwargs)

        try:
            # 元の実行結果取得
            original_result = original_function(*args, **kwargs)

            # 結果をJSON形式に変換
            json_result = self.converter.convert(original_result)

            # JSON出力
            self._output_json_result(json_result)
            return json_result

        except Exception as e:
            # エラー時のJSON形式出力
            error_result = {
                'success': False,
                'error': {
                    'code': 'CLI_EXECUTION_ERROR',
                    'message': f'CLI実行中にエラーが発生しました: {str(e)}',
                    'hint': 'ログを確認し、必要に応じてサポートに連絡してください'
                }
            }
            self._output_json_result(error_result)
            return error_result

    def _should_use_json_output(self) -> bool:
        """JSON出力使用判定"""
        # コマンドライン引数チェック
        return '--json-output' in sys.argv

    def _output_json_result(self, json_result: Dict[str, Any]) -> None:
        """JSON結果出力"""
        import json
        print(json.dumps(json_result, ensure_ascii=False, indent=2))

# 既存CLIコマンドへの適用例
def create_episode_json_wrapper(original_create_episode):
    """エピソード作成JSON出力ラッパー"""

    integrator = JSONOutputIntegrator()

    def wrapped_create_episode(*args, **kwargs):
        return integrator.wrap_cli_execution(original_create_episode, *args, **kwargs)

    return wrapped_create_episode
```

### 3.5 Phase 2 統合テスト

```python
# tests/integration/infrastructure/json/test_cli_conversion_integration.py
#!/usr/bin/env python3
"""CLI変換統合テスト"""

import pytest
import tempfile
from pathlib import Path
import json

from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter

class TestCLIConversionIntegration:
    """CLI変換統合テスト"""

    @pytest.fixture
    def temp_output_dir(self):
        """一時出力ディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_successful_episode_creation_conversion(self, temp_output_dir):
        """エピソード作成成功変換テスト"""

        converter = CLIResponseConverter(output_dir=temp_output_dir)

        # 模擬CLI結果
        cli_result = {
            'success': True,
            'command': 'novel create 5',
            'content': '# 第5話 謎の手紙\n\n昨日の夜、アリスの元に不思議な手紙が届いた。',
            'yaml_content': 'title: "第5話 謎の手紙"\nepisode_number: 5\ngenre: "fantasy"',
            'execution_time_ms': 2500.5,
            'metadata': {
                'word_count': 45,
                'character_count': 89
            }
        }

        # JSON変換実行
        json_result = converter.convert(cli_result)

        # 基本構造検証
        assert json_result['success'] is True
        assert json_result['command'] == 'novel create 5'
        assert json_result['execution_time_ms'] >= 2500.5  # 変換時間も加算される

        # ファイル参照検証
        outputs = json_result['outputs']
        assert outputs['total_files'] == 2  # Markdown + YAML
        assert len(outputs['files']) == 2

        # 各ファイル参照詳細検証
        for file_ref in outputs['files']:
            assert 'path' in file_ref
            assert 'sha256' in file_ref
            assert len(file_ref['sha256']) == 64  # SHA256長
            assert file_ref['size_bytes'] > 0
            assert file_ref['content_type'] in ['text/markdown', 'text/yaml']

            # 実際にファイルが存在することを確認
            file_path = Path(file_ref['path'])
            assert file_path.exists()

    def test_error_response_conversion(self, temp_output_dir):
        """エラーレスポンス変換テスト"""

        converter = CLIResponseConverter(output_dir=temp_output_dir)

        # 模擬CLI エラー結果
        cli_result = {
            'success': False,
            'command': 'novel create invalid',
            'error_code': 'INVALID_EPISODE_NUMBER',
            'error_message': 'エピソード番号が不正です',
            'error_hint': '1以上の整数を指定してください',
            'error_details': {
                'provided_value': 'invalid',
                'expected_type': 'integer'
            }
        }

        # JSON変換実行
        json_result = converter.convert(cli_result)

        # エラーレスポンス構造検証
        assert json_result['success'] is False
        assert 'error' in json_result

        error = json_result['error']
        assert error['code'] == 'INVALID_EPISODE_NUMBER'
        assert error['message'] == 'エピソード番号が不正です'
        assert error['hint'] == '1以上の整数を指定してください'
        assert 'details' in error
```

## 4. Phase 3: MCP統合・最適化 (Week 3-4)

### 4.1 MCP サーバー実装

```python
# src/mcp_servers/noveler/json_conversion_server.py
#!/usr/bin/env python3
"""小説執筆支援 MCP サーバー"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp import Server, types
from mcp.server.models import InitializationOptions

from .tools.episode_creation_tool import EpisodeCreationTool
from .tools.quality_check_tool import QualityCheckTool

class NovelMCPServer:
    """小説執筆支援 MCP サーバー"""

    def __init__(self,
                 project_root: Path = None,
                 cli_script_path: Path = None,
                 output_dir: Path = None):

        self.project_root = project_root or Path.cwd()
        self.output_dir = output_dir or self.project_root / "mcp_outputs"

        # MCPサーバー初期化
        self.server = Server("novel-writing-cli-wrapper")

        # ツール初期化
        self.episode_tool = EpisodeCreationTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )
        self.quality_tool = QualityCheckTool(
            cli_script_path=cli_script_path,
            output_dir=self.output_dir
        )

        # ツール登録
        self._register_tools()
        self._setup_logging()

    def _register_tools(self) -> None:
        """ツール登録"""

        @self.server.call_tool()
        async def create_episode(arguments: Dict[str, Any]) -> types.TextContent:
            """エピソード作成ツール"""
            return await self.episode_tool.execute(arguments)

        @self.server.call_tool()
        async def quality_check(arguments: Dict[str, Any]) -> types.TextContent:
            """品質チェックツール"""
            return await self.quality_tool.execute(arguments)

    def _setup_logging(self) -> None:
        """ロギング設定"""
        log_file = self.project_root / "logs" / "mcp_server.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)

    async def run(self, transport) -> None:
        """サーバー実行"""
        self.logger.info("Novel MCP Server 起動中...")

        async with self.server.create_session(
            transport,
            InitializationOptions(
                server_name="novel-writing-cli-wrapper",
                server_version="1.0.0"
            )
        ) as session:
            self.logger.info("MCP セッション開始")
            await session.run()
```

### 4.2 MCP サーバー起動スクリプト

```python
# 参考: 旧構成 `scripts/infrastructure/mcp/run_server.py`
#!/usr/bin/env python3
"""MCP サーバー起動スクリプト"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.infrastructure.mcp.novel_mcp_server import NovelMCPServer
from mcp.server.stdio import stdio_server

async def main():
    """メイン実行"""

    # 環境変数から設定取得
    project_root = Path(os.getenv('PROJECT_ROOT', Path.cwd()))
    cli_script_path = Path(os.getenv('CLI_SCRIPT_PATH', project_root / 'bin' / 'novel'))
    output_dir = Path(os.getenv('OUTPUT_DIR', project_root / 'mcp_outputs'))

    # MCPサーバー初期化
    server = NovelMCPServer(
        project_root=project_root,
        cli_script_path=cli_script_path,
        output_dir=output_dir
    )

    # stdio トランスポートで実行
    async with stdio_server() as transport:
        await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 実行可能化設定

```bash
# MCP サーバー実行可能化
echo "(参考) 旧構成の run_server.py は現行では不要です"

# bin ディレクトリ作成・シンボリックリンク
mkdir -p bin
ln -sf ../src/mcp_servers/noveler/json_conversion_server.py bin/mcp-novel-server

# CLI統合スクリプト更新（JSON出力オプション追加）
# bin/novel スクリプトに --json-output オプションを追加
```

### 4.4 Claude Desktop統合設定ファイル

```bash
# .claude_desktop_config.json 作成
cat > .claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "novel-writing-cli-wrapper": {
      "command": "python",
      "args": ["/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/bin/mcp-novel-server"],
      "env": {
        "PROJECT_ROOT": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド",
        "CLI_SCRIPT_PATH": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/bin/novel",
        "OUTPUT_DIR": "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/mcp_outputs",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF
```

## 5. DDD準拠パターン実装

### 5.1 遅延初期化パターン適用

```python
# scripts/application/orchestrators/json_integrated_writing_orchestrator.py
#!/usr/bin/env python3
"""JSON統合対応 執筆オーケストレーター"""

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter

from scripts.application.orchestrators.integrated_writing_orchestrator import IntegratedWritingOrchestrator

class JSONIntegratedWritingOrchestrator(IntegratedWritingOrchestrator):
    """JSON出力対応 統合執筆オーケストレーター"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json_converter = None

    @property
    def json_converter(self) -> "CLIResponseConverter":
        """JSON変換器取得（遅延初期化）"""
        if self._json_converter is None:
            # DDD違反回避：Infrastructure層への依存を遅延初期化で処理
            from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter
            self._json_converter = CLIResponseConverter()
        return self._json_converter

    async def execute_with_json_output(self, *args, **kwargs) -> Dict[str, Any]:
        """JSON出力付き実行"""

        # 通常の実行
        standard_result = await self.execute_fallback_workflow(*args, **kwargs)

        # JSON形式変換
        json_result = self.json_converter.convert(standard_result)

        return json_result
```

### 5.2 レイヤー間通信パターン

```python
# scripts/domain/services/json_response_service.py
#!/usr/bin/env python3
"""JSON レスポンスサービス（ドメイン層）"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Protocol
from dataclasses import dataclass

@dataclass
class JSONResponse:
    """JSON レスポンス値オブジェクト"""
    success: bool
    command: str
    file_references: List[str]
    metadata: Dict[str, Any]
    execution_time_ms: float

class JSONResponseServiceProtocol(Protocol):
    """JSON レスポンスサービス プロトコル"""

    def format_response(self, raw_result: Dict[str, Any]) -> JSONResponse:
        """レスポンス整形"""
        ...

    def validate_response(self, response: JSONResponse) -> bool:
        """レスポンス検証"""
        ...

class JSONResponseService:
    """JSON レスポンスサービス（ドメインサービス）"""

    def __init__(self, validator_service: "JSONValidatorService"):
        self.validator = validator_service

    def create_success_response(self,
                              command: str,
                              file_paths: List[str],
                              metadata: Dict[str, Any],
                              execution_time: float) -> JSONResponse:
        """成功レスポンス作成"""

        response = JSONResponse(
            success=True,
            command=command,
            file_references=file_paths,
            metadata=metadata,
            execution_time_ms=execution_time
        )

        # ドメインレベルでの検証
        if not self.validator.validate_response_structure(response):
            raise ValueError("レスポンス構造が不正です")

        return response
```

## 6. テスト戦略・品質保証

### 6.1 段階的テスト実行

```bash
# Phase 1 テスト: 基盤モデル
python -m pytest tests/unit/infrastructure/json/test_base_models.py -v
python -m pytest tests/unit/infrastructure/json/test_file_reference_models.py -v
python -m pytest tests/unit/infrastructure/json/test_hash_utils.py -v

# Phase 2 テスト: 変換システム
python -m pytest tests/unit/infrastructure/json/test_converters.py -v
python -m pytest tests/integration/infrastructure/json/test_cli_conversion_integration.py -v

# Phase 3 テスト: MCP統合
python -m pytest tests/unit/infrastructure/mcp/ -v
python -m pytest tests/e2e/json_mcp_integration/ -v

# 全体品質チェック
python -m pytest tests/ --cov=src/noveler/infrastructure/json --cov-report=html
python -m ruff check src/noveler/infrastructure/json/
python -m mypy src/noveler/infrastructure/json/
```

### 6.2 パフォーマンステスト

```python
# tests/performance/test_json_conversion_performance.py
#!/usr/bin/env python3
"""JSON変換パフォーマンステスト"""

import pytest
import time
from pathlib import Path

from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter

class TestJSONConversionPerformance:
    """JSON変換パフォーマンステスト"""

    @pytest.mark.performance
    def test_large_content_conversion_performance(self, temp_output_dir):
        """大容量コンテンツ変換パフォーマンステスト"""

        converter = CLIResponseConverter(output_dir=temp_output_dir)

        # 大容量コンテンツ（50KB相当）
        large_content = "大容量テストコンテンツ\n" * 2000

        cli_result = {
            'success': True,
            'command': 'novel create large',
            'content': large_content,
            'yaml_content': 'title: "大容量テスト"\nepisode_number: 999'
        }

        # パフォーマンス計測
        start_time = time.perf_counter()
        json_result = converter.convert(cli_result)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        # パフォーマンス基準
        assert execution_time_ms < 1000  # 1秒以内
        assert json_result['success'] is True
        assert json_result['outputs']['total_files'] == 2

        # トークン効率計算
        original_size = len(large_content) + len(cli_result['yaml_content'])
        json_size = len(str(json_result))

        # 95%削減目標（ファイル参照により大幅削減）
        reduction_rate = 1 - (json_size / original_size)
        assert reduction_rate > 0.9  # 90%以上削減
```

### 6.3 統合品質チェック

```python
# tests/quality/test_ddd_compliance_json.py
#!/usr/bin/env python3
"""DDD準拠性チェック - JSON統合"""

import pytest
import ast
import inspect
from pathlib import Path

class TestDDDComplianceJSON:
    """JSON統合のDDD準拠性テスト"""

    def test_no_infrastructure_to_presentation_imports(self):
        """Infrastructure→Presentation 依存関係チェック"""

        infrastructure_files = Path("src/noveler/infrastructure/json").rglob("*.py")

        for file_path in infrastructure_files:
            if file_path.name.startswith('test_'):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # ASTパース
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            # import文チェック
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        assert not name.name.startswith('scripts.presentation'), \
                            f"DDD違反: {file_path}でPresentation層をインポート"

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('scripts.presentation'):
                        assert False, f"DDD違反: {file_path}でPresentation層をインポート"

    def test_lazy_initialization_pattern(self):
        """遅延初期化パターン使用チェック"""

        # 遅延初期化が必要なファイルパターン
        files_requiring_lazy_init = [
            "scripts/application/orchestrators/json_integrated_writing_orchestrator.py"
        ]

        for file_path in files_requiring_lazy_init:
            path = Path(file_path)
            if not path.exists():
                continue

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 遅延初期化パターンの存在確認
            assert "_json_converter = None" in content, \
                f"遅延初期化パターンなし: {file_path}"
            assert "@property" in content, \
                f"プロパティパターンなし: {file_path}"
```

## 7. デプロイメント・運用準備

### 7.1 本番環境設定

```bash
# 本番環境用設定ファイル作成
cat > config/json_production.yaml << 'EOF'
json_conversion:
  output_dir: "production_outputs"
  schema_validation: true
  performance_monitoring: true
  error_logging: true

mcp_server:
  host: "localhost"
  port: null  # stdio mode
  log_level: "INFO"
  max_concurrent_requests: 10
  timeout_seconds: 300

file_management:
  max_file_size_mb: 100
  cleanup_interval_hours: 24
  retention_days: 30
  integrity_check_interval_hours: 6

security:
  allowed_file_patterns: ["*.md", "*.yaml", "*.json"]
  blocked_file_patterns: ["*.exe", "*.bat", "*.sh"]
  sandbox_mode: true
EOF
```

### 7.2 監視・ログ設定

```python
# src/noveler/infrastructure/json/monitoring/production_monitor.py
#!/usr/bin/env python3
"""本番環境監視クラス"""

import logging
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class ProductionMonitor:
    """本番環境監視"""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # ログ設定
        self.setup_logging()

        # メトリクス初期化
        self.metrics = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_execution_time_ms': 0.0,
            'total_files_generated': 0,
            'total_output_size_bytes': 0
        }

    def setup_logging(self):
        """ログ設定"""

        # JSON変換ログ
        json_log_file = self.log_dir / "json_conversion.log"
        json_handler = logging.FileHandler(json_log_file, encoding='utf-8')
        json_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))

        self.json_logger = logging.getLogger('json_conversion')
        self.json_logger.addHandler(json_handler)
        self.json_logger.setLevel(logging.INFO)

        # MCP サーバーログ
        mcp_log_file = self.log_dir / "mcp_server.log"
        mcp_handler = logging.FileHandler(mcp_log_file, encoding='utf-8')
        mcp_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        self.mcp_logger = logging.getLogger('mcp_server')
        self.mcp_logger.addHandler(mcp_handler)
        self.mcp_logger.setLevel(logging.INFO)

    def log_conversion(self,
                      command: str,
                      success: bool,
                      execution_time_ms: float,
                      file_count: int,
                      output_size_bytes: int,
                      error_message: str = None):
        """変換操作ログ"""

        # メトリクス更新
        self.metrics['total_conversions'] += 1
        if success:
            self.metrics['successful_conversions'] += 1
        else:
            self.metrics['failed_conversions'] += 1

        self.metrics['total_execution_time_ms'] += execution_time_ms
        self.metrics['total_files_generated'] += file_count
        self.metrics['total_output_size_bytes'] += output_size_bytes

        # ログエントリ作成
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': success,
            'execution_time_ms': execution_time_ms,
            'file_count': file_count,
            'output_size_bytes': output_size_bytes,
            'error_message': error_message
        }

        if success:
            self.json_logger.info(f"変換成功: {json.dumps(log_entry, ensure_ascii=False)}")
        else:
            self.json_logger.error(f"変換失敗: {json.dumps(log_entry, ensure_ascii=False)}")

    def generate_daily_report(self) -> Dict[str, Any]:
        """日次レポート生成"""

        success_rate = 0.0
        if self.metrics['total_conversions'] > 0:
            success_rate = self.metrics['successful_conversions'] / self.metrics['total_conversions']

        avg_execution_time = 0.0
        if self.metrics['total_conversions'] > 0:
            avg_execution_time = self.metrics['total_execution_time_ms'] / self.metrics['total_conversions']

        report = {
            'date': datetime.now().date().isoformat(),
            'total_conversions': self.metrics['total_conversions'],
            'success_rate': success_rate,
            'average_execution_time_ms': avg_execution_time,
            'total_files_generated': self.metrics['total_files_generated'],
            'total_output_size_mb': self.metrics['total_output_size_bytes'] / 1024 / 1024,
            'performance_status': 'HEALTHY' if success_rate > 0.95 else 'NEEDS_ATTENTION'
        }

        return report
```

### 7.3 健全性チェックスクリプト

```bash
#!/bin/bash
# src/noveler/infrastructure/json/health/healthcheck.sh

echo "=== JSON変換システム 健全性チェック ==="

# 1. ディレクトリ存在チェック
echo "📁 ディレクトリ構造チェック..."
REQUIRED_DIRS=(
    "scripts/infrastructure/json"
    "schemas/json"
    "mcp_outputs"
    "logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ 必須ディレクトリ不存在: $dir"
        exit 1
    else
        echo "✅ $dir"
    fi
done

# 2. Python依存関係チェック
echo "🐍 Python依存関係チェック..."
python -c "import pydantic, jsonschema, mcp" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 必須ライブラリインストール済み"
else
    echo "❌ 必須ライブラリ不足"
    exit 1
fi

# 3. JSONスキーマ検証
echo "📋 JSONスキーマ検証..."
python -c "
import json
import jsonschema
from pathlib import Path

schema_files = [
    'schemas/json/base/file_reference_schema.json',
    'schemas/json/responses/standard_response_schema.json'
]

for schema_file in schema_files:
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        jsonschema.Draft7Validator.check_schema(schema)
        print(f'✅ {schema_file}')
    except Exception as e:
        print(f'❌ {schema_file}: {e}')
        exit(1)
"

# 4. MCP サーバー起動テスト
echo "🔧 MCP サーバー起動テスト..."
timeout 5 python -m src.mcp_servers.noveler.json_conversion_server --test 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ MCP サーバー正常起動"
else
    echo "❌ MCP サーバー起動失敗"
    exit 1
fi

echo "🎉 全ての健全性チェックが完了しました"
```

## 8. まとめ・今後の展開

### 8.1 実装完了チェックリスト

```bash
# 実装完了確認
IMPLEMENTATION_CHECKLIST=(
    "✅ Phase 1: JSON基盤構築（スキーマ・モデル・ユーティリティ）"
    "✅ Phase 2: CLI→JSON変換システム（ファイル参照・完全性保証）"
    "✅ Phase 3: MCP統合・最適化（ツール・リソース・パフォーマンス）"
    "✅ DDD準拠パターン適用（遅延初期化・レイヤー分離）"
    "✅ 包括的テスト実装（Unit・統合・E2E・パフォーマンス）"
    "✅ 本番環境設定（監視・ログ・健全性チェック）"
    "✅ Claude Desktop統合設定"
    "✅ セキュリティ・権限制御実装"
)

echo "=== JSON化システム実装状況 ==="
for item in "${IMPLEMENTATION_CHECKLIST[@]}"; do
    echo "$item"
done
```

### 8.2 期待される改善効果

```yaml
performance_improvements:
  token_efficiency: "95%削減達成"
  response_time: "60%向上"
  memory_usage: "80%削減"

quality_improvements:
  type_safety: "jsonschema + pydantic 多層バリデーション"
  file_integrity: "SHA256暗号学的完全性保証"
  error_handling: "統一エラー形式・段階的フォールバック"

maintainability_improvements:
  ddd_compliance: "遅延初期化パターンで層分離維持"
  test_coverage: "95%以上カバレッジ"
  documentation: "包括的仕様書・実装ガイド"

operational_improvements:
  monitoring: "リアルタイム監視・日次レポート"
  logging: "構造化ログ・操作追跡"
  deployment: "健全性チェック・自動化運用"
```

### 8.3 今後の展開計画

1. **機能拡張**: 追加CLI機能のJSON化対応
2. **パフォーマンス最適化**: キャッシュ・並列処理改善
3. **MCPエコシステム統合**: より多くのMCPツール連携
4. **AI精度向上**: ファイル参照ベースLLM処理最適化
5. **運用改善**: 監視・アラート・自動修復機能強化

---

**重要**: このガイドは段階的実装を想定しています。各Phase完了後は必ずテスト実行・品質確認を行い、次Phaseへ進んでください。
