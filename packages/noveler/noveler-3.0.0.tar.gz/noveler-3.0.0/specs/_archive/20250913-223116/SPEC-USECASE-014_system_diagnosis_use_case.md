# システム診断ユースケース仕様書

## 概要
`SystemDiagnosisUseCase`は、執筆支援システム全体の健全性を診断し、問題の特定と修復推奨を行うユースケースです。プロジェクト構造、ファイル整合性、設定状態、依存関係、品質チェック機能の診断を包括的に実行し、システム状態レポートと修復ガイドを提供します。

## クラス設計

### SystemDiagnosisUseCase

**責務**
- システム全体の健全性診断
- プロジェクト構造の検証
- 設定ファイルの整合性チェック
- 依存関係の確認
- 問題の特定と分類
- 修復推奨の生成
- 診断レポートの作成

## データ構造

### DiagnosisCategory (Enum)
```python
class DiagnosisCategory(Enum):
    PROJECT_STRUCTURE = "project_structure"      # プロジェクト構造
    FILE_INTEGRITY = "file_integrity"            # ファイル整合性
    CONFIGURATION = "configuration"              # 設定状態
    DEPENDENCIES = "dependencies"                # 依存関係
    QUALITY_SYSTEM = "quality_system"            # 品質チェックシステム
    PERMISSIONS = "permissions"                  # ファイル権限
    DISK_SPACE = "disk_space"                    # ディスク容量
```

### DiagnosisSeverity (Enum)
```python
class DiagnosisSeverity(Enum):
    CRITICAL = "critical"    # 重大（システム動作不可）
    ERROR = "error"          # エラー（機能制限あり）
    WARNING = "warning"      # 警告（推奨修正）
    INFO = "info"            # 情報（問題なし）
```

### DiagnosisRequest (DataClass)
```python
@dataclass
class DiagnosisRequest:
    project_name: str | None = None             # 対象プロジェクト名（None=システム全体）
    categories: list[DiagnosisCategory] = []    # 診断カテゴリ（空=全て）
    include_recommendations: bool = True        # 修復推奨を含める
    detailed_mode: bool = False                # 詳細モード
    output_format: str = "markdown"             # 出力フォーマット
    save_report: bool = True                   # レポート保存フラグ
```

### DiagnosisIssue (DataClass)
```python
@dataclass
class DiagnosisIssue:
    category: DiagnosisCategory                 # 診断カテゴリ
    severity: DiagnosisSeverity                # 重要度
    title: str                                 # 問題タイトル
    description: str                           # 詳細説明
    file_path: Path | None = None              # 関連ファイルパス
    recommendations: list[str] = []            # 修復推奨
    auto_fixable: bool = False                 # 自動修復可能フラグ
```

### DiagnosisResponse (DataClass)
```python
@dataclass
class DiagnosisResponse:
    success: bool                              # 診断成功フラグ
    message: str                               # 結果メッセージ
    overall_status: str                        # 全体ステータス（HEALTHY/WARNING/ERROR/CRITICAL）
    issues: list[DiagnosisIssue] = []          # 発見された問題
    critical_count: int = 0                    # 重大問題数
    error_count: int = 0                       # エラー数
    warning_count: int = 0                     # 警告数
    recommendations_summary: str = ""          # 推奨事項サマリー
    report_file_path: Path | None = None       # レポートファイルパス
    auto_fix_available: bool = False           # 自動修復利用可能フラグ
```

## パブリックメソッド

### diagnose()

**シグネチャ**
```python
def diagnose(self, request: DiagnosisRequest) -> DiagnosisResponse:
```

**目的**
システム診断を実行し、問題の特定と修復推奨を行う。

**引数**
- `request`: 診断リクエスト

**戻り値**
- `DiagnosisResponse`: 診断結果

**処理フロー**
1. **診断準備**: 診断対象とカテゴリの決定
2. **各カテゴリ診断**: 順次診断実行
3. **問題分析**: 重要度分類と優先度決定
4. **推奨生成**: 修復推奨の作成
5. **レポート作成**: 診断結果の整理
6. **結果統合**: レスポンスの構築

### auto_fix()

**シグネチャ**
```python
def auto_fix(self, issues: list[DiagnosisIssue]) -> AutoFixResponse:
```

**目的**
自動修復可能な問題を修復する。

**対象問題**
- 不足ディレクトリの作成
- ファイル権限の修正
- 設定ファイルの初期化
- テンプレートファイルの作成

## プライベートメソッド

### _diagnose_project_structure()

**シグネチャ**
```python
def _diagnose_project_structure(self, project_path: Path | None) -> list[DiagnosisIssue]:
```

**目的**
プロジェクト構造の健全性を診断する。

**診断項目**
- 必須ディレクトリの存在確認
- ファイル構造の妥当性チェック
- 命名規則の遵守確認
- 不要ファイルの検出

**チェック例**
```python
required_dirs = [
    "10_企画", "20_プロット", "30_設定集",
    "40_原稿", "50_管理資料"
]

for dir_name in required_dirs:
    dir_path = project_path / dir_name
    if not dir_path.exists():
        issues.append(DiagnosisIssue(
            category=DiagnosisCategory.PROJECT_STRUCTURE,
            severity=DiagnosisSeverity.ERROR,
            title=f"必須ディレクトリが不足: {dir_name}",
            file_path=dir_path,
            auto_fixable=True
        ))
```

