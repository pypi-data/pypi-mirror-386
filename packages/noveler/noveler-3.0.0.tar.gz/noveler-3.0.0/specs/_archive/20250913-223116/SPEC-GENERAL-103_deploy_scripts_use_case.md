# SPEC-GENERAL-103: スクリプトデプロイユースケース仕様書

## 概要
`DeployScriptsUseCase`は、小説執筆支援システムのスクリプトをプロジェクトや環境にデプロイするユースケースです。スクリプトの配置、権限設定、依存関係の解決、環境別設定の適用、バージョン管理を包括的に処理し、安全で確実なデプロイメントを実現します。

## クラス設計

### DeployScriptsUseCase

**責務**
- スクリプトの環境別デプロイ
- 依存関係の自動解決とインストール
- 実行権限の適切な設定
- 設定ファイルの環境別カスタマイズ
- デプロイ履歴とロールバック管理
- ヘルスチェックと検証

## データ構造

### DeployTarget (Enum)
```python
class DeployTarget(Enum):
    LOCAL = "local"                    # ローカル開発環境
    PROJECT = "project"                # 特定プロジェクト
    GLOBAL = "global"                  # グローバル環境
    CI_CD = "ci_cd"                    # CI/CD環境
    PRODUCTION = "production"          # 本番環境
```

### DeploymentMode (Enum)
```python
class DeploymentMode(Enum):
    FULL = "full"                      # 完全デプロイ
    UPDATE = "update"                  # 更新のみ
    ROLLBACK = "rollback"              # ロールバック
    VERIFY = "verify"                  # 検証のみ
    REPAIR = "repair"                  # 修復
```

### DeployRequest (DataClass)
```python
@dataclass
class DeployRequest:
    target: DeployTarget               # デプロイ対象
    mode: DeploymentMode               # デプロイモード
    project_name: str | None = None    # プロジェクト名（PROJECT時）
    scripts: list[str] = []            # 特定スクリプト（空=全て）
    version: str | None = None         # バージョン指定
    environment_vars: dict[str, str] = {} # 環境変数
    force: bool = False                # 強制デプロイ
    dry_run: bool = False              # ドライラン
    create_backup: bool = True         # バックアップ作成
```

### DeployResponse (DataClass)
```python
@dataclass
class DeployResponse:
    success: bool                      # デプロイ成功フラグ
    deployed_scripts: list[str]        # デプロイされたスクリプト
    skipped_scripts: list[str]         # スキップされたスクリプト
    errors: list[DeployError]          # エラー情報
    deployment_id: str                 # デプロイメントID
    rollback_info: dict[str, any] = {} # ロールバック情報
    verification_results: dict[str, bool] = {} # 検証結果
    deployment_log: str = ""           # デプロイログ
```

### ScriptMetadata (DataClass)
```python
@dataclass
class ScriptMetadata:
    name: str                          # スクリプト名
    version: str                       # バージョン
    dependencies: list[str]            # 依存関係
    required_permissions: list[str]    # 必要な権限
    supported_platforms: list[str]     # サポートプラットフォーム
    environment_requirements: dict[str, str] # 環境要件
    configuration: dict[str, any]      # 設定項目
    health_check_command: str | None = None # ヘルスチェックコマンド
```

### DeploymentPlan (DataClass)
```python
@dataclass
class DeploymentPlan:
    deployment_id: str                 # デプロイメントID
    target: DeployTarget               # デプロイ対象
    steps: list[DeploymentStep]        # デプロイステップ
    estimated_time: float              # 推定所要時間
    required_space: int                # 必要ディスク容量
    rollback_strategy: str             # ロールバック戦略
```

## パブリックメソッド

### deploy_scripts()

**シグネチャ**
```python
def deploy_scripts(self, request: DeployRequest) -> DeployResponse:
```

**目的**
指定された環境にスクリプトをデプロイする。

**引数**
- `request`: デプロイリクエスト

**戻り値**
- `DeployResponse`: デプロイ結果

