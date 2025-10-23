"""
ヘキサゴナルアーキテクチャ（Port & Adapter）パターン Golden Sample
参考元: import-linter プロジェクト

このサンプルは以下の優秀な設計パターンを実装しています：
1. ポート&アダプタ パターン（ヘキサゴナル）
2. 依存性注入（DI）による疎結合
3. プラグイン可能な設定システム
4. ストラテジーパターンによる実装交換
5. 抽象基底クラス（ABC）による契約定義
6. エラーハンドリングと検証システム
7. CLI統合パターン

使用例：
    # 標準設定での実行
    processor = create_processor()
    result = processor.process_data("test.yaml")

    # テスト用の設定での実行
    test_processor = create_test_processor()
    result = test_processor.process_data("mock_data")
"""

import abc
from enum import Enum
from typing import Any

import click

# ========================================
# Domain Layer (ドメイン層)
# ========================================

class ProcessingError(Exception):
    """処理エラーの基底クラス"""


class ValidationError(ProcessingError):
    """検証エラー"""
    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__(str(errors))


class DataFormat(Enum):
    """サポートするデータ形式"""
    YAML = "yaml"
    JSON = "json"
    INI = "ini"


class ProcessResult:
    """処理結果を表現するドメインオブジェクト"""
    def __init__(self, success: bool, data: dict[str, Any], warnings: list[str] = None):
        self.success = success
        self.data = data
        self.warnings = warnings or []
        self.metadata = {}

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value


# ========================================
# Port Interfaces (ポート インターフェース)
# ========================================