### _diagnose_file_integrity()

**シグネチャ**
```python
def _diagnose_file_integrity(self, project_path: Path | None) -> list[DiagnosisIssue]:
```

**目的**
ファイルの整合性と妥当性を診断する。

**診断項目**
- YAMLファイルの構文チェック
- Markdownファイルの形式確認
- ファイル参照の整合性
- 文字エンコーディングの検証

### _diagnose_configuration()

**シグネチャ**
```python
def _diagnose_configuration(self) -> list[DiagnosisIssue]:
```

**目的**
システム設定の健全性を診断する。

**診断項目**
- 品質チェック設定の妥当性
- CLIコマンド設定の確認
- 環境変数の設定状態
- 設定ファイルの整合性

### _diagnose_dependencies()

**シグネチャ**
```python
def _diagnose_dependencies(self) -> list[DiagnosisIssue]:
```

**目的**
依存関係の状態を診断する。

**診断項目**
- Pythonパッケージの確認
- バージョン互換性チェック
- 必須ツールの存在確認
- Git設定の検証

### _diagnose_quality_system()

**シグネチャ**
```python
def _diagnose_quality_system(self, project_path: Path | None) -> list[DiagnosisIssue]:
```

**目的**
品質チェックシステムの動作を診断する。

**診断項目**
- 品質チェッカーの動作確認
- テストケースの整合性
- 品質記録ファイルの状態
- 自動化設定の確認

### _generate_recommendations()

**シグネチャ**
```python
def _generate_recommendations(self, issues: list[DiagnosisIssue]) -> str:
```

**目的**
診断結果に基づいた総合的な修復推奨を生成する。

**推奨例**
```markdown
## 優先修復事項
1. 【CRITICAL】プロジェクト設定.yamlが破損しています → 再作成が必要
2. 【ERROR】品質記録.yamlが見つかりません → `novel quality init`を実行
3. 【WARNING】不要なバックアップファイルがあります → 定期クリーンアップを推奨

## 自動修復可能項目
- 不足ディレクトリの作成
- ファイル権限の修正
- テンプレートファイルの作成

実行コマンド: `novel doctor --auto-fix`
```

### _create_diagnosis_report()

**シグネチャ**
```python
def _create_diagnosis_report(
    self,
    issues: list[DiagnosisIssue],
    recommendations: str
) -> str:
```

**目的**
診断結果の詳細レポートを作成する。

**レポート構成**
```markdown
# システム診断レポート

## 診断サマリー
- 実行日時: YYYY-MM-DD HH:MM:SS
- 診断対象: プロジェクト名 / システム全体
- 総合ステータス: HEALTHY/WARNING/ERROR/CRITICAL

## 問題一覧
### CRITICAL（重大）
- ...

### ERROR（エラー）
- ...

### WARNING（警告）
- ...

## 修復推奨
...

## 詳細診断結果
...
```

## 依存関係

### ドメインサービス
- `ProjectStructureValidator`: プロジェクト構造の検証
- `FileIntegrityChecker`: ファイル整合性の確認
- `ConfigurationValidator`: 設定の妥当性確認
- `DependencyChecker`: 依存関係の確認

### リポジトリ
- `ProjectRepository`: プロジェクト情報の取得
- `ConfigurationRepository`: 設定情報の取得
- `SystemRepository`: システム情報の取得

## 設計原則遵守

### DDD準拠
- ✅ ドメインサービス（各種Validator）の適切な活用
- ✅ エンティティ（`DiagnosisIssue`）の適切な管理
- ✅ 値オブジェクト（列挙型）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
config_repo = YamlConfigurationRepository()
system_repo = SystemRepository()
structure_validator = ProjectStructureValidator()
file_checker = FileIntegrityChecker()
config_validator = ConfigurationValidator()
dependency_checker = DependencyChecker()

# ユースケース作成
use_case = SystemDiagnosisUseCase(
    project_repository=project_repo,
    configuration_repository=config_repo,
    system_repository=system_repo,
    structure_validator=structure_validator,
    file_integrity_checker=file_checker,
    configuration_validator=config_validator,
    dependency_checker=dependency_checker
)

# システム全体の包括的診断
request = DiagnosisRequest(
    project_name=None,  # システム全体
    categories=[],      # 全カテゴリ
    include_recommendations=True,
    detailed_mode=True,
    save_report=True
)

response = use_case.diagnose(request)

