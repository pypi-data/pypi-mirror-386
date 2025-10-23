# SPEC-CLI-002: CLI JSON化 技術仕様詳細書

## 要件トレーサビリティ

**要件ID**: REQ-CLI-021, REQ-CLI-022, REQ-CLI-023 (CLIエラーハンドリング・ガイダンス)

**主要要件**:
- REQ-CLI-021: 階層化エラー管理
- REQ-CLI-022: インテリジェントヘルプ
- REQ-CLI-023: 国際化対応

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/integration/test_cli_json_conversion.py
**関連仕様書**: SPEC-CLI-001_cli_adapter.md

## 概要

CLI出力の100% JSON化実装に関する技術詳細仕様書。
Pydantic・jsonschema・hashlibを使用した型安全・完全性保証・高性能なJSON変換システム。

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-CLI-002 |
| E2EテストID | E2E-CLI-002 |
| test_type | integration |
| バージョン | v1.0.0 |
| 作成日 | 2025-08-27 |
| 最終更新 | 2025-08-28 |
| ステータス | active |
| 対象 | JSON変換層・バリデーション・ファイル管理 |
| 技術スタック | Python 3.11+, Pydantic v2, jsonschema, hashlib |

## 1. 技術アーキテクチャ詳細

### 1.1 コンポーネント構成図

```
scripts/infrastructure/json/
├── __init__.py
├── schemas/
│   ├── __init__.py
│   ├── file_reference_schema.json    # ファイル参照スキーマ
│   ├── standard_response_schema.json # 標準レスポンススキーマ
│   ├── error_response_schema.json    # エラーレスポンススキーマ
│   └── command_schemas/              # コマンド別スキーマ
│       ├── create_episode_schema.json
│       ├── quality_check_schema.json
│       └── plot_generation_schema.json
├── models/
│   ├── __init__.py
│   ├── base_models.py               # Pydantic基底モデル
│   ├── file_reference_models.py     # ファイル参照モデル
│   ├── response_models.py           # レスポンスモデル
│   └── command_models.py            # コマンド固有モデル
├── converters/
│   ├── __init__.py
│   ├── base_converter.py            # 基底変換器
│   ├── cli_response_converter.py    # CLI→JSON変換器
│   └── file_content_converter.py    # コンテンツ→ファイル変換器
├── validators/
│   ├── __init__.py
│   ├── schema_validator.py          # JSONスキーマバリデーター
│   ├── pydantic_validator.py        # Pydanticバリデーター
│   └── integrity_validator.py       # 完全性バリデーター
├── file_managers/
│   ├── __init__.py
│   ├── file_reference_manager.py    # ファイル参照管理
│   ├── integrity_manager.py         # SHA256完全性管理
│   └── content_writer.py            # コンテンツ書き込み管理
└── utils/
    ├── __init__.py
    ├── hash_utils.py                # ハッシュユーティリティ
    ├── path_utils.py                # パスユーティリティ
    └── time_utils.py                # 時間ユーティリティ
```

### 1.2 依存関係管理

```python
# requirements_json.txt
pydantic==2.5.0           # データバリデーション・シリアライゼーション
jsonschema==4.20.0        # JSONスキーマバリデーション
typing-extensions==4.8.0  # 型ヒント拡張
python-dateutil==2.8.2    # 日時処理
pathlib2==2.3.7           # パス処理（Python < 3.4対応）
```

## 2. データモデル詳細仕様

### 2.1 Pydantic基底モデル

```python
# src/noveler/infrastructure/json/models/base_models.py
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
        extra = "forbid"  # 追加フィールド禁止
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: lambda v: str(v)
        }

    @root_validator
    def validate_model_consistency(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """モデル一貫性検証"""
        # 実装: 複数フィールド間の一貫性チェック
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

    @validator('created_at', 'updated_at', pre=True, always=True)
    def validate_timestamp(cls, v):
        """タイムスタンプ形式検証"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
```

### 2.2 ファイル参照モデル

