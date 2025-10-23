#!/usr/bin/env python3
"""JSON変換基底クラス"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, TypeVar

import jsonschema
from pydantic import ValidationError

from noveler.infrastructure.json.models.base_models import BaseJSONModel

T = TypeVar("T", bound=BaseJSONModel)


class BaseConverter(ABC):
    """JSON変換基底クラス"""

    def __init__(self, schema_dir: Path | None = None, output_dir: Path | None = None, validate_schema: bool = True) -> None:
        self.schema_dir = schema_dir or Path("schemas/json")
        self.output_dir = output_dir or Path("outputs")
        self.validate_schema = validate_schema
        self._schema_cache: dict[str, dict] = {}

        # ディレクトリ確保
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_schema(self, schema_name: str) -> dict[str, Any]:
        """JSONスキーマロード・キャッシュ"""
        if schema_name not in self._schema_cache:
            schema_path = self.schema_dir / f"{schema_name}.json"
            if not schema_path.exists():
                msg = f"スキーマファイル未発見: {schema_path}"
                raise FileNotFoundError(msg)

            with schema_path.open(encoding="utf-8") as f:
                self._schema_cache[schema_name] = json.load(f)

        return self._schema_cache[schema_name]

    def validate_with_schema(self, data: dict[str, Any], schema_name: str) -> None:
        """JSONスキーマバリデーション"""
        if not self.validate_schema:
            return

        try:
            schema = self.load_schema(schema_name)
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            msg = f"スキーマ検証エラー: {e.message}"
            raise ValueError(msg)

    def validate_with_pydantic(self, data: dict[str, Any], model_class: type[T]) -> T:
        """Pydanticバリデーション"""
        try:
            return model_class(**data)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                error_details.append(f"{field}: {error['msg']}")

            msg = f"Pydantic検証エラー: {'; '.join(error_details)}"
            raise ValueError(msg)

    @abstractmethod
    def convert(self, input_data: Any) -> dict[str, Any]:
        """変換実行（抽象メソッド）"""

    def measure_execution_time(self, func):
        """実行時間計測デコレーター"""

        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            if isinstance(result, dict):
                result["execution_time_ms"] = result.get("execution_time_ms", 0) + execution_time_ms

            return result

        return wrapper
