---
spec_id: SPEC-QUALITY-001
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: QUALITY
sources: [E2E, REQ]
tags: [quality]
---
# SPEC-QUALITY-001: A31原稿執筆チェックリスト自動修正システム

## 仕様書メタデータ

- **仕様書ID**: SPEC-QUALITY-001
- **タイトル**: A31原稿執筆チェックリスト自動修正システム
- **作成日**: 2025-07-28
- **最終更新**: 2025-09-04
- **バージョン**: 1.3
- **ステータス**: 実装済み
- **関連ドメイン**: QUALITY (品質管理)
- **実装優先度**: HIGH
- **要件ID**: REQ-QUALITY-001 (A31品質チェック68項目実装)

## 概要

A31_原稿執筆チェックリスト.yamlの68項目に対して、「評価→閾値判定→自動修正」のワークフローを提供する統合自動修正システム。各話毎のチェック結果をテンプレートから生成し、プロジェクトの50_管理資料フォルダに保存。手動チェックの負担を軽減し、執筆品質の継続的改善を支援する。

## 仕様変更（v1.2）

### チェック結果保存方式の変更
- **テンプレート**: `$GUIDE_ROOT/templates/A31_原稿執筆チェックリストテンプレート.yaml`
- **保存場所**: `$PROJECT_ROOT/50_管理資料/A31_チェックリスト/A31_チェックリスト_第XXX話.yaml`
- **フォルダ構造**: `50_管理資料/A31_チェックリスト/` (自動作成)
- **命名規則**: `A31_チェックリスト_第{話数:03d}話_{タイトル}.yaml`

## 背景・動機

### 現在の課題
1. **手動チェックの負担**: 68項目の手動確認は時間コストが高い
2. **品質の一貫性**: 人的確認による品質のばらつき
3. **修正作業の効率性**: 発見した問題の修正に追加時間が必要
4. **学習効果の限界**: 同じミスの反復発生

### 解決目標
1. **自動化率60%以上**: 42項目以上の自動処理実現
2. **修正精度95%以上**: フォーマット系・用語系の高精度修正
3. **処理時間短縮80%**: 手動確認時間の大幅削減
4. **品質向上**: 継続的な品質改善サイクル構築

## 機能要件

### 1. 自動評価・閾値判定システム

#### 1.1 評価エンジン
```python
class A31AutoEvaluationEngine:
    """A31チェックリスト項目の自動評価"""

    def evaluate_item(self, item_id: str, episode_file: Path) -> EvaluationResult:
        """個別項目の評価実行"""

    def evaluate_all_items(self, episode_file: Path) -> Dict[str, EvaluationResult]:
        """全項目の一括評価"""

    def get_threshold(self, item_id: str) -> Threshold:
        """項目別閾値の取得"""
```

#### 1.2 閾値設定
```yaml
# 閾値設定例
thresholds:
  A31-045: # 段落頭字下げ確認
    type: "percentage"
    value: 100.0  # 100%の段落が字下げ済み

  A31-042: # 品質スコア70点以上
    type: "score"
    value: 70.0

  A31-022: # 会話と地の文バランス
    type: "range"
    min: 30.0
    max: 40.0
```

### 2. 段階的自動修正システム

#### 2.1 修正レベル定義
```python
class FixLevel(Enum):
    SAFE = "safe"           # 確実な修正（フォーマット系）
    STANDARD = "standard"   # パターンベース修正
    INTERACTIVE = "interactive"  # 人的確認付き修正
```

#### 2.2 修正プロセッサー
```python
class A31AutoFixProcessor:
    """段階的自動修正の実行"""

    def apply_safe_fixes(self, file: Path, items: List[str]) -> FixResult:
        """レベル1: 確実な修正"""

    def apply_pattern_fixes(self, file: Path, items: List[str]) -> FixResult:
        """レベル2: パターンベース修正"""

    def apply_interactive_fixes(self, file: Path, items: List[str]) -> FixResult:
        """レベル3: 人的確認付き修正"""
```

### 3. 具体的修正機能

#### 3.1 フォーマット系修正（完全自動）
- **A31-045**: 段落頭字下げ → 全角スペース自動挿入
- **A31-035**: 記号統一 → "..." → "…", "--" → "――"
- **A31-031**: 誤字脱字 → 辞書ベース自動修正