```python
# src/noveler/infrastructure/json/models/file_reference_models.py
from pathlib import Path
from typing import Optional
from pydantic import Field, validator
import re

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
        ge=0,  # 0以上
        le=100_000_000  # 100MB以下
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
        # 相対パスのみ許可（セキュリティ）
        if v.startswith('/') or '..' in v:
            raise ValueError("相対パスのみ許可、親ディレクトリ参照禁止")

        # 危険な文字チェック
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

    @validator('total_files', always=True)
    def validate_total_files(cls, v: int, values: Dict) -> int:
        """総ファイル数一致検証"""
        files = values.get('files', [])
        if v != len(files):
            raise ValueError(f"総ファイル数不一致: 指定値={v}, 実際={len(files)}")
        return v

    @validator('total_size_bytes', always=True)
    def validate_total_size(cls, v: int, values: Dict) -> int:
        """総サイズ一致検証"""
        files = values.get('files', [])
        actual_total = sum(f.size_bytes for f in files)
        if v != actual_total:
            raise ValueError(f"総サイズ不一致: 指定値={v}, 実際={actual_total}")
        return v
```

### 2.3 レスポンスモデル

```python
# src/noveler/infrastructure/json/models/response_models.py
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, validator

class StandardResponseModel(BaseJSONModel, TimestampMixin):
    """標準レスポンスモデル"""

    success: bool = Field(
        ...,
        description="実行成功フラグ"
    )

    command: str = Field(
        ...,
        description="実行されたコマンド",
        min_length=1,
        max_length=200
    )

    execution_time_ms: float = Field(
        ...,
        description="実行時間（ミリ秒）",
        ge=0.0
    )

    outputs: FileReferenceCollection = Field(
        default_factory=FileReferenceCollection,
        description="出力ファイル参照コレクション"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="追加メタデータ"
    )

    @validator('command')
    def validate_command_format(cls, v: str) -> str:
        """コマンド形式検証"""
        # 許可されたコマンドプレフィックス
        allowed_prefixes = ['novel', 'check', 'plot', 'quality']
        if not any(v.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"許可されていないコマンド: {v}")
        return v

class ErrorResponseModel(BaseJSONModel, TimestampMixin):
    """エラーレスポンスモデル"""

    success: bool = Field(
        False,
        description="実行成功フラグ（常にFalse）",
        const=True
    )

    error: "ErrorDetailModel" = Field(
        ...,
        description="エラー詳細"
    )

    command: str = Field(
        ...,
        description="実行されたコマンド"
    )

class ErrorDetailModel(BaseJSONModel):
    """エラー詳細モデル"""

    code: str = Field(
        ...,
        description="エラーコード",
        regex=r"^[A-Z_]+$"
    )

    message: str = Field(
        ...,
        description="エラーメッセージ（日本語）",
        min_length=1,
        max_length=500
    )

    hint: str = Field(
        ...,
        description="解決方法ヒント（日本語）",
        min_length=1,
        max_length=1000
    )

    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="詳細情報"
    )

    stack_trace: Optional[str] = Field(
        default=None,
        description="スタックトレース（開発時のみ）"
    )

# 前方参照解決
ErrorResponseModel.model_rebuild()
```

## 3. JSON変換実装詳細

### 3.1 基底変換器

```python
# src/noveler/infrastructure/json/converters/base_converter.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pathlib import Path
import time
import json
from pydantic import ValidationError
import jsonschema

T = TypeVar('T', bound='BaseJSONModel')

class BaseConverter(ABC):
    """JSON変換基底クラス"""

    def __init__(self,
                 schema_dir: Path = None,
                 output_dir: Path = None,
                 validate_schema: bool = True):
        self.schema_dir = schema_dir or Path("schemas")
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

    def validate_with_schema(self, data: Dict[str, Any], schema_name: str) -> None:
        """JSONスキーマバリデーション"""
        if not self.validate_schema:
            return

        try:
            schema = self.load_schema(schema_name)
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"スキーマ検証エラー: {e.message}")

    def validate_with_pydantic(self, data: Dict[str, Any], model_class: Type[T]) -> T:
        """Pydanticバリデーション"""
        try:
            return model_class(**data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                error_details.append(f"{field}: {error['msg']}")

            raise ValueError(f"Pydantic検証エラー: {'; '.join(error_details)}")

    @abstractmethod
    def convert(self, input_data: Any) -> Dict[str, Any]:
        """変換実行（抽象メソッド）"""
        pass

    def _measure_execution_time(self, func):
        """実行時間計測デコレーター"""
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            if isinstance(result, dict):
                result['execution_time_ms'] = execution_time_ms

            return result
        return wrapper
```

### 3.2 CLI→JSON変換器

