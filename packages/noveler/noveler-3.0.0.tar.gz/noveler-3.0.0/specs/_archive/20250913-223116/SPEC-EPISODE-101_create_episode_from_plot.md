# SPEC-EPISODE-101: プロットからエピソード作成ユースケース仕様書

## SPEC-EPISODE-014: プロットからエピソード作成


## 概要
`CreateEpisodeFromPlotUseCase`は、プロット情報を基にエピソードを作成するユースケースです。プロット検証、重複チェック、初期コンテンツ生成、執筆記録初期化を含む包括的なエピソード作成フローを提供します。

## クラス設計

### CreateEpisodeFromPlotUseCase

**責務**
- プロット情報の検証
- エピソード重複チェック
- プロット情報からのエピソード作成
- プロットステータス更新
- 初期コンテンツの生成

## データ構造

### CreateEpisodeCommand (DataClass)
```python
@dataclass(frozen=True)
class CreateEpisodeCommand:
    project_id: str                 # プロジェクトID
    plot_info: dict[str, Any]       # プロット情報
```

**プロット情報の必須フィールド**
```python
{
    "episode_number": int,          # エピソード番号
    "title": str,                   # タイトル
    "summary": str,                 # あらすじ（オプション）
    "word_count_target": int,       # 目標文字数（オプション）
    "plot_points": list[str],       # プロットポイント（オプション）
    "character_focus": list[str],   # 登場キャラクター（オプション）
}
```

### CreateEpisodeResult (DataClass)
```python
@dataclass(frozen=True)
class CreateEpisodeResult:
    success: bool                   # 作成成功フラグ
    episode: Episode | None = None  # 作成されたエピソード
    error_message: str | None = None # エラーメッセージ
```

### ValidationResult (DataClass)
```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool                  # 検証結果
    error_message: str | None = None # エラーメッセージ
```

## パブリックメソッド

### execute()

**シグネチャ**
```python
def execute(self, command: CreateEpisodeCommand) -> CreateEpisodeResult:
```

**目的**
プロット情報からエピソードを作成し、関連する初期化処理を実行する。

**引数**
- `command`: エピソード作成コマンド

**戻り値**
- `CreateEpisodeResult`: エピソード作成結果

**処理フロー**
1. **プロット情報検証**: 必須フィールドとデータ形式の確認
2. **重複チェック**: 同じエピソード番号の存在確認
3. **エピソード作成**: プロット情報からのエピソードエンティティ生成
4. **エピソード保存**: リポジトリでの永続化
5. **プロットステータス更新**: プロット管理での状態更新

**成功パターン**
- 有効なプロット情報から新規エピソード作成
- 初期コンテンツの自動生成
- プロットステータスの適切な更新

**エラーパターン**
- プロット情報不正（必須フィールド不足、データ形式エラー）
- エピソード重複
- リポジトリ操作エラー

## プライベートメソッド

### _validate_plot_info()

**シグネチャ**
```python
def _validate_plot_info(self, plot_info: dict[str, Any]) -> ValidationResult:
```

**目的**
プロット情報の妥当性を検証する。

**検証項目**
1. **必須フィールド**: `episode_number`, `title`の存在確認
2. **エピソード番号**: 正の整数であることの確認
3. **タイトル**: 非空文字列であることの確認

**エラー例**
- `"必須フィールド 'episode_number' が不足しています"`
- `"話数は1以上である必要があります"`
- `"タイトルは空文字列以外の文字列である必要があります"`

### _create_episode_from_plot()

**シグネチャ**
```python
def _create_episode_from_plot(self, project_id: str, plot_info: dict[str, Any]) -> Episode:
```

**目的**
検証済みのプロット情報からエピソードエンティティを作成する。

**処理内容**
- タイトルの正規化（「第X話」部分の除去）
- 初期コンテンツの生成
- エピソードステータスの設定（`UNWRITTEN`）
- プロット情報の保持

### _extract_clean_title()

**シグネチャ**
```python
def _extract_clean_title(self, title_text: str) -> str:
```

**目的**
タイトルテキストから純粋なタイトル部分を抽出する。

**対応パターン**
- `第1話　魔法の覚醒` → `魔法の覚醒`
- `第5話：新たな仲間` → `新たな仲間`
- `3. 決戦の時` → `決戦の時`

**正規表現パターン**
```python
patterns = [
    r"第\d+話[　\s]+(.+)",        # 第1話　タイトル
    r"第\d+話[：:_\-\s]+(.+)",    # 第1話：タイトル
    r"^\d+[．.]\s*(.+)",          # 1. タイトル
]
```

### _generate_initial_content()

**シグネチャ**
```python
def _generate_initial_content(self, plot_info: dict[str, Any]) -> str:
```

**目的**
プロット情報から初期コンテンツテンプレートを生成する。

**生成内容**
```markdown
# 第X話　タイトル

## あらすじ
[プロット情報のsummary]

## 構成プロット
- [プロットポイント1]
- [プロットポイント2]

**登場キャラクター:** キャラ1, キャラ2
**目標文字数:** 3000文字

---

## 導入部


## 展開部


## 転換部


## 結末部


---

**執筆メモ:**
-
```

## 依存関係

