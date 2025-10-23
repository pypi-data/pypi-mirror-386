"""Domain.services.project_structure_value_objects
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
SPEC-WORKFLOW-001: プロジェクト構造検証 - 値オブジェクト定義

プロジェクト構造検証に関する値オブジェクトを定義。
DDD設計に基づく不変オブジェクトとして実装。
"""


from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class ValidationErrorType(Enum):
    """検証エラータイプ列挙型"""

    MISSING_DIRECTORY = "missing_directory"
    MISSING_REQUIRED_FILE = "missing_required_file"
    INVALID_FILE_NAME = "invalid_file_name"
    INVALID_YAML_SYNTAX = "invalid_yaml_syntax"
    SCHEMA_VIOLATION = "schema_violation"
    CROSS_REFERENCE_ERROR = "cross_reference_error"
    METADATA_MISMATCH = "metadata_mismatch"


class ErrorSeverity(Enum):
    """エラー重要度列挙型"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RepairAction(Enum):
    """修復アクション列挙型"""

    CREATE_DIRECTORY = "create_directory"
    CREATE_FROM_TEMPLATE = "create_from_template"
    FIX_FILE_NAME = "fix_file_name"
    FIX_YAML_SYNTAX = "fix_yaml_syntax"
    UPDATE_METADATA = "update_metadata"
    REMOVE_INVALID_FILE = "remove_invalid_file"


class RiskLevel(Enum):
    """リスクレベル列挙型"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DirectoryStructure:
    """ディレクトリ構造値オブジェクト"""

    required_dirs: list[str]
    existing_dirs: list[str]
    invalid_dirs: list[str]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.required_dirs, list):
            msg = "必須ディレクトリはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.existing_dirs, list):
            msg = "既存ディレクトリはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.invalid_dirs, list):
            msg = "無効ディレクトリはリスト形式である必要があります"
            raise TypeError(msg)

    def get_missing_directories(self) -> list[str]:
        """欠損ディレクトリを取得"""
        return [d for d in self.required_dirs if d not in self.existing_dirs]

    def get_compliance_rate(self) -> float:
        """準拠率を計算"""
        if not self.required_dirs:
            return 1.0

        existing_required = len([d for d in self.required_dirs if d in self.existing_dirs])
        return existing_required / len(self.required_dirs)


@dataclass(frozen=True)
class FileInventory:
    """ファイルインベントリ値オブジェクト"""

    required_files: list[str]
    existing_files: list[str]
    invalid_files: list[str]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.required_files, list):
            msg = "必須ファイルはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.existing_files, list):
            msg = "既存ファイルはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.invalid_files, list):
            msg = "無効ファイルはリスト形式である必要があります"
            raise TypeError(msg)

    def get_missing_files(self) -> list[str]:
        """欠損ファイルを取得"""
        return [f for f in self.required_files if f not in self.existing_files]

    def get_compliance_rate(self) -> float:
        """準拠率を計算"""
        if not self.required_files:
            return 1.0

        existing_required = len([f for f in self.required_files if f in self.existing_files])
        return existing_required / len(self.required_files)


@dataclass(frozen=True)
class ConfigurationFile:
    """設定ファイル値オブジェクト"""

    path: Path
    is_valid: bool
    schema_errors: list[str]
    last_validated: datetime | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.schema_errors, list):
            msg = "スキーマエラーはリスト形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class ValidationError:
    """検証エラー値オブジェクト"""

    error_type: ValidationErrorType
    severity: ErrorSeverity
    description: str
    affected_path: str
    repair_action: RepairAction | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.description or not self.description.strip():
            msg = "エラー説明は必須です"
            raise ValueError(msg)
        if not self.affected_path or not self.affected_path.strip():
            msg = "影響パスは必須です"
            raise ValueError(msg)


@dataclass(frozen=True)
class ValidationWarning:
    """検証警告値オブジェクト"""

    warning_type: str
    description: str
    affected_path: str
    recommendation: str | None = None


