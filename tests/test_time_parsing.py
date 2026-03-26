from datetime import datetime

from empathy_engine.utils.time import parse_iso_timestamp


def test_parse_iso_timestamp_accepts_z_suffix():
    parsed = parse_iso_timestamp("2025-01-02T03:04:05Z")
    assert isinstance(parsed, datetime)
    assert parsed.year == 2025


def test_parse_iso_timestamp_rejects_invalid():
    assert parse_iso_timestamp("not-a-date") is None
    assert parse_iso_timestamp("") is None