#### 3.2 用語・表記系修正（辞書ベース）
- **A31-044**: 固有名詞統一 → プロジェクト用語集.yaml照合
- **A31-033**: キャラクター口調 → キャラクター.yaml照合

#### 3.3 数値計測系修正（閾値ベース）
- **A31-022**: 会話比率調整 → 地の文/会話追加提案
- **A31-042**: 品質スコア改善 → カテゴリ別改善提案

### 4. A31チェックリスト68項目詳細定義

#### 4.1 感情表現（12項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-001 | 感情表現の具体性 | 抽象的感情語（嬉しい、悲しい）vs具体的表現の比率 | 抽象表現30%以下 | 具体的表現候補を提示 |
| A31-002 | 感情変化の論理性 | 感情変化に適切な理由・きっかけがあるか | 論理性スコア80%以上 | 論理性不足箇所にコメント挿入 |
| A31-003 | 身体的反応の描写 | 感情に伴う身体反応が適切に描写されているか | 感情場面の70%以上で身体反応あり | 身体反応候補を提示 |
| A31-004 | 感情の多層性 | 複数の感情が混在する場面の表現 | 複合感情場面50%以上 | 複合感情表現例を提示 |
| A31-005 | 感情表現の独自性 | ありふれた表現ではなく独自の感情描写 | 独自表現率60%以上 | 独自表現候補を提示 |
| A31-006 | 内面独白の効果性 | 内面描写が効果的に配置されているか | 効果的配置スコア70%以上 | 内面独白挿入位置を提案 |
| A31-007 | 感情の段階的変化 | 感情が段階的に変化しているか | 段階的変化70%以上 | 中間感情ステップを提案 |
| A31-008 | 対立感情の表現 | 相反する感情の同時表現 | 対立場面40%以上で表現 | 対立感情例を提示 |
| A31-009 | 感情の視覚化 | 感情を視覚的に表現する工夫 | 視覚的表現50%以上 | 視覚化表現例を提示 |
| A31-010 | 感情の余韻描写 | 感情の後に残る余韻の描写 | 余韻描写60%以上 | 余韻表現を提案 |
| A31-011 | 感情と環境の連動 | 感情と周囲環境の連動表現 | 連動表現40%以上 | 環境描写連動例を提示 |
| A31-012 | 感情表現のリズム | 感情表現の文章リズム | リズムスコア70%以上 | リズム改善提案 |

#### 4.2 キャラクター（12項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-013 | 口調の一貫性 | キャラクター別口調パターンの統一 | 一貫性スコア90%以上 | 口調不一致箇所を指摘・修正候補提示 |
| A31-014 | 行動パターン一貫性 | キャラクター別行動特徴の統一 | 行動一貫性85%以上 | 行動不一致を指摘 |
| A31-015 | 成長の表現 | キャラクターの心理的・技能的成長 | 成長描写60%以上の話で明確化 | 成長描写の挿入提案 |
| A31-016 | 個性の差別化 | キャラクター間の個性の明確な差 | 個性差別化スコア80%以上 | 個性強化提案 |
| A31-017 | 関係性の変化 | キャラクター間関係の動的変化 | 関係変化40%以上の話で明確化 | 関係変化の演出提案 |
| A31-018 | 内面の複雑性 | キャラクターの内面的複雑さ | 複雑性スコア70%以上 | 内面複雑化の提案 |
| A31-019 | 動機の明確性 | キャラクターの行動動機の明確さ | 動機明確度80%以上 | 動機説明の挿入提案 |
| A31-020 | 弱点・欠点の活用 | キャラクターの弱点が物語に活かされているか | 弱点活用60%以上 | 弱点活用シーンを提案 |
| A31-021 | 対立構造の明確化 | キャラクター間の対立・葛藤の明確さ | 対立明確度70%以上 | 対立強化の演出提案 |
| A31-022 | 会話の個性化 | キャラクター別会話スタイルの差別化 | 会話個性度80%以上 | 会話個性強化提案 |
| A31-023 | 感情表現の個性 | キャラクター別感情表現パターン | 感情個性度75%以上 | 個性的感情表現提案 |
| A31-024 | バックストーリー活用 | 過去の設定が現在の行動に反映されているか | 背景活用度60%以上 | 背景設定活用提案 |

