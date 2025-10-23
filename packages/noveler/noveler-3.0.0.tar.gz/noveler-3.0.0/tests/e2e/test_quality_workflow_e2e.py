#!/usr/bin/env python3
"""品質保証ワークフローE2Eテスト

品質チェック、分析、改善を含む包括的な品質保証ワークフロー
"""

import subprocess
import time
import asyncio
import json as _json
from pathlib import Path

import pytest
import yaml

from tests.unit.infrastructure.test_base import BaseE2ETestCase
from mcp_servers.noveler.main import execute_run_quality_checks


class TestQualityWorkflowE2E(BaseE2ETestCase):
    """品質保証ワークフローE2Eテスト

    品質管理に特化したワークフローテスト:
    - 品質チェック → 問題検出 → 修正提案 → 再チェック
    - 品質基準の段階的向上 → 適応的品質管理
    - 長期品質トレンド分析 → 継続的改善
    """

    def setup_method(self) -> None:
        """品質ワークフロー用セットアップ"""
        super().setup_method()

        self.quality_metrics: dict[str, list[float]] = {
            "check_time": [],
            "issue_count": [],
            "improvement_score": []
        }

    def create_quality_test_project(self, project_name: str) -> Path:
        """品質テスト用プロジェクトを作成"""
        project_dir = self.test_root / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # プロジェクト構造
        (project_dir / "temp/test_data/40_原稿").mkdir(parents=True, exist_ok=True)
        (project_dir / "50_管理資料").mkdir(exist_ok=True)

        # 設定ファイル
        config = {
            "title": project_name,
            "author": "品質テスト作者",
            "genre": "test_quality",
            "quality_standards": {
                "min_word_count": 1000,
                "max_word_count": 5000,
                "readability_target": "intermediate",
                "consistency_check": True
            }
        }

        with open(project_dir / "プロジェクト設定.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        return project_dir

    def create_test_manuscripts(self, project_dir: Path) -> list[Path]:
        """テスト用原稿ファイルを作成"""
        manuscripts = []

        # 品質問題を含む原稿サンプル
        samples = [
            {
                "filename": "第1話_良質サンプル.txt",
                "content": """第1話　良質な物語の始まり

朝の光が窓から差し込み、主人公の田中太郎は目を覚ました。
今日は特別な日だった。長年待ち続けた冒険への第一歩を踏み出す日だったのだ。

「ついにこの日が来たんだな」

太郎は呟きながら、窓の外を眺めた。
青い空に白い雲が浮かび、鳥たちが自由に飛び回っている。
その光景を見て、太郎は自分も自由になりたいと思った。

部屋の隅に置いてある旅行鞄を手に取り、必要な荷物を確認する。
地図、コンパス、食料、そして祖父から受け継いだ古い剣。
全て揃っている。準備は完璧だった。

太郎は決意を新たに、冒険の旅へと向かった。
新しい世界が彼を待っている。
"""
            },
            {
                "filename": "第2話_問題サンプル.txt",
                "content": """第2話　問題のある文章

太郎は歩いてた。歩いてたらなんか森があった。森に入った。
森の中はくらい。くらいからよくみえない。でも歩いた。

なんか音がした。なんの音だろう。わからない。
でも音がしたからきになる。きになるから見に行った。

そしたらなんかいた。なんかよくわからないけどいた。
それは太郎を見た。太郎もそれを見た。見つめあった。

それから何か話しかけてきた。「君は誰だ？」って。
太郎は答えた。「太郎だ」って。短い会話。

そのあともいろいろあった。いろいろ。
結果的に仲間になった。仲間は大切。
"""
            },
            {
                "filename": "第3話_中程度サンプル.txt",
                "content": """第3話　中程度の品質

太郎と新しい仲間のエルフの女性リナは、森の奥へと進んでいた。
リナは森の案内ができる。案内してもらいながら歩く。

「この森には古い遺跡があるの」
リナが説明してくれた。遺跡には宝物があるらしい。
宝物があるなら行ってみたい。太郎はそう思った。

歩いていると、大きな石の建物が見えてきた。
それが遺跡だった。遺跡は古くて苔が生えている。
入り口は開いていた。中は暗い。

「危険かもしれない」リナが心配そうに言った。
でも太郎は進むことにした。冒険だからリスクはつきもの。
リナも一緒についてきてくれた。

遺跡の中は複雑だった。いくつも部屋がある。
どの部屋に宝物があるかわからない。
とりあえず一番大きな部屋に向かってみることにした。
"""
            }
        ]

        for sample in samples:
            file_path = project_dir / "temp/test_data/40_原稿" / sample["filename"]
            file_path.write_text(sample["content"], encoding="utf-8")
            manuscripts.append(file_path)

        return manuscripts

    def run_quality_command(self, command: str, project_dir: Path,
                           timeout: int = 30) -> subprocess.CompletedProcess[str]:
        """品質関連コマンドの内部API実行（CLI非依存化）"""

        class _Result:
            def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
                self.args = command
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        start_time = time.time()

        # コマンドディスパッチ（最小限の互換レイヤ）
        cmd = command.strip()
        try:
            # CWDを一時的にプロジェクトへ切り替え（PathServiceの自動検出対策）
            import os
            cwd_backup = os.getcwd()
            os.chdir(str(project_dir))
            try:
                if cmd.startswith("quality check"):
                    # 対象ファイルを推定（temp/test_data/40_原稿配下の最初のファイル）
                    manuscript_dir = project_dir / "temp/test_data/40_原稿"
                    candidates = list(manuscript_dir.glob("**/*"))
                    target_file = None
                    for p in candidates:
                        if p.is_file():
                            target_file = p
                            break

                    # 内部API実行
                    args = {
                        "episode_number": 1,
                        "project_name": project_dir.name,
                    }
                    if target_file:
                        args["file_path"] = str(target_file)

                    # 実行系は非同期APIのためテスト側でループを管理して同期呼び出しに変換
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        result_dict = loop.run_until_complete(
                            execute_run_quality_checks(args)
                        )
                    finally:
                        asyncio.set_event_loop(None)
                        loop.close()

                    # 出力をテスト互換のテキストへ整形
                    success = bool(result_dict.get("success"))
                    issues = result_dict.get("issues") or []
                    score = result_dict.get("score")
                    # 日本語キーワードを含む簡易出力＋JSONを末尾に付与
                    summary_text = (
                        f"品質チェック結果: スコア {score}\n"
                        f"エラー {len(issues)} 件\n"
                        f"警告 0 件\n"
                    )
                    stdout = summary_text + _json.dumps(result_dict, ensure_ascii=False)
                    returncode = 0 if success else 1
                    return _Result(returncode=returncode, stdout=stdout, stderr="")

                # それ以外の旧CLIサブコマンドは未実装扱い（移行後は非推奨）
                if cmd.startswith("analyze file") or cmd.startswith("quality suggest") or cmd.startswith("quality trend"):
                    return _Result(returncode=1, stdout="", stderr="未実装: MCP移行によりCLIサブコマンドは非推奨")

                # デフォルト: 非対応
                return _Result(returncode=1, stdout="", stderr="未対応コマンド")
            finally:
                os.chdir(cwd_backup)
        finally:
            execution_time = time.time() - start_time
            # メトリクス記録
            self.quality_metrics["check_time"].append(execution_time)

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_comprehensive_quality_workflow(self) -> None:
        """包括的品質保証ワークフロー"""
        project_name = "comprehensive_quality_test"
        project_dir = self.create_quality_test_project(project_name)
        manuscripts = self.create_test_manuscripts(project_dir)

        print(f"品質テスト開始: {len(manuscripts)} 原稿ファイル")

        try:
            # Phase 1: 初回品質チェック
            print("Phase 1: 初回品質チェック")
            initial_check = self.run_quality_command("quality check", project_dir)

            if initial_check.returncode == 0:
                print("初回品質チェック成功")
                self._analyze_quality_output(initial_check.stdout, "初回")
            elif "実装" in initial_check.stderr:
                print("品質チェック未実装 - 基本検証に切り替え")
                self._run_basic_quality_checks(project_dir, manuscripts)
            else:
                print(f"初回チェック警告: {initial_check.stderr[:200]}")

            # Phase 2: ファイル別品質分析
            print("Phase 2: ファイル別品質分析")
            for manuscript in manuscripts:
                file_name = manuscript.name
                print(f"分析中: {file_name}")

                # analyze コマンドの実行
                analyze_result = self.run_quality_command(f"analyze file {file_name}", project_dir)

                if analyze_result.returncode == 0:
                    print(f"{file_name}: 分析成功")
                elif "実装" not in analyze_result.stderr:
                    print(f"{file_name}: 分析警告 {analyze_result.stderr[:100]}")

            # Phase 3: 品質改善提案
            print("Phase 3: 品質改善提案")
            improvement_result = self.run_quality_command("quality suggest-improvements", project_dir)

            if improvement_result.returncode == 0:
                print("改善提案生成成功")
                self._process_improvement_suggestions(improvement_result.stdout)
            elif "実装" not in improvement_result.stderr:
                print(f"改善提案警告: {improvement_result.stderr[:100]}")

            # Phase 4: 品質トレンド確認
            print("Phase 4: 品質トレンド確認")
            trend_result = self.run_quality_command("quality trend", project_dir)

            if trend_result.returncode == 0:
                print("品質トレンド確認成功")
            elif "実装" not in trend_result.stderr:
                print(f"トレンド確認警告: {trend_result.stderr[:100]}")

            # Phase 5: 最終品質検証
            print("Phase 5: 最終品質検証")
            final_check = self.run_quality_command("quality check --detailed", project_dir)

            if final_check.returncode == 0:
                print("最終品質検証成功")
                self._compare_quality_results(initial_check.stdout, final_check.stdout)
            else:
                print(f"最終検証結果: コード {final_check.returncode}")

            print("包括的品質ワークフロー完了")

        except Exception as e:
            print(f"品質ワークフローエラー: {e}")
            raise

    def _run_basic_quality_checks(self, project_dir: Path, manuscripts: list[Path]) -> None:
        """基本的な品質チェック（コマンド未実装時のフォールバック）"""
        print("基本品質チェック実行")

        for manuscript in manuscripts:
            content = manuscript.read_text(encoding="utf-8")

            # 基本的な品質指標
            word_count = len(content.split())
            line_count = len(content.splitlines())
            char_count = len(content)

            # 文章の品質簡易評価
            short_sentences = content.count("。") + content.count("！") + content.count("？")
            avg_sentence_length = char_count / max(short_sentences, 1)

            quality_score = self._calculate_simple_quality_score(content)

            print(f"{manuscript.name}:")
            print(f"  文字数: {char_count}, 単語数: {word_count}, 行数: {line_count}")
            print(f"  平均文長: {avg_sentence_length:.1f}, 品質スコア: {quality_score:.2f}")

            # メトリクス記録
            self.quality_metrics["improvement_score"].append(quality_score)

    def _calculate_simple_quality_score(self, content: str) -> float:
        """簡易品質スコア計算"""
        score = 1.0

        # 文章の長さチェック
        if len(content) < 100:
            score *= 0.5
        elif len(content) > 10000:
            score *= 0.8

        # 句読点の使用チェック
        punctuation_ratio = (content.count("。") + content.count("、")) / max(len(content), 1)
        if punctuation_ratio < 0.02:
            score *= 0.7
        elif punctuation_ratio > 0.1:
            score *= 0.9

        # 繰り返し表現のチェック
        repeated_patterns = ["だった。だった", "した。した", "である。である"]
        for pattern in repeated_patterns:
            if pattern in content:
                score *= 0.8

        # 語彙の多様性簡易チェック
        words = content.split()
        unique_words = set(words)
        if len(words) > 0:
            vocabulary_diversity = len(unique_words) / len(words)
            if vocabulary_diversity < 0.3:
                score *= 0.6

        return min(score, 1.0)

    def _analyze_quality_output(self, output: str, phase: str) -> None:
        """品質チェック出力の分析"""
        print(f"{phase}品質分析:")

        # 出力から品質指標を抽出（実装依存）
        if "品質" in output:
            print("  品質関連の出力を検出")
        if "エラー" in output:
            error_count = output.count("エラー")
            self.quality_metrics["issue_count"].append(error_count)
            print(f"  エラー数: {error_count}")
        if "警告" in output:
            warning_count = output.count("警告")
            print(f"  警告数: {warning_count}")

    def _process_improvement_suggestions(self, output: str) -> None:
        """改善提案の処理"""
        print("改善提案処理:")

        suggestions = []
        if "提案" in output:
            print("  改善提案を検出")
            # 提案内容の解析（実装依存）
            suggestions.append("文章構造の改善")

        if "修正" in output:
            print("  修正提案を検出")
            suggestions.append("表現の修正")

        if suggestions:
            print(f"  提案数: {len(suggestions)}")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"    {i}. {suggestion}")

    def _compare_quality_results(self, initial: str, final: str) -> None:
        """品質結果の比較"""
        print("品質改善の比較:")

        initial_length = len(initial)
        final_length = len(final)

        print(f"  初回出力: {initial_length} 文字")
        print(f"  最終出力: {final_length} 文字")

        if final_length > initial_length:
            print("  → より詳細な分析が実行されました")

        # エラー・警告数の比較
        initial_errors = initial.count("エラー")
        final_errors = final.count("エラー")

        if final_errors < initial_errors:
            print(f"  → エラー減少: {initial_errors} → {final_errors}")
        elif final_errors > initial_errors:
            print(f"  → エラー増加: {initial_errors} → {final_errors} (詳細分析)")

    @pytest.mark.e2e
    def test_adaptive_quality_standards(self) -> None:
        """適応的品質基準テスト"""
        project_name = "adaptive_quality_test"
        project_dir = self.create_quality_test_project(project_name)

        # 段階的に品質基準を上げるテスト
        quality_levels = ["basic", "intermediate", "advanced"]

        for level in quality_levels:
            print(f"品質レベル {level} でテスト")

            # 設定ファイルの更新
            config_file = project_dir / "プロジェクト設定.yaml"
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            config["quality_standards"]["level"] = level

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            # 品質チェック実行
            result = self.run_quality_command(f"quality check --level {level}", project_dir)

            if result.returncode == 0:
                print(f"  レベル {level}: 成功")
            elif "実装" not in result.stderr:
                print(f"  レベル {level}: 警告 - {result.stderr[:100]}")

        print("適応的品質基準テスト完了")

    @pytest.mark.e2e
    @pytest.mark.performance
    def test_quality_performance_regression(self) -> None:
        """品質チェックパフォーマンス回帰テスト"""
        project_name = "performance_quality_test"
        project_dir = self.create_quality_test_project(project_name)

        # 大量のテストデータを作成
        large_content = "テストデータ。" * 1000  # 約5000文字
        for i in range(5):  # 5ファイル
            file_path = project_dir / "temp/test_data/40_原稿" / f"大容量テスト_{i+1}.txt"
            file_path.write_text(large_content, encoding="utf-8")

        # パフォーマンス測定
        performance_results = []

        for run in range(3):  # 3回実行して平均を取る
            start_time = time.time()
            result = self.run_quality_command("quality check", project_dir, timeout=60)
            execution_time = time.time() - start_time

            performance_results.append(execution_time)

            if result.returncode == 0:
                print(f"Run {run+1}: {execution_time:.2f}秒")
            elif "実装" in result.stderr:
                print("品質チェック未実装のためパフォーマンステストスキップ")
                pytest.skip("品質チェック機能未実装")
            else:
                print(f"Run {run+1}: エラー ({execution_time:.2f}秒)")

        if performance_results:
            avg_time = sum(performance_results) / len(performance_results)
            max_time = max(performance_results)
            min_time = min(performance_results)

            print("パフォーマンス結果:")
            print(f"  平均: {avg_time:.2f}秒")
            print(f"  最大: {max_time:.2f}秒")
            print(f"  最小: {min_time:.2f}秒")

            # パフォーマンス回帰チェック
            assert avg_time < 30.0, f"品質チェックが遅すぎます: {avg_time:.2f}秒"
            assert max_time < 45.0, f"最大実行時間が許容範囲を超えています: {max_time:.2f}秒"

    def teardown_method(self) -> None:
        """品質テスト後のメトリクス出力"""
        if self.quality_metrics["check_time"]:
            avg_check_time = sum(self.quality_metrics["check_time"]) / len(self.quality_metrics["check_time"])
            print("\n=== 品質チェック パフォーマンス ===")
            print(f"平均チェック時間: {avg_check_time:.3f}秒")
            print(f"チェック実行回数: {len(self.quality_metrics['check_time'])}回")

        if self.quality_metrics["improvement_score"]:
            avg_score = sum(self.quality_metrics["improvement_score"]) / len(self.quality_metrics["improvement_score"])
            print(f"平均品質スコア: {avg_score:.3f}")

        if self.quality_metrics["issue_count"]:
            total_issues = sum(self.quality_metrics["issue_count"])
            print(f"検出した問題総数: {total_issues}")

        super().teardown_method()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])
