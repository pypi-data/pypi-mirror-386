# SPEC-COUNT-001: Unicode文字数詳細分析機能

**作成日**: 2025-08-28
**更新日**: 2025-08-28
**ステータス**: 設計中
**実装者**: Claude Code
**レビュー者**: -

## 概要

小説執筆時の文字数を正確かつ詳細に分析する機能を実装する。現在LLMが手動で文字数をカウントしているが、MCPサーバー側で高速・正確に処理することで執筆品質向上を図る。

## 背景・課題

### 現在の問題
1. **LLMによる文字数カウント**：不正確で時間がかかる
2. **品質基準の定量化不足**：A38ガイドラインの「1行40字以内」「1文100字以内」等の基準が自動チェックされていない
3. **問題箇所の特定困難**：長すぎる文や行を見つけるのに時間がかかる

### 解決策
MCPサーバー側でUnicode文字数を詳細分析し、品質基準との照合まで自動化する。

## 要件

### 機能要件

#### FR-001: 基本文字数カウント
- **目的**: Unicode日本語文字数の正確なカウント
- **詳細**:
  - 全体文字数（ひらがな/カタカナ/漢字/英数字/記号の内訳付き）
  - 改行文字・空白文字も含めた正確なカウント
  - A38ガイドラインで定義された「Unicode文字数」基準に準拠

#### FR-002: 詳細構造分析
- **目的**: 行・文・段落レベルの詳細分析
- **詳細**:
  - **行分析**: 各行の文字数、改行位置の特定
  - **文分析**: 句点（。！？）で区切られた文の文字数
  - **段落分析**: 空行で区切られた段落の文字数・文数

#### FR-003: ハッシュID指定機能
- **目的**: 特定の行・文・段落を一意に識別
- **詳細**:
  - 各行・文・段落にMD5ハッシュ（先頭8文字）を付与
  - ハッシュIDによる特定箇所の文字数確認
  - LLMが「行ID: abc12345の文字数を確認」のように指定可能

#### FR-004: 品質基準自動チェック
- **目的**: A38ガイドライン基準との自動照合
- **詳細**:
  - 1行40字超過の警告
  - 1文100字超過の警告
  - スマホ読みやすさ基準との照合
  - カスタム閾値の設定可能

### 非機能要件

#### NFR-001: パフォーマンス
- 8000字程度のテキスト分析を1秒以内で完了
- メモリ使用量は分析対象テキストの5倍以下

#### NFR-002: 可用性
- MCPサーバーとして安定動作
- エラー時の適切なフォールバック

## アーキテクチャ設計

### FC/IS（Functional Core / Imperative Shell）準拠

#### Functional Core（純粋関数層）
```
src/noveler/domain/services/text_analysis_service.py
```
- **責務**: テキスト分析の純粋なロジック
- **特徴**: 副作用なし、決定論的、テスト可能
- **入出力**: 文字列 → 分析結果データクラス

#### Imperative Shell（副作用層）
```
src/noveler/application/use_cases/text_analysis_use_case.py
src/noveler/presentation/cli/commands/count_commands.py
src/mcp_servers/noveler/text_analysis_server.py
```
- **責務**: ファイルI/O、CLI、MCPサーバー統合
- **特徴**: 薄いラッパー、外部システムとの境界

## データ構造

### 分析結果
```python
@dataclass
class TextAnalysisResult:
    """テキスト分析結果"""
    total_characters: int          # 総文字数
    total_lines: int               # 総行数
    total_sentences: int           # 総文数
    total_paragraphs: int          # 総段落数
    breakdown: CharacterBreakdown  # 文字種別内訳
    lines: List[LineInfo]          # 行詳細情報
    sentences: List[SentenceInfo]  # 文詳細情報
    paragraphs: List[ParagraphInfo] # 段落詳細情報
    quality_warnings: List[QualityWarning] # 品質警告

@dataclass
class LineInfo:
    """行情報"""
    id: str              # ハッシュID（MD5先頭8文字）
    line_number: int     # 行番号（1始まり）
    text: str           # テキスト内容
    char_count: int     # 文字数
    is_empty: bool      # 空行かどうか

@dataclass
class SentenceInfo:
    """文情報"""
    id: str                 # ハッシュID
    sentence_number: int    # 文番号（1始まり）
    text: str              # 文内容
    char_count: int        # 文字数
    start_line: int        # 開始行
    end_line: int          # 終了行
    terminator: str        # 終端記号（。！？など）

@dataclass
class QualityWarning:
    """品質警告"""
    type: str              # warning種別
    target_id: str         # 対象のハッシュID
    message: str           # 警告メッセージ
    severity: str          # 重要度（info/warning/error）
```