#### 4.3 ストーリー展開（12項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-025 | 起承転結の明確性 | 4部構成の明確な区分 | 各部構成比率の適切性90%以上 | 構成バランス調整提案 |
| A31-026 | 読解テンポの調整 | 読み進める速度感の調整 | テンポスコア70%以上 | テンポ調整箇所を指摘 |
| A31-027 | 伏線の配置 | 効果的な伏線の設置 | 伏線設置度60%以上 | 伏線配置位置を提案 |
| A31-028 | 伏線の回収 | 設置した伏線の適切な回収 | 回収率90%以上 | 未回収伏線を指摘 |
| A31-029 | 意外性と必然性 | 予想外だが納得できる展開 | 意外性・必然性バランス75%以上 | バランス調整提案 |
| A31-030 | 緊張感の維持 | ストーリー全体の緊張感 | 緊張感維持度70%以上 | 緊張感強化提案 |
| A31-031 | 情報開示のタイミング | 重要情報の効果的な開示 | 開示タイミング適切度80%以上 | 開示タイミング調整提案 |
| A31-032 | 場面転換の自然さ | シーン間の自然な移行 | 転換自然度85%以上 | 転換改善提案 |
| A31-033 | クライマックスの盛り上がり | 最高潮部分の効果的な演出 | クライマックス効果度85%以上 | 盛り上がり強化提案 |
| A31-034 | 読者の感情誘導 | 意図した感情反応の誘発 | 感情誘導成功度75%以上 | 感情誘導強化提案 |
| A31-035 | サブプロットの統合 | 副次的な話の統合度 | 統合度70%以上 | サブプロット強化提案 |
| A31-036 | 終盤への収束 | 物語要素の効果的な収束 | 収束度80%以上 | 収束改善提案 |

#### 4.4 文章表現（12項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-037 | 描写の臨場感 | 情景描写の臨場感 | 臨場感スコア75%以上 | 五感描写の追加提案 |
| A31-038 | 比喩表現の効果 | 比喩・修辞の効果的使用 | 比喩効果度70%以上 | 効果的比喩例を提示 |
| A31-039 | 文章リズムの調整 | 文の長短によるリズム感 | リズムスコア80%以上 | 文長調整提案 |
| A31-040 | 語彙の豊富性 | 多様で適切な語彙使用 | 語彙多様度70%以上 | 語彙強化提案 |
| A31-041 | 文体の統一性 | 全体を通じた文体の一貫性 | 文体一貫度90%以上 | 文体不統一箇所を指摘 |
| A31-042 | 読みやすさ | 全体的な読みやすさ | 可読性スコア80%以上 | 読みにくい箇所を指摘・改善提案 |
| A31-043 | 専門用語の説明 | 専門的内容の適切な説明 | 説明適切度85%以上 | 説明不足用語を指摘 |
| A31-044 | 固有名詞の統一 | 人名・地名等の表記統一 | 統一度100% | 表記不統一を自動修正 |
| A31-045 | 段落構成 | 適切な段落分けと字下げ | 段落構成適切度95%以上 | 段落分け・字下げを自動修正 |
| A31-046 | 文章の簡潔性 | 冗長性の排除 | 簡潔性スコア75%以上 | 冗長箇所を指摘・簡潔化提案 |
| A31-047 | 感覚的描写の豊富さ | 五感に訴える描写 | 五感描写50%以上の場面で使用 | 感覚描写の追加提案 |
| A31-048 | 文章の流れ | 論理的で自然な文章の流れ | 流れ自然度80%以上 | 流れ改善提案 |

