# EpisodeNumber Validation Audit Report

**調査日時**: 2025-10-11
**調査対象**: `src/noveler/application/use_cases/` 配下の104個のUseCaseファイル
**調査目的**: `episode_number`使用箇所のDDD準拠バリデーション実施状況の確認

---

## Executive Summary

### 現状評価

| カテゴリ | ファイル数 | 割合 | 説明 |
|---------|-----------|------|------|
| ✅ **OK（バリデーション実施済み）** | 14 | 13.5% | `EpisodeNumber` VO でバリデーション後、`.value` を使用 |
| ⚠️ **要注意（バリデーションバイパス）** | 30 | 28.8% | `request.episode_number` を直接Repository/Serviceに渡す |
| └ P0（高優先度）| 10 | 9.6% | 即座に修正推奨 |
| └ P1（中優先度）| 10 | 9.6% | 計画的に修正 |
| └ P2（低優先度）| 10 | 9.6% | リファクタリング時に対応 |
| ℹ️ **許容（Domain層定義）** | 0 | 0% | Domain Entity/Value Objectとして定義 |
| **その他** | 60 | 57.7% | `episode_number` を使用していない |

### 主要な発見事項

1. **模範実装が存在**: `integrated_writing_use_case.py`, `quality_check_command_use_case.py`, `stepwise_writing_use_case.py` が模範的なパターンを実装済み
2. **P0の10ファイルが深刻**: A31品質保証、主要執筆フロー等の中核機能でバリデーションバイパスが発生
3. **パターンの一貫性欠如**: UseCase間でバリデーション実施の有無が不統一

---

## 1. OK（バリデーション実施済み）: 14ファイル

### 模範実装トップ3

#### 1. `integrated_writing_use_case.py` ⭐⭐⭐

```python
# Line 169
def _create_session(self, request: IntegratedWritingRequest, session_id: str) -> IntegratedWritingSession:
    """セッション作成"""
    episode_number = EpisodeNumber(request.episode_number)  # ✅ 早期バリデーション

    return IntegratedWritingSession(
        session_id=session_id,
        episode_number=episode_number,  # Value Object を保持
        project_root=request.project_root,
        workflow_type=WritingWorkflowType.INTEGRATED,
        custom_requirements=request.custom_requirements.copy(),
    )
```

**評価ポイント**:
- API境界（`_create_session`）で早期バリデーション実施
- Value Objectをそのままセッションに保持
- 後続処理で `.value` プロパティを使用

#### 2. `quality_check_command_use_case.py` ⭐⭐⭐

```python
# Line 162-169
def _check_single_episode(self, request: QualityCheckCommandRequest):
    # Validate episode number with Value Object (DDD compliance)
    try:
        episode_number_vo = EpisodeNumber(request.episode_number)  # ✅ 早期バリデーション
    except ValueError as e:
        return QualityCheckCommandResponse(success=False, error_message=str(e))

    # Retrieve episode metadata
    episode_info = self.episode_repository.get_episode_info(
        request.project_name, episode_number_vo.value  # ✅ .value で渡す
    )
```

**評価ポイント**:
- try-except で ValueError をキャッチ
- エラーハンドリングが適切
- Repository層には `.value` プロパティで int を渡す

#### 3. `stepwise_writing_use_case.py` ⭐⭐⭐

```python
# Line 358-368
async def _prepare_work_context(
    self,
    request: StepwiseWritingRequest,
    target_steps: list[int]
) -> dict[str, Any]:
    """作業コンテキスト準備"""
    # Validate episode number with Value Object (DDD compliance)
    episode_number_vo = EpisodeNumber(request.episode_number)  # ✅ 早期バリデーション

    work_context = {
        "episode_number": episode_number_vo.value,  # ✅ Use validated value
        "episode_number_vo": episode_number_vo,  # ✅ Keep Value Object for domain operations
        "project_root": request.project_root,
        "target_steps": target_steps,
        "cached_results": {},
        "work_files": {}
    }
```