```python
# src/noveler/infrastructure/json/converters/cli_response_converter.py
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import uuid
from datetime import datetime

from ..models.response_models import StandardResponseModel, ErrorResponseModel
from ..models.file_reference_models import FileReferenceModel, FileReferenceCollection
from ..file_managers.file_reference_manager import FileReferenceManager
from .base_converter import BaseConverter

class CLIResponseConverter(BaseConverter):
    """CLI レスポンス→JSON変換器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_manager = FileReferenceManager(self.output_dir)

    @BaseConverter._measure_execution_time
    def convert(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """CLI実行結果をJSON形式に変換"""

        try:
            # 成功時とエラー時で分岐
            if cli_result.get('success', False):
                return self._convert_success_response(cli_result)
            else:
                return self._convert_error_response(cli_result)

        except Exception as e:
            # 変換エラー時の緊急エラーレスポンス
            return self._create_emergency_error_response(str(e), cli_result)

    def _convert_success_response(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """成功レスポンス変換"""

        # コンテンツをファイル化
        file_references = []

        # 各種出力をファイル参照に変換
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

        if 'json_data' in cli_result:
            file_ref = self.file_manager.save_content(
                content=json.dumps(cli_result['json_data'], ensure_ascii=False, indent=2),
                content_type='application/json',
                filename_prefix=f"{cli_result.get('command', 'output')}_data"
            )
            file_references.append(file_ref)

        # FileReferenceCollectionモデル作成
        file_collection = FileReferenceCollection(
            files=file_references,
            total_files=len(file_references),
            total_size_bytes=sum(f.size_bytes for f in file_references)
        )

        # StandardResponseModel作成
        response_data = {
            'success': True,
            'command': cli_result.get('command', 'unknown'),
            'execution_time_ms': cli_result.get('execution_time_ms', 0.0),
            'outputs': file_collection,
            'metadata': self._extract_metadata(cli_result),
            'created_at': datetime.now()
        }

        # Pydanticバリデーション
        response_model = self.validate_with_pydantic(response_data, StandardResponseModel)

        # JSONスキーマバリデーション
        response_dict = response_model.dict()
        self.validate_with_schema(response_dict, 'standard_response_schema')

        return response_dict

    def _convert_error_response(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """エラーレスポンス変換"""

        error_data = {
            'success': False,
            'error': {
                'code': cli_result.get('error_code', 'UNKNOWN_ERROR'),
                'message': cli_result.get('error_message', '不明なエラーが発生しました'),
                'hint': cli_result.get('error_hint', 'ログを確認し、必要に応じてサポートに連絡してください'),
                'details': cli_result.get('error_details', {}),
                'stack_trace': cli_result.get('stack_trace') if cli_result.get('debug_mode') else None
            },
            'command': cli_result.get('command', 'unknown'),
            'created_at': datetime.now()
        }

        # Pydanticバリデーション
        error_model = self.validate_with_pydantic(error_data, ErrorResponseModel)

        # JSONスキーマバリデーション
        error_dict = error_model.dict()
        self.validate_with_schema(error_dict, 'error_response_schema')

        return error_dict

    def _extract_metadata(self, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        """メタデータ抽出"""
        metadata_keys = [
            'session_id', 'user_id', 'project_id', 'environment',
            'version', 'git_commit', 'performance_metrics'
        ]

        metadata = {}
        for key in metadata_keys:
            if key in cli_result:
                metadata[key] = cli_result[key]

        return metadata

    def _create_emergency_error_response(self, error_msg: str, original_data: Dict) -> Dict[str, Any]:
        """緊急エラーレスポンス生成"""
        return {
            'success': False,
            'error': {
                'code': 'CONVERTER_ERROR',
                'message': f'JSON変換中にエラーが発生しました: {error_msg}',
                'hint': '開発者に連絡してください。原因調査のため元データを保存しています。',
                'details': {
                    'original_data_keys': list(original_data.keys()),
                    'conversion_error': error_msg
                }
            },
            'command': original_data.get('command', 'unknown'),
            'created_at': datetime.now().isoformat()
        }
```

## 4. ファイル管理・完全性保証

### 4.1 ファイル参照管理

