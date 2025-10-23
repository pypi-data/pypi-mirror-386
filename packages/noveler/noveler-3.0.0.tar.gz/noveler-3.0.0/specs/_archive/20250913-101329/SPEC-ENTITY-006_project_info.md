# ProjectInfo 値オブジェクト仕様書

## 1. 目的
小説プロジェクトの基本情報（名前、パス）を管理し、各種ディレクトリへの統一的なアクセスを提供する値オブジェクト

## 2. 前提条件
- プロジェクト名は空文字列不可
- パスはPathオブジェクトとして管理
- 値オブジェクトとして不変性を保証（frozen=True）
- 標準的なディレクトリ構造を前提とする

## 3. 主要な振る舞い

### 3.1 初期化と検証
- **入力**:
  - name: プロジェクト名（文字列）
  - root_path: プロジェクトルートパス（Path）
  - config_path: 設定ファイルパス（Path）
- **処理**:
  - プロジェクト名の空文字列チェック
  - パスオブジェクトの型チェック
- **出力**: ProjectInfoインスタンス
- **例外**:
  - ValueError（名前が空の場合）
  - TypeError（パスがPathオブジェクトでない場合）

### 3.2 原稿フォルダパス取得
- **入力**: なし
- **処理**: root_path / "40_原稿" を計算
- **出力**: 原稿フォルダのPath

### 3.3 管理資料フォルダパス取得
- **入力**: なし
- **処理**: root_path / "50_管理資料" を計算
- **出力**: 管理資料フォルダのPath

## 4. ディレクトリ構造
```
プロジェクトルート/
├── 10_企画/
├── 20_プロット/
├── 30_設定集/
├── 40_原稿/          ← manuscript_path
├── 50_管理資料/      ← management_path
└── プロジェクト設定.yaml  ← config_path
```

## 5. 使用例
```python
# プロジェクト情報の作成
project_info = ProjectInfo(
    name="転生魔法学園",
    root_path=Path("/novels/転生魔法学園"),
    config_path=Path("/novels/転生魔法学園/プロジェクト設定.yaml")
)

# 各種パスの取得
manuscript_dir = project_info.manuscript_path  # /novels/転生魔法学園/40_原稿
management_dir = project_info.management_path  # /novels/転生魔法学園/50_管理資料
```

## 6. 実装チェックリスト
- [x] プロジェクト名の空文字列検証
- [x] Pathオブジェクトの型検証
- [x] 不変性の保証（frozen=True）
- [x] manuscript_pathプロパティ
- [x] management_pathプロパティ
- [ ] テストケース作成