**評価ポイント**:
- 検証済み値（`.value`）と Value Object の両方を保持
- パフォーマンス最適化（`.value` アクセスの繰り返しを回避）
- 明確なコメントでDDD準拠を明示

### 完全リスト

1. ✅ `integrated_writing_use_case.py` - L169
2. ✅ `quality_check_command_use_case.py` - L164-169
3. ✅ `stepwise_writing_use_case.py` - L359-368
4. ✅ `pre_writing_check_use_case.py` - L212
5. ✅ `previous_episode_analysis_use_case.py`
6. ✅ `publish_preparation_use_case.py`
7. ✅ `smart_auto_enhancement_use_case.py` - L177
8. ✅ `episode_management_integration_use_case.py`
9. ✅ `enhanced_plot_generation_use_case.py`
10. ✅ `create_episode_from_plot.py`
11. ✅ `create_episode_use_case.py`
12. ✅ `auto_chaining_plot_generation_use_case.py`
13. ✅ `a31_detailed_evaluation_use_case.py`
14. ✅ `a31_claude_code_evaluation_use_case.py`

---

## 2. 要注意（バリデーションバイパス）: 30ファイル

### P0（高優先度・即座に修正推奨）: 10ファイル

#### 1. `a31_complete_check_use_case.py` 🔴 P0

**問題箇所**:
```python
# Line 85
episode_content = self._get_episode_content(request.project_name, request.episode_number)  # ❌

# Line 100
evaluation_context = self._prepare_evaluation_context(request.project_name, request.episode_number)  # ❌

# Line 348
def _get_episode_content(self, project_name: str, episode_number: int) -> str:
    return self._episode_repository.get_episode_content(project_name, episode_number)  # ❌
```

**影響範囲**: A31完全チェックは品質保証の中核機能
**修正推奨度**: P0 - 即座に修正すべき
**理由**: バリデーション欠落は品質保証プロセス全体の信頼性を損なう

**推奨修正**:
```python
async def execute(self, request: A31CompleteCheckRequest) -> A31CompleteCheckResponse:
    start_time = time.time()

    try:
        # ✅ 早期バリデーション（DDD準拠）
        episode_number_vo = EpisodeNumber(request.episode_number)

        # ✅ 検証済み値を使用
        episode_content = self._get_episode_content(request.project_name, episode_number_vo.value)
        evaluation_context = self._prepare_evaluation_context(request.project_name, episode_number_vo.value)
```

#### 2. `enhanced_writing_use_case.py` 🔴 P0

**問題箇所**:
```python
# Line 34
def __init__(
    self,
    project_root: str,
    episode_number: int,  # ❌ 生のintを受け取る
    console_service: IConsoleService | None = None,
) -> None:
    self.episode_number = episode_number  # ❌ バリデーションなしで保持
```

**影響範囲**: 包括的エラーハンドリング統合版
**修正推奨度**: P0 - 即座に修正すべき
**理由**: コンストラクタで受け取った値を検証せず後続処理で使用

**推奨修正**:
```python
def __init__(
    self,
    project_root: str,
    episode_number: int,
    console_service: IConsoleService | None = None,
) -> None:
    # ✅ 早期バリデーション
    self.episode_number_vo = EpisodeNumber(episode_number)
    self.episode_number = self.episode_number_vo.value
```

#### 3. `ten_stage_episode_writing_use_case.py` 🔴 P0

**問題箇所**:
```python
# Line 278
progress_start_request = TenStageProgressRequest(
    episode_number=request.episode_number,  # ❌
    project_root=request.project_root,
    operation="start"
)

# Line 583
dry_run_manuscript_path = path_service.get_manuscript_path(request.episode_number)  # ❌

# Line 1195
manuscript_path = path_service.get_manuscript_path(episode_number)  # ❌
```

**影響範囲**: 主要執筆フロー
**修正推奨度**: P0 - 即座に修正すべき
**理由**: 執筆プロセス全体で多用されており、影響範囲が広い