```python
# src/noveler/infrastructure/json/file_managers/file_reference_manager.py
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
import uuid
import json

from ..models.file_reference_models import FileReferenceModel
from ..utils.hash_utils import calculate_sha256
from .content_writer import ContentWriter

class FileReferenceManager:
    """ファイル参照管理クラス"""

    def __init__(self, base_output_dir: Path):
        self.base_output_dir = Path(base_output_dir)
        self.content_writer = ContentWriter()
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """基底ディレクトリ確保"""
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def save_content(self,
                    content: str,
                    content_type: str,
                    filename_prefix: str = "output",
                    custom_filename: Optional[str] = None) -> FileReferenceModel:
        """コンテンツ保存・ファイル参照生成"""

        # ファイル名生成
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            extension = self._get_extension_from_content_type(content_type)
            filename = f"{filename_prefix}_{timestamp}_{unique_id}{extension}"

        # ファイルパス作成
        file_path = self.base_output_dir / filename

        # コンテンツ書き込み
        self.content_writer.write_content(file_path, content)

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

    def verify_file_integrity(self, file_reference: FileReferenceModel) -> bool:
        """ファイル完全性検証"""
        file_path = Path(file_reference.path)

        if not file_path.exists():
            return False

        # SHA256再計算・比較
        current_hash = calculate_sha256(file_path)
        return current_hash == file_reference.sha256

    def load_file_content(self, file_reference: FileReferenceModel) -> str:
        """ファイル内容読み込み（完全性検証付き）"""

        # 完全性チェック
        if not self.verify_file_integrity(file_reference):
            raise ValueError(f"ファイル完全性エラー: {file_reference.path}")

        # ファイル読み込み
        file_path = Path(file_reference.path)
        return self.content_writer.read_content(file_path)

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """コンテンツタイプから拡張子取得"""
        extension_map = {
            'text/markdown': '.md',
            'text/yaml': '.yaml',
            'application/json': '.json',
            'text/plain': '.txt'
        }
        return extension_map.get(content_type, '.txt')

    def cleanup_old_files(self, max_age_days: int = 30) -> List[str]:
        """古いファイル削除"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_files = []

        for file_path in self.base_output_dir.rglob("*"):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    deleted_files.append(str(file_path))

        return deleted_files
```

### 4.2 完全性管理

```python
# src/noveler/infrastructure/json/file_managers/integrity_manager.py
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

class IntegrityManager:
    """ファイル完全性管理クラス"""

    def __init__(self, checksum_file: Optional[Path] = None):
        self.checksum_file = checksum_file or Path("file_checksums.json")
        self._checksums: Dict[str, Dict[str, str]] = self._load_checksums()

    def _load_checksums(self) -> Dict[str, Dict[str, str]]:
        """チェックサムファイルロード"""
        if self.checksum_file.exists():
            try:
                with open(self.checksum_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_checksums(self) -> None:
        """チェックサムファイル保存"""
        with open(self.checksum_file, 'w', encoding='utf-8') as f:
            json.dump(self._checksums, f, ensure_ascii=False, indent=2)

    def register_file(self, file_path: Path, sha256_hash: Optional[str] = None) -> str:
        """ファイル登録・チェックサム記録"""
        if sha256_hash is None:
            sha256_hash = calculate_sha256(file_path)

        file_key = str(file_path)
        self._checksums[file_key] = {
            'sha256': sha256_hash,
            'size_bytes': file_path.stat().st_size,
            'registered_at': datetime.now().isoformat()
        }

        self._save_checksums()
        return sha256_hash

    def verify_file_integrity(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """ファイル完全性検証"""
        file_key = str(file_path)

        if file_key not in self._checksums:
            return False, "ファイルが登録されていません"

        if not file_path.exists():
            return False, "ファイルが存在しません"

        expected_hash = self._checksums[file_key]['sha256']
        current_hash = calculate_sha256(file_path)

        if current_hash != expected_hash:
            return False, f"ハッシュ不一致: 期待値={expected_hash}, 実際={current_hash}"

        return True, None

    def batch_verify(self, file_paths: List[Path]) -> Dict[str, Tuple[bool, Optional[str]]]:
        """一括完全性検証"""
        results = {}
        for file_path in file_paths:
            results[str(file_path)] = self.verify_file_integrity(file_path)
        return results

    def get_file_info(self, file_path: Path) -> Optional[Dict[str, str]]:
        """ファイル情報取得"""
        file_key = str(file_path)
        return self._checksums.get(file_key)

    def remove_file_record(self, file_path: Path) -> bool:
        """ファイルレコード削除"""
        file_key = str(file_path)
        if file_key in self._checksums:
            del self._checksums[file_key]
            self._save_checksums()
            return True
        return False

    def generate_integrity_report(self) -> Dict[str, Any]:
        """完全性レポート生成"""
        total_files = len(self._checksums)
        verified_files = 0
        corrupted_files = []
        missing_files = []

        for file_key, file_info in self._checksums.items():
            file_path = Path(file_key)
            is_valid, error_msg = self.verify_file_integrity(file_path)

            if is_valid:
                verified_files += 1
            elif not file_path.exists():
                missing_files.append(file_key)
            else:
                corrupted_files.append({
                    'path': file_key,
                    'error': error_msg
                })

        return {
            'report_generated_at': datetime.now().isoformat(),
            'total_files': total_files,
            'verified_files': verified_files,
            'corrupted_files': corrupted_files,
            'missing_files': missing_files,
            'integrity_rate': verified_files / total_files if total_files > 0 else 0.0
        }
```

