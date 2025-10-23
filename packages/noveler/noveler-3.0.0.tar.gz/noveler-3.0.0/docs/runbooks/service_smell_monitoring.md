# Service Logic Smell Check - 運用監視ガイド

**目的**: Service Logic Smell Check（WARNING モード）の誤検知率を測定し、本格運用（ERROR モード）への移行判断を行う

**監視期間**: 2025-10-12 ～ 2025-10-19 (7日間)
**目標**: 誤検知率 < 10%

---

## 1. 監視手順

### 1.1. 日次ログ確認（毎日実施）

**コマンド**:
```bash
# 今日のコミットログを確認
git log --since="1 day ago" --all --oneline --grep="Service Logic Smell"

# または、pre-commit hook実行時の標準出力を確認
# （コミット時にターミナルに表示される）
```

**記録項目**:
- 日付
- 検知回数（WARNING が表示された回数）
- 誤検知数（後述の判定基準に基づく）

### 1.2. 週次レビュー（1週間後実施）

**実施日**: 2025-10-19（予定）

**確認事項**:
1. 総検知回数
2. 誤検知回数
3. 誤検知率 = (誤検知回数 / 総検知回数) × 100%
4. ERROR モード移行可否判断

---

## 2. 誤検知判定基準

### 2.1. 誤検知（False Positive）と判定するケース

以下のパターンは**正当な使用**であり、検知されても誤検知とみなす：

#### Pattern 1: リクエスト検証
```python
# ✅ 正当: Use Case入力のバリデーション
def execute(self, request: CreateEpisodeRequest) -> None:
    if not request.episode_number:  # ← 誤検知（正当）
        raise ValueError("Episode number is required")
```

**判定理由**: Use Caseはリクエストの検証責務を持つ

#### Pattern 2: Repository問い合わせ
```python
# ✅ 正当: Repositoryへの存在確認
def execute(self, episode_id: int) -> None:
    if self.repository.exists(episode_id):  # ← 誤検知（正当）
        raise ValueError("Episode already exists")
```

**判定理由**: Repositoryへの委譲は正しいアーキテクチャ

#### Pattern 3: ファクトリメソッド呼び出し
```python
# ✅ 正当: Entityのファクトリメソッド使用
def execute(self, title: str) -> Episode:
    episode = Episode.create_draft(title=title)  # ← 誤検知（正当）
    return episode
```

**判定理由**: ファクトリメソッドはDomain層の正しいパターン

#### Pattern 4: DTOマッピング
```python
# ✅ 正当: EntityからResponseへの変換
def execute(self, episode: Episode) -> EpisodeResponse:
    return EpisodeResponse(
        title=episode.title,  # ← 誤検知（正当）
        status=episode.status
    )
```

**判定理由**: DTOマッピングはPresentation層の責務

#### Pattern 5: 集約操作の調整
```python
# ✅ 正当: 複数Entityの調整（Use Caseの正当な責務）
def execute(self, episode: Episode, author: Author) -> None:
    episode.assign_author(author.id)  # ← Entity操作（正当）
    author.add_episode(episode.id)    # ← Entity操作（正当）
    # ↑ 両方のEntityにメソッドがあるため正当
```

**判定理由**: 集約間の調整はUse Caseの責務

### 2.2. 真陽性（True Positive）と判定するケース

以下のパターンは**改善すべき**であり、検知が正しい：

#### Pattern A: Tell Don't Ask違反
```python
# ❌ 要改善: Entityのプロパティチェック
def execute(self, episode: Episode) -> None:
    if episode.status == "draft":  # ← 真陽性（要改善）
        episode.status = "published"
```

**改善策**: `episode.publish()` メソッドに委譲

#### Pattern B: 直接変更（Direct Mutation）
```python
# ❌ 要改善: Entityの内部状態を直接変更
def execute(self, episode: Episode, new_title: str) -> None:
    episode.title = new_title  # ← 真陽性（要改善）
    episode.updated_at = datetime.now()
```

**改善策**: `episode.update_title(new_title)` メソッドに委譲

#### Pattern C: 業務ルールの実装
```python
# ❌ 要改善: Use Case内での業務ルール実装
def execute(self, episode_number: int) -> bool:
    if not 1 <= episode_number <= 9999:  # ← 真陽性（要改善）
        return False
```

**改善策**: `EpisodeNumber` Value Objectに移動

---

## 3. 監視ログテンプレート

### 3.1. 日次ログ（毎日記録）

```markdown
## 2025-10-12（月）

**検知回数**: 2回
**詳細**:
1. `src/noveler/application/use_cases/episode_use_case.py:42`
   - パターン: Tell Don't Ask違反 (`if episode.status == "draft"`)
   - 判定: **真陽性** (要改善)
   - アクション: リファクタリング予定

2. `src/noveler/application/use_cases/create_episode_use_case.py:28`
   - パターン: リクエスト検証 (`if not request.episode_number`)
   - 判定: **誤検知** (正当)
   - アクション: なし（正当な使用）

**小計**:
- 真陽性: 1件
- 誤検知: 1件
```

### 3.2. 週次サマリー（1週間後作成）