**処理フロー**
1. **環境検証**: デプロイ先環境の確認
2. **依存関係解決**: 必要な依存関係の特定
3. **デプロイ計画作成**: 実行計画の生成
4. **バックアップ**: 既存環境のバックアップ
5. **デプロイ実行**: スクリプトの配置と設定
6. **検証**: デプロイ後の動作確認
7. **クリーンアップ**: 一時ファイルの削除

### verify_deployment()

**シグネチャ**
```python
def verify_deployment(
    self,
    target: DeployTarget,
    project_name: str | None = None
) -> dict[str, bool]:
```

**目的**
デプロイされたスクリプトの動作を検証する。

### rollback_deployment()

**シグネチャ**
```python
def rollback_deployment(
    self,
    deployment_id: str
) -> bool:
```

**目的**
指定されたデプロイメントをロールバックする。

### get_deployment_status()

**シグネチャ**
```python
def get_deployment_status(
    self,
    deployment_id: str
) -> DeploymentStatus:
```

**目的**
デプロイメントの状態を取得する。

## プライベートメソッド

### _validate_environment()

**シグネチャ**
```python
def _validate_environment(
    self,
    target: DeployTarget,
    project_name: str | None
) -> EnvironmentValidation:
```

**目的**
デプロイ先環境を検証する。

**検証項目**
```python
validation_checks = {
    "platform_compatible": bool,       # プラットフォーム互換性
    "permissions_available": bool,     # 必要権限の有無
    "space_sufficient": bool,          # ディスク容量
    "dependencies_met": bool,          # 依存関係充足
    "conflicts_detected": list[str],   # 競合検出
    "python_version": str,             # Pythonバージョン
}
```

### _resolve_dependencies()

**シグネチャ**
```python
def _resolve_dependencies(
    self,
    scripts: list[str]
) -> DependencyGraph:
```

**目的**
スクリプトの依存関係を解決する。

### _create_deployment_plan()

**シグネチャ**
```python
def _create_deployment_plan(
    self,
    request: DeployRequest,
    dependency_graph: DependencyGraph
) -> DeploymentPlan:
```

**目的**
依存関係を考慮したデプロイ計画を作成する。

### _deploy_script()

**シグネチャ**
```python
def _deploy_script(
    self,
    script_metadata: ScriptMetadata,
    target_path: Path,
    environment_vars: dict[str, str]
) -> bool:
```

**目的**
個別のスクリプトをデプロイする。

**デプロイ処理**
1. スクリプトファイルのコピー
2. 設定ファイルの生成/更新
3. 実行権限の設定
4. 環境変数の設定
5. シンボリックリンクの作成

### _apply_environment_config()

**シグネチャ**
```python
def _apply_environment_config(
    self,
    script_path: Path,
    target: DeployTarget,
    custom_config: dict[str, any]
) -> None:
```

**目的**
環境別の設定を適用する。

### _run_health_checks()

**シグネチャ**
```python
def _run_health_checks(
    self,
    deployed_scripts: list[str],
    target_path: Path
) -> dict[str, bool]:
```

**目的**
デプロイされたスクリプトのヘルスチェックを実行する。

## デプロイ設定例

### スクリプトメタデータ
```yaml
# scripts/metadata/quality_checker.yaml
name: quality_checker
version: "2.1.0"
dependencies:
  - "pyyaml>=6.0"
  - "click>=8.0"
  - "rich>=12.0"
required_permissions:
  - read_file
  - write_file
supported_platforms:
  - linux
  - darwin
  - win32
environment_requirements:
  python_version: ">=3.8"
  min_memory_mb: 512
configuration:
  default_threshold: 70
  enable_auto_fix: false
  log_level: INFO
health_check_command: "python -m quality_checker --version"
```

### 環境別設定
```yaml
# deploy/environments/production.yaml
environment: production
settings:
  log_level: WARNING
  enable_auto_fix: false
  backup_enabled: true
  max_workers: 4
paths:
  scripts: /opt/novel-tools/scripts
  logs: /var/log/novel-tools
  config: /etc/novel-tools
permissions:
  user: novel-user
  group: novel-group
  mode: "755"
```

## 依存関係