class DataReader(abc.ABC):
    """データ読み込み用ポート"""

    @abc.abstractmethod
    def read_data(self, source: str) -> dict[str, Any]:
        """データを読み込む

        Args:
            source: データソース（ファイルパス、URL等）

        Returns:
            読み込んだデータ辞書

        Raises:
            ProcessingError: 読み込みに失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    def can_handle(self, source: str) -> bool:
        """このリーダーが指定されたソースを処理できるかどうか

        Args:
            source: データソース

        Returns:
            処理可能な場合True
        """
        raise NotImplementedError


class DataValidator(abc.ABC):
    """データ検証用ポート"""

    @abc.abstractmethod
    def validate(self, data: dict[str, Any]) -> list[str]:
        """データを検証し、エラーメッセージのリストを返す

        Args:
            data: 検証対象のデータ

        Returns:
            エラーメッセージのリスト（エラーがない場合は空リスト）
        """
        raise NotImplementedError


class OutputWriter(abc.ABC):
    """出力用ポート"""

    @abc.abstractmethod
    def write_result(self, result: ProcessResult) -> None:
        """処理結果を出力する

        Args:
            result: 出力する処理結果
        """
        raise NotImplementedError

    @abc.abstractmethod
    def write_error(self, error: str) -> None:
        """エラーメッセージを出力する

        Args:
            error: エラーメッセージ
        """
        raise NotImplementedError


class ProcessingTimer(abc.ABC):
    """処理時間計測用ポート"""

    @abc.abstractmethod
    def __enter__(self) -> "ProcessingTimer":
        """コンテキストマネージャの開始"""
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャの終了"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_duration_ms(self) -> int:
        """経過時間をミリ秒で取得"""
        raise NotImplementedError


# ========================================
# Application Service Layer (アプリケーションサービス層)
# ========================================

class DataProcessorConfig:
    """データ処理器の設定クラス"""

    def __init__(self):
        self._config = {}

    def configure(self, **config_dict: Any) -> None:
        """設定を更新

        Args:
            **config_dict: 設定項目
        """
        self._config.update(config_dict)

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return super().__getattribute__(name)
        try:
            return self._config[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def copy(self) -> "DataProcessorConfig":
        """設定のコピーを作成"""
        new_config = self.__class__()
        new_config.configure(**self._config)
        return new_config


# グローバル設定インスタンス
settings = DataProcessorConfig()


class DataProcessor:
    """メインのデータ処理アプリケーションサービス"""

    def __init__(self, config: DataProcessorConfig = None):
        self.config = config or settings

    def process_data(self, source: str, validate_only: bool = False) -> ProcessResult:
        """データを処理する

        Args:
            source: データソース
            validate_only: 検証のみ実行するかどうか

        Returns:
            処理結果

        Raises:
            ProcessingError: 処理に失敗した場合
        """
        # 適切なリーダーを選択
        reader = self._get_appropriate_reader(source)
        if not reader:
            raise ProcessingError(f"No suitable reader found for source: {source}")

        # タイマー開始
        with self.config.TIMER as timer:
            # データ読み込み
            try:
                raw_data = reader.read_data(source)
            except Exception as e:
                raise ProcessingError(f"Failed to read data: {e}")

        # 処理結果の初期化
        result = ProcessResult(success=True, data=raw_data)
        result.add_metadata("read_duration_ms", timer.get_duration_ms())

        # データ検証
        validation_errors = []
        for validator in self._get_validators():
            errors = validator.validate(raw_data)
            validation_errors.extend(errors)

        if validation_errors:
            if self._is_strict_mode():
                raise ValidationError({f"validation_{i}": error for i, error in enumerate(validation_errors)})
            for error in validation_errors:
                result.add_warning(error)

        # 検証のみの場合はここで終了
        if validate_only:
            return result

        # データ変換処理
        try:
            processed_data = self._transform_data(raw_data)
            result.data = processed_data
        except Exception as e:
            result.success = False
            raise ProcessingError(f"Data transformation failed: {e}")

        return result

    def _get_appropriate_reader(self, source: str) -> DataReader | None:
        """適切なリーダーを取得"""
        readers = self.config.get("DATA_READERS", {})
        for reader in readers.values():
            if reader.can_handle(source):
                return reader
        return None

    def _get_validators(self) -> list[DataValidator]:
        """設定されたバリデーターのリストを取得"""
        return list(self.config.get("VALIDATORS", {}).values())

    def _is_strict_mode(self) -> bool:
        """厳密モードかどうか"""
        return self.config.get("STRICT_MODE", False)

    def _transform_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """データ変換処理（拡張ポイント）"""
        transformer = self.config.get("DATA_TRANSFORMER")
        if transformer:
            return transformer.transform(data)
        return data


# ========================================
# Adapter Layer (アダプター層)
# ========================================

import json
import time
from configparser import ConfigParser

import yaml


class SystemTimer(ProcessingTimer):
    """システムタイマーアダプター"""

    def __init__(self):
        self._start_time = None
        self._duration_ms = 0

    def __enter__(self) -> "SystemTimer":
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._start_time:
            self._duration_ms = int((time.time() - self._start_time) * 1000)

    def get_duration_ms(self) -> int:
        return self._duration_ms


class YamlDataReader(DataReader):
    """YAMLファイル読み込みアダプター"""

    def read_data(self, source: str) -> dict[str, Any]:
        try:
            with open(source, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ProcessingError(f"File not found: {source}")
        except yaml.YAMLError as e:
            raise ProcessingError(f"Invalid YAML format: {e}")

    def can_handle(self, source: str) -> bool:
        return source.endswith((".yaml", ".yml"))


class JsonDataReader(DataReader):
    """JSONファイル読み込みアダプター"""

    def read_data(self, source: str) -> dict[str, Any]:
        try:
            with open(source, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise ProcessingError(f"File not found: {source}")
        except json.JSONDecodeError as e:
            raise ProcessingError(f"Invalid JSON format: {e}")

    def can_handle(self, source: str) -> bool:
        return source.endswith(".json")


class IniDataReader(DataReader):
    """INIファイル読み込みアダプター"""

    def read_data(self, source: str) -> dict[str, Any]:
        try:
            config = ConfigParser()
            config.read(source, encoding="utf-8")
            return {section: dict(config.items(section)) for section in config.sections()}
        except FileNotFoundError:
            raise ProcessingError(f"File not found: {source}")
        except Exception as e:
            raise ProcessingError(f"Invalid INI format: {e}")

    def can_handle(self, source: str) -> bool:
        return source.endswith(".ini")


class BasicDataValidator(DataValidator):
    """基本的なデータバリデーター"""

    def __init__(self, required_fields: list[str] = None):
        self.required_fields = required_fields or []

    def validate(self, data: dict[str, Any]) -> list[str]:
        errors = []

        # 必須フィールドチェック
        for field in self.required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")

        # データ型チェック
        if not isinstance(data, dict):
            errors.append("Data must be a dictionary")

        return errors


class ConsoleOutputWriter(OutputWriter):
    """コンソール出力アダプター"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def write_result(self, result: ProcessResult) -> None:
        if result.success:
            click.echo("✓ Processing completed successfully")
            if self.verbose:
                click.echo(f"Data: {result.data}")
                if result.metadata:
                    click.echo(f"Metadata: {result.metadata}")
        else:
            click.echo("✗ Processing failed")

        # 警告の表示
        for warning in result.warnings:
            click.echo(f"Warning: {warning}", err=True)

    def write_error(self, error: str) -> None:
        click.echo(f"Error: {error}", err=True)


# テスト用のフェイクアダプター

class FakeDataReader(DataReader):
    """テスト用のフェイクデータリーダー"""

    def __init__(self):
        self._injected_data = {}

    def inject_data(self, data: dict[str, Any]) -> None:
        """テスト用にデータを注入"""
        self._injected_data = data

    def read_data(self, source: str) -> dict[str, Any]:
        return self._injected_data.copy()

    def can_handle(self, source: str) -> bool:
        return True


