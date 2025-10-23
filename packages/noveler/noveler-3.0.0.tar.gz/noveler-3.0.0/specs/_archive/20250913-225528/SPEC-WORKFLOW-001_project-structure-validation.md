---
spec_id: SPEC-WORKFLOW-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: WORKFLOW
sources: [E2E]
tags: [workflow]
---
# SPEC-WORKFLOW-001: プロジェクト構造検証システム

## 概要

小説プロジェクトのディレクトリ構造、ファイル命名規則、必須ファイルの存在を検証し、プロジェクト品質保証を行うドメインサービス。標準構造からの逸脱を検出し、自動修復提案を提供する。

## 要求仕様

### 機能要求

1. **構造検証機能**
   - 標準ディレクトリ構造の検証
   - ファイル命名規則の確認
   - 必須ファイルの存在確認
   - 不要ファイル・ディレクトリの検出

2. **整合性検証機能**
   - YAML設定ファイルの構文・スキーマ検証
   - エピソード番号の連続性確認
   - クロスリファレンスの整合性確認
   - メタデータとファイル実体の一致確認

3. **自動修復機能**
   - 欠損ディレクトリの自動作成
   - ファイル名の標準化提案
   - 設定ファイルのテンプレート生成
   - バックアップ・復元機能

### 非機能要求

1. **パフォーマンス**: プロジェクト検証 < 2秒
2. **安全性**: 修復操作前の必須バックアップ
3. **拡張性**: カスタム検証ルールの追加対応
4. **ユーザビリティ**: 分かりやすい検証レポート

## DDD設計

### エンティティ

#### ProjectStructureValidationAggregate
- **責務**: プロジェクト構造検証の集約ルート
- **不変条件**:
  - 検証ルールの一貫性
  - 修復操作の安全性保証
  - 検証結果の完全性

### 値オブジェクト

#### ProjectStructure
```python
@dataclass(frozen=True)
class ProjectStructure:
    project_path: ProjectPath
    directory_structure: DirectoryStructure
    file_inventory: FileInventory
    configuration_files: List[ConfigurationFile]

    def validate_against_standard(self, standard: StandardStructure) -> ValidationResult:
        pass

    def get_deviation_summary(self) -> DeviationSummary:
        pass
```

#### ValidationResult
```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    validation_errors: List[ValidationError]
    validation_warnings: List[ValidationWarning]
    repair_suggestions: List[RepairSuggestion]
    compliance_score: ComplianceScore
```

#### ValidationError
```python
@dataclass(frozen=True)
class ValidationError:
    error_type: ValidationErrorType
    severity: ErrorSeverity
    description: str
    affected_path: str
    repair_action: Optional[RepairAction]
```

#### RepairSuggestion
```python
@dataclass(frozen=True)
class RepairSuggestion:
    suggestion_id: str
    description: str
    affected_items: List[str]
    repair_commands: List[RepairCommand]
    risk_level: RiskLevel
    estimated_time: timedelta
```

#### StandardStructure
```python
@dataclass(frozen=True)
class StandardStructure:
    required_directories: List[DirectoryRequirement]
    required_files: List[FileRequirement]
    naming_conventions: NamingConventions
    schema_definitions: Dict[str, SchemaDefinition]
```

### ドメインサービス

#### ProjectStructureValidationService
- **責務**: プロジェクト構造の包括的検証
- **主要メソッド**:
  - `validate_project_structure()`: プロジェクト構造検証
  - `generate_repair_plan()`: 修復計画生成
  - `execute_safe_repairs()`: 安全な自動修復実行
  - `create_validation_report()`: 検証レポート作成

#### StructureComplianceAnalyzer
- **責務**: 構造準拠性の分析
- **主要メソッド**:
  - `analyze_compliance_level()`: 準拠レベル分析
  - `identify_critical_issues()`: 重要問題特定
  - `suggest_priority_fixes()`: 優先修復提案

#### AutoRepairEngine
- **責務**: 自動修復処理の実行
- **主要メソッド**:
  - `create_safety_backup()`: 安全バックアップ作成
  - `execute_repair_commands()`: 修復コマンド実行
  - `verify_repair_results()`: 修復結果検証

### リポジトリ

#### ProjectStructureRepository
```python
class ProjectStructureRepository(ABC):
    @abstractmethod
    def load_project_structure(self, project_path: ProjectPath) -> ProjectStructure:
        pass

    @abstractmethod
    def save_validation_report(self, report: ValidationReport) -> None:
        pass

    @abstractmethod
    def get_standard_structure(self, project_type: ProjectType) -> StandardStructure:
        pass

    @abstractmethod
    def create_backup(self, project_path: ProjectPath) -> BackupInfo:
        pass
```

## テストケース

### ユニットテスト

1. **ProjectStructure値オブジェクト**
   - 構造表現の正確性
   - 検証ロジックの正確性
   - 偏差計算の検証

2. **ProjectStructureValidationService**
   - 各種検証ルールの実行
   - エラー検出の精度
   - 修復提案の妥当性

### 統合テスト

1. **実プロジェクト検証**
   - 正常プロジェクトの検証通過
   - 異常プロジェクトの適切な検出
   - 修復後の再検証成功

2. **自動修復機能**
   - バックアップ作成の確実性
   - 修復操作の安全性
   - ロールバック機能

### E2Eテスト

1. **プロジェクト品質保証**
   - 新規プロジェクトの構造検証
   - 既存プロジェクトの健全性確認
   - CI/CD統合による継続的検証

## 実装

### Phase 1: 基本検証機能
- ProjectStructure値オブジェクト
- ProjectStructureValidationService
- FileSystemProjectStructureRepository

### Phase 2: 自動修復機能
- AutoRepairEngine
- 安全バックアップシステム
- 修復後検証機能

### Phase 3: 高度分析
- 構造品質メトリクス
- カスタムルール対応
- 継続的監視機能