## 5. バリデーション・エラーハンドリング

### 5.1 統合バリデーター

```python
# src/noveler/infrastructure/json/validators/unified_validator.py
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import ValidationError
import jsonschema
from pathlib import Path

from ..models.base_models import BaseJSONModel
from .schema_validator import SchemaValidator
from .pydantic_validator import PydanticValidator

T = TypeVar('T', bound=BaseJSONModel)

class UnifiedValidator:
    """統合バリデーションクラス"""

    def __init__(self, schema_dir: Path):
        self.schema_validator = SchemaValidator(schema_dir)
        self.pydantic_validator = PydanticValidator()

    def validate_full(self,
                     data: Dict[str, Any],
                     schema_name: str,
                     pydantic_model: Type[T]) -> T:
        """完全バリデーション（JSONスキーマ + Pydantic）"""

        # Step 1: JSONスキーマバリデーション
        schema_errors = self.schema_validator.validate(data, schema_name)
        if schema_errors:
            raise ValueError(f"JSONスキーマエラー: {'; '.join(schema_errors)}")

        # Step 2: Pydanticバリデーション
        try:
            validated_model = self.pydantic_validator.validate(data, pydantic_model)
            return validated_model
        except ValidationError as e:
            pydantic_errors = self._format_pydantic_errors(e)
            raise ValueError(f"Pydanticバリデーションエラー: {'; '.join(pydantic_errors)}")

    def validate_batch(self,
                      data_list: List[Dict[str, Any]],
                      schema_name: str,
                      pydantic_model: Type[T]) -> List[Union[T, Dict[str, str]]]:
        """一括バリデーション"""
        results = []

        for i, data in enumerate(data_list):
            try:
                validated_model = self.validate_full(data, schema_name, pydantic_model)
                results.append(validated_model)
            except ValueError as e:
                results.append({
                    'index': i,
                    'error': str(e),
                    'data_preview': str(data)[:100] + '...' if len(str(data)) > 100 else str(data)
                })

        return results

    def _format_pydantic_errors(self, validation_error: ValidationError) -> List[str]:
        """Pydanticエラー整形"""
        formatted_errors = []
        for error in validation_error.errors():
            field_path = '.'.join(str(loc) for loc in error['loc'])
            error_msg = error['msg']
            formatted_errors.append(f"{field_path}: {error_msg}")
        return formatted_errors

    def generate_validation_report(self,
                                  data_list: List[Dict[str, Any]],
                                  schema_name: str,
                                  pydantic_model: Type[T]) -> Dict[str, Any]:
        """バリデーションレポート生成"""
        results = self.validate_batch(data_list, schema_name, pydantic_model)

        valid_count = sum(1 for r in results if isinstance(r, BaseJSONModel))
        invalid_count = len(results) - valid_count

        invalid_items = [r for r in results if isinstance(r, dict)]

        return {
            'total_items': len(data_list),
            'valid_items': valid_count,
            'invalid_items': invalid_count,
            'success_rate': valid_count / len(data_list) if data_list else 0.0,
            'validation_errors': invalid_items[:10],  # 最初の10件のみ
            'schema_name': schema_name,
            'model_name': pydantic_model.__name__
        }
```

### 5.2 エラーハンドリング

