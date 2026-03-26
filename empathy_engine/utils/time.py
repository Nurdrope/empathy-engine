"""
Time parsing helpers for EmpathyEngine.
"""

from datetime import datetime
from typing import Optional


def parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO-8601 timestamp into a datetime.

    Returns None on invalid input.
    """
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
