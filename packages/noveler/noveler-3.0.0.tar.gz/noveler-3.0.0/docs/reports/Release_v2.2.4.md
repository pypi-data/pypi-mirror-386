# Release v2.2.4 (2025-09-21)

## 主要変更
- PathServiceAdapter が `.novelerrc.{yaml,yml}` の `file_templates.project_config` を優先的に解決し、CLI やユーティリティから任意のプロジェクト設定ファイル名を透過的に利用できるようになりました。
- YamlProjectSettingsRepository が DI 非依存でテンプレートを参照するフォールバック経路を実装し、`get_title` / `get_genre` などの取得時にもカスタムファイル名を尊重します。
- ファイルテンプレート機能の回帰を防ぐため、PathServiceAdapter・YamlProjectSettingsRepository・YamlProjectConfigRepository のユニットテストを追加 / 強化しました。

## 背景
- ファイル名テンプレート機能は導入済みでしたが、パス解決アダプターやリポジトリのフォールバック経路が従来のハードコード (`プロジェクト設定.yaml`) のままで残存しており、`.novelerrc` によるカスタム設定が反映されないケースがありました。
- テンプレート設定を利用するユーザーにとって、CLI / ドメイン層の挙動を一致させることが急務でした。

## 実装ハイライト
- `src/noveler/infrastructure/adapters/path_service_adapter.py` に `_resolve_project_config_filename()` を追加し、プロジェクトローカルのテンプレート → グローバル設定 → デフォルトの順でファイル名を決定。
- `src/noveler/infrastructure/yaml_project_settings_repository.py` に `_resolve_project_config_path()` を追加して DI 非依存の解決経路を共通化。
- `tests/unit/infrastructure/adapters/test_path_service_adapter_side_effects.py` にテンプレート解決の回帰テストを追加し、`PathConfiguration` のデフォルト値に追随するよう期待値を整理。
- `tests/unit/infrastructure/repositories/test_yaml_project_settings_repository_templates.py` を新設し、`.novelerrc` 上書きが `resolve_service` フォールバックでも機能することを検証。
- `tests/unit/domain/services/test_file_template_service.py` で `YamlProjectConfigRepository` のテンプレート連携テストと例外フォールバックテストを追加。

## 品質確認
- `pytest tests/unit/infrastructure/adapters/test_path_service_adapter_side_effects.py`
- `pytest tests/unit/infrastructure/repositories/test_yaml_project_settings_repository_templates.py`
- `pytest tests/unit/domain/services/test_file_template_service.py`

## 移行影響
- `.novelerrc` に `file_templates.project_config` を設定している場合、CLI・DIコンテナなしスクリプトの双方で同一ファイル名が利用されます。追加作業は不要です。
- ハードコードされた `プロジェクト設定.yaml` を参照する独自スクリプトがある場合は、`ConfigurationManager.get_project_config_filename()` もしくは `PathServiceAdapter.get_project_config_file()` を利用する形へリファクタリングしてください。