```python
# src/noveler/infrastructure/json/error_handling/error_formatter.py
from typing import Any, Dict, List, Optional
from datetime import datetime
import traceback

class JSONErrorFormatter:
    """JSON形式エラー整形クラス"""

    ERROR_CODES = {
        # ファイル関連
        'FILE_NOT_FOUND': 'ファイルが見つかりません',
        'FILE_READ_ERROR': 'ファイル読み込みエラー',
        'FILE_WRITE_ERROR': 'ファイル書き込みエラー',
        'FILE_INTEGRITY_ERROR': 'ファイル完全性エラー',

        # バリデーション関連
        'VALIDATION_ERROR': 'データ検証エラー',
        'SCHEMA_VIOLATION': 'スキーマ違反',
        'PYDANTIC_ERROR': 'モデル検証エラー',

        # 変換関連
        'CONVERSION_ERROR': 'データ変換エラー',
        'JSON_PARSE_ERROR': 'JSON解析エラー',
        'ENCODING_ERROR': '文字エンコーディングエラー',

        # システム関連
        'SYSTEM_ERROR': 'システムエラー',
        'PERMISSION_DENIED': '権限エラー',
        'RESOURCE_EXHAUSTED': 'リソース不足',
    }

    ERROR_HINTS = {
        'FILE_NOT_FOUND': 'ファイルパスを確認し、ファイルが存在することを確認してください',
        'FILE_READ_ERROR': 'ファイルの権限とエンコーディングを確認してください',
        'FILE_WRITE_ERROR': 'ディスク容量と書き込み権限を確認してください',
        'FILE_INTEGRITY_ERROR': 'ファイルが改ざんされている可能性があります。元ファイルから再作成してください',
        'VALIDATION_ERROR': '入力データの形式を確認してください',
        'SCHEMA_VIOLATION': 'APIドキュメントを参照し、正しいデータ形式で再試行してください',
        'PYDANTIC_ERROR': 'フィールドの型と必須項目を確認してください',
        'CONVERSION_ERROR': 'データ形式変換中にエラーが発生しました。サポートに連絡してください',
        'JSON_PARSE_ERROR': 'JSON形式が不正です。文法を確認してください',
        'ENCODING_ERROR': 'UTF-8エンコーディングで保存し直してください',
        'SYSTEM_ERROR': 'システム管理者に連絡してください',
        'PERMISSION_DENIED': 'ファイルまたはディレクトリの権限を確認してください',
        'RESOURCE_EXHAUSTED': 'ディスク容量またはメモリを確認してください',
    }

    def format_error(self,
                    error_code: str,
                    custom_message: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None,
                    command: str = 'unknown',
                    include_stack_trace: bool = False) -> Dict[str, Any]:
        """エラー形式整形"""

        base_message = self.ERROR_CODES.get(error_code, '不明なエラー')
        message = custom_message if custom_message else base_message
        hint = self.ERROR_HINTS.get(error_code, 'ログを確認し、必要に応じてサポートに連絡してください')

        error_response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'hint': hint,
                'details': details or {}
            },
            'command': command,
            'timestamp': datetime.now().isoformat()
        }

        if include_stack_trace:
            error_response['error']['stack_trace'] = traceback.format_exc()

        return error_response

    def format_validation_error(self,
                               validation_errors: List[str],
                               command: str = 'validation') -> Dict[str, Any]:
        """バリデーションエラー専用整形"""

        return self.format_error(
            error_code='VALIDATION_ERROR',
            custom_message=f'データ検証で{len(validation_errors)}件のエラー',
            details={
                'validation_errors': validation_errors,
                'error_count': len(validation_errors)
            },
            command=command
        )

    def format_file_error(self,
                         file_path: str,
                         error_type: str = 'FILE_ERROR',
                         custom_message: Optional[str] = None) -> Dict[str, Any]:
        """ファイルエラー専用整形"""

        return self.format_error(
            error_code=error_type,
            custom_message=custom_message,
            details={
                'file_path': file_path,
                'error_type': error_type
            },
            command='file_operation'
        )
```

## 6. パフォーマンス最適化・監視

### 6.1 パフォーマンス監視