@dataclass(frozen=True)
class RepairCommand:
    """修復コマンド値オブジェクト"""

    command_type: str
    command: str
    target_path: str
    backup_required: bool = True

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.command or not self.command.strip():
            msg = "コマンドは必須です"
            raise ValueError(msg)
        if not self.target_path or not self.target_path.strip():
            msg = "対象パスは必須です"
            raise ValueError(msg)


@dataclass(frozen=True)
class RepairSuggestion:
    """修復提案値オブジェクト"""

    suggestion_id: str
    description: str
    affected_items: list[str]
    repair_commands: list[RepairCommand]
    risk_level: RiskLevel
    estimated_time: timedelta

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.suggestion_id or not self.suggestion_id.strip():
            msg = "提案IDは必須です"
            raise ValueError(msg)
        if not self.description or not self.description.strip():
            msg = "説明は必須です"
            raise ValueError(msg)
        if not isinstance(self.affected_items, list):
            msg = "影響項目はリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.repair_commands, list):
            msg = "修復コマンドはリスト形式である必要があります"
            raise TypeError(msg)

    def requires_user_confirmation(self) -> bool:
        """ユーザー確認が必要か判定"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def calculate_priority_score(self) -> float:
        """優先度スコアを計算"""
        risk_weight = {RiskLevel.CRITICAL: 1.0, RiskLevel.HIGH: 0.8, RiskLevel.MEDIUM: 0.6, RiskLevel.LOW: 0.4}

        base_score = risk_weight.get(self.risk_level, 0.5)

        # 影響項目数による調整
        impact_factor = min(1.0, len(self.affected_items) / 10.0)

        # 推定時間による調整(短時間ほど高優先度)
        time_factor = max(0.1, 1.0 - (self.estimated_time.total_seconds() / 3600.0))

        return base_score * (0.5 + 0.3 * impact_factor + 0.2 * time_factor)


@dataclass(frozen=True)
class ComplianceScore:
    """準拠スコア値オブジェクト"""

    overall_score: float  # 0.0-1.0
    directory_compliance: float
    file_compliance: float
    configuration_compliance: float

    def __post_init__(self) -> None:
        """バリデーション"""
        scores = [self.overall_score, self.directory_compliance, self.file_compliance, self.configuration_compliance]

        for score in scores:
            if not 0.0 <= score <= 1.0:
                msg = "スコアは0.0から1.0の範囲である必要があります"
                raise ValueError(msg)

    def get_grade(self) -> str:
        """グレードを取得"""
        if self.overall_score >= 0.95:
            return "A+"
        if self.overall_score >= 0.90:
            return "A"
        if self.overall_score >= 0.80:
            return "B"
        if self.overall_score >= 0.70:
            return "C"
        if self.overall_score >= 0.60:
            return "D"
        return "F"


@dataclass(frozen=True)
class ValidationResult:
    """検証結果値オブジェクト"""

    is_valid: bool
    validation_errors: list[ValidationError]
    validation_warnings: list[ValidationWarning]
    repair_suggestions: list[RepairSuggestion]
    compliance_score: ComplianceScore

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.validation_errors, list):
            msg = "検証エラーはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.validation_warnings, list):
            msg = "検証警告はリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.repair_suggestions, list):
            msg = "修復提案はリスト形式である必要があります"
            raise TypeError(msg)

    def get_critical_errors(self) -> list[ValidationError]:
        """重要エラーを取得"""
        return [error for error in self.validation_errors if error.severity == ErrorSeverity.CRITICAL]

    def get_high_priority_repairs(self) -> list[RepairSuggestion]:
        """高優先度修復を取得"""
        repairs = [(suggestion, suggestion.calculate_priority_score()) for suggestion in self.repair_suggestions]
        repairs.sort(key=lambda x: x[1], reverse=True)

        return [repair[0] for repair in repairs[:5]]  # 上位5つ


@dataclass(frozen=True)
class StandardStructure:
    """標準構造値オブジェクト"""

    required_directories: list[str]
    required_files: list[str]
    naming_conventions: dict[str, str]  # パターン名 -> 正規表現
    schema_definitions: dict[str, str]  # ファイルタイプ -> スキーマファイルパス

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.required_directories, list):
            msg = "必須ディレクトリはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.required_files, list):
            msg = "必須ファイルはリスト形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.naming_conventions, dict):
            msg = "命名規則は辞書形式である必要があります"
            raise TypeError(msg)
        if not isinstance(self.schema_definitions, dict):
            msg = "スキーマ定義は辞書形式である必要があります"
            raise TypeError(msg)


@dataclass(frozen=True)
class ProjectStructure:
    """プロジェクト構造値オブジェクト"""

    project_path: Path
    directory_structure: DirectoryStructure
    file_inventory: FileInventory
    configuration_files: list[ConfigurationFile]

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.configuration_files, list):
            msg = "設定ファイルはリスト形式である必要があります"
            raise TypeError(msg)

    def validate_against_standard(self, _standard: StandardStructure) -> ValidationResult:
        """標準構造に対して検証"""
        errors: list[Any] = []
        warnings = []
        suggestions = []

        # ディレクトリ検証
        missing_dirs = self.directory_structure.get_missing_directories()
        for missing_dir in missing_dirs:
            errors.append(
                ValidationError(
                    error_type=ValidationErrorType.MISSING_DIRECTORY,
                    severity=ErrorSeverity.HIGH,
                    description=f"必須ディレクトリが存在しません: {missing_dir}",
                    affected_path=missing_dir,
                    repair_action=RepairAction.CREATE_DIRECTORY,
                )
            )

            suggestions.append(
                RepairSuggestion(
                    suggestion_id=f"create_dir_{missing_dir}",
                    description=f"ディレクトリ '{missing_dir}' を作成",
                    affected_items=[missing_dir],
                    repair_commands=[
                        RepairCommand(
                            command_type="mkdir",
                            command=f"mkdir -p {missing_dir}",
                            target_path=missing_dir,
                            backup_required=False,
                        )
                    ],
                    risk_level=RiskLevel.LOW,
                    estimated_time=timedelta(seconds=5),
                )
            )

        # ファイル検証
        missing_files = self.file_inventory.get_missing_files()
        errors.extend(
            ValidationError(
                error_type=ValidationErrorType.MISSING_REQUIRED_FILE,
                severity=ErrorSeverity.HIGH,
                description=f"必須ファイルが存在しません: {missing_file}",
                affected_path=missing_file,
                repair_action=RepairAction.CREATE_FROM_TEMPLATE,
            )
            for missing_file in missing_files
        )

        # 準拠スコア計算
        dir_compliance = self.directory_structure.get_compliance_rate()
        file_compliance = self.file_inventory.get_compliance_rate()
        config_compliance = self._calculate_config_compliance()
        overall_compliance = (dir_compliance + file_compliance + config_compliance) / 3

        compliance_score = ComplianceScore(
            overall_score=overall_compliance,
            directory_compliance=dir_compliance,
            file_compliance=file_compliance,
            configuration_compliance=config_compliance,
        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors,
            validation_warnings=warnings,
            repair_suggestions=suggestions,
            compliance_score=compliance_score,
        )

    def get_deviation_summary(self) -> dict[str, Any]:
        """偏差サマリーを取得"""
        return {
            "missing_directories": self.directory_structure.get_missing_directories(),
            "missing_files": self.file_inventory.get_missing_files(),
            "invalid_directories": self.directory_structure.invalid_dirs,
            "invalid_files": self.file_inventory.invalid_files,
            "configuration_issues": len([cf for cf in self.configuration_files if not cf.is_valid]),
        }

    def _calculate_config_compliance(self) -> float:
        """設定ファイル準拠率を計算"""
        if not self.configuration_files:
            return 1.0

        valid_configs = len([cf for cf in self.configuration_files if cf.is_valid])
        return valid_configs / len(self.configuration_files)
