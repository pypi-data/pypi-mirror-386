# B31_MCPマイクロサービス設計ガイド

最終更新: 2025-09-02
バージョン: v1.0.0
対象: システム開発者・アーキテクト

## 📋 概要

小説執筆支援システムにおけるMCPツールのマイクロサービス化設計原則と実装指針。単一責任・独立実行・再実行可能性を核とした効率的なアーキテクチャの設計ガイド。

### 🎯 設計目的

- **LLMツール選択精度の向上**: 目的明確なツール名による適切な選択
- **修正サイクルの効率化**: チェック→修正→再チェックの最適化
- **並列実行による高速化**: 独立性を活かした並列処理
- **拡張性の確保**: 新機能追加の容易性

---

## 🏗️ 設計原則（SPEC-MCP-001準拠）

### 1. コア原則

#### 1.1 単一責任原則（Single Responsibility Principle）
```
❌ 悪い例: check_all → 全チェックを1つのツールで実行
✅ 良い例: check_basic, check_story_elements, check_writing_expression → 各々が専門的なチェックを実行
```

**メリット**:
- LLMが正確にツールを選択できる
- エラー発生時の影響範囲が限定される
- 個別の改善・拡張が容易

#### 1.2 独立性（Independence）
```python
# 各ツールは独立して実行可能
mcp__noveler__check_story_elements(episode=3)  # 他のツールに依存しない
mcp__noveler__check_writing_expression(episode=3)  # 独立して実行可能
```

**実装要件**:
- 他のツールの実行状態に依存しない
- 必要な情報は引数で明示的に受け取る
- 共有状態への依存を最小化

#### 1.3 再実行可能性（Idempotency）
```python
# 同じ入力に対して同じ結果を返す（冪等性）
result1 = mcp__noveler__check_basic(episode=1)
result2 = mcp__noveler__check_basic(episode=1)
assert result1.issues == result2.issues  # 同じ問題を検出
```

#### 1.4 段階的修正対応（Incremental Correction）
```python
# ワークフロー例
issues = mcp__noveler__noveler_check(episode=1)  # 全問題を発見
mcp__noveler__check_fix(episode=1, fix_level="safe")  # 安全な修正のみ
remaining = mcp__noveler__check_basic(episode=1)  # 基本問題の再チェック
```

### 2. 命名規則

#### 2.1 主要ツール
- **動作**を表す動詞を使用
- シンプルで理解しやすい名前

```
noveler_write  # 執筆（19ステップ一括：構造設計→品質保証）
noveler_check  # 品質チェック（3段階）
noveler_plot   # プロット生成
status         # 状況確認
noveler_complete # 完了処理
```

#### 2.2 専門ツール
- **機能**_**対象**形式
- アンダースコアで機能と対象を分離

```
write_stage             # 執筆_ステージ
write_resume            # 執筆_再開
check_basic             # チェック_基本
check_story_elements    # チェック_小説要素
check_writing_expression# チェック_文章表現
check_story_structure   # チェック_構成
```

> `plot_generate` / `plot_validate` / `init` は 2025-09-18 に廃止され、`noveler_plot` と品質チェック系ツールへ役割が統合されました。

#### 2.3 修正系ツール
- 統合的な修正機能
- レベル指定による制御

```
check_fix  # 修正（safe/standard/aggressiveレベル対応）
```

---

## 🔧 実装アーキテクチャ

### 1. ツール分類体系

```
MCPツール（17個）
├── 執筆関連（3個）
│   ├── noveler_write  # メイン執筆（19ステップ）
│   ├── write_stage    # 部分執筆
│   └── write_resume   # 再開
├── 品質チェック関連（7個）
│   ├── noveler_check  # 完全チェック
│   ├── check_basic    # 基本チェック
│   ├── check_story_elements     # 小説要素（68項目）
│   ├── check_story_structure    # ストーリー構成
│   ├── check_writing_expression # 文章表現
│   ├── check_rhythm   # 文章リズム
│   └── check_fix      # 自動修正
├── プロット関連（1個）
│   └── noveler_plot   # プロット生成
├── プロジェクト管理（2個）
│   ├── status         # 状況確認
│   └── noveler_complete # 完了処理
└── JSON変換（3個）
    ├── convert_cli_to_json
    ├── validate_json_response
    └── get_file_reference_info
```