#### 4.5 世界観・設定（10項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-049 | 設定の一貫性 | 世界設定の論理的一貫性 | 一貫性スコア90%以上 | 矛盾箇所を指摘 |
| A31-050 | 世界観の深み | 設定の詳細度と奥深さ | 深度スコア70%以上 | 設定深化提案 |
| A31-051 | リアリティの確保 | 設定の現実味・説得力 | リアリティスコア75%以上 | 説得力強化提案 |
| A31-052 | 独自性の確保 | オリジナルな世界観要素 | 独自性スコア65%以上 | 独自要素強化提案 |
| A31-053 | 設定説明の自然さ | 世界設定の自然な説明 | 説明自然度80%以上 | 説明方法改善提案 |
| A31-054 | 環境描写の効果 | 環境が物語に与える影響 | 環境効果度70%以上 | 環境活用提案 |
| A31-055 | 文化・慣習の描写 | 世界の文化的背景 | 文化描写度60%以上 | 文化要素追加提案 |
| A31-056 | 技術・魔法体系 | ファンタジー要素の体系性 | 体系性スコア80%以上 | 体系整理提案 |
| A31-057 | 歴史・背景の活用 | 世界の歴史的背景の活用 | 背景活用度55%以上 | 歴史要素活用提案 |
| A31-058 | 社会構造の描写 | 社会システムの描写 | 社会描写度65%以上 | 社会要素強化提案 |

#### 4.6 読者エンゲージメント（10項目）
| 項目ID | 項目名 | チェック内容 | 閾値 | 自動修正戦略 |
|--------|-------|-------------|-----|--------------|
| A31-059 | 冒頭の引き込み力 | 最初の1000字の引き込み効果 | 引き込み度85%以上 | 冒頭強化提案 |
| A31-060 | 続きへの誘引 | 次話への期待感醸成 | 誘引度80%以上 | 引き込み要素強化提案 |
| A31-061 | 読後の満足感 | エピソード完読後の充実感 | 満足度75%以上 | 満足感向上提案 |
| A31-062 | ターゲット読者適合 | 想定読者層への適合度 | 適合度80%以上 | ターゲット調整提案 |
| A31-063 | 感情移入の誘発 | キャラクターへの感情移入 | 感情移入度70%以上 | 移入促進提案 |
| A31-064 | 驚きと発見の提供 | 読者の予想を超える展開 | 驚き度65%以上 | 意外性強化提案 |
| A31-065 | 共感要素の配置 | 読者が共感できる要素 | 共感度75%以上 | 共感要素強化提案 |
| A31-066 | 緊張感の演出 | 読者をハラハラさせる演出 | 緊張演出度70%以上 | 緊張演出強化提案 |
| A31-067 | 読みやすさの確保 | ストレスなく読める文章 | ストレスフリー度85%以上 | 可読性改善提案 |
| A31-068 | 記憶に残る要素 | 印象的で記憶に残る場面・要素 | 印象度60%以上 | 印象強化提案 |

### 5. CLIインターフェース

#### 4.1 基本コマンド
```bash
# 完全自動修正（安全な修正のみ）
novel check episode.md --auto-fix --level safe

# パターンベース修正（中精度修正含む）
novel check episode.md --auto-fix --level standard

# 対話式修正（人的確認付き）
novel check episode.md --auto-fix --level interactive

# 特定項目のみ修正
novel check episode.md --auto-fix --items A31-045,A31-035,A31-031
```

#### 4.2 修正結果レポート
```bash
📊 自動修正結果レポート - 第001話「冒険の始まり」
🔧 適用された修正:
  - A31-045: 段落字下げ 15箇所修正 ✅
  - A31-035: 記号統一 8箇所修正 ✅
  - A31-031: 誤字修正 3箇所修正 ✅

⚠️  確認が必要な修正提案:
  - A31-022: 会話比率 38% → 35%推奨 (地の文追加提案3箇所)
  - A31-033: キャラ口調 2箇所で不整合検出

📈 修正後品質スコア: 67点 → 73点 (+6点改善)
📁 チェックリスト保存: $PROJECT_ROOT/50_管理資料/A31_チェックリスト/A31_チェックリスト_第001話_冒険の始まり.yaml
```

## アーキテクチャ設計

### 1. ドメイン層

#### 1.1 エンティティ
```python
@dataclass
class A31ChecklistItem:
    """A31チェックリスト項目"""
    item_id: str
    title: str
    required: bool
    item_type: ChecklistItemType
    threshold: Threshold
    auto_fix_strategy: AutoFixStrategy

@dataclass
class AutoFixSession:
    """自動修正セッション"""
    session_id: str
    target_file: Path
    fix_level: FixLevel
    items_to_fix: List[str]
    results: List[FixResult]
```

