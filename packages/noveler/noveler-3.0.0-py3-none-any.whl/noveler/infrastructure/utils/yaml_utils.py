"""Infrastructure.utils.yaml_utils
Where: Infrastructure utility module for YAML manipulation.
What: Provides helpers to read, write, and validate YAML documents.
Why: Ensures YAML handling is consistent across infrastructure components.
"""

from datetime import date, datetime

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

"""YAML操作の共通ユーティリティ"""
import io
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.exceptions import FileSystemException, YAMLParseException

# B20/B30品質作業指示書準拠: Console重複作成回避必須
from noveler.presentation.shared.shared_utilities import console

# パフォーマンス監視インポート（フォールバック付き）
try:
    from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor
except ImportError:

    def performance_monitor(name: str):
        """パフォーマンス監視デコレータ（フォールバック）"""

        def decorator(func):
            return func

        return decorator


# オプション: ruamel.yaml + yamllintによる高度な整形機能
try:
    from noveler.domain.value_objects.project_time import project_now
    from noveler.infrastructure.utils.yaml_formatter import YAMLFormatter
    HAS_FORMATTER = True
except ImportError:
    from noveler.domain.value_objects.project_time import project_now
    HAS_FORMATTER = False


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YAMLHandler:
    """YAML読み書きの統一インターフェース"""

    @staticmethod
    @performance_monitor("YAMLHandler.load_yaml")
    def load_yaml(file_path: Path) -> dict[str, Any]:
        """YAMLファイルを読み込む

        Args:
            file_path: YAMLファイルのパス

        Returns:
            Dict[str, Any]: 読み込んだデータ

        Raises:
            FileSystemException: ファイルが存在しない場合
            YAMLParseException: YAML解析エラーの場合
        """
        if not file_path.exists():
            msg = f"YAMLファイルが存在しません: {file_path}"
            raise FileSystemException(msg)

        try:
            with Path(file_path).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except yaml.YAMLError as e:
            msg = f"YAML解析エラー: {file_path}"
            raise YAMLParseException(
                msg,
                cause=e,
            )

        except Exception as e:
            msg = f"ファイル読み込みエラー: {file_path}"
            raise FileSystemException(
                msg,
                cause=e,
            )

    @staticmethod
    @performance_monitor("YAMLHandler.save_yaml")
    def save_yaml(
        file_path: Path, data: dict[str, Any], create_backup: bool = False, use_formatter: bool = False
    ) -> None:
        """YAMLファイルに保存する

        Args:
            file_path: 保存先のパス
            data: 保存するデータ
            create_backup: バックアップを作成するか
            use_formatter: ruamel.yaml + yamllintによる整形を使用するか

        Raises:
            FileSystemException: ファイル書き込みエラーの場合
        """
        # フォーマッターが利用可能で、使用が指定されている場合
        if use_formatter and HAS_FORMATTER:
            try:
                formatter = YAMLFormatter()
                success, messages = formatter.save_yaml(file_path, data, backup=create_backup)
                if not success:
                    msg = f"YAML整形エラー: {messages}"
                    raise FileSystemException(msg)
                return
            except Exception:
                # フォーマッターが利用できない場合やエラー時は通常の処理にフォールバック
                pass

        # 通常のYAML保存処理
        try:
            # バックアップ作成
            if create_backup and file_path.exists():
                backup_path = file_path.with_suffix(f".yaml.bak.{project_now().datetime.strftime('%Y%m%d_%H%M%S')}")
                file_path.rename(backup_path)

            # 親ディレクトリを作成
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # YAML保存
            with Path(file_path).open("w", encoding="utf-8") as f:
                # カスタムDumper作成
                class CustomDumper(yaml.SafeDumper):
                    pass

                # カスタムリプレゼンター登録
                CustomDumper.add_representer(datetime, YAMLHandler._yaml_representer)
                CustomDumper.add_representer(date, YAMLHandler._yaml_representer)
                CustomDumper.add_representer(YAMLMultilineString, yaml_multiline_representer)

                yaml.dump(
                    data,
                    f,
                    Dumper=CustomDumper,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )

        except Exception as e:
            msg = f"ファイル書き込みエラー: {file_path}"
            raise FileSystemException(
                msg,
                cause=e,
            )

    @staticmethod
    def load_or_create(file_path: Path, default_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """YAMLファイルを読み込む。存在しない場合はデフォルトデータを返す

        Args:
            file_path: YAMLファイルのパス
            default_data: ファイルが存在しない場合のデフォルトデータ

        Returns:
            Dict[str, Any]: 読み込んだまたはデフォルトのデータ
        """
        if file_path.exists():
            return YAMLHandler.load_yaml(file_path)
        return default_data or {}

    @staticmethod
    def _yaml_representer(dumper: object, data: object) -> object:
        """datetime/dateオブジェクトのYAML表現をカスタマイズ"""
        # isinstance に tuple を使用して UnionType による TypeError を回避
        if isinstance(data, (datetime, date)):
            return dumper.represent_str(data.isoformat())
        return dumper.represent_data(data)

    @staticmethod
    def validate_yaml_file(file_path: Path) -> tuple[bool, list[str]]:
        """YAMLファイルを検証

        Args:
            file_path: 検証するファイルのパス

        Returns:
            (有効か, メッセージのリスト)
        """
        if HAS_FORMATTER:
            formatter = YAMLFormatter()
            return formatter.validate_yaml_file(file_path)
        # 基本的な検証のみ
        try:
            YAMLHandler.load_yaml(file_path)
            return True, ["YAMLファイルは有効です"]
        except Exception as e:
            return False, [f"YAMLエラー: {e}"]

    @staticmethod
    def check_syntax(file_path: Path) -> dict[str, bool | str | list[str]]:
        """YAML構文チェック(レガシーutils/check_yaml_syntax.py統合)

        Args:
            file_path: チェック対象のYAMLファイルパス

        Returns:
            チェック結果(valid, error_message, warnings)
        """
        if not file_path.exists():
            return {"valid": False, "error_message": f"ファイルが存在しません: {file_path}", "warnings": []}

        try:
            # Path.open を正しく使用
            with file_path.open(encoding="utf-8") as f:
                content = f.read()

            # YAML構文チェック
            yaml.safe_load(content)

            return {"valid": True, "error_message": "", "warnings": YAMLHandler._check_warnings(content)}

        except yaml.YAMLError as e:
            return {"valid": False, "error_message": f"YAML構文エラー: {e!s}", "warnings": []}
        except Exception as e:
            return {"valid": False, "error_message": f"ファイル読み込みエラー: {e!s}", "warnings": []}

    @staticmethod
    def check_syntax_content(content: str) -> dict[str, bool | str | list[str]]:
        """YAML文字列の構文チェック

        Args:
            content: チェック対象のYAML文字列

        Returns:
            チェック結果
        """
        try:
            yaml.safe_load(content)

            return {"valid": True, "error_message": "", "warnings": YAMLHandler._check_warnings(content)}

        except yaml.YAMLError as e:
            return {"valid": False, "error_message": f"YAML構文エラー: {e!s}", "warnings": []}

    @staticmethod
    def _check_warnings(content: str) -> list[str]:
        """YAML警告チェック

        Args:
            content: YAML内容

        Returns:
            警告メッセージのリスト
        """
        warnings = []

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # タブ文字の使用を警告
            if "\t" in line:
                warnings.append(f"行{i}: タブ文字が使用されています(スペースを推奨)")

            # 行末の空白を警告
            if line.endswith((" ", "\t")):
                warnings.append(f"行{i}: 行末に空白文字があります")

        return warnings

    @staticmethod
    def batch_check_syntax(directory: Path, pattern: str = "*.yaml") -> dict[str, dict]:
        """ディレクトリ内の複数YAMLファイルを一括構文チェック

        Args:
            directory: チェック対象ディレクトリ
            pattern: ファイルパターン

        Returns:
            ファイルパスをキーとしたチェック結果
        """
        results: dict[str, Any] = {}

        if not directory.exists():
            return {"error": f"ディレクトリが存在しません: {directory}"}

        yaml_files = list(directory.glob(pattern))
        yaml_files.extend(list(directory.glob("*.yml")))

        for yaml_file in yaml_files:
            results[str(yaml_file)] = YAMLHandler.check_syntax(yaml_file)

        return results


class UnifiedYAMLService:
    """統合YAML生成・バリデーションサービス

    プロジェクト全体のYAML操作を共通基盤化し、
    一貫したフォーマット・バリデーション・エラーハンドリングを提供
    """

    # 標準化パラメータセット
    STANDARD_DUMP_PARAMS = {
        "default": {
            "default_flow_style": False,
            "allow_unicode": True,
            "sort_keys": False,
        },
        "formatted": {
            "default_flow_style": False,
            "allow_unicode": True,
            "sort_keys": False,
            "indent": 2,
        },
        "compact": {
            "default_flow_style": False,
            "allow_unicode": True,
            "sort_keys": False,
            "width": 120,
        },
        "plot": {  # プロット生成専用
            "default_flow_style": False,
            "allow_unicode": True,
            "sort_keys": False,
            "indent": 2,
            "width": float("inf"),  # 長いテキスト対応
        },
    }

    def __init__(self, enable_validation: bool = True, enable_backup: bool = False, logger_service=None, console_service=None) -> None:
        """統合YAMLサービス初期化

        Args:
            enable_validation: バリデーション機能の有効化
            enable_backup: バックアップ機能の有効化
        """
        self.enable_validation = enable_validation
        self.enable_backup = enable_backup
        self._formatter = None

        # フォーマッター初期化（利用可能な場合）
        if enable_validation and HAS_FORMATTER:
            try:
                self._formatter = YAMLFormatter()
            except ImportError:
                self.console_service.print("YAMLFormatter not available, using basic validation")

    @performance_monitor("UnifiedYAMLService.generate_with_validation")
    def generate_with_validation(
        self,
        data: dict[str, Any],
        output_path: Path,
        format_type: str = "default",
        validate_before: bool | None = None,
        validate_after: bool | None = None,
        create_backup: bool | None = None,
    ) -> tuple[bool, list[str]]:
        """統合YAML生成（バリデーション付き）

        Args:
            data: 出力するデータ
            output_path: 出力先パス
            format_type: フォーマットタイプ ('default', 'formatted', 'compact', 'plot')
            validate_before: 生成前バリデーション (None=設定に従う)
            validate_after: 生成後バリデーション (None=設定に従う)
            create_backup: バックアップ作成 (None=設定に従う)

        Returns:
            (成功フラグ, メッセージリスト)
        """
        messages: list[Any] = []

        # パラメータデフォルト値設定
        validate_before = validate_before if validate_before is not None else self.enable_validation
        validate_after = validate_after if validate_after is not None else self.enable_validation
        create_backup = create_backup if create_backup is not None else self.enable_backup

        try:
            # 1. 生成前データバリデーション
            if validate_before:
                is_valid, validation_msgs = self._validate_data_structure(data)
                if not is_valid:
                    messages.extend([f"生成前バリデーションエラー: {msg}" for msg in validation_msgs])
                    return False, messages
                messages.extend([f"生成前バリデーション: {msg}" for msg in validation_msgs])

            # 2. 標準化されたYAML生成
            success, generation_msgs = self._generate_yaml_with_standard_params(
                data, output_path, format_type, create_backup
            )

            messages.extend(generation_msgs)

            if not success:
                return False, messages

            # 3. 生成後ファイルバリデーション
            if validate_after:
                is_valid, validation_msgs = self._validate_generated_file(output_path)
                if not is_valid:
                    messages.extend([f"生成後バリデーションエラー: {msg}" for msg in validation_msgs])
                    return False, messages
                messages.extend([f"生成後バリデーション: {msg}" for msg in validation_msgs])

            return True, messages

        except Exception as e:
            error_msg = f"統合YAML生成エラー: {e}"
            messages.append(error_msg)
            return False, messages

    @performance_monitor("UnifiedYAMLService.generate_string_with_validation")
    def generate_string_with_validation(
        self, data: dict[str, Any], format_type: str = "default", validate_data: bool | None = None
    ) -> tuple[str | None, list[str]]:
        """統合YAML文字列生成（バリデーション付き）

        Args:
            data: 出力するデータ
            format_type: フォーマットタイプ
            validate_data: データバリデーション実行

        Returns:
            (YAML文字列 | None, メッセージリスト)
        """
        messages: list[Any] = []
        validate_data: dict[str, Any] = validate_data if validate_data is not None else self.enable_validation

        try:
            # データバリデーション
            if validate_data:
                is_valid, validation_msgs = self._validate_data_structure(data)
                if not is_valid:
                    messages.extend([f"データバリデーションエラー: {msg}" for msg in validation_msgs])
                    return None, messages
                messages.extend([f"データバリデーション: {msg}" for msg in validation_msgs])

            # YAML文字列生成
            yaml_content = self._generate_yaml_string(data, format_type)

            # 生成された文字列のバリデーション
            if validate_data and self._formatter:
                is_valid, validation_msgs = self._formatter.validate_yaml_string(yaml_content)
                if not is_valid:
                    messages.extend([f"YAML文字列バリデーションエラー: {msg}" for msg in validation_msgs])
                    return None, messages
                messages.extend([f"YAML文字列バリデーション: {msg}" for msg in validation_msgs])

            return yaml_content, messages

        except Exception as e:
            error_msg = f"統合YAML文字列生成エラー: {e}"
            messages.append(error_msg)
            return None, messages

    def migrate_legacy_dump(
        self, data: dict[str, Any], output_path: Path, legacy_params: dict[str, Any] | None = None
    ) -> tuple[bool, list[str]]:
        """レガシーyaml.dump呼び出しの互換移行

        Args:
            data: 出力データ
            output_path: 出力先
            legacy_params: 従来のdumpパラメータ（マイグレーション分析用）

        Returns:
            (成功フラグ, メッセージリスト)
        """
        messages: list[Any] = []

        # レガシーパラメータから最適なフォーマットタイプを推定
        format_type = self._infer_format_type_from_legacy(legacy_params or {})
        messages.append(f"レガシーパラメータから推定されたフォーマット: {format_type}")

        # 統合サービス経由で生成
        return self.generate_with_validation(data, output_path, format_type)

    def get_format_info(self, format_type: str | None = None) -> dict[str, Any]:
        """フォーマット情報取得

        Args:
            format_type: 特定フォーマット（None=全フォーマット）

        Returns:
            フォーマット情報辞書
        """
        if format_type:
            return {
                "type": format_type,
                "params": self.STANDARD_DUMP_PARAMS.get(format_type, {}),
                "available": format_type in self.STANDARD_DUMP_PARAMS,
            }

        return {
            "available_formats": list(self.STANDARD_DUMP_PARAMS.keys()),
            "default_format": "default",
            "validation_enabled": self.enable_validation,
            "formatter_available": self._formatter is not None,
        }

    def _generate_yaml_with_standard_params(
        self, data: dict[str, Any], output_path: Path, format_type: str, create_backup: bool
    ) -> tuple[bool, list[str]]:
        """標準パラメータでYAML生成"""
        messages: list[Any] = []

        try:
            # フォーマットタイプ検証
            if format_type not in self.STANDARD_DUMP_PARAMS:
                messages.append(f"不明なフォーマットタイプ: {format_type}、defaultを使用")
                format_type = "default"

            # バックアップ作成
            if create_backup and output_path.exists():
                backup_path = output_path.with_suffix(f".yaml.bak.{project_now().datetime.strftime('%Y%m%d_%H%M%S')}")

                output_path.rename(backup_path)
                messages.append(f"バックアップ作成: {backup_path}")

            # ディレクトリ作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 標準パラメータ取得
            dump_params = self.STANDARD_DUMP_PARAMS[format_type].copy()

            # YAML生成・保存
            # Path.open を正しく使用
            with output_path.open("w", encoding="utf-8") as f:
                # カスタムDumper設定
                class StandardDumper(yaml.SafeDumper):
                    pass

                # カスタムリプレゼンター登録
                StandardDumper.add_representer(datetime, YAMLHandler._yaml_representer)
                StandardDumper.add_representer(date, YAMLHandler._yaml_representer)
                StandardDumper.add_representer(YAMLMultilineString, yaml_multiline_representer)

                yaml.dump(data, f, Dumper=StandardDumper, **dump_params)

            messages.append(f"YAML生成完了: {output_path} (フォーマット: {format_type})")
            return True, messages

        except Exception as e:
            messages.append(f"YAML生成エラー: {e}")
            return False, messages

    def _generate_yaml_string(self, data: dict[str, Any], format_type: str) -> str:
        """標準パラメータでYAML文字列生成"""

        # フォーマットタイプ検証・修正
        if format_type not in self.STANDARD_DUMP_PARAMS:
            format_type = "default"

        # 標準パラメータ取得
        dump_params = self.STANDARD_DUMP_PARAMS[format_type].copy()

        # 文字列生成
        output = io.StringIO()

        # カスタムDumper設定
        class StandardDumper(yaml.SafeDumper):
            pass

        # カスタムリプレゼンター登録
        StandardDumper.add_representer(datetime, YAMLHandler._yaml_representer)
        StandardDumper.add_representer(date, YAMLHandler._yaml_representer)
        StandardDumper.add_representer(YAMLMultilineString, yaml_multiline_representer)

        yaml.dump(data, output, Dumper=StandardDumper, **dump_params)
        return output.getvalue()

    def _validate_data_structure(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """データ構造バリデーション"""
        messages: list[Any] = []

        # 基本的な構造チェック
        if not isinstance(data, dict):
            return False, ["データは辞書型である必要があります"]

        # データサイズチェック（循環安全・深さ制限付き）
        def approx_size(obj: Any, seen: set[int] | None = None, depth: int = 0, max_depth: int = 6) -> int:
            if seen is None:
                seen = set()
            oid = id(obj)
            if oid in seen:
                return 0
            seen.add(oid)
            try:
                size = sys.getsizeof(obj)
            except Exception:
                size = 0
            if depth >= max_depth:
                return size
            # 再帰的に大枠だけ概算
            if isinstance(obj, dict):
                for k, v in obj.items():
                    size += approx_size(k, seen, depth + 1, max_depth)
                    size += approx_size(v, seen, depth + 1, max_depth)
            elif isinstance(obj, (list, tuple, set)):
                for item in obj:
                    size += approx_size(item, seen, depth + 1, max_depth)
            return size

        data_size = approx_size(data)
        if data_size > 10 * 1024 * 1024:  # 10MB制限（概算）
            messages.append(f"警告: データサイズが大きいです (概算 {data_size / 1024 / 1024:.1f}MB)")

        # 循環参照チェック（安全版）
        def has_cycle(obj: Any, seen: set[int] | None = None, stack: set[int] | None = None) -> bool:
            if seen is None:
                seen = set()
            if stack is None:
                stack = set()
            oid = id(obj)
            if oid in stack:
                return True
            if oid in seen:
                return False
            seen.add(oid)
            stack.add(oid)
            try:
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if has_cycle(k, seen, stack) or has_cycle(v, seen, stack):
                            return True
                elif isinstance(obj, (list, tuple, set)):
                    for item in obj:
                        if has_cycle(item, seen, stack):
                            return True
                return False
            finally:
                stack.discard(oid)

        if has_cycle(data):
            return False, ["データに循環参照が含まれています"]

        messages.append("データ構造バリデーション成功")
        return True, messages

    def _validate_generated_file(self, file_path: Path) -> tuple[bool, list[str]]:
        """生成されたファイルのバリデーション"""
        if self._formatter:
            return self._formatter.validate_yaml_file(file_path)

        # 基本的なバリデーション
        try:
            YAMLHandler.load_yaml(file_path)
            return True, ["基本バリデーション成功"]
        except Exception as e:
            return False, [f"基本バリデーションエラー: {e}"]

    def _infer_format_type_from_legacy(self, legacy_params: dict[str, Any]) -> str:
        """レガシーパラメータからフォーマットタイプを推定"""
        # indent付き = formatted
        if legacy_params.get("indent"):
            return "formatted"

        # widthが設定されている = compact
        if "width" in legacy_params:
            return "compact"

        # プロット系の判定（ファイル名やデータ内容から推定可能）
        # ここでは基本的にdefaultを返す
        return "default"


# 統合サービスのファクトリー関数
def get_unified_yaml_service(enable_validation: bool = True, enable_backup: bool = False) -> UnifiedYAMLService:
    """統合YAMLサービスのインスタンス取得

    Args:
        enable_validation: バリデーション機能有効化
        enable_backup: バックアップ機能有効化

    Returns:
        UnifiedYAMLService: 設定済み統合サービス
    """
    return UnifiedYAMLService(enable_validation=enable_validation, enable_backup=enable_backup)


# 統合テスト用のユーティリティ関数
def test_unified_yaml_service() -> dict[str, Any]:
    """統合YAMLサービスの動作テスト

    Returns:
        テスト結果辞書
    """
    results: dict[str, Any] = {
        "service_creation": False,
        "validation_enabled": False,
        "format_types": [],
        "generation_test": False,
        "validation_test": False,
        "error_handling_test": False,
        "errors": [],
    }

    try:
        # サービス作成テスト
        service = get_unified_yaml_service(enable_validation=True)
        results["service_creation"] = True
        results["validation_enabled"] = service.enable_validation

        # フォーマットタイプテスト
        format_info = service.get_format_info()
        results["format_types"] = format_info["available_formats"]

        # YAML文字列生成テスト
        test_data: dict[str, Any] = {
            "test": True,
            "message": "UnifiedYAMLService動作テスト",
            "timestamp": project_now().datetime.isoformat(),
            "formats": format_info["available_formats"],
        }

        yaml_content, messages = service.generate_string_with_validation(test_data, format_type="formatted")

        if yaml_content:
            results["generation_test"] = True

            # バリデーションテスト
            if messages and any("バリデーション" in msg for msg in messages):
                results["validation_test"] = True

        # エラーハンドリングテスト（無効なフォーマットタイプ）
        try:
            invalid_content, error_messages = service.generate_string_with_validation(
                test_data, format_type="invalid_format"
            )

            if error_messages or invalid_content:
                results["error_handling_test"] = True
        except Exception:
            results["error_handling_test"] = True

    except Exception as e:
        results["errors"].append(f"統合テストエラー: {e}")

    return results


def benchmark_yaml_generation(iterations: int = 100) -> dict[str, float]:
    """YAML生成パフォーマンスベンチマーク

    Args:
        iterations: ベンチマーク反復数

    Returns:
        パフォーマンス結果辞書
    """


    # テストデータ準備
    test_data: dict[str, Any] = {
        "benchmark": True,
        "iteration_count": iterations,
        "test_data": {f"key_{i}": f"value_{i}" for i in range(50)},
        "nested_data": {"level1": {"level2": {"level3": ["item1", "item2", "item3"] * 10}}},
    }

    results: dict[str, Any] = {}

    try:
        # 統合YAMLサービス ベンチマーク
        service = get_unified_yaml_service(enable_validation=True)

        start_time = time.perf_counter()
        for _ in range(iterations):
            yaml_content, _ = service.generate_string_with_validation(test_data, format_type="default")

        unified_time = time.perf_counter() - start_time
        results["unified_service_time"] = unified_time

        # 従来のyaml.dump ベンチマーク
        start_time = time.perf_counter()
        for _ in range(iterations):

            output = io.StringIO()
            yaml.dump(test_data, output, default_flow_style=False, allow_unicode=True)
            _ = output.getvalue()
        legacy_time = time.perf_counter() - start_time
        results["legacy_yaml_time"] = legacy_time

        # パフォーマンス比較
        results["performance_ratio"] = unified_time / legacy_time if legacy_time > 0 else 0
        results["overhead_percentage"] = ((unified_time - legacy_time) / legacy_time * 100) if legacy_time > 0 else 0

    except Exception as e:
        results["error"] = f"ベンチマークエラー: {e}"

    return results


# レガシーコード互換用のラッパー関数
def unified_yaml_dump(
    data: dict[str, Any],
    file_handle_or_path: Path | Any,
    format_type: str = "default",
    legacy_params: dict[str, Any] | None = None,
    **kwargs,
) -> bool:
    """統合yaml.dump互換関数

    レガシーコードから段階的に移行するための互換ラッパー

    Args:
        data: 出力データ
        file_handle_or_path: ファイルハンドル or パス
        format_type: 統合フォーマットタイプ
        legacy_params: レガシーパラメータ（分析用）
        **kwargs: その他のパラメータ

    Returns:
        成功フラグ
    """
    service = get_unified_yaml_service()

    # パス指定の場合
    if isinstance(file_handle_or_path, str | Path):
        output_path = Path(file_handle_or_path)
        success, messages = service.generate_with_validation(data, output_path, format_type)

        # メッセージ出力（デバッグ用）
        for msg in messages:
            if "エラー" in msg:
                console.print(f"[統合YAML] {msg}")

        return success

    # ファイルハンドル指定の場合（レガシー対応）
    yaml_content, messages = service.generate_string_with_validation(data, format_type)

    if yaml_content:
        file_handle_or_path.write(yaml_content)
        return True
    return False


class YAMLMultilineString(str):
    """YAMLマルチライン文字列表現クラス

    改行を含む文字列をYAMLリテラルブロック形式(|)で保存するためのカスタムクラス
    """

    def __new__(cls, value: str) -> "YAMLMultilineString":
        """YAMLMultilineStringインスタンス作成

        Args:
            value: マルチライン文字列

        Returns:
            YAMLMultilineString: カスタム文字列インスタンス
        """
        return str.__new__(cls, value)


def yaml_multiline_representer(dumper: yaml.SafeDumper, data: YAMLMultilineString) -> yaml.ScalarNode:
    """YAMLMultilineStringのカスタムリプレゼンター

    Args:
        dumper: YAMLダンパー
        data: YAMLMultilineString

    Returns:
        yaml.ScalarNode: リテラルブロック形式ノード
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


# YAMLMultilineString用リプレゼンターを登録（Dumperクラス別）
yaml.add_representer(YAMLMultilineString, yaml_multiline_representer)
yaml.SafeDumper.add_representer(YAMLMultilineString, yaml_multiline_representer)


# レガシー互換関数(後方互換性のため)
def check_yaml_syntax(file_path: str | Path) -> bool:
    """YAML構文の簡易チェック関数(レガシー互換)

    Args:
        file_path: YAMLファイルパス

    Returns:
        構文が正しい場合True
    """
    result = YAMLHandler.check_syntax(Path(file_path))
    return result["valid"]


def get_yaml_errors(file_path: str | Path) -> str | None:
    """YAMLファイルのエラーメッセージを取得(レガシー互換)

    Args:
        file_path: YAMLファイルパス

    Returns:
        エラーメッセージ、エラーがない場合はNone
    """
    result = YAMLHandler.check_syntax(Path(file_path))
    return result["error_message"] if not result["valid"] else None