```markdown
# Service Logic Smell Check - 週次レビュー

**監視期間**: 2025-10-12 ～ 2025-10-19
**総コミット数**: 47回
**Service Smell検知回数**: 12回

## 誤検知率

| 項目 | 件数 | 割合 |
|------|------|------|
| 総検知回数 | 12 | 100% |
| 真陽性（要改善） | 10 | 83.3% |
| 誤検知（正当） | 2 | **16.7%** |

**誤検知率**: 16.7% （目標: < 10%）

## 判定

⚠️ **ERROR モード移行: 不可**

**理由**:
- 誤検知率16.7%は目標10%を超過
- 主な誤検知パターン: リクエスト検証（2件）

## 推奨アクション

1. **除外ルールの改善**:
   - リクエスト検証パターンを除外ロジックに追加
   - `if not request.` パターンを正当とマーク

2. **再監視**:
   - 除外ルール追加後、さらに1週間監視
   - 次回レビュー: 2025-10-26

3. **暫定対応**:
   - WARNING モード継続
```

---

## 4. ERROR モード移行判断基準

### 4.1. 移行可能条件

以下の**全条件を満たす**場合、ERROR モード移行可：

- ✅ 誤検知率 < 10%
- ✅ 真陽性の改善方針が明確（リファクタリング計画あり）
- ✅ チーム内でコンセンサス形成済み
- ✅ 緊急時の無効化手順が文書化済み

### 4.2. 移行手順

**Step 1**: `.pre-commit-config.yaml` を修正

```yaml
# 変更前（WARNING モード）
- id: service-logic-smell-check
  name: Service Logic Smell Check (WARNING mode)
  entry: bash -c 'python scripts/hooks/check_service_logic_smell.py; rc=$?; if [ $rc -eq 1 ]; then echo "[WARNING] Service Logic Smell detected (non-blocking)"; exit 0; elif [ $rc -eq 0 ]; then exit 0; else echo "[ERROR] Service Logic Smell Check failed with exit code $rc"; exit $rc; fi'

# 変更後（ERROR モード）
- id: service-logic-smell-check
  name: Service Logic Smell Check (ERROR mode - blocking)
  entry: python scripts/hooks/check_service_logic_smell.py
  language: system
  pass_filenames: false
  stages: [pre-commit]
  files: '^src/noveler/application/use_cases/.*\.py$'
```

**Step 2**: チーム通知

```
【重要】Service Logic Smell Check が ERROR モードに移行します

- 移行日: 2025-10-20
- 影響: Use Case層でService Logic Smellが検知された場合、コミットがブロックされます
- 回避方法: `git commit --no-verify`（緊急時のみ使用）
- 問い合わせ先: [担当者名]
```

**Step 3**: 段階的ロールアウト

1. 特定のディレクトリから開始（例: `use_cases/episode/`）
2. 1週間問題なければ全体に拡大
3. 問題発生時は即座にWARNINGモードに戻す

### 4.3. 緊急時のロールバック

ERROR モード移行後に問題が発生した場合：

```bash
# 1. .pre-commit-config.yaml を編集（WARNING モードに戻す）
git checkout HEAD -- .pre-commit-config.yaml

# 2. コミット
git commit -m "Revert: Service Logic Smell Check to WARNING mode"

# 3. チーム通知
```

---

## 5. 自動化スクリプト（将来実装）

### 5.1. ログ収集スクリプト

```bash
#!/bin/bash
# scripts/monitoring/collect_service_smell_logs.sh

# 直近7日間のService Smell検知をカウント
git log --since="7 days ago" --all --oneline | \
  grep -i "service logic smell" | \
  wc -l
```

### 5.2. 誤検知率計算スクリプト（将来実装）

```python
# scripts/monitoring/calculate_false_positive_rate.py

import re
from pathlib import Path

def analyze_logs(log_file: Path) -> dict:
    """日次ログから誤検知率を計算"""
    true_positive = 0
    false_positive = 0

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
        true_positive = content.count("判定: **真陽性**")
        false_positive = content.count("判定: **誤検知**")

    total = true_positive + false_positive
    if total == 0:
        return {"rate": 0, "total": 0}

    rate = (false_positive / total) * 100
    return {
        "rate": round(rate, 2),
        "total": total,
        "true_positive": true_positive,
        "false_positive": false_positive
    }

if __name__ == "__main__":
    result = analyze_logs(Path("docs/monitoring/service_smell_logs.md"))
    print(f"誤検知率: {result['rate']}%")
    print(f"  真陽性: {result['true_positive']}件")
    print(f"  誤検知: {result['false_positive']}件")
```

---

## 6. 参考資料

- **検知スクリプト**: `scripts/hooks/check_service_logic_smell.py`
- **除外パターン**: `docs/guides/anemic_domain_detection.md#除外パターン`
- **Tell, Don't Ask原則**: https://martinfowler.com/bliki/TellDontAsk.html
- **pre-commit設定**: `.pre-commit-config.yaml` (line 107-113)

---

## 7. 監視開始チェックリスト

- [x] 本ガイド作成完了
- [x] WARNING モードで運用開始（2025-10-12）
- [ ] 日次ログ記録開始
- [ ] 週次レビュー実施（2025-10-19予定）
- [ ] ERROR モード移行判断

---

**Last Updated**: 2025-10-12
**Next Review**: 2025-10-19
**Maintainer**: Development Team
