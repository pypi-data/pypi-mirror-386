# SPEC-EPISODE-007: CLIエピソード番号統合 仕様書

## 1. 目的

EpisodeNumberResolverをCLIコマンドに統合し、ユーザーが話数指定でコマンドを実行できるようにする。

## 2. 前提条件

- EpisodeNumberResolverが実装済み
- 話数管理.yamlが存在する
- 既存のCLIコマンドがファイル名を受け取る形式で実装されている

## 3. 主要な振る舞い

### 3.1 quality_checkコマンドの拡張
- 入力: 数値（話数）または文字列（ファイル名）
- 処理:
  - 数値の場合: EpisodeNumberResolverで解決してファイルパスを取得
  - 文字列の場合: 従来通りファイル名として処理
- 出力: 品質チェック結果

### 3.2 エラーハンドリング
- 話数が見つからない場合: わかりやすいエラーメッセージを表示
- 話数管理.yamlが存在しない場合: ファイル名指定を促すメッセージ
- ファイルが存在しない場合: 話数管理には登録されているが実ファイルがない旨を表示

## 4. 実装詳細

### 4.1 引数パーサーの拡張
```python
def parse_episode_argument(arg: str, project_root: Path) -> Path:
    """話数またはファイル名を解析してファイルパスを返す"""
    try:
        # 数値として解析を試みる
        episode_number = int(arg)
        resolver = EpisodeNumberResolver(project_root)
        info = resolver.resolve_episode_number(episode_number)
        if not info.exists:
            raise FileNotFoundError(f"話数{episode_number}のファイルが存在しません: {info.file_path}")
        return info.file_path
    except ValueError:
        # 数値でない場合はファイル名として処理
        return Path(arg)
```

### 4.2 CLIコマンドの修正
- quality_check関数の最初に引数解析を追加
- 他のコマンド（write, complete-episode等）も同様に対応

## 5. テスト要件

### 5.1 単体テスト
- parse_episode_argumentの正常系・異常系テスト
- 数値入力、ファイル名入力、無効な入力のテスト

### 5.2 統合テスト
- CLIコマンドが話数指定で正しく動作することを確認
- エラーメッセージが適切に表示されることを確認

## 6. 実装チェックリスト

- [x] parse_episode_argument関数の実装
- [x] quality_checkコマンドへの統合
- [x] エラーハンドリングの実装
- [x] 単体テストの作成
- [x] 統合テストの作成
- [ ] 既存テストの修正
- [ ] ドキュメントの更新
