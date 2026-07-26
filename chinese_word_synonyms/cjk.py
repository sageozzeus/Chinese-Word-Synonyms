# -*- coding: utf-8 -*-
"""CJK character helpers for Chinese Word Synonyms."""

from __future__ import annotations

import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")

# CJK Unified Ideographs + Extension A (covers virtually all modern Chinese chars)
_CJK_RANGES = (
    (0x3400, 0x4DBF),  # Extension A
    (0x4E00, 0x9FFF),  # Unified Ideographs
)


def is_cjk_char(ch: str) -> bool:
    """Return True if *ch* is a single CJK ideograph we care about."""
    if not ch or len(ch) != 1:
        return False
    code = ord(ch)
    for start, end in _CJK_RANGES:
        if start <= code <= end:
            return True
    return False


def strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    if not text:
        return ""
    cleaned = _HTML_TAG_RE.sub("", text)
    return cleaned.replace("&nbsp;", " ").strip()


def extract_cjk_chars(text: str, *, unique: bool = True) -> list[str]:
    """
    Extract CJK characters from *text* in appearance order.

    HTML is stripped first. If *unique* is True, each character appears once
    (first occurrence wins).
    """
    plain = strip_html(text)
    chars: list[str] = []
    seen: set[str] = set()
    for ch in plain:
        if not is_cjk_char(ch):
            continue
        if unique:
            if ch in seen:
                continue
            seen.add(ch)
        chars.append(ch)
    return chars


def cjk_length(text: str) -> int:
    """Count of CJK ideographs in *text* (non-unique)."""
    return len(extract_cjk_chars(text, unique=False))