**推奨修正**:
```python
async def execute(self, request: FiveStageWritingRequest) -> FiveStageWritingResponse:
    # ✅ 早期バリデーション
    episode_number_vo = EpisodeNumber(request.episode_number)

    progress_start_request = TenStageProgressRequest(
        episode_number=episode_number_vo.value,  # ✅
        project_root=request.project_root,
        operation="start"
    )
```

#### 4-10. その他のP0ファイル

4. 🔴 `complete_episode_use_case.py` - L216
5. 🔴 `unified_context_analysis_use_case.py` - L446
6. 🔴 `viewpoint_aware_quality_check.py` - L107
7. 🔴 `narrative_depth_evaluation.py` - L37, L42, L68
8. 🔴 `claude_analysis_request_generation_use_case.py` - L308
9. 🔴 `plot_generation_use_case.py` - L41
10. 🔴 `quality_check_prompt_use_case.py` - L117, L203, L268

### P1（中優先度・計画的に修正）: 10ファイル

11. 🟠 `a31_auto_fix_use_case.py`
12. 🟠 `generate_episode_plot_use_case.py`
13. 🟠 `episode_management_sync_use_case.py`
14. 🟠 `plot_version_use_cases.py`
15. 🟠 `validate_plot_adherence_use_case.py`
16. 🟠 `track_writing_progress.py`
17. 🟠 `ten_stage_progress_use_case.py`
18. 🟠 `universal_prompt_request.py`
19. 🟠 `theme_uniqueness_verification_use_case.py`
20. 🟠 `session_based_analysis_use_case.py`

### P2（低優先度・リファクタリング時に対応）: 10ファイル

21. 🟡 `quality_record_enhancement_use_case.py`
22. 🟡 `prompt_generation_use_case.py`
23. 🟡 `ml_quality_evaluation_use_case.py`
24. 🟡 `episode_prompt_save_use_case.py`
25. 🟡 `interactive_plot_improvement_use_case.py`
26. 🟡 `interactive_writing_controller.py`
27. 🟡 `learning_data_accumulator.py`
28. 🟡 `staged_prompt_generation_use_case.py`
29. 🟡 `b18_eighteen_step_writing_use_case.py`
30. 🟡 `a31_batch_auto_fix_use_case.py`

---

## 3. 修正パターンテンプレート

### パターン1: execute メソッド冒頭でのバリデーション（推奨）

```python
async def execute(self, request: XxxRequest) -> XxxResponse:
    """実行メソッド（早期バリデーション）"""
    # ✅ DDD準拠: API境界での早期バリデーション
    episode_number_vo = EpisodeNumber(request.episode_number)

    # ✅ 以降は episode_number_vo.value を使用
    episode_content = self._get_episode_content(
        request.project_name,
        episode_number_vo.value
    )

    # Repository/Service呼び出しには常に .value を渡す
    result = self._repository.process(episode_number_vo.value)

    return XxxResponse(
        success=True,
        episode_number=episode_number_vo.value
    )
```

### パターン2: コンストラクタでのバリデーション

```python
def __init__(self, episode_number: int, **kwargs):
    """コンストラクタ（早期バリデーション）"""
    # ✅ 早期バリデーション
    self.episode_number_vo = EpisodeNumber(episode_number)
    self.episode_number = self.episode_number_vo.value

    # 以降のメソッドでは self.episode_number を使用
```

### パターン3: work_context パターン（StepwiseWritingUseCase方式）

```python
async def _prepare_work_context(
    self,
    request: XxxRequest,
    **kwargs
) -> dict[str, Any]:
    """作業コンテキスト準備"""
    # ✅ 早期バリデーション
    episode_number_vo = EpisodeNumber(request.episode_number)

    work_context = {
        "episode_number": episode_number_vo.value,  # ✅ プリミティブ値（高速アクセス用）
        "episode_number_vo": episode_number_vo,  # ✅ Value Object（ドメイン操作用）
        # ... 他のコンテキスト
    }

    return work_context
```

### パターン4: エラーハンドリング付きバリデーション（推奨）