### ドメイン層
- `Episode`: エピソードエンティティ
- `EpisodeStatus`: エピソードステータス値オブジェクト
- `EpisodeNumber`: エピソード番号値オブジェクト
- `EpisodeTitle`: エピソードタイトル値オブジェクト
- `WordCount`: 文字数値オブジェクト

### リポジトリ
- `EpisodeRepository`: エピソードリポジトリ
- `WritingRecordRepository`: 執筆記録リポジトリ

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`Episode`）の適切な使用
- ✅ 値オブジェクト（`EpisodeNumber`, `EpisodeTitle`等）の活用
- ✅ リポジトリパターンによるデータアクセス抽象化
- ✅ ドメインルールの適切な検証

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的な検証処理
- ✅ 型安全な実装
- ✅ 不変オブジェクトの使用

## 使用例

```python
# 依存関係の準備
episode_repo = YamlEpisodeRepository()
writing_record_repo = YamlWritingRecordRepository()

# ユースケース作成
use_case = CreateEpisodeFromPlotUseCase(
    episode_repository=episode_repo,
    writing_record_repository=writing_record_repo
)

# 基本的なプロット情報からエピソード作成
plot_info = {
    "episode_number": 5,
    "title": "第5話　魔法学院への入学",
    "summary": "主人公が魔法学院に入学し、新たな仲間と出会う",
    "word_count_target": 4000,
    "plot_points": [
        "入学式での自己紹介",
        "ルームメイトとの出会い",
        "初回授業での困惑",
        "新たな友情の芽生え"
    ],
    "character_focus": ["主人公", "エリス", "マックス", "リリア先生"]
}

command = CreateEpisodeCommand(
    project_id="magic_academy_story",
    plot_info=plot_info
)

result = use_case.execute(command)

if result.success and result.episode:
    episode = result.episode
    print(f"エピソード作成成功: 第{episode.episode_number.value}話")
    print(f"タイトル: {episode.title.value}")
    print(f"ステータス: {episode.status.value}")
    print(f"初期文字数: {episode.word_count.value}")

    # 初期コンテンツの確認
    print("初期コンテンツ:")
    print(episode.content[:500] + "...")
else:
    print(f"エピソード作成失敗: {result.error_message}")

# 最小限のプロット情報での作成
minimal_plot = {
    "episode_number": 6,
    "title": "第6話　初めての試験"
}

minimal_command = CreateEpisodeCommand(
    project_id="magic_academy_story",
    plot_info=minimal_plot
)

minimal_result = use_case.execute(minimal_command)

# 重複チェックのテスト
duplicate_plot = {
    "episode_number": 5,  # 既存のエピソード番号
    "title": "第5話　別のタイトル"
}

duplicate_command = CreateEpisodeCommand(
    project_id="magic_academy_story",
    plot_info=duplicate_plot
)

duplicate_result = use_case.execute(duplicate_command)
# expected: success=False, error_message="エピソード 5 は既に存在します"
```

## タイトル抽出例

### 正常な抽出
```python
# 入力: "第1話　魔法の覚醒"
# 出力: "魔法の覚醒"

# 入力: "第15話：決戦の日"
# 出力: "決戦の日"

# 入力: "3. 新たな仲間"
# 出力: "新たな仲間"

# 入力: "シンプルタイトル"
# 出力: "シンプルタイトル"
```

### エラー処理
```python
# 不正なプロット情報
invalid_plot = {
    "episode_number": "abc",  # 数値以外
    "title": ""               # 空文字列
}

# expected error: "話数は数値である必要があります"
# expected error: "タイトルは空文字列以外の文字列である必要があります"
```

## 初期コンテンツ生成

### 完全なプロット情報の場合
```markdown
# 第5話　魔法学院への入学

## あらすじ
主人公が魔法学院に入学し、新たな仲間と出会う

## 構成プロット
- 入学式での自己紹介
- ルームメイトとの出会い
- 初回授業での困惑
- 新たな友情の芽生え

**登場キャラクター:** 主人公, エリス, マックス, リリア先生
**目標文字数:** 4000文字

---

## 導入部


## 展開部


## 転換部


## 結末部


---

**執筆メモ:**
-
```

### 最小限のプロット情報の場合
```markdown
# 第6話　初めての試験

## あらすじ


## 構成プロット


**目標文字数:** 3000文字

---

## 導入部


## 展開部


## 転換部


## 結末部


---

**執筆メモ:**
-
```

## エラーハンドリング

### プロット検証エラー
- 必須フィールド不足
- エピソード番号の型・範囲エラー
- タイトルの形式エラー

### ビジネスルールエラー
- エピソード重複
- プロジェクト不存在

### システムエラー
- リポジトリアクセスエラー
- ファイル操作エラー

## テスト観点

### 単体テスト
- 正常なエピソード作成フロー
- プロット情報検証の各種条件
- タイトル抽出の各種パターン
- 初期コンテンツ生成の確認
- エラー条件での動作

### 統合テスト
- 実際のリポジトリとの連携
- プロット管理システムとの協調

## 品質基準

- **検証完全性**: プロット情報の包括的な検証
- **コンテンツ品質**: 有用な初期コンテンツの生成
- **一意性保証**: エピソード重複の確実な防止
- **拡張性**: 新しいプロット要素への対応
- **ユーザビリティ**: 分かりやすいエラーメッセージ