#### 1.2 値オブジェクト
```python
@dataclass(frozen=True)
class EvaluationResult:
    """評価結果"""
    item_id: str
    current_score: float
    threshold: float
    passed: bool
    details: Dict[str, Any]

@dataclass(frozen=True)
class FixResult:
    """修正結果"""
    item_id: str
    fix_applied: bool
    fix_type: str
    changes_made: List[str]
    before_score: float
    after_score: float
```

#### 1.3 ドメインサービス
```python
class A31EvaluationService:
    """A31項目評価サービス"""

    def evaluate_format_items(self, content: str) -> Dict[str, EvaluationResult]:
        """フォーマット系項目の評価"""

    def evaluate_quality_items(self, content: str, metadata: Dict) -> Dict[str, EvaluationResult]:
        """品質系項目の評価"""

class A31AutoFixService:
    """A31自動修正サービス"""

    def apply_format_fixes(self, content: str, items: List[str]) -> str:
        """フォーマット系修正の適用"""

    def generate_improvement_suggestions(self, content: str, evaluation: EvaluationResult) -> List[str]:
        """改善提案の生成"""
```

### 2. アプリケーション層

#### 2.1 ユースケース

##### 2.1.1 DI契約設計（2025-09-22更新）
```python
class A31AutoFixUseCase(AbstractUseCase[object, AutoFixSession]):
    """A31自動修正ユースケース - DDD準拠のDI契約実装"""

    def __init__(
        self,
        logger_service=None,
        unit_of_work=None,
        *,
        console_service: "IConsoleService" | None = None,
        path_service: "IPathService" | None = None,
        episode_repository=None,
        project_repository=None,
        evaluation_service: A31EvaluationService | None = None,
        auto_fix_service: A31AutoFixService | None = None,
        a31_checklist_repository=None,
        **legacy_kwargs,
    ) -> None:
        """DI契約に基づく初期化

        Args:
            logger_service (ILoggerService): ログサービス
            unit_of_work (IUnitOfWork): Unit of Work（トランザクション管理）
            console_service (IConsoleService, optional): コンソール出力サービス
            path_service (IPathService, optional): パス管理サービス
            episode_repository (IEpisodeRepository, optional): エピソードリポジトリ
            project_repository (IProjectRepository, optional): プロジェクトリポジトリ
            evaluation_service (A31EvaluationService, optional): 評価ドメインサービス
            auto_fix_service (A31AutoFixService, optional): 自動修正ドメインサービス
            a31_checklist_repository (IA31ChecklistRepository, optional): チェックリストリポジトリ

        Note:
            - unit_of_workが未指定の場合、episode_repository/project_repositoryから
              自動でUnitOfWorkインスタンスを構築（フォールバック機能）
            - ドメインサービス（evaluation_service/auto_fix_service）は
              未指定時に自動生成される（依存関係なしで構築可能）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            console_service=console_service,
            path_service=path_service,
            **legacy_kwargs,
        )

        # UnitOfWork フォールバック機能
        if self.unit_of_work is None:
            if episode_repository is None or project_repository is None:
                msg = "unit_of_work または episode_repository/project_repository を指定してください"
                raise ValueError(msg)

            from noveler.infrastructure.unit_of_work import UnitOfWork
            unit_of_work = UnitOfWork(
                episode_repository=episode_repository,
                project_repository=project_repository,
            )
        else:
            unit_of_work = self.unit_of_work

        self._unit_of_work = unit_of_work
        self._episode_repository = episode_repository or getattr(unit_of_work, "episode_repository", None)
        self._project_repository = project_repository or getattr(unit_of_work, "project_repository", None)

        # 必須依存関係の検証
        if self._episode_repository is None or self._project_repository is None:
            msg = "A31AutoFixUseCase には episode_repository と project_repository が必要です"
            raise ValueError(msg)

        self._evaluation_service = evaluation_service
        self._auto_fix_service = auto_fix_service
        self._checklist_repository = a31_checklist_repository

    def execute(self, project_name: str, episode_number: int, fix_level: FixLevel, items_to_fix: list[str]) -> AutoFixSession:
        """自動修正の実行

        Args:
            project_name (str): プロジェクト識別子
            episode_number (int): エピソード番号
            fix_level (FixLevel): 修正レベル（safe/standard/interactive）
            items_to_fix (list[str]): 修正対象チェックリスト項目ID

        Returns:
            AutoFixSession: 修正セッション（結果と修正内容を含む）

        Raises:
            FileNotFoundError: 対象エピソードが見つからない場合
            ValueError: チェックリスト項目が存在しない場合
        """
        self._logger_service.info(f"A31自動修正開始: {project_name} #{episode_number}")

        # B20準拠: Unit of Work トランザクション管理
        with self._unit_of_work.transaction():
            try:
                # 1. エピソード内容の取得
                episode_content = self._unit_of_work.episode_repository.get_episode_content(
                    project_name, episode_number
                )

                # 2. チェックリスト項目の取得
                checklist_items = self._unit_of_work.project_repository.get_checklist_items(
                    project_name, items_to_fix
                )

                if not checklist_items:
                    msg = "指定されたチェックリスト項目が見つかりません"
                    raise ValueError(msg)

                # 3. セッションの作成
                session_id = SessionId.generate()
                target_file = self._get_episode_file_path(project_name, episode_number)
                session = AutoFixSession(
                    session_id=session_id, target_file=target_file, fix_level=fix_level, items_to_fix=items_to_fix
                )

                # 4. ドメインサービスの生成（必要時）
                evaluation_service = self._create_evaluation_service()
                auto_fix_service = self._create_auto_fix_service()

                # 5. 評価の実行
                evaluation_results = evaluation_service.evaluate_all_items(
                    checklist_items, episode_content, self._get_project_metadata(project_name)
                )

                # 6. 修正の実行
                fixed_content, fix_results = auto_fix_service.apply_fixes(
                    episode_content, evaluation_results, checklist_items, fix_level
                )

                # 7. セッション結果の記録
                for fix_result in fix_results:
                    session.add_result(fix_result)

                # 8. 修正内容の保存(変更があった場合のみ)
                if fixed_content != episode_content:
                    self.save_fixed_content(session, fixed_content)

                # 9. セッションの完了
                session.complete()

                self._logger_service.info(f"A31自動修正完了: セッション{session_id.value}")
                return session

            except Exception as e:
                self._logger_service.error(f"A31自動修正エラー: {e}")
                raise
```