> **執筆ツールのLLM制御**: `noveler_write` と関連ステップは `defaults.writing_steps.use_llm`（config/novel_config.yaml）で LLM 使用可否を切り替え可能。モック実行時は `false`、本番環境は `true` を推奨。テンプレートの必須キーと構造は `docs/technical/prompt_template_schema_v2.md` を満たす必要があります。

### 2. ツール仕様テンプレート

```python
@self.server.tool(
    name="tool_name",
    description="""具体的な機能説明 - 何をチェック/実行するかを明記:
    • 項目1: 具体的な内容
    • 項目2: 具体的な内容
    • 項目3: 具体的な内容""",
)
def tool_function(
    episode: int,                    # 必須パラメータ
    optional_param: bool = False,    # オプションパラメータ
    project_root: str | None = None  # 共通パラメータ
) -> str:
    """ツール実行関数"""
    try:
        # 実装ロジック
        result = self._execute_noveler_command(cmd, project_root)
        return self._format_tool_result(result, "操作名")
    except Exception as e:
        self.logger.exception("エラーログ")
        return f"エラーメッセージ: {e}"
```

### 3. 共通パラメータ設計

#### 3.1 必須パラメータ
```json
{
  "episode": {
    "type": "integer",
    "description": "対象エピソード番号",
    "required": true
  }
}
```

#### 3.2 オプションパラメータ
```json
{
  "project_root": {
    "type": "string",
    "description": "プロジェクトルートパス（省略時は現在のディレクトリ）",
    "required": false
  },
  "auto_fix": {
    "type": "boolean",
    "default": false,
    "description": "自動修正を有効化"
  },
  "fix_level": {
    "type": "string",
    "enum": ["safe", "standard", "aggressive"],
    "default": "safe",
    "description": "修正の積極性レベル"
  }
}
```

### 4. レスポンス形式統一

```json
{
  "success": "boolean",
  "command": "string",
  "output": "string",
  "stderr": "string",
  "execution_time_seconds": "number",
  "project_root": "string"
}
```

---

## 📊 品質チェック項目設計

### 1. 階層構造

```
品質チェック
├── Level 1: 基本チェック（check_basic）
│   ├── 文字数チェック
│   ├── 禁止表現検出
│   ├── 基本的な文章構造
│   └── 誤字脱字可能性
├── Level 2: 小説要素チェック（check_story_elements）
│   ├── 感情描写（12項目）
│   ├── キャラクター（12項目）
│   ├── ストーリー展開（12項目）
│   ├── 文章表現（12項目）
│   ├── 世界観・設定（10項目）
│   └── 読者エンゲージメント（10項目）
├── Level 3: 専門チェック
│   ├── ストーリー構成（check_story_structure）
│   ├── 文章表現力（check_writing_expression）
│   └── 文章リズム（check_rhythm）
└── Level 4: 自動修正（check_fix）
```

### 2. チェック項目詳細設計

#### 感情描写（12項目）の例
```yaml
emotion_expression:
  items:
    - name: "感情表現の具体性"
      description: "「怒り」「喜び」等の感情が具体的に表現されているか"
      weight: 8.5
    - name: "読者共感性"
      description: "読者が共感できる感情描写になっているか"
      weight: 9.0
    - name: "感情変化の論理性"
      description: "感情変化に論理性があるか"
      weight: 7.5
    # ... 残り9項目
```

---

## 🚀 実装手順

### 1. 新規ツール追加手順

#### Step 1: 機能要件定義
```markdown
## 新ツール: check_dialogue_naturalness
**目的**: 会話文の自然さをチェック
**対象**: キャラクターの台詞・会話の流れ
**チェック項目**:
- 口調の一貫性
- 話し方のキャラクター性
- 会話の自然な流れ
```