```python
async def execute(self, request: XxxRequest) -> XxxResponse:
    """実行メソッド（エラーハンドリング付き）"""
    try:
        # ✅ 早期バリデーション（例外キャッチ）
        episode_number_vo = EpisodeNumber(request.episode_number)
    except ValueError as e:
        # ✅ ユーザーフレンドリーなエラーメッセージ
        return XxxResponse(
            success=False,
            error_message=f"無効なエピソード番号: {e}"
        )

    # 正常処理
    result = self._process(episode_number_vo.value)
    return XxxResponse(success=True, result=result)
```

---

## 4. 契約違反の影響範囲

### 潜在的な問題

#### 1. 範囲外値の伝播

**シナリオ**:
```python
# ユーザー入力: episode_number = 10000
request = XxxRequest(episode_number=10000)

# ❌ バリデーションなしでRepository層まで到達
episode_content = repository.get_episode_content(project_name, 10000)

# Repository層でファイルシステムアクセス失敗
# → データ整合性の破壊リスク
```

**影響**:
- データベースやファイルシステムに範囲外の値が伝播
- 後続処理で予期しないエラーが発生
- デバッグが困難（どの層で問題が発生したか不明）

#### 2. エラーメッセージの不明瞭化

**バリデーションなしの場合**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/第10000話.md'
```

**バリデーションありの場合**:
```
ValueError: エピソード番号は9999以下である必要があります: 10000
```

**比較**:
- ❌ バリデーションなし: Repository層でのファイルシステムエラー（原因不明）
- ✅ バリデーションあり: Application層でのドメインルール違反（原因明確）

#### 3. テストの脆弱性

**バリデーションなしのテスト**:
```python
def test_execute_with_invalid_episode():
    """無効なエピソード番号でも処理が進む（問題）"""
    request = XxxRequest(episode_number=10000)
    response = use_case.execute(request)

    # ❌ Repository層でエラーが発生するまで処理が進む
    assert response.success is False
    assert "FileNotFoundError" in response.error_message  # 不明瞭
```

**バリデーションありのテスト**:
```python
def test_execute_with_invalid_episode():
    """無効なエピソード番号で即座にエラー"""
    request = XxxRequest(episode_number=10000)
    response = use_case.execute(request)

    # ✅ Application層で即座にエラー
    assert response.success is False
    assert "9999以下である必要があります" in response.error_message  # 明確
```

### DDD原則との整合性

#### Value Object の責務

```python
@dataclass(frozen=True)
class EpisodeNumber:
    """エピソード番号を表す値オブジェクト"""
    value: int

    def __post_init__(self) -> None:
        """バリデーション（ドメイン不変条件の保護）"""
        if not isinstance(self.value, int):
            raise ValueError("エピソード番号は整数である必要があります")
        if self.value < 1:
            raise ValueError(f"エピソード番号は1以上である必要があります: {self.value}")
        if self.value > 9999:
            raise ValueError(f"エピソード番号は9999以下である必要があります: {self.value}")
```

**責務**: ドメインルール（1 ≤ value ≤ 9999）の保護

#### Application Layer の責務

```python
async def execute(self, request: XxxRequest) -> XxxResponse:
    """Application層の責務: API境界での早期バリデーション"""
    # ✅ API境界でValue Objectを構築 → ドメインルール検証
    episode_number_vo = EpisodeNumber(request.episode_number)

    # ✅ Repository層には検証済みのプリミティブ値を渡す
    result = self._repository.process(episode_number_vo.value)
```

**責務**: API境界での早期バリデーション、プリミティブ型からValue Objectへの変換

#### 現状の問題

```python
# ❌ 問題: Application層でプリミティブ型をそのまま使用
async def execute(self, request: XxxRequest) -> XxxResponse:
    # バリデーションをバイパス
    result = self._repository.process(request.episode_number)