##### 2.1.2 DI契約の特徴とフォールバック機能

**フォールバック機能**:
- `unit_of_work` 未指定時の自動UnitOfWork構築
- ドメインサービスの遅延生成（依存関係なしで構築可能）
- 共通基盤サービス（logger/console/path）の統一DI

**エラーハンドリング**:
- 必須依存関係の実行時検証
- トランザクション管理による整合性保証
- 詳細ログによる問題診断支援

**開発者ガイド**:
1. **最小構成**: `episode_repository`と`project_repository`のみ指定
2. **フル構成**: `unit_of_work`で統一的なトランザクション管理
3. **テスト用**: モックサービスの注入による単体テスト対応
```

#### 2.2 リクエスト・レスポンス
```python
@dataclass
class A31AutoFixRequest:
    target_file: Path
    fix_level: FixLevel
    specific_items: Optional[List[str]] = None
    dry_run: bool = False

@dataclass
class A31AutoFixResponse:
    session_id: str
    success: bool
    fixes_applied: List[FixResult]
    suggestions_generated: List[str]
    before_score: float
    after_score: float
    report_path: Path
    checklist_path: Path  # エピソード用チェックリストファイルのパス
```

### 3. インフラストラクチャ層

#### 3.1 リポジトリ実装
```python
class YamlA31ChecklistRepository:
    """A31チェックリスト設定のYAML管理"""

    def load_template(self) -> Dict[str, Any]:
        """テンプレートYAMLの読み込み"""
        template_path = Path("$GUIDE_ROOT/templates/A31_原稿執筆チェックリストテンプレート.yaml")
        return self._load_yaml(template_path)

    def create_episode_checklist(self, episode_number: int, episode_title: str, project_root: Path) -> Path:
        """エピソード用チェックリストファイルの作成"""
        template = self.load_template()

        # チェックリスト専用フォルダを作成
        checklist_dir = project_root / "50_管理資料" / "A31_チェックリスト"
        checklist_dir.mkdir(parents=True, exist_ok=True)

        output_path = checklist_dir / f"A31_チェックリスト_第{episode_number:03d}話_{episode_title}.yaml"

        # メタデータを更新
        template['metadata']['target_episode'] = episode_number
        template['metadata']['target_title'] = episode_title
        template['metadata']['created_date'] = datetime.now().isoformat()

        self._save_yaml(output_path, template)
        return output_path

    def save_results(self, session: AutoFixSession, results_path: Path) -> None:
        """修正結果をエピソード用チェックリストに保存"""
        checklist = self._load_yaml(results_path)

        # チェック結果を更新
        for result in session.results:
            if result.item_id in checklist['checklist_items']:
                checklist['checklist_items'][result.item_id]['status'] = result.fix_applied
                checklist['checklist_items'][result.item_id]['auto_fix_applied'] = True
                checklist['checklist_items'][result.item_id]['fix_details'] = result.changes_made

        # 検証サマリーを更新
        checklist['validation_summary']['completed_items'] = sum(1 for item in checklist['checklist_items'].values() if item['status'])
        checklist['validation_summary']['completion_rate'] = checklist['validation_summary']['completed_items'] / checklist['validation_summary']['total_items']

        self._save_yaml(results_path, checklist)