#### Step 2: ツール実装
```python
@self.server.tool(
    name="check_dialogue_naturalness",
    description="""会話文の自然さチェック - キャラクター台詞の品質を評価:
    • 口調の一貫性: そのキャラクターらしい話し方が維持されているか
    • キャラクター性: 個性的で魅力的な話し方になっているか
    • 会話の流れ: 自然で現実的な会話の展開になっているか""",
)
def check_dialogue_naturalness(episode: int, character_focus: str | None = None, project_root: str | None = None) -> str:
    # 実装
```

#### Step 3: テスト作成
```python
def test_check_dialogue_naturalness():
    result = mcp__noveler__check_dialogue_naturalness(episode=1)
    assert result.success
    assert len(result.issues) >= 0
```

#### Step 4: ドキュメント更新
- SPEC-MCP-001.mdの提供ツール一覧に追加
- B33_MCPツール統合ガイド.mdに使用例を追加

### 2. 既存ツール改良手順

#### Step 1: 改良要件定義
#### Step 2: 後方互換性確認
#### Step 3: 段階的ロールアウト
#### Step 4: 旧バージョン廃止予告

---

## 📈 パフォーマンス要件

### 1. 実行時間要件

| ツール分類 | 目標実行時間 | 最大許容時間 |
|-----------|-------------|-------------|
| 基本チェック | 1秒以下 | 3秒 |
| 小説要素チェック | 2秒以下 | 5秒 |
| 専門チェック | 2秒以下 | 5秒 |
| 執筆ツール | 30秒以下 | 60秒 |
| プロット生成 | 10秒以下 | 20秒 |

### 2. 並列実行設計

```python
# 複数チェックの並列実行
import asyncio

async def parallel_quality_check(episode: int):
    tasks = [
        check_basic_async(episode),
        check_story_elements_async(episode),
        check_rhythm_async(episode)
    ]
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### 3. キャッシュ戦略

```python
# 結果キャッシュによる高速化
@lru_cache(maxsize=128)
def cached_check_basic(episode: int, content_hash: str):
    # 同じコンテンツに対する重複チェックを回避
```

---

## 🔍 テスト戦略

### 1. ユニットテスト

```python
class TestMCPTools:
    def test_tool_independence(self):
        """各ツールの独立性テスト"""
        result1 = mcp__noveler__check_basic(episode=1)
        result2 = mcp__noveler__check_story_elements(episode=1)
        # 互いに影響しないことを確認

    def test_idempotency(self):
        """冪等性テスト"""
        result1 = mcp__noveler__check_basic(episode=1)
        result2 = mcp__noveler__check_basic(episode=1)
        assert result1 == result2
```

### 2. 統合テスト

```python
def test_workflow_integration():
    """ワークフロー統合テスト"""
    # 1. 基本チェック
    basic_result = mcp__noveler__check_basic(episode=1)

    # 2. 問題修正
    if not basic_result.success:
        mcp__noveler__check_fix(episode=1, fix_level="safe")

    # 3. 再チェック
    recheck_result = mcp__noveler__check_basic(episode=1)
    assert recheck_result.issues_count < basic_result.issues_count
```

---

## 📚 拡張ガイドライン

### 1. 新機能追加時の判断基準

#### 新ツール作成条件
- 単一の明確な責任を持つ
- 既存ツールでは対応できない専門性
- 独立して価値を提供できる

#### 既存ツール拡張条件
- 既存の責任範囲内
- 後方互換性を維持可能
- 複雑度が著しく増加しない

### 2. API設計指針

#### RESTful設計の適用
```
GET    /check/{episode}           # チェック実行
POST   /fix/{episode}             # 修正実行
GET    /status/{project}          # 状況確認
POST   /init/{project_name}       # 初期化
```

#### バージョニング戦略
```python
# セマンティックバージョニング
v1.0.0  # メジャー.マイナー.パッチ
v2.0.0  # 後方互換性を破る変更
v1.1.0  # 新機能追加（後方互換あり）
v1.0.1  # バグ修正
```

---

## 🔗 関連ドキュメント

- **SPEC-MCP-001.md**: 詳細仕様書
- **B33_MCPツール統合ガイド.md**: 実用ガイド
- **A32_執筆コマンドガイド.md**: コマンドリファレンス

---

**最終更新**: 2025-09-02
**バージョン**: v1.0.0
**責任者**: システムアーキテクト
