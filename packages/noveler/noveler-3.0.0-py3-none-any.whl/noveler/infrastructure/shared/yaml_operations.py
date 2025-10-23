#!/usr/bin/env python3
"""統一YAML操作ライブラリ

中優先度問題解決:コード重複の解消
- YAML読み込み処理の統一化
- ファイル操作の共通化
- エラーハンドリングの統一
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from noveler.infrastructure.shared.unified_error_handler import ErrorSeverity, get_error_handler


class YamlOperations:
    """YAML操作の統一クラス"""

    def __init__(self, component_name: str) -> None:
        self.error_handler = get_error_handler(component_name)

    def load_yaml_file(self, file_path: Path | str, default_value: dict[str, object] | None) -> dict[str, object]:
        """YAMLファイルを安全に読み込み

        Args:
            file_path: ファイルパス
            default_value: ファイルが存在しない場合のデフォルト値

        Returns:
            読み込まれたデータまたはデフォルト値
        """
        if default_value is None:
            default_value = {}

        def _load_operation() -> dict[str, object]:
            path = Path(file_path)

            if not path.exists():
                if default_value is not None:
                    return default_value
                msg = f"YAMLファイルが見つかりません: {file_path}"
                raise FileNotFoundError(msg)

            with path.Path(encoding="utf-8").open() as f:
                content = yaml.safe_load(f)
                return content if content is not None else {}

        result, error_info = self.error_handler.handle_with_result(
            _load_operation,
            f"YAML読み込み({file_path})",
            default_value,
            ErrorSeverity.MEDIUM,
            f"YAMLファイル {file_path} の読み込みに失敗しました",
        )

        return result

    def save_yaml_file(self, file_path: Path | str, data: dict[str, object], create_dirs: bool = True) -> bool:
        """YAMLファイルを安全に保存

        Args:
            file_path: ファイルパス
            data: 保存するデータ
            create_dirs: ディレクトリを自動作成するか

        Returns:
            保存成功時True
        """

        def _save_operation() -> bool:
            path = Path(file_path)

            # ディレクトリ作成
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            with path.Path("w").open(encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )

            return True

        result, error_info = self.error_handler.handle_boolean_operation(
            _save_operation,
            f"YAML保存({file_path})",
            ErrorSeverity.HIGH,
            f"YAMLファイル {file_path} の保存に失敗しました",
        )

        return result

    def update_yaml_field(
        self, file_path: Path | str, field_path: str, value: object, create_if_missing: bool = False
    ) -> bool:
        """YAML内の特定フィールドを更新

        Args:
            file_path: ファイルパス
            field_path: フィールドパス(例: "metadata.version")
            value: 設定値
            create_if_missing: ファイルが存在しない場合に作成するか

        Returns:
            更新成功時True
        """

        def _update_operation() -> bool:
            # 既存データ読み込み
            data = self.load_yaml_file(file_path, {} if create_if_missing else None)
            if data is None:
                return False

            # フィールドパスを解析して値を設定
            keys = field_path.split(".")
            current = data

            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            current[keys[-1]] = value

            # 保存
            return self.save_yaml_file(file_path, data)

        result, error_info = self.error_handler.handle_boolean_operation(
            _update_operation,
            f"YAMLフィールド更新({file_path})",
            ErrorSeverity.HIGH,
            f"YAMLフィールド {field_path} の更新に失敗しました",
        )

        return result

    def get_yaml_field(self, file_path: str, field_path: str, default_value: object = None) -> object:
        """YAML内の特定フィールドを取得

        Args:
            file_path: ファイルパス
            field_path: フィールドパス(例: "metadata.version")
            default_value: フィールドが存在しない場合のデフォルト値

        Returns:
            フィールド値またはデフォルト値
        """

        def _get_operation() -> object:
            data = self.load_yaml_file(file_path, {})

            # フィールドパスを解析して値を取得
            keys = field_path.split(".")
            current = data

            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return default_value
                current = current[key]

            return current

        result, error_info = self.error_handler.handle_with_result(
            _get_operation,
            f"YAMLフィールド取得({file_path})",
            default_value,
            ErrorSeverity.LOW,  # 取得失敗は軽微
            None,  # ユーザーメッセージ不要(内部処理
        )

        return result

    def backup_yaml_file(self, file_path: str | Path, backup_suffix: str) -> bool:
        """YAMLファイルのバックアップを作成

        Args:
            file_path: ファイルパス
            backup_suffix: バックアップファイルの接尾辞

        Returns:
            バックアップ成功時True
        """

        def _backup_operation() -> bool:
            # import shutil # Moved to top-level
            # from datetime import datetime, timezone # Moved to top-level

            path = Path(file_path)
            if not path.exists():
                return False

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = path.with_suffix(f"{backup_suffix}_{timestamp}{path.suffix}")

            shutil.copy2(path, backup_path)
            return True

        result, error_info = self.error_handler.handle_boolean_operation(
            _backup_operation,
            f"YAMLバックアップ({file_path})",
            ErrorSeverity.MEDIUM,
            f"YAMLファイル {file_path} のバックアップに失敗しました",
        )

        return result


# シングルトンインスタンス(便利関数用)
_default_yaml_ops = YamlOperations()


# 便利関数
def load_yaml(file_path: Path | str, default: dict[str, object] | None) -> dict[str, object]:
    """YAML読み込み便利関数"""
    return _default_yaml_ops.load_yaml_file(file_path, default)


def save_yaml(file_path: Path | str, data: dict[str, object]) -> bool:
    """YAML保存便利関数"""
    return _default_yaml_ops.save_yaml_file(file_path, data)


def update_yaml_field(file_path: Path | str, field_path: str, value: object) -> bool:
    """YAMLフィールド更新便利関数"""
    return _default_yaml_ops.update_yaml_field(file_path, field_path, value)


def get_yaml_field(file_path: str, field_path: str, default: object = None) -> object:
    """YAMLフィールド取得便利関数"""
    return _default_yaml_ops.get_yaml_field(file_path, field_path, default)