class FileSystemEpisodeRepository:
    """エピソードファイルの管理"""

    def read_episode(self, file_path: Path) -> str:
        """エピソード内容読み込み"""

    def write_episode(self, file_path: Path, content: str) -> None:
        """エピソード内容書き込み"""

    def backup_episode(self, file_path: Path) -> Path:
        """エピソードのバックアップ作成"""

    def get_episode_info(self, file_path: Path) -> tuple[int, str]:
        """ファイルパスからエピソード番号とタイトルを抽出"""
        filename = file_path.stem
        # 第001話_タイトル.md の形式を想定
        match = re.match(r'第(\d+)話_(.+)', filename)
        if match:
            episode_number = int(match.group(1))
            episode_title = match.group(2)
            return episode_number, episode_title
        raise ValueError(f"Invalid episode filename format: {filename}")
```

#### 3.2 外部サービス連携
```python
class JapaneseTextAnalyzer:
    """日本語テキスト解析"""

    def check_spelling(self, text: str) -> List[SpellingError]:
        """誤字脱字チェック"""

    def analyze_dialogue_ratio(self, text: str) -> float:
        """会話比率分析"""

class ProperNounExtractor:
    """固有名詞抽出・統一"""

    def extract_proper_nouns(self, text: str) -> List[str]:
        """固有名詞抽出"""

    def check_consistency(self, text: str, reference_dict: Dict[str, str]) -> List[ConsistencyError]:
        """表記統一チェック"""
```

## 実装計画

### Phase 1: コア機能実装（2週間）
1. **ドメイン層実装**
   - A31ChecklistItem, AutoFixSession エンティティ
   - EvaluationResult, FixResult 値オブジェクト
   - A31EvaluationService, A31AutoFixService

2. **基本評価・修正機能**
   - フォーマット系項目（A31-045, A31-035）
   - 品質スコア項目（A31-042）

### Phase 2: 高度修正機能（3週間）
1. **用語・表記系修正**
   - 固有名詞統一（A31-044）
   - キャラクター口調（A31-033）

2. **数値計測系修正**
   - 会話比率調整（A31-022）
   - 誤字脱字修正（A31-031）

### Phase 3: CLI統合・最適化（2週間）
1. **CLIインターフェース実装**
   - novel check --auto-fix コマンド拡張
   - 修正レベル選択機能

2. **レポート・ログ機能**
   - 修正結果レポート生成
   - 修正履歴管理

### Phase 4: テスト・品質保証（1週間）
1. **包括的テスト**
   - ユニットテスト（90%以上のカバレッジ）
   - 統合テスト（実際のエピソードファイル使用）

2. **パフォーマンス最適化**
   - 大量ファイル処理の最適化
   - メモリ使用量の最適化

## テストケース

### 1. ユニットテスト

#### 1.1 評価エンジンテスト
```python
def test_evaluate_paragraph_indentation():
    """段落字下げ評価のテスト"""
    content = "　これは正しい字下げです。\nこれは字下げなしです。"
    result = evaluation_engine.evaluate_item("A31-045", content)
    assert result.current_score == 50.0  # 50%のみ字下げ済み
    assert not result.passed  # 閾値100%未達
