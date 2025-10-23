# YAML検証アダプター仕様書

## 概要
YAML検証アダプターは、システム全体で使用される各種YAMLファイルの検証・妥当性チェック機能を提供するアダプターです。スキーマ検証、データ型チェック、ビジネスルール検証、構造検証を統合し、信頼性の高いYAMLデータ処理を保証します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import yaml
import jsonschema

class ValidationType(Enum):
    """検証タイプ"""
    SCHEMA = "schema"
    STRUCTURE = "structure"
    BUSINESS_RULE = "business_rule"
    DATA_TYPE = "data_type"
    REFERENCE = "reference"
    CUSTOM = "custom"

class SeverityLevel(Enum):
    """重要度レベル"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"

class YamlType(Enum):
    """YAMLタイプ"""
    PROJECT_CONFIG = "project_config"
    EPISODE_METADATA = "episode_metadata"
    PLOT_DATA = "plot_data"
    CHARACTER_DATA = "character_data"
    QUALITY_RECORD = "quality_record"
    FORESHADOWING = "foreshadowing"
    SCENE_DATA = "scene_data"
    ACCESS_ANALYTICS = "access_analytics"

@dataclass
class ValidationError:
    """検証エラー"""
    type: ValidationType
    severity: SeverityLevel
    message: str
    path: str
    expected: Optional[Any]
    actual: Optional[Any]
    rule_name: Optional[str]
    suggestions: List[str]
    context: Dict[str, Any]

@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    yaml_type: YamlType
    file_path: Optional[str]
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info_messages: List[ValidationError]
    validation_timestamp: datetime
    schema_version: str
    metadata: Dict[str, Any]

class ISchemaProvider(ABC):
    """スキーマプロバイダーインターフェース"""

    @abstractmethod
    def get_schema(self, yaml_type: YamlType) -> Dict[str, Any]:
        """スキーマを取得"""
        pass

    @abstractmethod
    def get_schema_version(self, yaml_type: YamlType) -> str:
        """スキーマバージョンを取得"""
        pass

    @abstractmethod
    def list_supported_types(self) -> List[YamlType]:
        """サポート対象タイプを一覧取得"""
        pass

class YamlValidatorAdapter:
    """YAML検証アダプター"""

    def __init__(
        self,
        schema_provider: ISchemaProvider,
        business_rule_validator: IBusinessRuleValidator,
        reference_validator: IReferenceValidator,
        custom_validators: Dict[str, ICustomValidator],
        error_formatter: IErrorFormatter
    ):
        self._schema_provider = schema_provider
        self._business_validator = business_rule_validator
        self._reference_validator = reference_validator
        self._custom_validators = custom_validators
        self._error_formatter = error_formatter
```

## データ構造

### インターフェース定義

```python
class IBusinessRuleValidator(ABC):
    """ビジネスルール検証インターフェース"""

    @abstractmethod
    def validate_rules(
        self,
        yaml_type: YamlType,
        data: Dict[str, Any]
    ) -> List[ValidationError]:
        """ビジネスルールを検証"""
        pass

    @abstractmethod
    def get_rules(self, yaml_type: YamlType) -> List[Dict[str, Any]]:
        """適用ルールを取得"""
        pass

class IReferenceValidator(ABC):
    """参照検証インターフェース"""

    @abstractmethod
    def validate_references(
        self,
        yaml_type: YamlType,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        """参照の整合性を検証"""
        pass

    @abstractmethod
    def resolve_reference(
        self,
        reference_path: str,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """参照を解決"""
        pass

class ICustomValidator(ABC):
    """カスタム検証インターフェース"""

    @abstractmethod
    def validate(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        """カスタム検証を実行"""
        pass

    @abstractmethod
    def get_validator_name(self) -> str:
        """検証器名を取得"""
        pass

class IErrorFormatter(ABC):
    """エラーフォーマッターインターフェース"""

    @abstractmethod
    def format_error(self, error: ValidationError) -> str:
        """エラーをフォーマット"""
        pass

    @abstractmethod
    def format_summary(self, result: ValidationResult) -> str:
        """検証結果サマリーをフォーマット"""
        pass

    @abstractmethod
    def suggest_fixes(self, errors: List[ValidationError]) -> List[str]:
        """修正提案を生成"""
        pass
```

### アダプター実装

```python
@dataclass
class ValidationContext:
    """検証コンテキスト"""
    file_path: Optional[str]
    yaml_type: YamlType
    project_name: Optional[str]
    episode_number: Optional[int]
    external_data: Dict[str, Any]
    strict_mode: bool

@dataclass
class SchemaValidationConfig:
    """スキーマ検証設定"""
    strict_type_checking: bool
    allow_additional_properties: bool
    validate_formats: bool
    check_required_fields: bool
    custom_format_checkers: Dict[str, callable]

class JsonSchemaProvider(ISchemaProvider):
    """JSONスキーマプロバイダー"""

    def __init__(self, schema_directory: str):
        self._schema_dir = schema_directory
        self._schemas = {}
        self._load_schemas()

    def get_schema(self, yaml_type: YamlType) -> Dict[str, Any]:
        schema = self._schemas.get(yaml_type)
        if not schema:
            raise ValueError(f"スキーマが見つかりません: {yaml_type}")
        return schema

    def get_schema_version(self, yaml_type: YamlType) -> str:
        schema = self.get_schema(yaml_type)
        return schema.get("$schema_version", "1.0.0")

    def list_supported_types(self) -> List[YamlType]:
        return list(self._schemas.keys())

    def _load_schemas(self) -> None:
        """スキーマファイルを読み込み"""
        schema_files = {
            YamlType.PROJECT_CONFIG: "project_config_schema.json",
            YamlType.EPISODE_METADATA: "episode_metadata_schema.json",
            YamlType.PLOT_DATA: "plot_data_schema.json",
            YamlType.CHARACTER_DATA: "character_data_schema.json",
            YamlType.QUALITY_RECORD: "quality_record_schema.json",
            YamlType.FORESHADOWING: "foreshadowing_schema.json",
            YamlType.SCENE_DATA: "scene_data_schema.json",
            YamlType.ACCESS_ANALYTICS: "access_analytics_schema.json"
        }

        for yaml_type, filename in schema_files.items():
            schema_path = os.path.join(self._schema_dir, filename)
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self._schemas[yaml_type] = json.load(f)

class DefaultBusinessRuleValidator(IBusinessRuleValidator):
    """デフォルトビジネスルール検証器"""

    def __init__(self):
        self._rules = self._load_business_rules()

    def validate_rules(
        self,
        yaml_type: YamlType,
        data: Dict[str, Any]
    ) -> List[ValidationError]:
        errors = []
        rules = self._rules.get(yaml_type, [])

        for rule in rules:
            try:
                if not self._evaluate_rule(rule, data):
                    error = ValidationError(
                        type=ValidationType.BUSINESS_RULE,
                        severity=SeverityLevel(rule.get("severity", "error")),
                        message=rule["message"],
                        path=rule.get("path", ""),
                        expected=rule.get("expected"),
                        actual=self._extract_actual_value(rule, data),
                        rule_name=rule["name"],
                        suggestions=rule.get("suggestions", []),
                        context={"rule": rule}
                    )
                    errors.append(error)
            except Exception as e:
                # ルール評価エラー
                error = ValidationError(
                    type=ValidationType.BUSINESS_RULE,
                    severity=SeverityLevel.ERROR,
                    message=f"ルール評価エラー: {e}",
                    path=rule.get("path", ""),
                    expected=None,
                    actual=None,
                    rule_name=rule["name"],
                    suggestions=["ルール定義を確認してください"],
                    context={"rule_error": str(e)}
                )
                errors.append(error)

        return errors

    def get_rules(self, yaml_type: YamlType) -> List[Dict[str, Any]]:
        return self._rules.get(yaml_type, [])

    def _load_business_rules(self) -> Dict[YamlType, List[Dict[str, Any]]]:
        """ビジネスルールを読み込み"""
        return {
            YamlType.EPISODE_METADATA: [
                {
                    "name": "valid_episode_number",
                    "condition": "episode_number > 0",
                    "message": "エピソード番号は1以上である必要があります",
                    "severity": "error",
                    "path": "episode_number",
                    "suggestions": ["エピソード番号を1以上に設定してください"]
                },
                {
                    "name": "non_empty_title",
                    "condition": "len(title.strip()) > 0",
                    "message": "タイトルは空にできません",
                    "severity": "error",
                    "path": "title",
                    "suggestions": ["タイトルを入力してください"]
                },
                {
                    "name": "reasonable_word_count",
                    "condition": "0 <= word_count <= 50000",
                    "message": "文字数は0-50000文字の範囲である必要があります",
                    "severity": "warning",
                    "path": "word_count",
                    "suggestions": ["文字数を確認してください"]
                }
            ],
            YamlType.QUALITY_RECORD: [
                {
                    "name": "valid_score_range",
                    "condition": "all(0 <= score <= 100 for score in scores.values())",
                    "message": "品質スコアは0-100の範囲である必要があります",
                    "severity": "error",
                    "path": "scores",
                    "suggestions": ["スコアを0-100の範囲に修正してください"]
                }
            ]
        }

    def _evaluate_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """ルールを評価"""
        condition = rule["condition"]

        # 簡易的な条件評価（実際の実装では安全な評価器を使用）
        local_vars = data.copy()

        try:
            return eval(condition, {"__builtins__": {}}, local_vars)
        except Exception:
            return False

    def _extract_actual_value(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Any:
        """実際の値を抽出"""
        path = rule.get("path", "")
        if not path:
            return None

        try:
            keys = path.split(".")
            value = data
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
```

## パブリックメソッド

### YamlValidatorAdapter

```python
def validate_yaml_file(
    self,
    file_path: str,
    yaml_type: YamlType,
    context: Optional[ValidationContext] = None
) -> ValidationResult:
    """
    YAMLファイルを検証

    Args:
        file_path: YAMLファイルパス
        yaml_type: YAMLタイプ
        context: 検証コンテキスト

    Returns:
        ValidationResult: 検証結果
    """
    try:
        # YAMLファイル読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # コンテキスト設定
        if not context:
            context = ValidationContext(
                file_path=file_path,
                yaml_type=yaml_type,
                project_name=None,
                episode_number=None,
                external_data={},
                strict_mode=True
            )

        # 検証実行
        return self.validate_yaml_data(data, yaml_type, context)

    except yaml.YAMLError as e:
        # YAML構文エラー
        error = ValidationError(
            type=ValidationType.STRUCTURE,
            severity=SeverityLevel.ERROR,
            message=f"YAML構文エラー: {e}",
            path="",
            expected=None,
            actual=None,
            rule_name="yaml_syntax",
            suggestions=["YAML構文を確認してください"],
            context={"yaml_error": str(e)}
        )

        return ValidationResult(
            is_valid=False,
            yaml_type=yaml_type,
            file_path=file_path,
            errors=[error],
            warnings=[],
            info_messages=[],
            validation_timestamp=datetime.now(),
            schema_version="unknown",
            metadata={"syntax_error": True}
        )

    except Exception as e:
        # その他のエラー
        error = ValidationError(
            type=ValidationType.CUSTOM,
            severity=SeverityLevel.ERROR,
            message=f"検証エラー: {e}",
            path="",
            expected=None,
            actual=None,
            rule_name="validation_error",
            suggestions=["ファイルパスと内容を確認してください"],
            context={"exception": str(e)}
        )

        return ValidationResult(
            is_valid=False,
            yaml_type=yaml_type,
            file_path=file_path,
            errors=[error],
            warnings=[],
            info_messages=[],
            validation_timestamp=datetime.now(),
            schema_version="unknown",
            metadata={"exception_occurred": True}
        )

def validate_yaml_data(
    self,
    data: Dict[str, Any],
    yaml_type: YamlType,
    context: Optional[ValidationContext] = None
) -> ValidationResult:
    """
    YAMLデータを検証

    Args:
        data: YAMLデータ
        yaml_type: YAMLタイプ
        context: 検証コンテキスト

    Returns:
        ValidationResult: 検証結果
    """
    if not context:
        context = ValidationContext(
            file_path=None,
            yaml_type=yaml_type,
            project_name=None,
            episode_number=None,
            external_data={},
            strict_mode=True
        )

    all_errors = []
    all_warnings = []
    all_info = []

    # 1. スキーマ検証
    schema_errors = self._validate_schema(data, yaml_type)
    self._categorize_errors(schema_errors, all_errors, all_warnings, all_info)

    # 2. ビジネスルール検証
    business_errors = self._business_validator.validate_rules(yaml_type, data)
    self._categorize_errors(business_errors, all_errors, all_warnings, all_info)

    # 3. 参照検証
    reference_errors = self._reference_validator.validate_references(
        yaml_type,
        data,
        context.external_data
    )
    self._categorize_errors(reference_errors, all_errors, all_warnings, all_info)

    # 4. カスタム検証
    for validator_name, validator in self._custom_validators.items():
        try:
            custom_errors = validator.validate(data, context.external_data)
            self._categorize_errors(custom_errors, all_errors, all_warnings, all_info)
        except Exception as e:
            error = ValidationError(
                type=ValidationType.CUSTOM,
                severity=SeverityLevel.ERROR,
                message=f"カスタム検証エラー ({validator_name}): {e}",
                path="",
                expected=None,
                actual=None,
                rule_name=f"custom_{validator_name}",
                suggestions=["カスタム検証器の実装を確認してください"],
                context={"validator": validator_name, "exception": str(e)}
            )
            all_errors.append(error)

    # 結果作成
    is_valid = len(all_errors) == 0
    schema_version = self._schema_provider.get_schema_version(yaml_type)

    return ValidationResult(
        is_valid=is_valid,
        yaml_type=yaml_type,
        file_path=context.file_path,
        errors=all_errors,
        warnings=all_warnings,
        info_messages=all_info,
        validation_timestamp=datetime.now(),
        schema_version=schema_version,
        metadata={
            "strict_mode": context.strict_mode,
            "total_checks": len(all_errors) + len(all_warnings) + len(all_info)
        }
    )

def batch_validate(
    self,
    file_paths: List[str],
    yaml_type: YamlType,
    context: Optional[ValidationContext] = None
) -> Dict[str, ValidationResult]:
    """
    複数YAMLファイルを一括検証

    Args:
        file_paths: YAMLファイルパスのリスト
        yaml_type: YAMLタイプ
        context: 検証コンテキスト

    Returns:
        Dict[str, ValidationResult]: ファイル別検証結果
    """
    results = {}

    for file_path in file_paths:
        try:
            # ファイル固有のコンテキスト作成
            file_context = context._replace(file_path=file_path) if context else None

            result = self.validate_yaml_file(file_path, yaml_type, file_context)
            results[file_path] = result

        except Exception as e:
            # 個別ファイルエラーは結果に含める
            error = ValidationError(
                type=ValidationType.CUSTOM,
                severity=SeverityLevel.ERROR,
                message=f"ファイル処理エラー: {e}",
                path="",
                expected=None,
                actual=None,
                rule_name="file_processing_error",
                suggestions=["ファイルの存在とアクセス権限を確認してください"],
                context={"file_path": file_path, "exception": str(e)}
            )

            results[file_path] = ValidationResult(
                is_valid=False,
                yaml_type=yaml_type,
                file_path=file_path,
                errors=[error],
                warnings=[],
                info_messages=[],
                validation_timestamp=datetime.now(),
                schema_version="unknown",
                metadata={"file_error": True}
            )

    return results

def get_validation_summary(
    self,
    results: Dict[str, ValidationResult]
) -> Dict[str, Any]:
    """
    検証結果のサマリーを取得

    Args:
        results: 検証結果辞書

    Returns:
        Dict[str, Any]: 検証サマリー
    """
    total_files = len(results)
    valid_files = sum(1 for r in results.values() if r.is_valid)
    invalid_files = total_files - valid_files

    total_errors = sum(len(r.errors) for r in results.values())
    total_warnings = sum(len(r.warnings) for r in results.values())
    total_info = sum(len(r.info_messages) for r in results.values())

    error_types = {}
    for result in results.values():
        for error in result.errors:
            error_type = error.type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1

    # 最も多いエラータイプ
    most_common_errors = sorted(
        error_types.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    # 修正提案
    all_errors = []
    for result in results.values():
        all_errors.extend(result.errors)

    suggestions = self._error_formatter.suggest_fixes(all_errors)

    return {
        "total_files": total_files,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "success_rate": (valid_files / total_files * 100) if total_files > 0 else 0,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_info": total_info,
        "error_types": error_types,
        "most_common_errors": most_common_errors,
        "suggestions": suggestions[:10]  # 上位10件の修正提案
    }

def auto_fix_common_issues(
    self,
    file_path: str,
    yaml_type: YamlType,
    backup: bool = True
) -> Dict[str, Any]:
    """
    一般的な問題を自動修正

    Args:
        file_path: YAMLファイルパス
        yaml_type: YAMLタイプ
        backup: バックアップ作成フラグ

    Returns:
        Dict[str, Any]: 修正結果
    """
    # 初回検証
    original_result = self.validate_yaml_file(file_path, yaml_type)

    if original_result.is_valid:
        return {
            "fixed": False,
            "message": "修正の必要なエラーはありません",
            "original_errors": 0,
            "fixed_errors": 0
        }

    # バックアップ作成
    if backup:
        backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(file_path, backup_path)

    try:
        # YAMLデータ読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # 自動修正実行
        fixed_data, fixed_count = self._apply_auto_fixes(
            data,
            original_result.errors,
            yaml_type
        )

        # 修正データ保存
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                fixed_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )

        # 修正後検証
        fixed_result = self.validate_yaml_file(file_path, yaml_type)

        return {
            "fixed": True,
            "backup_path": backup_path if backup else None,
            "original_errors": len(original_result.errors),
            "remaining_errors": len(fixed_result.errors),
            "fixed_errors": fixed_count,
            "success_rate": (1 - len(fixed_result.errors) / len(original_result.errors)) * 100
        }

    except Exception as e:
        # 修正失敗時はバックアップから復元
        if backup and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)

        return {
            "fixed": False,
            "message": f"自動修正エラー: {e}",
            "original_errors": len(original_result.errors),
            "fixed_errors": 0
        }
```

## プライベートメソッド

```python
def _validate_schema(
    self,
    data: Dict[str, Any],
    yaml_type: YamlType
) -> List[ValidationError]:
    """スキーマ検証を実行"""
    try:
        schema = self._schema_provider.get_schema(yaml_type)
        jsonschema.validate(data, schema)
        return []

    except jsonschema.ValidationError as e:
        error = ValidationError(
            type=ValidationType.SCHEMA,
            severity=SeverityLevel.ERROR,
            message=e.message,
            path=".".join(str(p) for p in e.absolute_path),
            expected=e.schema.get("type") if hasattr(e, "schema") else None,
            actual=e.instance if hasattr(e, "instance") else None,
            rule_name="schema_validation",
            suggestions=self._generate_schema_suggestions(e),
            context={"schema_path": list(e.schema_path) if hasattr(e, "schema_path") else []}
        )
        return [error]

    except Exception as e:
        error = ValidationError(
            type=ValidationType.SCHEMA,
            severity=SeverityLevel.ERROR,
            message=f"スキーマ検証エラー: {e}",
            path="",
            expected=None,
            actual=None,
            rule_name="schema_error",
            suggestions=["スキーマ定義を確認してください"],
            context={"exception": str(e)}
        )
        return [error]

def _categorize_errors(
    self,
    errors: List[ValidationError],
    all_errors: List[ValidationError],
    all_warnings: List[ValidationError],
    all_info: List[ValidationError]
) -> None:
    """エラーを重要度別に分類"""
    for error in errors:
        if error.severity == SeverityLevel.ERROR:
            all_errors.append(error)
        elif error.severity == SeverityLevel.WARNING:
            all_warnings.append(error)
        elif error.severity == SeverityLevel.INFO:
            all_info.append(error)
        # DEBUG レベルは無視

def _generate_schema_suggestions(self, validation_error) -> List[str]:
    """スキーマエラーの修正提案を生成"""
    suggestions = []

    if validation_error.validator == "required":
        missing_property = validation_error.message.split("'")[1]
        suggestions.append(f"必須フィールド '{missing_property}' を追加してください")

    elif validation_error.validator == "type":
        expected_type = validation_error.schema.get("type", "unknown")
        suggestions.append(f"データ型を {expected_type} に修正してください")

    elif validation_error.validator == "enum":
        allowed_values = validation_error.schema.get("enum", [])
        suggestions.append(f"許可された値のいずれかを使用してください: {allowed_values}")

    elif validation_error.validator == "minLength":
        min_length = validation_error.schema.get("minLength", 0)
        suggestions.append(f"最低 {min_length} 文字以上入力してください")

    elif validation_error.validator == "maxLength":
        max_length = validation_error.schema.get("maxLength", 0)
        suggestions.append(f"最大 {max_length} 文字以内にしてください")

    return suggestions

def _apply_auto_fixes(
    self,
    data: Dict[str, Any],
    errors: List[ValidationError],
    yaml_type: YamlType
) -> Tuple[Dict[str, Any], int]:
    """自動修正を適用"""
    fixed_data = data.copy()
    fixed_count = 0

    for error in errors:
        if error.type == ValidationType.SCHEMA:
            if self._try_fix_schema_error(fixed_data, error):
                fixed_count += 1
        elif error.type == ValidationType.BUSINESS_RULE:
            if self._try_fix_business_rule_error(fixed_data, error):
                fixed_count += 1

    return fixed_data, fixed_count

def _try_fix_schema_error(
    self,
    data: Dict[str, Any],
    error: ValidationError
) -> bool:
    """スキーマエラーの自動修正を試行"""
    try:
        path_parts = error.path.split(".") if error.path else []

        if "required" in error.message:
            # 必須フィールド追加
            missing_field = error.message.split("'")[1]
            if path_parts:
                target = data
                for part in path_parts[:-1]:
                    target = target[part]
                target[missing_field] = self._get_default_value(missing_field)
            else:
                data[missing_field] = self._get_default_value(missing_field)
            return True

        elif "type" in error.message and error.expected:
            # データ型修正
            if self._try_convert_type(data, path_parts, error.expected):
                return True

    except Exception:
        pass

    return False

def _try_fix_business_rule_error(
    self,
    data: Dict[str, Any],
    error: ValidationError
) -> bool:
    """ビジネスルールエラーの自動修正を試行"""
    try:
        if error.rule_name == "non_empty_title" and error.path == "title":
            data["title"] = "無題"
            return True
        elif error.rule_name == "valid_episode_number" and error.path == "episode_number":
            data["episode_number"] = 1
            return True
    except Exception:
        pass

    return False

def _get_default_value(self, field_name: str) -> Any:
    """フィールドのデフォルト値を取得"""
    defaults = {
        "title": "",
        "episode_number": 1,
        "word_count": 0,
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "tags": [],
        "metadata": {}
    }
    return defaults.get(field_name, "")

def _try_convert_type(
    self,
    data: Dict[str, Any],
    path_parts: List[str],
    expected_type: str
) -> bool:
    """データ型の変換を試行"""
    try:
        # パスに従って値を取得
        target = data
        for part in path_parts[:-1]:
            target = target[part]

        field_name = path_parts[-1]
        current_value = target[field_name]

        # 型変換
        if expected_type == "integer":
            target[field_name] = int(float(str(current_value)))
        elif expected_type == "number":
            target[field_name] = float(str(current_value))
        elif expected_type == "string":
            target[field_name] = str(current_value)
        elif expected_type == "boolean":
            target[field_name] = str(current_value).lower() in ["true", "1", "yes"]
        elif expected_type == "array":
            if not isinstance(current_value, list):
                target[field_name] = [current_value] if current_value else []

        return True

    except (ValueError, KeyError, IndexError):
        return False
```

## アダプターパターン実装

### 具体的カスタム検証器

```python
class EpisodeNumberValidator(ICustomValidator):
    """エピソード番号検証器"""

    def __init__(self, episode_repository):
        self._episode_repo = episode_repository

    def validate(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        errors = []

        episode_number = data.get("episode_number")
        project_name = context.get("project_name")

        if episode_number and project_name:
            # 重複チェック
            existing_episode = self._episode_repo.find_by_number(
                project_name,
                episode_number
            )

            if existing_episode:
                errors.append(ValidationError(
                    type=ValidationType.REFERENCE,
                    severity=SeverityLevel.ERROR,
                    message=f"エピソード番号 {episode_number} は既に使用されています",
                    path="episode_number",
                    expected=None,
                    actual=episode_number,
                    rule_name="unique_episode_number",
                    suggestions=[
                        f"エピソード番号を {episode_number + 1} に変更してください",
                        "既存のエピソードを確認してください"
                    ],
                    context={"existing_episode": existing_episode.title}
                ))

        return errors

    def get_validator_name(self) -> str:
        return "episode_number_validator"

class CharacterReferenceValidator(ICustomValidator):
    """キャラクター参照検証器"""

    def __init__(self, character_repository):
        self._character_repo = character_repository

    def validate(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        errors = []

        # キャラクター参照を検索
        character_refs = self._extract_character_references(data)
        project_name = context.get("project_name")

        if character_refs and project_name:
            # 既知のキャラクターを取得
            known_characters = self._character_repo.get_character_names(project_name)

            for ref in character_refs:
                if ref not in known_characters:
                    errors.append(ValidationError(
                        type=ValidationType.REFERENCE,
                        severity=SeverityLevel.WARNING,
                        message=f"未定義のキャラクター '{ref}' が参照されています",
                        path="character_references",
                        expected="defined_character",
                        actual=ref,
                        rule_name="character_reference_check",
                        suggestions=[
                            f"キャラクター '{ref}' を定義してください",
                            "キャラクター名のスペルを確認してください"
                        ],
                        context={"known_characters": known_characters}
                    ))

        return errors

    def get_validator_name(self) -> str:
        return "character_reference_validator"

    def _extract_character_references(self, data: Dict[str, Any]) -> List[str]:
        """データからキャラクター参照を抽出"""
        references = set()

        def extract_from_value(value):
            if isinstance(value, str):
                # 簡易的なキャラクター名抽出（実際はより高度な解析が必要）
                import re
                matches = re.findall(r'【([^】]+)】', value)
                references.update(matches)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)

        extract_from_value(data)
        return list(references)
```

## 依存関係

```python
from domain.entities import Episode, Project
from domain.repositories import EpisodeRepository, CharacterRepository
from domain.value_objects import EpisodeNumber, EpisodeTitle
from application.use_cases import ValidateYamlUseCase
from infrastructure.repositories import YamlEpisodeRepository
```

## 設計原則遵守

### アダプターパターン
- **検証器の統合**: 複数の検証機能を統一インターフェースで提供
- **プラグイン機能**: カスタム検証器の動的追加が容易
- **エラーハンドリング**: 一貫したエラー形式で結果を提供

### 戦略パターン
- **検証戦略**: スキーマ、ビジネスルール、参照、カスタム検証を選択可能
- **修正戦略**: 自動修正の手法を戦略として実装
- **フォーマット戦略**: エラーフォーマットを切り替え可能

## 使用例

### 基本的な使用

```python
# 検証アダプター設定
schema_provider = JsonSchemaProvider("./schemas")
business_validator = DefaultBusinessRuleValidator()
reference_validator = DefaultReferenceValidator()
error_formatter = DefaultErrorFormatter()

# カスタム検証器
episode_validator = EpisodeNumberValidator(episode_repository)
character_validator = CharacterReferenceValidator(character_repository)

custom_validators = {
    "episode_number": episode_validator,
    "character_reference": character_validator
}

# アダプター初期化
validator = YamlValidatorAdapter(
    schema_provider=schema_provider,
    business_rule_validator=business_validator,
    reference_validator=reference_validator,
    custom_validators=custom_validators,
    error_formatter=error_formatter
)

# 単一ファイル検証
result = validator.validate_yaml_file(
    file_path="./project/episodes/episode_001.yaml",
    yaml_type=YamlType.EPISODE_METADATA
)

if result.is_valid:
    print("検証成功")
else:
    print(f"検証エラー数: {len(result.errors)}")
    for error in result.errors:
        print(f"  - {error.message} ({error.path})")
```

### 一括検証使用

```python
# プロジェクト全体の検証
episode_files = glob.glob("./project/episodes/*.yaml")
plot_files = glob.glob("./project/plots/*.yaml")

# エピソード一括検証
episode_results = validator.batch_validate(
    episode_files,
    YamlType.EPISODE_METADATA
)

# プロット一括検証
plot_results = validator.batch_validate(
    plot_files,
    YamlType.PLOT_DATA
)

# 結果サマリー
all_results = {**episode_results, **plot_results}
summary = validator.get_validation_summary(all_results)

print(f"検証ファイル数: {summary['total_files']}")
print(f"成功率: {summary['success_rate']:.1f}%")
print(f"エラー数: {summary['total_errors']}")
```

### 自動修正使用

```python
# 問題のあるファイルを自動修正
invalid_files = [
    path for path, result in episode_results.items()
    if not result.is_valid
]

for file_path in invalid_files:
    fix_result = validator.auto_fix_common_issues(
        file_path=file_path,
        yaml_type=YamlType.EPISODE_METADATA,
        backup=True
    )

    if fix_result["fixed"]:
        print(f"修正完了: {file_path}")
        print(f"  修正エラー数: {fix_result['fixed_errors']}")
        print(f"  残存エラー数: {fix_result['remaining_errors']}")
    else:
        print(f"修正失敗: {file_path} - {fix_result['message']}")
```

## エラーハンドリング

```python
try:
    result = validator.validate_yaml_file(file_path, yaml_type)

    if not result.is_valid:
        # エラー詳細分析
        critical_errors = [e for e in result.errors if e.severity == SeverityLevel.ERROR]

        if critical_errors:
            print("致命的エラー:")
            for error in critical_errors:
                print(f"  {error.message}")
                for suggestion in error.suggestions:
                    print(f"    提案: {suggestion}")

        # 自動修正可能性チェック
        auto_fixable = [e for e in result.errors if e.rule_name in AUTO_FIXABLE_RULES]

        if auto_fixable:
            print(f"{len(auto_fixable)} 個のエラーは自動修正可能です")

except Exception as e:
    logger.error(f"検証処理エラー: {e}")
    # フォールバック: 基本的な構文チェックのみ
    basic_result = perform_basic_yaml_check(file_path)
```

## テスト観点

### ユニットテスト
- スキーマ検証の正確性
- ビジネスルール評価の動作
- 参照検証の完全性
- エラーフォーマットの一貫性

### 統合テスト
- 実際のYAMLファイルでの検証
- 複数検証器の連携動作
- 自動修正機能の動作確認
- パフォーマンス測定

### 回帰テスト
- スキーマ変更時の影響確認
- 既存YAMLファイルの継続検証
- 修正機能の副作用チェック

## 品質基準

### コード品質
- 循環的複雑度: 8以下
- テストカバレッジ: 90%以上
- 型ヒント: 100%実装

### 設計品質
- 検証ルールの明確性
- エラーメッセージの有用性
- 修正提案の実用性

### 運用品質
- 検証処理の高速性
- メモリ使用量の最適化
- 大量ファイル処理の安定性
