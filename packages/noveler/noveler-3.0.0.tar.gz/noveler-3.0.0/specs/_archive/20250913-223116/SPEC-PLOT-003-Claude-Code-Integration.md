# SPEC-PLOT-003: Claude Code統合プロット生成機能

## 概要

Claude Code環境内でのプロット生成機能の統合仕様。Claude CodeのAI能力を直接活用して高品質なエピソードプロットを自動生成する。

## 機能要件

### FR-001: Claude Code実行環境検出
- **要件**: Claude Code内での実行を自動検出
- **実装**: 環境変数やプロセス情報による判定
- **目的**: 実行環境に応じた処理分岐

### FR-002: Claude Code内プロット生成
- **要件**: Claude Code自身による高品質プロット生成
- **入力**: 章プロット情報、エピソード番号
- **出力**: 詳細なエピソードプロット（6000文字相当）
- **品質**: 手動作成レベルの創作品質

### FR-003: 自動YAML変換
- **要件**: Claude Code生成内容の構造化YAML変換
- **形式**: 既存テンプレートとの互換性維持
- **メタデータ**: 生成情報の自動記録

### FR-004: ファイル自動保存
- **要件**: 生成プロットの自動ファイル保存
- **命名**: `第XXX話_タイトル_Claude生成.yaml`
- **場所**: プロジェクト内話別プロットディレクトリ

## 技術仕様

### TS-001: 実行環境検出ロジック
```python
def is_running_in_claude_code() -> bool:
    """Claude Code実行環境の検出"""
    # 1. 環境変数チェック
    if os.environ.get('CLAUDE_CODE_SESSION'):
        return True

    # 2. プロセス名チェック
    if 'claude' in sys.argv[0].lower():
        return True

    # 3. 実行パスチェック
    if 'claude-code' in os.getcwd():
        return True

    return False
```

### TS-002: Claude Code統合生成フロー
```python
def _generate_claude_plot_integrated(episode_number, chapter_plot_info, project_root):
    """Claude Code統合プロット生成"""
    if is_running_in_claude_code():
        # Claude Code内実行
        return _generate_with_claude_ai()
    else:
        # 外部CLI実行（手動連携モード）
        return _generate_manual_integration()
```

### TS-003: プロット生成プロンプト構造
```
小説「Fランク魔法使いはDEBUGログを読む」第{episode_number}話詳細プロット作成

【基本情報】
- エピソード番号: {episode_number}
- 章情報: {chapter_data}
- 既存エピソード情報: {episode_info}

【要求品質】
1. 三幕構成での詳細シーン展開（7-8シーン）
2. キャラクター成長描写（直人・あすか）
3. 技術要素の自然な組み込み
4. DEBUGログ能力の効果的活用
5. 次話への適切な伏線設置

【出力要件】
- 約6000文字の詳細プロット
- 各シーンの具体的内容
- キャラクター心理描写
- 技術的正確性の確保
```

## 実装方針

### IM-001: 段階的実装
1. **Phase 1**: 環境検出機能
2. **Phase 2**: Claude Code統合生成
3. **Phase 3**: YAML変換・保存
4. **Phase 4**: テスト・品質確認

### IM-002: フォールバック戦略
- Claude Code外実行時は手動連携モード
- エラー時は既存テンプレート生成
- 段階的品質劣化による安定性確保

### IM-003: 品質管理
- 生成内容の構造検証
- キャラクター一貫性チェック
- 技術要素の適切性確認

## 期待効果

### EF-001: 創作品質向上
- 手動作成レベルの高品質プロット
- 一貫したキャラクター描写
- 適切な技術要素の統合

### EF-002: 作業効率化
- 自動生成による時間短縮
- Claude Code能力の直接活用
- 人間による最小限の修正で完成

### EF-003: システム統合
- 既存ワークフローとの親和性
- CLIコマンド体系の統一
- プロジェクト構造との整合性

## 成功指標

### SI-001: 機能的指標
- Claude Code環境での100%動作
- 6000文字相当の詳細プロット生成
- YAML構造の完全準拠

### SI-002: 品質指標
- 手動作成プロットとの品質比較
- キャラクター一貫性スコア
- 技術要素統合の自然さ

### SI-003: 運用指標
- 生成時間の短縮率
- エラー発生率の最小化
- ユーザー満足度の向上

## 実装優先度

1. **High**: 環境検出・基本生成機能
2. **Medium**: YAML変換・ファイル保存
3. **Low**: 品質向上・追加機能

---

**策定日**: 2025-08-04
**策定者**: Claude Code統合開発チーム
**承認者**: プロジェクト管理者
**次回レビュー**: 実装完了後
