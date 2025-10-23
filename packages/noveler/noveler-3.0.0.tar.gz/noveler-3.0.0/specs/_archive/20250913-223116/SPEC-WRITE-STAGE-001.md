# SPEC-WRITE-STAGE-001: 段階別執筆MCPツール仕様書

## 1. 概要

### 1.1 目的
`noveler write`コマンドの10段階執筆プロセスを、個別のMCPツールとして実装し、Claude Code内でインタラクティブに実行可能にする。

### 1.2 背景
- 現状：`noveler write`は10段階を自動的に連続実行する
- 課題：段階ごとの確認・調整ができない、部分的な再実行が困難
- 解決：各段階を独立したMCPツールとして公開し、柔軟な実行を可能にする

## 2. 設計方針

### 2.1 基本原則
- **段階独立性**：各段階は独立して実行可能
- **データ連携**：前段階の出力を次段階で活用可能
- **プロンプト生成**：各ツールはClaude用プロンプトを生成
- **セッション管理**：段階間でセッション情報を保持

### 2.2 命名規則
段階番号を含まない、意味的に明確な名前を使用：
- ❌ 悪い例：`write_stage1_plot_preparation`
- ✅ 良い例：`prepare_plot_data`

## 3. MCPツール定義

### 3.1 ツール一覧

| ツール名 | 対応段階 | 説明 |
|---------|---------|------|
| `prepare_plot_data` | データ準備 | プロット・設定データの収集と準備 |
| `analyze_plot_structure` | プロット分析 | プロット構造の分析と設計 |
| `design_emotional_flow` | 感情設計 | 感情・関係性の流れを設計 |
| `design_humor_elements` | ユーモア設計 | ユーモア・魅力要素の設計 |
| `design_character_dialogue` | 対話設計 | キャラクター心理と対話の設計 |
| `design_scene_atmosphere` | 場面設計 | 場面演出と雰囲気の設計 |
| `adjust_logic_consistency` | 論理調整 | 論理整合性の確認と調整 |
| `write_manuscript_draft` | 原稿執筆 | 原稿の執筆実行 |
| `refine_manuscript_quality` | 品質改善 | 原稿品質の仕上げ |
| `finalize_manuscript` | 最終調整 | 最終調整と完成処理 |

### 3.2 共通パラメータ

すべてのツールで共通：
```python
{
    "episode": int,           # エピソード番号（必須）
    "project_root": str,      # プロジェクトルート（省略可）
    "session_id": str,        # セッションID（継続実行時）
    "previous_output": dict,  # 前段階の出力（段階間連携時）
}
```

### 3.3 各ツールの詳細

#### 3.3.1 `prepare_plot_data`
**目的**：プロットと設定データの準備
**入力**：
- episode: エピソード番号
- project_root: プロジェクトパス

**出力**：
```json
{
    "success": true,
    "plot_content": "プロット内容",
    "settings": {...},
    "characters": [...],
    "prompt": "Claude用プロンプト",
    "session_id": "uuid"
}
```

#### 3.3.2 `analyze_plot_structure`
**目的**：プロット構造の分析
**入力**：
- episode: エピソード番号
- previous_output: prepare_plot_dataの出力

**出力**：
```json
{
    "success": true,
    "structure_analysis": {...},
    "key_scenes": [...],
    "turning_points": [...],
    "prompt": "Claude用プロンプト",
    "session_id": "uuid"
}
```

#### 3.3.3 `design_emotional_flow`
**目的**：感情・関係性の設計
**入力**：
- episode: エピソード番号
- previous_output: analyze_plot_structureの出力

**出力**：
```json
{
    "success": true,
    "emotional_arc": {...},
    "relationship_dynamics": {...},
    "prompt": "Claude用プロンプト",
    "session_id": "uuid"
}
```

（以下、同様の形式で各ツールを定義）

## 4. 実装詳細

### 4.1 実装ファイル
`src/noveler/infrastructure/json/mcp/servers/json_conversion_server.py`

### 4.2 実装方法
```python
def _register_staged_writing_tools(self) -> None:
    """段階別執筆ツール登録"""

    @self.server.tool(
        name="prepare_plot_data",
        description="プロットと設定データを準備し、執筆の基盤を構築"
    )
    async def prepare_plot_data(
        episode: int,
        project_root: str | None = None
    ) -> str:
        # 実装
        pass

    # 他のツールも同様に実装
```

### 4.3 セッション管理
```python
class WritingSessionManager:
    """執筆セッション管理"""

    def create_session(self, episode: int) -> str:
        """新規セッション作成"""

    def save_stage_output(self, session_id: str, stage: str, output: dict):
        """段階出力の保存"""

    def load_session(self, session_id: str) -> dict:
        """セッション読み込み"""
```

## 5. 使用例

### 5.1 新規執筆（全段階実行）
```python
# Stage 1: データ準備
result1 = await prepare_plot_data(episode=1)

# Claude内で確認・編集

# Stage 2: プロット分析
result2 = await analyze_plot_structure(
    episode=1,
    previous_output=result1
)

# 以下、順次実行
```

### 5.2 部分再実行
```python
# 感情設計のみやり直し
result = await design_emotional_flow(
    episode=1,
    session_id="existing_session_id"
)
```

### 5.3 特定段階からの継続
```python
# 原稿執筆から再開
result = await write_manuscript_draft(
    episode=1,
    session_id="existing_session_id"
)
```

## 6. 利点

### 6.1 柔軟性
- 必要な段階のみ実行可能
- 各段階での手動調整が可能
- 部分的な再実行が容易

### 6.2 効率性
- トークン使用量の削減
- 問題のある段階のみ修正
- Claude Codeとの対話的な作業

### 6.3 品質向上
- 段階ごとの品質確認
- 人間による中間チェック
- 細かな調整が可能

## 7. 移行計画

### 7.1 段階的実装
1. 仕様書承認
2. 基本ツール実装（prepare_plot_data, write_manuscript_draft）
3. 全ツール実装
4. セッション管理機能追加
5. テストと最適化

### 7.2 後方互換性
- 既存の`noveler write`コマンドは維持
- 新ツールは追加機能として実装
- 段階的な移行をサポート

## 8. テスト計画

### 8.1 単体テスト
- 各ツールの独立動作確認
- エラーハンドリング
- パラメータ検証

### 8.2 統合テスト
- 段階間のデータ連携
- セッション管理
- 全段階通しての実行

## 9. 成功基準

- [ ] 10個のMCPツールが独立して動作
- [ ] 段階間でデータ連携が可能
- [ ] Claude Code内で完結する執筆フロー
- [ ] 部分再実行が正常に機能
- [ ] セッション管理が適切に動作

## 10. 更新履歴

- 2025-01-02: 初版作成
- 作成者: Claude Code Assistant
- レビュー待ち
