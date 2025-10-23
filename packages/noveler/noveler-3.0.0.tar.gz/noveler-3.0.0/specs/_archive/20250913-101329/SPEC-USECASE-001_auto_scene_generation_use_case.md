# シーン自動生成ユースケース仕様書

## 概要
`AutoSceneGenerationUseCase`は、プロジェクト情報に基づいて物語のシーンを自動生成するユースケースです。CLIコマンドからの呼び出しに応答し、適切なテンプレートとコンテキストを使用してシーンを生成します。

## クラス設計

### AutoSceneGenerationUseCase

**責務**
- プロジェクト情報の検証・取得
- シーン生成エンティティの調整
- シーン自動生成の実行
- 生成結果の統合・提供
- 事前検証とガイダンス

## パブリックメソッド

### generate_scene()

**シグネチャ**
```python
def generate_scene(
    self,
    scene_category: str,
    scene_id: str,
    options_dict: dict[str, Any],
    project_root: str | None = None,
) -> dict[str, Any]:
```

**目的**
指定されたカテゴリ・IDでシーンを自動生成する。

**引数**
- `scene_category`: シーンカテゴリ（"climax_scenes", "emotional_scenes"等）
- `scene_id`: シーンID
- `options_dict`: 生成オプション（辞書形式）
- `project_root`: プロジェクトルートパス

**戻り値**
```python
{
    "success": bool,                    # 生成成功フラグ
    "scene": GeneratedScene | None,     # 生成されたシーン
    "yaml_content": dict,               # YAML形式のシーンデータ
    "messages": list[str],              # 成功メッセージ
    "warnings": list[str],              # 警告メッセージ
    "errors": list[str],                # エラーメッセージ
    "completion_score": float,          # 完成度スコア
    "missing_elements": list[str],      # 不足要素
}
```

**処理フロー**
1. プロジェクト構造の検証
2. プロジェクトコンテキストの読み込み
3. 生成オプションの構築
4. シーン生成エンティティの準備
5. シーン生成の実行
6. 結果の構築・返却

### get_available_scene_categories()

**シグネチャ**
```python
def get_available_scene_categories(self, project_root: str | None = None) -> list[str]:
```

**目的**
プロジェクトのジャンルに基づいて利用可能なシーンカテゴリ一覧を提供する。

**戻り値**
プロジェクトのジャンルに適したシーンカテゴリのリスト

**ジャンル別カテゴリ**
- **ファンタジー**: climax_scenes, emotional_scenes, action_scenes
- **恋愛**: romance_scenes, emotional_scenes, dialogue_scenes
- **ミステリー**: climax_scenes, dialogue_scenes, description_scenes
- **デフォルト**: climax_scenes, emotional_scenes, romance_scenes

### validate_generation_request()

**シグネチャ**
```python
def validate_generation_request(
    self,
    scene_category: str,
    scene_id: str,
    options_dict: dict[str, Any],
    project_root: str | None = None,
) -> dict[str, Any]:
```

**目的**
シーン生成リクエストの事前検証を行い、問題点と推奨事項を提供する。

**戻り値**
```python
{
    "is_valid": bool,              # 検証結果
    "errors": list[str],           # エラー一覧
    "warnings": list[str],         # 警告一覧
    "recommendations": list[str],  # 推奨事項
}
```

**検証項目**
1. プロジェクト構造の検証
2. シーンカテゴリの妥当性チェック
3. 生成オプションの検証
4. プロジェクト情報の充実度チェック

### get_project_summary()

**シグネチャ**
```python
def get_project_summary(self, project_root: str | None = None) -> dict[str, Any]:
```

**目的**
プロジェクトの基本情報要約を取得する。

### get_generation_statistics()

**シグネチャ**
```python
def get_generation_statistics(self) -> dict[str, Any]:
```

**目的**
シーン生成の統計情報を取得する。

**戻り値**
```python
{
    "total_generations": int,      # 総生成数
    "categories_used": list[str],  # 使用されたカテゴリ
    "templates_used": list[str],   # 使用されたテンプレート
    "average_per_day": float,      # 1日平均生成数
}
```

### clear_generation_history()

**シグネチャ**
```python
def clear_generation_history(self) -> None:
```

**目的**
生成履歴をクリアする。

## プライベートメソッド

### _prepare_scene_generator()

**目的**
シーン生成エンティティを準備し、プロジェクトコンテキストとデフォルトテンプレートを設定する。

### _add_default_templates()

**目的**
デフォルトのシーンテンプレートを生成エンティティに追加する。

## 依存関係

### ドメイン層
- `AutoSceneGenerator`: シーン自動生成エンティティ
- `ProjectInfoService`: プロジェクト情報サービス
- `GenerationOptions`: 生成オプション値オブジェクト
- `ProjectContext`: プロジェクトコンテキスト値オブジェクト
- `SceneTemplate`: シーンテンプレート値オブジェクト

### インフラ層
- `ProjectInfoRepository`: プロジェクト情報リポジトリ

## 設計原則遵守

### DDD準拠
- ✅ ドメインロジックは`AutoSceneGenerator`に委譲
- ✅ 値オブジェクト（`GenerationOptions`, `ProjectContext`等）を適切に使用
- ✅ リポジトリパターンでデータアクセスを抽象化
- ✅ ドメインサービス（`ProjectInfoService`）の活用

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な例外処理
- ✅ 型安全な実装

## 使用例

```python
# リポジトリの準備
project_info_repo = YamlProjectInfoRepository()
use_case = AutoSceneGenerationUseCase(project_info_repo)

# 事前検証
validation = use_case.validate_generation_request(
    scene_category="climax_scenes",
    scene_id="final_battle",
    options_dict={"style": "dramatic", "length": "long"},
    project_root="/path/to/project"
)

if validation["is_valid"]:
    # シーン生成の実行
    result = use_case.generate_scene(
        scene_category="climax_scenes",
        scene_id="final_battle",
        options_dict={"style": "dramatic", "length": "long"},
        project_root="/path/to/project"
    )

    if result["success"]:
        generated_scene = result["scene"]
        completion_score = result["completion_score"]
    else:
        errors = result["errors"]
```

## エラーハンドリング

### BusinessRuleViolationError
- プロジェクト構造が無効
- 生成オプションがビジネスルールに違反

### 一般例外
- ファイル読み込みエラー
- YAML解析エラー
- ネットワークエラー（外部API使用時）

## テスト観点

### 単体テスト
- 正常なシーン生成フロー
- プロジェクト構造無効時の処理
- 各種エラー条件での動作
- カテゴリ推奨ロジック

### 統合テスト
- 実際のプロジェクトファイルとの連携
- ドメインエンティティとの協調動作

## 品質基準

- **機能性**: ジャンル別に適切なシーンカテゴリを提供
- **信頼性**: 例外安全な実装とフォールバック
- **使いやすさ**: 明確な検証メッセージと推奨事項
- **保守性**: 明確な責務分離と型安全性
- **拡張性**: 新しいシーンカテゴリ・テンプレートへの対応
