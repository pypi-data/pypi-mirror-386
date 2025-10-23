import datetime
import pytest

from noveler.domain.value_objects.project_time import (
    parse_compact_timestamp,
    parse_project_time_iso,
)


def test_parse_project_time_iso_supports_z_suffix():
    result = parse_project_time_iso("2025-10-04T03:45:00Z")
    assert result.datetime.isoformat().startswith("2025-10-04T12:45:00")
    assert result.project_timezone.timezone.utcoffset(None) == datetime.timedelta(hours=9)


def test_parse_compact_timestamp_accepts_multiple_lengths():
    minute = parse_compact_timestamp("202510041045")
    seconds = parse_compact_timestamp("20251004104530")
    micro = parse_compact_timestamp("20251004104530999999")
    assert minute.datetime.minute == 45
    assert seconds.datetime.second == 30
    assert micro.datetime.microsecond == 999999


def test_parse_compact_timestamp_rejects_invalid():
    with pytest.raises(ValueError):
        parse_compact_timestamp("")
    with pytest.raises(ValueError):
        parse_compact_timestamp("not-a-timestamp")