### ドメインサービス
- `DependencyResolver`: 依存関係解決
- `EnvironmentValidator`: 環境検証
- `PermissionManager`: 権限管理

### インフラストラクチャ
- `FileSystemService`: ファイルシステム操作
- `PackageManager`: パッケージ管理
- `ProcessRunner`: プロセス実行
- `ConfigurationManager`: 設定管理

### リポジトリ
- `DeploymentRepository`: デプロイ履歴管理
- `ScriptRepository`: スクリプト情報管理
- `EnvironmentRepository`: 環境設定管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`DeploymentPlan`, `ScriptMetadata`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
dependency_resolver = DependencyResolver()
environment_validator = EnvironmentValidator()
permission_manager = PermissionManager()
file_system_service = FileSystemService()
package_manager = PackageManager()
process_runner = ProcessRunner()
configuration_manager = ConfigurationManager()
deployment_repo = DeploymentRepository()
script_repo = ScriptRepository()
environment_repo = EnvironmentRepository()

# ユースケース作成
use_case = DeployScriptsUseCase(
    dependency_resolver=dependency_resolver,
    environment_validator=environment_validator,
    permission_manager=permission_manager,
    file_system_service=file_system_service,
    package_manager=package_manager,
    process_runner=process_runner,
    configuration_manager=configuration_manager,
    deployment_repository=deployment_repo,
    script_repository=script_repo,
    environment_repository=environment_repo
)

# プロジェクトへのデプロイ
project_deploy_request = DeployRequest(
    target=DeployTarget.PROJECT,
    mode=DeploymentMode.FULL,
    project_name="fantasy_adventure",
    scripts=[],  # 全スクリプト
    version="latest",
    environment_vars={
        "PROJECT_ROOT": "/projects/fantasy_adventure",
        "LOG_LEVEL": "INFO"
    },
    force=False,
    dry_run=True,
    create_backup=True
)

# ドライラン実行
dry_run_response = use_case.deploy_scripts(project_deploy_request)

if dry_run_response.success:
    print("=== デプロイプレビュー ===")
    print(f"デプロイ予定スクリプト: {len(dry_run_response.deployed_scripts)}件")
    for script in dry_run_response.deployed_scripts:
        print(f"  - {script}")

    if dry_run_response.skipped_scripts:
        print(f"\nスキップ予定: {len(dry_run_response.skipped_scripts)}件")
        for script in dry_run_response.skipped_scripts:
            print(f"  - {script}")

    # 実際のデプロイ実行
    if input("\n実際にデプロイしますか？ [y/N]: ").lower() == 'y':
        actual_request = DeployRequest(**project_deploy_request.__dict__)
        actual_request.dry_run = False

        response = use_case.deploy_scripts(actual_request)

        if response.success:
            print(f"\n✅ デプロイ完了: {response.deployment_id}")
            print(f"デプロイされたスクリプト: {len(response.deployed_scripts)}件")

            # 検証実行
            print("\n検証を実行中...")
            verification = use_case.verify_deployment(
                target=DeployTarget.PROJECT,
                project_name="fantasy_adventure"
            )

            failed_checks = [s for s, ok in verification.items() if not ok]
            if failed_checks:
                print(f"⚠️ 検証失敗: {failed_checks}")
            else:
                print("✅ 全スクリプトの検証成功")
        else:
            print(f"\n❌ デプロイ失敗")
            for error in response.errors:
                print(f"  - {error.message}")
else:
    print("ドライラン失敗")

# CI/CD環境へのデプロイ
ci_deploy_request = DeployRequest(
    target=DeployTarget.CI_CD,
    mode=DeploymentMode.UPDATE,
    scripts=["quality_checker", "test_runner", "coverage_reporter"],
    version="v2.1.0",
    environment_vars={
        "CI": "true",
        "GITHUB_ACTIONS": "true"
    }
)

ci_response = use_case.deploy_scripts(ci_deploy_request)

# 特定スクリプトの修復
repair_request = DeployRequest(
    target=DeployTarget.LOCAL,
    mode=DeploymentMode.REPAIR,
    scripts=["broken_script"],
    force=True
)