class FakeTimer(ProcessingTimer):
    """テスト用のフェイクタイマー"""

    def __init__(self, mock_duration: int = 100):
        self.mock_duration = mock_duration

    def __enter__(self) -> "FakeTimer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def get_duration_ms(self) -> int:
        return self.mock_duration


# ========================================
# Configuration (設定システム)
# ========================================

def configure_production():
    """本番環境用の設定"""
    settings.configure(
        DATA_READERS={
            "yaml": YamlDataReader(),
            "json": JsonDataReader(),
            "ini": IniDataReader(),
        },
        VALIDATORS={
            "basic": BasicDataValidator(required_fields=["name", "type"]),
        },
        TIMER=SystemTimer(),
        OUTPUT_WRITER=ConsoleOutputWriter(verbose=False),
        STRICT_MODE=True,
    )


def configure_test():
    """テスト環境用の設定"""
    fake_reader = FakeDataReader()
    fake_reader.inject_data({"name": "test", "type": "mock", "data": [1, 2, 3]})

    settings.configure(
        DATA_READERS={
            "fake": fake_reader,
        },
        VALIDATORS={
            "basic": BasicDataValidator(required_fields=["name"]),
        },
        TIMER=FakeTimer(mock_duration=50),
        OUTPUT_WRITER=ConsoleOutputWriter(verbose=True),
        STRICT_MODE=False,
    )


# ========================================
# Factory Functions (ファクトリー関数)
# ========================================

def create_processor() -> DataProcessor:
    """本番用のデータプロセッサーを作成"""
    configure_production()
    return DataProcessor()


def create_test_processor() -> DataProcessor:
    """テスト用のデータプロセッサーを作成"""
    configure_test()
    return DataProcessor()


def create_custom_processor(custom_settings: DataProcessorConfig) -> DataProcessor:
    """カスタム設定でデータプロセッサーを作成"""
    return DataProcessor(custom_settings)


# ========================================
# CLI Integration (CLI統合)
# ========================================

@click.group()
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--config", default=None, help="Configuration file")
@click.pass_context
def cli(ctx, verbose, config):
    """ヘキサゴナルアーキテクチャのサンプルCLI"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config


@cli.command()
@click.argument("source")
@click.option("--validate-only", is_flag=True, help="Only validate, do not process")
@click.pass_context
def process(ctx, source, validate_only):
    """データを処理する"""
    try:
        processor = create_processor()
        result = processor.process_data(source, validate_only=validate_only)

        output_writer = settings.OUTPUT_WRITER
        output_writer.write_result(result)

        if not result.success:
            ctx.exit(1)

    except ProcessingError as e:
        settings.OUTPUT_WRITER.write_error(str(e))
        ctx.exit(1)


@cli.command()
def test():
    """テスト用の処理を実行"""
    try:
        processor = create_test_processor()
        result = processor.process_data("mock_source")

        output_writer = settings.OUTPUT_WRITER
        output_writer.write_result(result)

    except ProcessingError as e:
        click.echo(f"Test failed: {e}", err=True)


# ========================================
# Usage Examples (使用例)
# ========================================

def main():
    """メイン関数 - 使用例"""

    # 例1: 基本的な使用
    print("=== Example 1: Basic Usage ===")
    try:
        processor = create_processor()
        # 実際のファイルがある場合の処理例
        # result = processor.process_data("config.yaml")
        print("Processor created successfully")
    except Exception as e:
        print(f"Error: {e}")

    # 例2: テスト設定での使用
    print("\n=== Example 2: Test Configuration ===")
    try:
        test_processor = create_test_processor()
        result = test_processor.process_data("mock_source")
        print(f"Test processing result: Success={result.success}")
        print(f"Data: {result.data}")
        print(f"Warnings: {result.warnings}")
        print(f"Metadata: {result.metadata}")
    except Exception as e:
        print(f"Error: {e}")

    # 例3: カスタム設定での使用
    print("\n=== Example 3: Custom Configuration ===")
    try:
        custom_config = DataProcessorConfig()
        fake_reader = FakeDataReader()
        fake_reader.inject_data({"custom": "data", "name": "custom_test"})

        custom_config.configure(
            DATA_READERS={"custom": fake_reader},
            VALIDATORS={"custom": BasicDataValidator(required_fields=["custom"])},
            TIMER=FakeTimer(mock_duration=25),
            OUTPUT_WRITER=ConsoleOutputWriter(verbose=True),
            STRICT_MODE=False,
        )

        custom_processor = create_custom_processor(custom_config)
        result = custom_processor.process_data("custom_source")
        print(f"Custom processing result: Success={result.success}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # コマンドライン引数がある場合はCLIを実行、そうでなければ使用例を実行
    import sys
    if len(sys.argv) > 1:
        cli()
    else:
        main()
