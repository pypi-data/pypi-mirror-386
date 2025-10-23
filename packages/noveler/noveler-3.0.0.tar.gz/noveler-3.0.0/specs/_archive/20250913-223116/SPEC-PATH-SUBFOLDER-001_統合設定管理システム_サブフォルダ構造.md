# SPEC-PATH-SUBFOLDER-001: 統合設定管理システム サブフォルダ構造

## 🎯 目的
統合設定管理システムを活用したサブフォルダアクセス機能の実装。ハードコーディングを完全排除し、設定ファイル駆動でのプロジェクト構造管理を実現する。

## 📋 要件

### REQ-1.1: 設定ファイル駆動サブフォルダアクセス
- `config/novel_config.yaml`の`sub_directories`セクションからサブフォルダ名を動的取得
- プロジェクトルート配下の各フォルダに対して、配下のサブフォルダへの統一アクセス提供
- ハードコーディング設定を完全排除

### REQ-1.2: CommonPathService拡張
- 既存のCommonPathServiceを拡張し、サブフォルダアクセス機能を追加
- `get_chapter_plots_dir()`, `get_episode_plots_dir()`, `get_quality_records_dir()` 等のメソッド提供
- 統合設定管理システム（configuration_service_factory）との連携

### REQ-1.3: 正しいサブフォルダ配置ルール準拠
- **話別プロット**: `20_プロット/話別プロット` に配置（60_プロンプトからの重複排除）
- **章別プロット**: `20_プロット/章別プロット` に配置
- **執筆記録**: `30_設定集/執筆記録` に配置
- **A31_チェックリスト**: `50_管理資料/A31_チェックリスト` に配置
- **全話分析結果**: `60_プロンプト/全話分析結果` に配置
- **.noveler配下（内部ログ/参照）**: 以下を標準とする
  - `.noveler/writes` … write系逐次I/Oログ
  - `.noveler/checks` … quality/check系逐次I/Oログ
  - `.noveler/artifacts` … 参照渡し用アーティファクト
  - `.noveler/steps` … Progressive系の内部状態/入出力

### REQ-1.4: 既存コード移行対応
- prompt_commands.pyの話別プロット参照を20_プロット配下に変更
- unified_context_analysis_use_case.py等の既存実装を設定ベースに移行
- 段階的移行による既存システムの安定性確保

## 🏗️ 実装予定

### ドメイン層
- `SubfolderPathService`: サブフォルダパス管理ドメインサービス
- `ProjectStructureEntity`: プロジェクト構造定義エンティティ
- `SubfolderConfiguration`: サブフォルダ設定値オブジェクト

### アプリケーション層
- `SubfolderPathResolutionUseCase`: サブフォルダパス解決ユースケース

### インフラストラクチャ層
- `CommonPathService`拡張: サブフォルダアクセスメソッド追加
- 統合設定管理システム連携コンポーネント

### プレゼンテーション層
- 既存CLIコマンドの設定ベース移行対応

## 🔧 実装詳細

### 設定構造
```yaml
# config/novel_config.yaml
sub_directories:
  plot_subdirs:
    chapter_plots: "章別プロット"
    episode_plots: "話別プロット"  # 20_プロット配下

  settings_subdirs:
    writing_records: "執筆記録"
    character_growth: "キャラクター成長記録"

  management_subdirs:
    quality_records: "品質記録"
    checklist_records: "A31_チェックリスト"
    foreshadowing: "伏線管理"

  prompt_subdirs:
    analysis_results: "全話分析結果"
    quality_checks: "品質チェックプロンプト"
```

### CommonPathService拡張API
```python
class CommonPathService:
    def get_chapter_plots_dir(self) -> Path:
        """章別プロットディレクトリ取得"""
        return self.get_plot_dir() / self._get_subfolder_name("plot_subdirs", "chapter_plots")

    def get_episode_plots_dir(self) -> Path:
        """話別プロットディレクトリ取得（20_プロット配下）"""
        return self.get_plot_dir() / self._get_subfolder_name("plot_subdirs", "episode_plots")

    def get_quality_records_dir(self) -> Path:
        """品質記録ディレクトリ取得"""
        return self.get_management_dir() / self._get_subfolder_name("management_subdirs", "quality_records")

    def get_a31_checklist_dir(self) -> Path:
        """A31チェックリストディレクトリ取得"""
        return self.get_management_dir() / self._get_subfolder_name("management_subdirs", "checklist_records")

    def get_analysis_results_dir(self) -> Path:
        """全話分析結果ディレクトリ取得"""
        return self.get_prompts_dir() / self._get_subfolder_name("prompt_subdirs", "analysis_results")
```

## ✅ 受け入れ条件

### 機能要件
- [ ] config/novel_config.yamlからサブフォルダ名を動的取得できること
- [ ] CommonPathServiceの各サブフォルダアクセスメソッドが正常動作すること
- [ ] 話別プロットが20_プロット配下に正しく配置されること
- [ ] prompt_commands.pyが設定ベースの話別プロットパスを使用すること

### 品質要件
- [ ] 全テストがパスすること（100%）
- [ ] B30品質基準に完全準拠すること
- [ ] ハードコーディングが0件であること
- [ ] 既存機能への影響がないこと

### 非機能要件
- [ ] 設定ファイル読み込みエラー時の適切なフォールバック
- [ ] 存在しないサブフォルダへのアクセス時の自動作成
- [ ] プラットフォーム依存性の完全排除
- [ ] パフォーマンス：設定読み込み時間 < 100ms

## 🧪 テスト戦略

### 単体テスト
- SubfolderPathServiceの各メソッド動作確認
- 設定値の不正値に対するエラーハンドリング
- CommonPathService拡張メソッドの正常動作

### 統合テスト
- 設定ファイル→サブフォルダパス解決のエンドツーエンドテスト
- 既存CLI機能の設定ベース移行動作確認

### 回帰テスト
- 既存機能に影響を与えないことの確認
- prompt_commands.py移行後の動作確認

## 🔄 移行計画

### Phase 1: コア機能実装
1. SubfolderPathService実装
2. CommonPathService拡張
3. 基本テスト実装

### Phase 2: 既存機能移行
1. prompt_commands.py移行
2. unified_context_analysis_use_case.py移行
3. 回帰テスト実行

### Phase 3: 最終検証
1. 全テスト実行・パス確認
2. B30品質基準チェック
3. システム健全性確認

## 📊 期待効果

### 保守性向上
- サブフォルダ名変更時の影響を設定ファイル変更のみに限定
- プロジェクト構造のカスタマイズ性向上

### 拡張性向上
- 新しいサブフォルダ追加が設定変更のみで対応可能
- プロジェクトテンプレート機能への発展可能性

### 品質向上
- ハードコーディング完全排除による不具合リスク削減
- 統一的なパス管理による整合性確保
