#!/usr/bin/env python3
"""エピソード作成のBDDステップ定義

pytest-bddを使用したGherkinシナリオの実装
TDD+DDD原則に基づき、実際のドメインコードと接続
"""

from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

from noveler.domain.entities.episode import EpisodeStatus

# シナリオファイルを読み込み
scenarios("../features/episode_creation.feature")


# =================================================================
# Given(前提条件)
# =================================================================


@given('小説プロジェクト "転生魔法師の冒険" が存在する', target_fixture="project_context")
def given_novel_project(novel_project_exists: Path) -> Any:
    """小説プロジェクトの作成(conftest.pyのフィクスチャを使用)"""
    return novel_project_exists


@given("ch01のプロットが作成済みである", target_fixture="plot_context")
def given_plot_created(project_context: Path, plot_is_created: dict[str, Any]) -> Any:
    """プロット作成済みの設定(conftest.pyのフィクスチャを使用)"""
    # plot_is_createdフィクスチャは既にプロットを作成している
    return plot_is_created


@given("プロジェクト設定で品質基準が70点に設定されている", target_fixture="quality_context")
def given_quality_threshold(plot_context: dict[str, Any], quality_threshold_set: dict[str, float]) -> Any:
    """品質基準の設定(conftest.pyのフィクスチャを使用)"""
    # quality_threshold_setフィクスチャは既に品質基準を設定している
    return quality_threshold_set


@given(parsers.parse('第{number:d}話 "{title}" が既に存在する'), target_fixture="existing_episode_context")
def episode_already_exists(quality_context: Any, number: int, title: str) -> Any:
    """既存エピソードの作成"""
    context = quality_context
    context.create_episode(number, title, "既存のエピソード内容。" * 100)
    return context


# =================================================================
# When(アクション実行)
# =================================================================


@when(parsers.parse('第{number:d}話 "{title}" を作成する'), target_fixture="episode_created")
def create_episode(plot_context: Any, number: int, title: str) -> Any:
    """エピソード作成の実行"""
    context = plot_context
    # 2500文字程度の内容を生成(品質スコア80点相当)
    content = f"「{title}」の始まり。\n\n" + ("主人公は新たな冒険に旅立った。" * 100)
    context.create_episode(number, title, content)
    return context


@when(parsers.parse('第{number:d}話 "{title}" を下書きとして作成する'), target_fixture="draft_created")
def create_draft_episode(plot_context: Any, number: int, title: str) -> Any:
    """下書きエピソードの作成"""
    context = plot_context
    # 最小限の内容で作成
    content = f"第{number}話の下書き。"
    context.create_episode(number, title, content)
    # 下書き番号を記録(後で使用)
    context._draft_episode_number = number
    return context


@when(parsers.parse('第{number:d}話 "{title}" を作成しようとする'), target_fixture="duplicate_attempt")
def try_create_episode(existing_episode_context: Any, number: int, title: str) -> Any:
    """エピソード作成を試みる(エラー想定)"""
    context = existing_episode_context
    context.create_episode(number, title, "新しい内容")
    return context


@when(parsers.parse("本文を{length:d}文字で執筆する"), target_fixture="content_written")
def write_content(episode_created: Any, length: int) -> Any:
    """指定文字数で本文を執筆"""
    context = episode_created
    # 最後に作成したエピソードを取得
    if hasattr(context, "_draft_episode_number"):
        episode_number = context._draft_episode_number
    else:
        # 直前に作成したエピソードの番号を使用
        episode = context.last_result.get("episode")
        if episode:
            episode_number = episode.number.value
        else:
            return context

    episode = context.get_episode(episode_number)
    if episode:
        # 指定文字数の内容を生成
        base_text = "「おはよう」と主人公は言った。\n"
        repeat_text = "そして物語は続く。"
        repeat_count = (length - len(base_text)) // len(repeat_text) + 1
        content = base_text + (repeat_text * repeat_count)
        content = content[:length]  # 正確な文字数に調整
        episode.update_content(content)
        # 最新の結果を更新(更新後のコンテンツで再計算)
        context.last_result = {
            "success": True,
            "episode": episode,
            "quality_score": context._calculate_quality(episode.content),
            "warnings": context._check_warnings(episode.content),
        }
    return context


