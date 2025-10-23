MCP サーバーの標準出力汚染防止ガイド（Python）

概要
- 目的: `stdout` は MCP の JSON-RPC 出力のみ、ログ/警告/例外は `stderr` に完全分離。
- 実装: `bootstrap_stdio.py` を import するだけで、ロギング・警告の経路と例外フックを設定。
- 検出: 開発/CI で `MCP_STRICT_STDOUT=1` を有効化し、誤って `print()` したら即失敗。
- 検証: CI とローカルで `MCP_STRICT_STDOUT=1` を有効にし、stdout が MCP フレームのみであることを実行時に確認。

統合ポイント（このリポジトリ）
- 主要エントリでブートストラップを読み込み済み
  - `src/mcp_servers/noveler/main.py`
  - `src/mcp_servers/local_context/main.py`
  - `archive/demo_servers/mcp_server*.py` (アーカイブ)
- dist ラッパー生成: CIは `scripts/ci/ensure_dist_wrapper.py` で `dist/mcp_servers/noveler/main.py` を用意、ローカルは `make build-dist-wrapper` で同等に生成可能。\n  さらに CI では `STRICT_DIST_WRAPPER=1 python scripts/ci/check_dist_wrapper.py` を実行し、必須パスの不整合（dist 未生成 / 設定が dist を参照していない）を検出した場合は即時失敗とします.
- MCP設定: `.mcp/config.json` の `args[0]` はスクリプトパス（`-u` は使用しない）。非バッファリングは `PYTHONUNBUFFERED=1`（env）で付与。
- Codex/Claude 用設定
  - `codex.mcp.json` の `noveler-dev` に `MCP_STRICT_STDOUT=1` を付与済み（開発時は常時ガード）
- Pytest 実行時のテスト環境
  - `tests/conftest.py` で以下をセッション全体に適用
    - `MCP_STRICT_STDOUT=1`（誤った stdout 出力を即検知）
    - `MCP_STDIO_SAFE=1`（コンソール等は stderr を使用）
    - `PYTHONUNBUFFERED=1`（バッファリング由来のズレを抑止）

使い方
1) サーバー起動コードの先頭でブートストラップ
```
import bootstrap_stdio
from bootstrap_stdio import logging, mcp_write

logging.info("server starting")
# SDKを利用する場合はSDKに任せる。直書きが必要なら:
# mcp_write({"jsonrpc": "2.0", "id": 1, "result": None})
```

2) 開発時に stdout ガードを有効化
```
MCP_STRICT_STDOUT=1 python your_server.py
```
`print()` が `stdout` を使うと例外になります。ログは `logging.*` を使ってください（`stderr`へ出力）。

テスト時（pytest）
- 既定で `MCP_STRICT_STDOUT=1` が有効（`tests/conftest.py`）
- サブプロセスも親環境を継承するため、基本的に自動でガードが効きます
- 特定テストのみ一時的に無効化したい場合:
  - pytest で全体無効化: `MCP_STRICT_STDOUT=0 pytest -q`
  - テストコード内（例: monkeypatch）:
    ```py
    def test_something(monkeypatch):
        monkeypatch.setenv("MCP_STRICT_STDOUT", "0")
        # あるいは create_subprocess_exec(..., env={**os.environ, "MCP_STRICT_STDOUT": "0"})
    ```

Codex/Claude 設定（codex.mcp.json）
- `noveler-dev` では `MCP_STRICT_STDOUT=1` を同梱済み
- pytest は `codex.mcp.json` を読みません（テストは Python から直接起動）
- そのため、テスト時の有効化は `tests/conftest.py` で行っています

3) CI での確認
CI では `MCP_STRICT_STDOUT=1` を有効にした pytest や統合テストで stdout を監視し、MCP フレームのみが出力されることを保証する。専用スクリプトは不要になったため削除済み。

設計ポイント
- `stdout` は MCP プロトコル専用: `mcp_write()` は `Content-Length` ヘッダ＋JSON本文をバイナリで書き込みます。
- ログ一元化: `logging.basicConfig(stream=sys.stderr, ...)` で `stderr` 固定。`warnings` も logging に取り込み。
- 例外はフェイルファスト: 予期せぬ例外は `stderr` にスタックトレースを出し、即時終了。
- ガード方針: SDK の stdout 出力を壊さないため、`sys.stdout` の低レベル書き換えは避け、開発時は `print()` を検出して失敗させます。
 - 追加の安全策: `MCP_STDIO_SAFE=1` でコンソールや独自ロガーを `stderr` に固定（本番・MCP環境推奨）

同梱ファイル
- `bootstrap_stdio.py` — ブートストラップ本体

備考: 以前同梱していたデモサーバ（`demo_server_*.py`）は整理のため`archive/demo_servers/`に移動しました。最新の利用例は本ドキュメント内のコードスニペットをご参照ください（完全な履歴はGit履歴へ）。

備考
- 依存ライブラリがバナーや進捗を `stdout` に出す場合は、そのライブラリの quiet/silent オプションを有効化してください。抑止できない場合はサブプロセス実行で `stdout` を親が回収し、プロトコルペイロードに詰め替える設計を検討します。
 - `sys.stdout.write` の全面差し替えは推奨しません（MCP SDK出力を壊す恐れがあるため）。本ガードは `print()` 誤用検出に留めています。

JSON Interaction Format
- tools/list: returns `{"jsonrpc":"2.0","id":<id>,"result":{"tools":[{name,description,inputSchema},...]}}`
- tools/call: returns `{"jsonrpc":"2.0","id":<id>,"result":{"content":[{"type":"text","text":"{...json...}"}]}}`
- initialize: returns `{"jsonrpc":"2.0","id":<id>,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":false}},"serverInfo":{"name":"noveler","version":"0.1.0"}}}`
- Notes: stdout carries only JSON-RPC frames; logs go to stderr. MD


Tool Options (selected)
- check_readability:
  - input properties:
    - episode_number: integer (required)
    - project_name: string (optional)
    - file_path: string (optional; overrides episode)
    - check_aspects: ["sentence_length","vocabulary_complexity","readability_score"] (optional)
    - exclude_dialogue_lines: boolean (default false) — 会話行（「…」/『…』）を文長チェックから除外
  - output: { success, score, issues[], metadata{ average_sentence_length, file_path, file_hash } }

Examples
- Exclude dialogue lines in readability check (stdio JSON-RPC):
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "check_readability",
    "arguments": {
      "episode_number": 1,
      "exclude_dialogue_lines": true,
      "check_aspects": ["sentence_length","readability_score"]
    }
  }
}
```