if response.success:
    print(f"診断完了: {response.overall_status}")
    print(f"重大問題: {response.critical_count}件")
    print(f"エラー: {response.error_count}件")
    print(f"警告: {response.warning_count}件")

    if response.critical_count > 0 or response.error_count > 0:
        print("\n=== 重要な問題 ===")
        for issue in response.issues:
            if issue.severity in [DiagnosisSeverity.CRITICAL, DiagnosisSeverity.ERROR]:
                print(f"[{issue.severity.value.upper()}] {issue.title}")
                if issue.recommendations:
                    for rec in issue.recommendations:
                        print(f"  → {rec}")

    # 自動修復の実行
    if response.auto_fix_available:
        auto_fixable = [issue for issue in response.issues if issue.auto_fixable]
        print(f"\n自動修復可能: {len(auto_fixable)}件")

        fix_response = use_case.auto_fix(auto_fixable)
        if fix_response.success:
            print(f"自動修復完了: {fix_response.fixed_count}件")

    if response.report_file_path:
        print(f"\n詳細レポート: {response.report_file_path}")
else:
    print(f"診断失敗: {response.message}")

# 特定プロジェクトの診断
project_request = DiagnosisRequest(
    project_name="fantasy_adventure",
    categories=[
        DiagnosisCategory.PROJECT_STRUCTURE,
        DiagnosisCategory.FILE_INTEGRITY
    ],
    detailed_mode=False
)

project_response = use_case.diagnose(project_request)

# 設定のみの診断
config_request = DiagnosisRequest(
    categories=[DiagnosisCategory.CONFIGURATION],
    include_recommendations=True
)

config_response = use_case.diagnose(config_request)
```

## 診断項目詳細

### プロジェクト構造診断
```python
# 必須ディレクトリ
required_directories = [
    "10_企画", "20_プロット", "30_設定集",
    "40_原稿", "50_管理資料", "backup"
]

# 必須ファイル
required_files = [
    "プロジェクト設定.yaml",
    "50_管理資料/話数管理.yaml",
    "50_管理資料/品質記録.yaml"
]

# 命名規則チェック
episode_naming_pattern = r"第\d{3}話_.+\.md"
plot_naming_pattern = r"第\d+章\.yaml"
```

### ファイル整合性診断
```python
# YAML構文チェック
try:
    with open(yaml_file, 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
except yaml.YAMLError as e:
    issues.append(DiagnosisIssue(
        category=DiagnosisCategory.FILE_INTEGRITY,
        severity=DiagnosisSeverity.ERROR,
        title=f"YAML構文エラー: {yaml_file.name}",
        description=str(e),
        file_path=yaml_file
    ))

# 参照整合性チェック
for episode_ref in episode_references:
    episode_file = episodes_dir / f"{episode_ref}.md"
    if not episode_file.exists():
        issues.append(DiagnosisIssue(
            category=DiagnosisCategory.FILE_INTEGRITY,
            severity=DiagnosisSeverity.WARNING,
            title=f"参照先エピソードが不存在: {episode_ref}"
        ))
```

## エラーハンドリング

### 診断実行エラー
```python
try:
    structure_issues = self._diagnose_project_structure(project_path)
except PermissionError:
    issues.append(DiagnosisIssue(
        category=DiagnosisCategory.PERMISSIONS,
        severity=DiagnosisSeverity.CRITICAL,
        title="プロジェクトディレクトリへのアクセス権限がありません"
    ))
except Exception as e:
    logger.error(f"プロジェクト構造診断エラー: {e}")
    # 診断続行
```

### 自動修復エラー
```python
try:
    missing_dir.mkdir(parents=True, exist_ok=True)
    fixed_count += 1
except PermissionError:
    failed_fixes.append(f"ディレクトリ作成権限なし: {missing_dir}")
except Exception as e:
    failed_fixes.append(f"ディレクトリ作成失敗: {missing_dir} ({e})")
```

## 自動修復機能

### 修復可能項目
```python
auto_fixable_checks = {
    "missing_directory": lambda path: path.mkdir(parents=True, exist_ok=True),
    "wrong_permissions": lambda path: path.chmod(0o644),
    "missing_template": lambda path: shutil.copy(template_path, path),
    "empty_config": lambda path: create_default_config(path)
}
```

### 修復実行例
```python
class AutoFixResponse:
    success: bool
    fixed_count: int
    failed_fixes: list[str]
    message: str

def auto_fix(self, issues: list[DiagnosisIssue]) -> AutoFixResponse:
    fixed_count = 0
    failed_fixes = []

    for issue in issues:
        if not issue.auto_fixable:
            continue

        try:
            self._apply_fix(issue)
            fixed_count += 1
        except Exception as e:
            failed_fixes.append(f"{issue.title}: {e}")

    return AutoFixResponse(
        success=len(failed_fixes) == 0,
        fixed_count=fixed_count,
        failed_fixes=failed_fixes,
        message=f"修復完了: {fixed_count}件, 失敗: {len(failed_fixes)}件"
    )
```

## テスト観点

### 単体テスト
- 各診断カテゴリの正常動作
- 問題検出の精度
- 重要度分類の正確性
- 自動修復機能の動作
- エラー条件での処理

### 統合テスト
- 実際のプロジェクトでの診断
- 複合的な問題の検出
- レポート生成機能の確認
- 自動修復の実際の効果

## 品質基準

- **網羅性**: システム全体の包括的な診断
- **精度**: 問題の正確な特定と分類
- **実用性**: 具体的で実行可能な修復推奨
- **安全性**: 自動修復時の安全な処理
- **視認性**: 分かりやすい診断レポート