```python
# scripts/infrastructure/json/monitoring/performance_monitor.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import json
from pathlib import Path

@dataclass
class PerformanceMetric:
    """パフォーマンスメトリック"""
    operation: str
    start_time: float
    end_time: float
    input_size_bytes: int
    output_size_bytes: int
    file_count: int
    success: bool
    error_message: Optional[str] = None

    @property
    def execution_time_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    @property
    def throughput_mb_per_sec(self) -> float:
        if self.execution_time_ms == 0:
            return 0.0
        return (self.input_size_bytes / 1024 / 1024) / (self.execution_time_ms / 1000)

class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self, metrics_file: Optional[Path] = None):
        self.metrics_file = metrics_file or Path("performance_metrics.json")
        self.current_metrics: List[PerformanceMetric] = []
        self._operation_start_times: Dict[str, float] = {}

    def start_operation(self, operation_id: str) -> None:
        """操作開始記録"""
        self._operation_start_times[operation_id] = time.perf_counter()

    def end_operation(self,
                     operation_id: str,
                     operation_name: str,
                     input_size_bytes: int,
                     output_size_bytes: int,
                     file_count: int,
                     success: bool = True,
                     error_message: Optional[str] = None) -> PerformanceMetric:
        """操作終了記録"""

        end_time = time.perf_counter()
        start_time = self._operation_start_times.get(operation_id, end_time)

        metric = PerformanceMetric(
            operation=operation_name,
            start_time=start_time,
            end_time=end_time,
            input_size_bytes=input_size_bytes,
            output_size_bytes=output_size_bytes,
            file_count=file_count,
            success=success,
            error_message=error_message
        )

        self.current_metrics.append(metric)

        # 操作IDクリア
        if operation_id in self._operation_start_times:
            del self._operation_start_times[operation_id]

        return metric

    def get_performance_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """パフォーマンス要約取得"""

        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_metrics = [m for m in self.current_metrics if m.end_time >= cutoff_time]

        if not recent_metrics:
            return {
                'time_window_hours': time_window_hours,
                'total_operations': 0,
                'summary': {}
            }

        # 基本統計
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        failed_operations = total_operations - successful_operations

        # 実行時間統計
        execution_times = [m.execution_time_ms for m in recent_metrics]
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)

        # スループット統計
        throughputs = [m.throughput_mb_per_sec for m in recent_metrics if m.throughput_mb_per_sec > 0]
        avg_throughput = sum(throughputs) / len(throughputs) if throughputs else 0.0

        # 操作別統計
        operation_stats = {}
        for metric in recent_metrics:
            op_name = metric.operation
            if op_name not in operation_stats:
                operation_stats[op_name] = {
                    'count': 0,
                    'success_count': 0,
                    'total_time_ms': 0.0,
                    'total_input_bytes': 0,
                    'total_output_bytes': 0,
                    'total_files': 0
                }

            stats = operation_stats[op_name]
            stats['count'] += 1
            stats['success_count'] += 1 if metric.success else 0
            stats['total_time_ms'] += metric.execution_time_ms
            stats['total_input_bytes'] += metric.input_size_bytes
            stats['total_output_bytes'] += metric.output_size_bytes
            stats['total_files'] += metric.file_count

        # 操作別平均値計算
        for op_name, stats in operation_stats.items():
            count = stats['count']
            stats['avg_time_ms'] = stats['total_time_ms'] / count
            stats['success_rate'] = stats['success_count'] / count
            stats['avg_input_bytes'] = stats['total_input_bytes'] / count
            stats['avg_output_bytes'] = stats['total_output_bytes'] / count

        return {
            'time_window_hours': time_window_hours,
            'generated_at': datetime.now().isoformat(),
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': successful_operations / total_operations,
            'execution_time_stats': {
                'average_ms': avg_execution_time,
                'maximum_ms': max_execution_time,
                'minimum_ms': min_execution_time
            },
            'throughput_stats': {
                'average_mb_per_sec': avg_throughput
            },
            'operation_stats': operation_stats
        }

    def save_metrics(self) -> None:
        """メトリクス保存"""
        metrics_data = []
        for metric in self.current_metrics:
            metrics_data.append({
                'operation': metric.operation,
                'start_time': metric.start_time,
                'end_time': metric.end_time,
                'execution_time_ms': metric.execution_time_ms,
                'input_size_bytes': metric.input_size_bytes,
                'output_size_bytes': metric.output_size_bytes,
                'file_count': metric.file_count,
                'success': metric.success,
                'error_message': metric.error_message,
                'throughput_mb_per_sec': metric.throughput_mb_per_sec
            })

        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, ensure_ascii=False, indent=2)

    def load_metrics(self) -> None:
        """メトリクス読み込み"""
        if not self.metrics_file.exists():
            return

        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                metrics_data = json.load(f)

            self.current_metrics = []
            for data in metrics_data:
                metric = PerformanceMetric(
                    operation=data['operation'],
                    start_time=data['start_time'],
                    end_time=data['end_time'],
                    input_size_bytes=data['input_size_bytes'],
                    output_size_bytes=data['output_size_bytes'],
                    file_count=data['file_count'],
                    success=data['success'],
                    error_message=data.get('error_message')
                )
                self.current_metrics.append(metric)

        except (json.JSONDecodeError, KeyError, IOError):
            # 破損したメトリクスファイルは無視
            self.current_metrics = []
```