## インターフェース仕様

### CLI コマンド
```bash
# 基本的な文字数カウント
/noveler count --file episode001.md

# 詳細分析（全データ出力）
/noveler count --file episode001.md --detail-level full

# 特定行の確認
/noveler count --file episode001.md --line 100

# 特定範囲の確認
/noveler count --file episode001.md --lines 100-150

# ハッシュIDでの特定
/noveler count --file episode001.md --target-id abc12345

# カスタム警告閾値
/noveler count --file episode001.md --warn-long-line 35 --warn-long-sentence 80

# JSON出力（MCP連携用）
/noveler count --file episode001.md --format json
```

### MCP サーバー API
```python
# テキスト分析ツール
{
    "tool": "analyze_text",
    "arguments": {
        "file_path": "60_作業ファイル/episode001_step10.md",
        "analysis_type": "full",  # summary/lines/sentences/paragraphs/full
        "target_id": null,        # 特定箇所指定用ハッシュID
        "warn_long_line": 40,
        "warn_long_sentence": 100
    }
}

# レスポンス例
{
    "success": true,
    "result": {
        "summary": {
            "total_characters": 8523,
            "total_lines": 234,
            "total_sentences": 89,
            "total_paragraphs": 12,
            "average_line_length": 36.4,
            "average_sentence_length": 95.8
        },
        "breakdown": {
            "hiragana": 3421,
            "katakana": 234,
            "kanji": 2156,
            "alphabet": 123,
            "numbers": 45,
            "punctuation": 2544
        },
        "quality_warnings": [
            {
                "type": "long_sentence",
                "target_id": "sent_abc123",
                "message": "文が156文字です（推奨: 100文字以内）",
                "severity": "warning"
            }
        ],
        "lines": [...],      # detail-level=fullの場合のみ
        "sentences": [...],  # detail-level=fullの場合のみ
        "paragraphs": [...]  # detail-level=fullの場合のみ
    }
}
```

## 実装計画

### Phase 1: Functional Core実装
1. `TextAnalysisService`（純粋関数）
2. データクラス群
3. 単体テスト

### Phase 2: Imperative Shell実装
1. `TextAnalysisUseCase`（アプリケーション層）
2. CLI コマンド
3. MCPサーバー統合

### Phase 3: 品質ゲート統合
1. A38ガイドライン基準との連携
2. `/noveler write`コマンドからの自動呼び出し
3. 品質レポート生成

## テスト方針

### 単体テスト（Functional Core）
- 文字数カウントの正確性
- ハッシュID生成の一意性
- 品質チェック基準の妥当性
- エッジケース（空文字、特殊文字等）

### 統合テスト（Imperative Shell）
- ファイル読み込み
- CLI コマンド実行
- MCPサーバー通信

### E2Eテスト
- 実際の小説原稿での分析
- `/noveler write`との連携

## 成功基準

1. **機能性**: Unicode文字数を100%正確にカウント
2. **パフォーマンス**: 8000字の分析を1秒以内
3. **使いやすさ**: LLMから簡単にMCP経由で呼び出し可能
4. **品質向上**: A38基準違反の自動検出率90%以上

## リスク・制約

### 技術的リスク
- Unicode正規化の複雑性
- 大容量テキストでのメモリ使用量

### 運用リスク
- MCPサーバーの可用性
- 既存コマンドとの競合

### 制約
- Python標準ライブラリのみ使用（外部依存最小化）
- 既存のMCPサーバーインフラ活用

## 参考資料

- A38_執筆プロンプトガイド.md（文字数基準）
- B20_Claude_Code開発作業指示書.md（開発プロセス）
- CODEMAP.yaml（アーキテクチャ構成）
- src/noveler/infrastructure/nlp/morphological_analyzer.py（既存分析機能）
