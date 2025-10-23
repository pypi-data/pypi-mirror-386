---
spec_id: SPEC-WORKFLOW-002
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: WORKFLOW
sources: [E2E]
tags: [workflow]
---
# SPEC-WORKFLOW-002: レガシーモジュールTDD+DDD移行

## 1. 仕様概要

### 目的
既存のレガシーモジュール（legacy_data_converter.py、format_standardizer.py、episode_preview_generator.py）をTDD+DDD設計に基づいて移行し、システムの一貫性と保守性を向上させる。

### スコープ
- レガシーデータ変換機能のドメインサービス化
- フォーマット標準化機能のドメインサービス化
- エピソードプレビュー生成機能のドメインサービス化
- 対応する値オブジェクトの設計・実装
- 完全なテストカバレッジの実現

## 2. DDD設計

### ドメインサービス
#### LegacyDataConversionService
- **責務**: レガシーフォーマットから新フォーマットへのデータ変換
- **依存**: ConversionRule（値オブジェクト）
- **提供メソッド**:
  - `convert_episode_data()`
  - `convert_project_metadata()`
  - `validate_conversion_result()`

#### FormatStandardizationService
- **責務**: 各種ファイルフォーマットの標準化
- **依存**: FormatSpecification（値オブジェクト）
- **提供メソッド**:
  - `standardize_yaml_format()`
  - `standardize_markdown_format()`
  - `validate_format_compliance()`

#### EpisodePreviewGenerationService
- **責務**: エピソードプレビューの生成・最適化
- **依存**: PreviewConfiguration（値オブジェクト）
- **提供メソッド**:
  - `generate_preview()`
  - `optimize_preview_content()`
  - `validate_preview_quality()`

### 値オブジェクト
#### ConversionRule
- **属性**: source_format, target_format, transformation_rules, validation_criteria
- **不変条件**: formatは有効な値、rulesは空でない

#### FormatSpecification
- **属性**: format_type, schema_version, validation_rules, formatting_options
- **不変条件**: 仕様は完全性を保つ

#### PreviewConfiguration
- **属性**: max_length, style_settings, content_filters, quality_thresholds
- **不変条件**: 設定値は有効範囲内

## 3. テストケース

### ユニットテスト（75%）
- 各ドメインサービスの単体機能テスト
- 値オブジェクトの不変条件テスト
- エラーハンドリングテスト

### 統合テスト（20%）
- サービス間連携テスト
- ファイルI/O統合テスト
- エンドツーエンド変換テスト

### E2Eテスト（5%）
- 実際のプロジェクトファイルでの変換テスト
- ユーザーワークフローテスト

## 4. 実装計画

### Phase 1: 環境準備
1. レガシーモジュールの作成（テスト用）
2. テストファイル構造の準備

### Phase 2: TDD実装サイクル
1. RED: 失敗するテストの作成
2. GREEN: 最小実装
3. REFACTOR: リファクタリング

### Phase 3: 統合・検証
1. 全体テストの実行
2. カバレッジ確認
3. 品質ゲートチェック

## 5. 受け入れ条件

- [ ] 全テストが成功すること
- [ ] テストカバレッジが80%以上であること
- [ ] 品質ゲートチェックをパスすること
- [ ] 既存機能との互換性が保たれること
- [ ] パフォーマンスが劣化しないこと

## 6. 技術的制約

- Python 3.8+
- pytest + pytest-bdd
- 統合インポート管理システム準拠
- DDD層分離アーキテクチャ準拠

## 7. 関連ドキュメント

- [B40_開発者ガイド.md](../B40_開発者ガイド.md)
- [CLAUDE.md](../CLAUDE.md)
- [統合インポート管理システム仕様](../CLAUDE.md#統合インポート管理システム)