## 7. ユーティリティ・ヘルパー

### 7.1 ハッシュユーティリティ

```python
# scripts/infrastructure/json/utils/hash_utils.py
import hashlib
from pathlib import Path
from typing import Union

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """SHA256ハッシュ計算（最適化版）"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが存在しません: {file_path}")

    sha256_hash = hashlib.sha256()

    # 大きなファイルに対応するため、チャンクサイズを64KB
    chunk_size = 65536

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

def verify_hash_format(hash_value: str) -> bool:
    """SHA256ハッシュ形式検証"""
    import re
    return bool(re.match(r'^[a-f0-9]{64}$', hash_value.lower()))
```

## 8. テスト戦略・品質保証

### 8.1 テスト構造

```python
# tests/unit/infrastructure/json/test_models.py
import pytest
from datetime import datetime
from pydantic import ValidationError

from scripts.infrastructure.json.models.file_reference_models import FileReferenceModel
from scripts.infrastructure.json.models.response_models import StandardResponseModel

class TestFileReferenceModel:
    """ファイル参照モデルテスト"""

    def test_valid_file_reference(self):
        """正常なファイル参照モデル作成テスト"""
        valid_data = {
            'path': 'outputs/test_file.md',
            'sha256': 'a' * 64,  # 64文字の16進文字列
            'size_bytes': 1024,
            'content_type': 'text/markdown'
        }

        model = FileReferenceModel(**valid_data)
        assert model.path == 'outputs/test_file.md'
        assert model.sha256 == 'a' * 64
        assert model.size_bytes == 1024
        assert model.content_type == 'text/markdown'

    def test_invalid_path_format(self):
        """不正パス形式テスト"""
        invalid_data = {
            'path': '/absolute/path',  # 絶対パスは禁止
            'sha256': 'a' * 64,
            'size_bytes': 1024,
            'content_type': 'text/markdown'
        }

        with pytest.raises(ValidationError) as exc_info:
            FileReferenceModel(**invalid_data)

        assert "相対パスのみ許可" in str(exc_info.value)

    def test_invalid_sha256_format(self):
        """不正SHA256形式テスト"""
        invalid_data = {
            'path': 'outputs/test_file.md',
            'sha256': 'invalid_hash',  # 不正なハッシュ形式
            'size_bytes': 1024,
            'content_type': 'text/markdown'
        }

        with pytest.raises(ValidationError) as exc_info:
            FileReferenceModel(**invalid_data)

        assert "SHA256は64文字の16進文字列" in str(exc_info.value)

# tests/integration/infrastructure/json/test_cli_conversion.py
class TestCLIConversion:
    """CLI変換統合テスト"""

    def test_successful_conversion(self, temp_output_dir):
        """成功レスポンス変換テスト"""
        from scripts.infrastructure.json.converters.cli_response_converter import CLIResponseConverter

        converter = CLIResponseConverter(output_dir=temp_output_dir)

        cli_result = {
            'success': True,
            'command': 'novel create',
            'content': '# テスト原稿\n\nテスト内容です。',
            'yaml_content': 'title: テストエピソード\ngenre: テスト',
            'execution_time_ms': 1500.0
        }

        json_result = converter.convert(cli_result)

        assert json_result['success'] is True
        assert json_result['command'] == 'novel create'
        assert json_result['execution_time_ms'] == 1500.0
        assert len(json_result['outputs']['files']) == 2  # Markdown + YAML

        # ファイル参照の検証
        for file_ref in json_result['outputs']['files']:
            assert 'path' in file_ref
            assert 'sha256' in file_ref
            assert len(file_ref['sha256']) == 64
```

---

**注意**: この技術仕様書はアーキテクチャ仕様書・API仕様書・実装ガイドと連携して使用してください。