```

**問題点**:
- Value Object の責務（ドメイン不変条件の保護）を無視
- Application層の責務（API境界での早期バリデーション）を放棄
- DDD の境界付けられたコンテキスト（Bounded Context）の破壊

---

## 5. 推奨アクション

### Phase 1: 即座に修正（P0の10ファイル）

**期間**: 1-2日
**優先度**: 最高
**対象**: 中核機能、高頻度使用UseCase

1. ✅ `stepwise_writing_use_case.py` - **完了** (Commit 6a9662c4, e9723e42)
2. 🔴 `a31_complete_check_use_case.py`
3. 🔴 `enhanced_writing_use_case.py`
4. 🔴 `ten_stage_episode_writing_use_case.py`
5. 🔴 `complete_episode_use_case.py`
6. 🔴 `unified_context_analysis_use_case.py`
7. 🔴 `viewpoint_aware_quality_check.py`
8. 🔴 `narrative_depth_evaluation.py`
9. 🔴 `claude_analysis_request_generation_use_case.py`
10. 🔴 `plot_generation_use_case.py`

**実施手順**:
1. ファイルを1つずつ修正
2. 既存テスト実行で影響確認
3. 必要に応じて新規テスト追加
4. コミット → レビュー

### Phase 2: 計画的に修正（P1の10ファイル）

**期間**: 1-2週間
**優先度**: 高
**対象**: 補助機能、中頻度使用UseCase

11-20. 🟠 P1ファイル（リスト省略）

**実施手順**:
1. Sprint計画に組み込み
2. ファイルをグループ化（機能別）
3. 一括修正 → 統合テスト
4. コミット → レビュー

### Phase 3: リファクタリング時に対応（P2の10ファイル）

**期間**: 1-3ヶ月
**優先度**: 中
**対象**: レガシー機能、低頻度使用UseCase

21-30. 🟡 P2ファイル（リスト省略）

**実施手順**:
1. 大規模リファクタリング時に統一的に対応
2. 技術的負債としてバックログに記録
3. 優先度に応じて段階的に対応

### Phase 4: Request クラス自体での事前バリデーション（長期）

**期間**: 3-6ヶ月
**優先度**: 低（将来的な改善）
**対象**: 全UseCaseに適用

**実装例**:
```python
@dataclass
class XxxRequest(SerializableRequest):
    """リクエスト（VO内包型）"""

    episode_number: int

    def __post_init__(self) -> None:
        """初期化後バリデーション"""
        # ✅ ValueObjectで検証（無効な値は例外送出）
        EpisodeNumber(self.episode_number)
```

**メリット**:
- Request作成時点で自動的にバリデーション実施
- UseCase内での冗長なバリデーションコードを削減
- DDD原則への完全準拠

**デメリット**:
- Request クラスがValue Objectに依存（循環依存のリスク）
- 既存コードへの影響が大きい

---

## 6. まとめ

### 達成状況

| フェーズ | 対象 | 完了 | 残存 | 完了率 |
|---------|------|------|------|--------|
| **Phase 1 (P0)** | 10 | 1 | 9 | 10% |
| **Phase 2 (P1)** | 10 | 0 | 10 | 0% |
| **Phase 3 (P2)** | 10 | 0 | 10 | 0% |
| **合計** | 30 | 1 | 29 | 3.3% |

### 次のステップ

1. **P0の残り9ファイルを優先的に修正** (1-2日)
2. **修正パターンのドキュメント化** (`docs/ddd/validation_patterns.md`)
3. **CI/CDへのバリデーションチェック統合** (importlinter等)
4. **P1ファイルの計画的修正** (次回Sprint)

### 期待される効果

1. **ドメインルール違反の早期検出**: API境界で不正な値をブロック
2. **エラーメッセージの明確化**: ユーザーフレンドリーなフィードバック
3. **テストカバレッジの向上**: 異常値のテストケースを網羅
4. **DDD原則への準拠**: Value Object の責務を完全に尊重
5. **保守性の向上**: 一貫したバリデーションパターンで可読性向上

---

**調査完了日時**: 2025-10-11
**調査実施者**: Claude Code (Sonnet 4.5)
**関連コミット**: 6a9662c4, e9723e42
**参照ドキュメント**: CLAUDE.md, AGENTS.md, SPEC-MCP-001