repair_response = use_case.deploy_scripts(repair_request)

# デプロイ状態の確認
status = use_case.get_deployment_status(response.deployment_id)

print(f"\nデプロイメント状態: {status.state}")
print(f"開始時刻: {status.started_at}")
print(f"完了時刻: {status.completed_at}")
print(f"成功率: {status.success_rate:.1f}%")

# ロールバック実行
if not verification_success:
    print("\nロールバックを実行しますか？")
    if input("[y/N]: ").lower() == 'y':
        rollback_success = use_case.rollback_deployment(response.deployment_id)
        if rollback_success:
            print("✅ ロールバック完了")
        else:
            print("❌ ロールバック失敗")
```

## デプロイフロー詳細

### 1. 環境検証
```python
validation = self._validate_environment(target, project_name)
if not validation.is_valid:
    raise EnvironmentError(f"環境検証失敗: {validation.errors}")
```

### 2. 依存関係解決
```python
dependency_graph = self._resolve_dependencies(scripts)
install_order = dependency_graph.get_install_order()
```

### 3. デプロイ実行
```python
for script in install_order:
    metadata = self.script_repository.get_metadata(script)

    # 依存パッケージのインストール
    self.package_manager.install(metadata.dependencies)

    # スクリプトのデプロイ
    self._deploy_script(metadata, target_path, environment_vars)

    # 権限設定
    self.permission_manager.set_permissions(
        target_path / script,
        metadata.required_permissions
    )
```

### 4. ヘルスチェック
```python
health_results = {}
for script in deployed_scripts:
    if metadata.health_check_command:
        result = self.process_runner.run(
            metadata.health_check_command,
            cwd=target_path
        )
        health_results[script] = result.return_code == 0
```

## エラーハンドリング

### 環境エラー
```python
try:
    validation = self._validate_environment(target, project_name)
except EnvironmentNotFoundError:
    return DeployResponse(
        success=False,
        errors=[DeployError("ENVIRONMENT_NOT_FOUND", "デプロイ先環境が見つかりません")]
    )
```

### 依存関係エラー
```python
try:
    self.package_manager.install(dependencies)
except PackageInstallError as e:
    logger.error(f"依存関係のインストール失敗: {e}")
    # ロールバック処理
    self._rollback_partial_deployment(completed_scripts)
```

### 権限エラー
```python
try:
    self.permission_manager.set_permissions(script_path, permissions)
except PermissionError as e:
    if request.force:
        logger.warning(f"権限設定をスキップ: {e}")
    else:
        raise DeploymentError(f"権限設定失敗: {e}")
```

## バックアップとロールバック

### バックアップ作成
```python
def _create_backup(self, target_path: Path, deployment_id: str) -> BackupInfo:
    backup_path = self.backup_dir / deployment_id
    backup_path.mkdir(parents=True)

    # 現在の状態を保存
    for item in target_path.iterdir():
        if item.is_file():
            shutil.copy2(item, backup_path)
        elif item.is_dir():
            shutil.copytree(item, backup_path / item.name)

    return BackupInfo(backup_path, datetime.now())
```

### ロールバック実行
```python
def rollback_deployment(self, deployment_id: str) -> bool:
    backup_info = self.deployment_repository.get_backup_info(deployment_id)
    if not backup_info:
        return False

    # バックアップから復元
    self._restore_from_backup(backup_info)

    # デプロイ履歴を更新
    self.deployment_repository.mark_rolled_back(deployment_id)

    return True
```

## テスト観点

### 単体テスト
- 環境検証ロジック
- 依存関係解決アルゴリズム
- 権限設定の正確性
- ヘルスチェック実行
- エラー処理

### 統合テスト
- 実際の環境へのデプロイ
- 複数スクリプトの依存関係
- ロールバック機能
- 環境別設定の適用

## 品質基準

- **安全性**: バックアップとロールバックの確実性
- **互換性**: 複数プラットフォームのサポート
- **検証性**: 包括的なヘルスチェック
- **追跡性**: 詳細なデプロイ履歴
- **柔軟性**: 環境別カスタマイズの容易さ