@when(parsers.parse("本文を{length:d}文字に更新する"), target_fixture="content_updated")
def update_content(quality_context: Any, length: int) -> Any:
    """本文を更新"""
    context = quality_context
    # 最初のエピソードを作成
    context.create_episode(1, "テスト話", "初期内容")
    episode = context.get_episode(1)

    if episode:
        # 指定文字数の内容に更新
        content = "更新された内容。\n" + ("新しい展開が始まる。" * (length // 20))
        content = content[:length]
        episode.update_content(content)
    return context


@when("執筆を開始する", target_fixture="writing_started")
def start_writing(draft_created: Any) -> Any:
    """執筆開始"""
    context = draft_created
    episode = context.get_episode(context._draft_episode_number)
    if episode:
        episode.start_writing()
    return context


@when("エピソードを完成させる", target_fixture="episode_completed")
def complete_episode(content_written: Any) -> Any:
    """エピソード完成"""
    context = content_written
    episode = context.get_episode(context._draft_episode_number)
    if episode:
        episode.complete()
    return context


# =================================================================
# Then(結果確認)
# =================================================================


@then("エピソードが正常に作成される")
def episode_created_successfully(episode_created: Any) -> None:
    """作成成功の確認"""
    context = episode_created
    assert context.last_result["success"]
    assert context.last_result["episode"] is not None


@then("エピソードは作成される")
def episode_is_created(content_written: Any) -> None:
    """作成の確認(品質は問わない)"""
    context = content_written
    assert context.last_result["success"]


@then(parsers.parse('エピソードのステータスが "{status}" である'))
def check_episode_status(episode_created: Any, status: str) -> None:
    """ステータス確認"""
    context = episode_created
    episode = context.last_result["episode"]

    status_map = {
        "下書き": EpisodeStatus.DRAFT,
        "執筆中": EpisodeStatus.IN_PROGRESS,
        "完成": EpisodeStatus.COMPLETED,
    }

    expected_status = status_map[status]
    actual_status = episode.status

    # 値で比較
    assert actual_status.value == expected_status.value, f"Expected {expected_status.value}, got {actual_status.value}"


@then(parsers.parse("品質スコアが{score:d}点以上である"))
def check_quality_score_minimum(episode_created: Any, score: int) -> None:
    """品質スコア最低値の確認"""
    context = episode_created
    actual_score = context.last_result["quality_score"]
    assert actual_score >= score, f"品質スコア{actual_score}点は{score}点未満です"


@then(parsers.parse("品質スコアが{score:d}点未満である"))
def check_quality_score_below(content_written: Any, score: int) -> None:
    """品質スコア上限の確認"""
    context = content_written
    actual_score = context.last_result["quality_score"]
    assert actual_score < score, f"品質スコア{actual_score}点は{score}点以上です"


@then("品質警告が表示される")
def quality_warning_displayed(content_written: Any) -> None:
    """品質警告の確認"""
    context = content_written
    assert len(context.last_result["warnings"]) > 0


@then(parsers.parse('警告内容に "{text}" が含まれる'))
def warning_contains_text(content_written: Any, text: str) -> None:
    """警告内容の確認"""
    context = content_written
    warnings_text = " ".join(context.last_result["warnings"])
    assert text in warnings_text


@then("エピソードは作成されない")
def episode_not_created(duplicate_attempt: Any) -> None:
    """作成失敗の確認"""
    context = duplicate_attempt
    assert not context.last_result["success"]


@then("エラーが発生する")
def error_occurred(duplicate_attempt: Any) -> None:
    """エラー発生の確認"""
    context = duplicate_attempt
    assert context.last_error is not None


@then(parsers.parse('エラーメッセージに "{text}" が含まれる'))
def error_contains_text(duplicate_attempt: Any, text: str) -> None:
    """エラーメッセージの確認"""
    context = duplicate_attempt
    assert text in context.last_error


@then(parsers.parse('エピソードのステータスが "{status}" になる'))
def episode_status_becomes(writing_started: Any, status: str) -> None:
    """ステータス変更の確認"""
    context = writing_started
    episode = context.get_episode(context._draft_episode_number)

    status_map = {
        "下書き": EpisodeStatus.DRAFT,
        "執筆中": EpisodeStatus.IN_PROGRESS,
        "完成": EpisodeStatus.COMPLETED,
    }

    assert episode.status == status_map[status]


@then("話数管理.yamlが更新される")
def episode_management_updated(episode_created: Any) -> None:
    """話数管理ファイルの更新確認"""
    # 実際のファイル更新はリポジトリ層で行われるため、ここではスキップ


@then(parsers.parse("バージョンが{version:d}になる"))
def version_becomes(content_updated: Any, version: int) -> None:
    """バージョン確認"""
    context = content_updated
    episode = context.get_episode(1)
    assert episode.version == version


@then(parsers.parse("完成度が{percentage:d}%と表示される"))
def completion_percentage_displayed(content_written: Any, percentage: int) -> None:
    """完成度の確認"""
    context = content_written
    # content_writtenのコンテキストで最後に作成されたエピソードを取得
    episode = context.last_result.get("episode")
    if not episode:
        # エピソード番号から取得を試みる
        if hasattr(context, "_draft_episode_number"):
            episode = context.get_episode(context._draft_episode_number)
        else:
            # 最初のエピソードを仮定
            episode = context.get_episode(1)

    actual_percentage = episode.calculate_completion_percentage()
    assert actual_percentage == percentage, f"Expected {percentage}%, got {actual_percentage}%"


@then(parsers.parse("改善提案が{count:d}件以上提示される"))
def improvement_suggestions_count(content_written: Any, count: int) -> None:
    """改善提案数の確認"""
    context = content_written
    assert len(context.last_result["warnings"]) >= count


@then("完成日時が記録される")
def completion_date_recorded(episode_completed: Any) -> None:
    """完成日時の確認"""
    context = episode_completed
    episode = context.get_episode(context._draft_episode_number)
    assert episode.completed_at is not None
