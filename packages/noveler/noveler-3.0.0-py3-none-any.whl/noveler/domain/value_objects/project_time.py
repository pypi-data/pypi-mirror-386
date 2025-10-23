"""Domain.value_objects.project_time
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""プロジェクト時刻値オブジェクト

DDD準拠の時刻管理 - ドメイン層
プロジェクトのビジネスルールに従った時刻処理を提供
"""


from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ProjectTimezone:
    """プロジェクトタイムゾーン値オブジェクト

    ビジネスルール:
    - 日本の小説執筆プロジェクトではJST(日本標準時)を使用
    - タイムゾーン情報は常に明示的に管理される
    """

    _timezone: timezone

    @classmethod
    def jst(cls) -> ProjectTimezone:
        """日本標準時のタイムゾーンを作成"""
        return cls(timezone(timedelta(hours=9)))

    @property
    def timezone(self) -> timezone:
        """タイムゾーンオブジェクトを取得"""
        return self._timezone

    def __str__(self) -> str:
        return "JST(+09)"

    def __hash__(self) -> int:
        return hash(self._timezone)


@dataclass(frozen=True)
class ProjectDateTime:
    """プロジェクト日時値オブジェクト

    ビジネスルール:
    - 執筆活動の記録にはタイムゾーン情報が必須
    - 日時の比較や計算はビジネスロジックとして扱う
    """

    _datetime: datetime
    _project_timezone: ProjectTimezone

    @classmethod
    def now(cls, project_timezone: ProjectTimezone | None = None) -> ProjectDateTime:
        """現在の日時を作成"""
        if project_timezone is None:
            project_timezone = ProjectTimezone.jst()
        return cls(datetime.now(project_timezone.timezone), project_timezone)

    @classmethod
    def create(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        project_timezone: ProjectTimezone | None = None,
    ) -> ProjectDateTime:
        """指定された日時を作成"""
        if project_timezone is None:
            project_timezone = ProjectTimezone.jst()
        dt = datetime(year, month, day, hour, minute, second, tzinfo=project_timezone.timezone)
        return cls(dt, project_timezone)

    @classmethod
    def today(cls, project_timezone: ProjectTimezone | None = None) -> ProjectDateTime:
        """今日の開始時刻(00:00:00)を作成"""
        if project_timezone is None:
            project_timezone = ProjectTimezone.jst()
        now = datetime.now(project_timezone.timezone)
        today_start = datetime(now.year, now.month, now.day, tzinfo=project_timezone.timezone)
        return cls(today_start, project_timezone)

    @property
    def datetime(self) -> datetime:
        """datetimeオブジェクトを取得"""
        return self._datetime

    @property
    def project_timezone(self) -> ProjectTimezone:
        """プロジェクトタイムゾーンを取得"""
        return self._project_timezone

    def format_timestamp(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """タイムスタンプ文字列を生成"""
        return self._datetime.strftime(format_str)

    def to_iso_string(self) -> str:
        """ISO形式の文字列を生成"""
        return self._datetime.isoformat()

    def is_same_day(self, other: ProjectDateTime) -> bool:
        """同じ日かどうか判定(ビジネスルール)"""
        return self._datetime.date() == other._datetime.date() and self._project_timezone == other._project_timezone

    def __str__(self) -> str:
        return f"{self._datetime.strftime('%Y-%m-%d %H:%M:%S')} {self._project_timezone}"

    def __eq__(self, other: object) -> bool:
        """等価性比較"""
        if not isinstance(other, ProjectDateTime):
            return False
        return self._datetime == other._datetime

    def __lt__(self, other: ProjectDateTime) -> bool:
        """小なり比較"""
        if not isinstance(other, ProjectDateTime):
            return NotImplemented  # type: ignore[unreachable]
        return self._datetime < other._datetime

    def __le__(self, other: ProjectDateTime) -> bool:
        """小なりイコール比較"""
        if not isinstance(other, ProjectDateTime):
            return NotImplemented  # type: ignore[unreachable]
        return self._datetime <= other._datetime

    def __gt__(self, other: ProjectDateTime) -> bool:
        """大なり比較"""
        if not isinstance(other, ProjectDateTime):
            return NotImplemented  # type: ignore[unreachable]
        return self._datetime > other._datetime

    def __ge__(self, other: ProjectDateTime) -> bool:
        """大なりイコール比較"""
        if not isinstance(other, ProjectDateTime):
            return NotImplemented  # type: ignore[unreachable]
        return self._datetime >= other._datetime

    def __hash__(self) -> int:
        return hash((self._datetime, self._project_timezone))


@dataclass(frozen=True)
class WritingSession:
    """執筆セッション値オブジェクト

    ビジネスルール:
    - 執筆セッションには開始時刻と終了時刻が必要
    - 執筆時間の計算はドメインロジック
    """

    started_at: ProjectDateTime
    ended_at: ProjectDateTime | None = None

    @property
    def duration_minutes(self) -> int:
        """執筆時間(分)を計算"""
        if self.ended_at is None:
            # 進行中のセッション
            now = ProjectDateTime.now(self.started_at.project_timezone)
            delta = now.datetime - self.started_at.datetime
        else:
            delta = self.ended_at.datetime - self.started_at.datetime

        return int(delta.total_seconds() / 60)

    @property
    def is_active(self) -> bool:
        """アクティブなセッションかどうか"""
        return self.ended_at is None

    def end_session(self) -> WritingSession:
        """セッションを終了"""
        if not self.is_active:
            return self  # 既に終了済み

        return WritingSession(
            started_at=self.started_at, ended_at=ProjectDateTime.now(self.started_at.project_timezone)
        )


# MCPサーバー環境でのフォールバック実装
class _FallbackProjectDateTime:
    """MCPサーバー環境でのProjectDateTime互換フォールバッククラス

    ProjectDateTimeの基本的なAPIを提供し、MCP環境でのimportエラーを回避
    """

    def __init__(self, dt: datetime) -> None:
        self._datetime = dt
        self._project_timezone = None

    @property
    def datetime(self) -> datetime:
        return self._datetime

    def format_timestamp(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        return self._datetime.strftime(format_str)

    def to_iso_string(self) -> str:
        return self._datetime.isoformat()

    def __str__(self) -> str:
        return f"{self._datetime.strftime('%Y-%m-%d %H:%M:%S')} JST(+09)"


# ドメインサービスからよく使用される便利関数
def project_now() -> ProjectDateTime:
    """現在のプロジェクト時刻を取得(便利関数)

    MCPサーバー環境でのフォールバック対応:
    - 通常環境では標準のProjectDateTime.now()を使用
    - MCP環境でのimportエラー時は基本的なdatetime機能で代替
    """
    try:
        return ProjectDateTime.now(None)
    except Exception:
        # MCPサーバー環境でのフォールバック実装（トップレベルimportを使用）
        jst = timezone(timedelta(hours=9))
        now_dt = datetime.now(jst)
        return _FallbackProjectDateTime(now_dt)  # type: ignore


def project_today() -> ProjectDateTime:
    """今日のプロジェクト時刻を取得(便利関数)

    MCPサーバー環境でのフォールバック対応:
    - 通常環境では標準のProjectDateTime.today()を使用
    - MCP環境でのimportエラー時は基本的なdatetime機能で代替
    """
    try:
        return ProjectDateTime.today(None)
    except Exception:
        # MCPサーバー環境でのフォールバック実装（トップレベルimportを使用）
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        today_start = datetime(now.year, now.month, now.day, tzinfo=jst)
        return _FallbackProjectDateTime(today_start)  # type: ignore


def project_datetime(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0
) -> ProjectDateTime:
    """プロジェクト日時を作成(便利関数)

    MCPサーバー環境でのフォールバック対応:
    - 通常環境では標準のProjectDateTime.create()を使用
    - MCP環境でのimportエラー時は基本的なdatetime機能で代替
    """
    try:
        return ProjectDateTime.create(year, month, day, hour, minute, second)
    except Exception:
        # MCPサーバー環境でのフォールバック実装（トップレベルimportを使用）
        jst = timezone(timedelta(hours=9))
        dt = datetime(year, month, day, hour, minute, second, tzinfo=jst)
        return _FallbackProjectDateTime(dt)  # type: ignore


ISO_Z_SUFFIX = 'Z'
_COMPACT_TIMESTAMP_FORMATS = {
    8: '%Y%m%d',
    12: '%Y%m%d%H%M',
    14: '%Y%m%d%H%M%S',
    20: '%Y%m%d%H%M%S%f',
}

def parse_project_time_iso(value: str, project_timezone: ProjectTimezone | None = None) -> ProjectDateTime:
    """Parse ISO8601 timestamp strings into `ProjectDateTime`."""

    if not value or not value.strip():
        raise ValueError('Timestamp value must not be empty')

    normalised = value.strip()
    if normalised.endswith(ISO_Z_SUFFIX):
        normalised = normalised[:-1] + '+00:00'

    try:
        parsed = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise ValueError(f'Invalid ISO timestamp: {value!r}') from exc

    tz = project_timezone or ProjectTimezone.jst()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    localised = parsed.astimezone(tz.timezone)
    return ProjectDateTime(localised, tz)


def parse_compact_timestamp(value: str, project_timezone: ProjectTimezone | None = None) -> ProjectDateTime:
    """Parse compact `YYYYMMDD[HH[MM[SS[ffffff]]]]` timestamps."""

    if not value or not value.strip():
        raise ValueError('Timestamp value must not be empty')

    stripped = value.strip()
    fmt = _COMPACT_TIMESTAMP_FORMATS.get(len(stripped))
    if fmt is None:
        raise ValueError(f'Unsupported compact timestamp length: {len(stripped)}')

    try:
        parsed = datetime.strptime(stripped, fmt)
    except ValueError as exc:
        raise ValueError(f'Invalid compact timestamp: {value!r}') from exc

    tz = project_timezone or ProjectTimezone.jst()
    aware = parsed.replace(tzinfo=tz.timezone)
    return ProjectDateTime(aware, tz)