```

#### 1.2 自動修正テスト
```python
def test_auto_fix_paragraph_indentation():
    """段落字下げ自動修正のテスト"""
    content = "これは字下げなしです。\nこれも字下げなしです。"
    fixed_content = auto_fix_service.apply_format_fixes(content, ["A31-045"])
    assert fixed_content == "　これは字下げなしです。\n　これも字下げなしです。"
```

### 2. 統合テスト

#### 2.1 エンドツーエンドテスト
```python
def test_complete_auto_fix_workflow():
    """完全な自動修正ワークフローのテスト"""
    # テスト用エピソードファイル作成
    # A31AutoFixUseCase実行
    # 修正結果の検証
    # レポート生成の確認
```

### 3. パフォーマンステスト

#### 3.1 大量ファイル処理テスト
```python
def test_bulk_auto_fix_performance():
    """大量ファイル処理のパフォーマンステスト"""
    # 100ファイルの一括処理時間測定
    # メモリ使用量監視
    # 修正精度の維持確認
```

## 運用・保守

### 1. 監視・ログ
- 修正実行ログの記録
- エラー発生時の詳細ログ
- パフォーマンス監視

### 2. 設定管理
- 閾値の動的調整機能
- プロジェクト固有設定の対応
- 修正ルールのカスタマイズ

### 3. 継続改善
- 修正精度の定期評価
- 新しい修正パターンの追加
- ユーザーフィードバックの反映

## リスク・制約

### 1. 技術的リスク
- **修正精度の限界**: 文脈理解が必要な項目は自動修正困難
- **互換性**: 既存ファイルフォーマットとの整合性
- **パフォーマンス**: 大量ファイル処理時の応答性

### 2. 運用リスク
- **過修正**: 不適切な自動修正による品質低下
- **依存**: 自動修正への過度な依存
- **学習機会**: 手動確認機会の減少による学習効果低下

### 3. 対応策
- 段階的修正レベルの提供
- 修正前バックアップの自動作成
- 人的確認フローの維持
- 定期的な精度評価・調整

## まとめ

本システムにより、A31原稿執筆チェックリストの約60%を自動化し、執筆者の負担軽減と品質向上を両立する。段階的な実装アプローチで確実な品質保証を行い、継続的改善サイクルを構築する。

## 関連仕様書

- SPEC-QUALITY-002: 品質履歴管理システム
- SPEC-QUALITY-003: 手動改善プロセス
- SPEC-EPISODE-004: エピソードメタデータ管理

---

## 要件トレーサビリティ

### 関連要件
- **REQ-QUALITY-001**: A31品質チェック68項目実装 → 実装済み
- **REQ-QUALITY-002**: 総合品質スコア算出システム → 実装済み
- **REQ-QUALITY-003**: 改善提案自動生成 → 実装済み
- **REQ-QUALITY-005**: 自動文章修正機能 → 実装済み

### 実装状況
- **実装済み**: A31自動評価エンジン、段階的修正システム
- **テスト済み**: 68項目の自動チェック機能
- **統合済み**: noveler check コマンドとの連携

### テストカバレッジ
- **Unit Tests**: `tests/unit/application/services/test_quality_gate_processor.py`
- **Integration Tests**: `tests/integration/test_a31_check_system.py`
- **E2E Tests**: `tests/e2e/test_quality_check_workflow.py`

### 変更履歴
- **2025-09-04**: 要件定義書との整合性確認、実装完了ステータス更新

---

**作成者**: Claude Code
**承認者**: [承認者名]
**最終レビュー**: 2025-09-04
