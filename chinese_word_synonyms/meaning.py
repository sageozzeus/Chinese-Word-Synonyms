# -*- coding: utf-8 -*-
"""Normalize Meaning fields into synonym lookup keys."""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from .cjk import extract_cjk_chars, strip_html

# Common part-of-speech prefixes in vocab decks
_POS_PREFIX_RE = re.compile(
    r"^(?:"
    r"n\.|v\.|adj\.|adv\.|prep\.|conj\.|interj\.|pron\.|num\.|art\.|"
    r"noun|verb|adjective|adverb|preposition|conjunction|interjection|"
    r"名词|动词|形容词|副词"
    r")\s*",
    re.IGNORECASE,
)

_EDGE_PUNCT_RE = re.compile(r"^[\s\.,;:|/\\'\"“”‘’（）()【】\[\]<>…·•\-–—]+|"
                            r"[\s\.,;:|/\\'\"“”‘’（）()【】\[\]<>…·•\-–—]+$")

_LEADING_TO_RE = re.compile(r"^to\s+", re.IGNORECASE)

_CJK_ONLY_RE = re.compile(r"^[\u3400-\u4DBF\u4E00-\u9FFF]+$")

DEFAULT_SPLIT_DELIMITERS = ";|/|；|、|,"
DEFAULT_IGNORE_KEYS = ("something", "someone", "somebody")

# Order shown in Settings → Meaning delimiters (labels are the characters).
KNOWN_SPLIT_DELIMITERS: tuple[str, ...] = (";", ",", "|", "/", "；", "、")
KNOWN_SPLIT_TOOLTIPS: dict[str, str] = {
    ";": "Semicolon — happy; glad",
    ",": "Comma — happy, glad",
    "|": "Pipe — happy|glad",
    "/": "Slash — happy/glad",
    "；": "Fullwidth semicolon — 快乐；高兴",
    "、": "Ideographic comma — 快乐、高兴",
}


def parse_delimiters(spec: str) -> list[str]:
    """
    Parse a delimiter config string into individual delimiter tokens.

    Accepts pipe-separated form like ``;|/|；|、|,`` (preferred) or a raw
    string of single-character delimiters.
    """
    raw = (spec or "").strip()
    if not raw:
        return [";", "|", "/", "；", "、", ","]
    if "|" in raw and len(raw) > 1:
        # Pipe-separated tokens. "|" cannot appear as a non-empty token when it
        # is also the meta-separator, so always include it as a sense delimiter.
        # e.g. ";|/|；|、|," → [";", "|", "/", "；", "、", ","]
        parts = [p for p in raw.split("|") if p]
        if "|" not in parts:
            # Insert after first token when present (keeps `;` first)
            insert_at = 1 if parts else 0
            parts.insert(insert_at, "|")
        seen: set[str] = set()
        ordered: list[str] = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                ordered.append(p)
        return ordered if ordered else [";", "|", "/", "；", "、", ","]
    return list(raw)


def delimiters_to_spec(selected: Iterable[str], extra: str = "") -> str:
    """
    Build a ``meaning_split_delimiters`` config string from UI choices.

    When ``|`` is among the selected delimiters, use pipe-separated form
    (parser always treats ``|`` as a delimiter in that form). When it is not,
    use a raw character string so ``|`` is not forced back in.
    """
    seen: set[str] = set()
    ordered: list[str] = []

    def _add(token: str) -> None:
        if not token or token in seen:
            return
        seen.add(token)
        ordered.append(token)

    selected_set = {str(t) for t in selected if str(t)}
    for d in KNOWN_SPLIT_DELIMITERS:
        if d in selected_set:
            _add(d)
    for d in selected_set:
        if d not in KNOWN_SPLIT_DELIMITERS:
            _add(d)
    for ch in extra or "":
        if not ch.isspace():
            _add(ch)

    if not ordered:
        return DEFAULT_SPLIT_DELIMITERS
    if "|" in ordered:
        # Meta-separator form; omit bare "|" from join — parse_delimiters reinserts it.
        return "|".join(d for d in ordered if d != "|")
    return "".join(ordered)


def spec_to_ui(spec: str) -> tuple[list[str], str]:
    """
    Split a delimiter spec into (known checked chars, extra chars string).

    *extra* is any delimiter not in ``KNOWN_SPLIT_DELIMITERS``, concatenated.
    """
    keys = parse_delimiters(spec)
    known = [d for d in KNOWN_SPLIT_DELIMITERS if d in keys]
    known_set = set(KNOWN_SPLIT_DELIMITERS)
    extra = "".join(k for k in keys if k not in known_set)
    return known, extra


def _split_on_delimiters(text: str, delimiters: Iterable[str]) -> list[str]:
    if not text:
        return []
    delims = [d for d in delimiters if d]
    if not delims:
        return [text]
    # Longest first so multi-char delims win
    ordered = sorted(set(delims), key=len, reverse=True)
    pattern = "|".join(re.escape(d) for d in ordered)
    return re.split(pattern, text)


def _strip_edges(chunk: str) -> str:
    prev = None
    out = chunk.strip()
    while prev != out:
        prev = out
        out = _EDGE_PUNCT_RE.sub("", out).strip()
    return out


def _clean_sense(
    chunk: str,
    *,
    strip_leading_to: bool = True,
) -> str:
    text = _strip_edges(chunk)
    if not text:
        return ""
    text = _POS_PREFIX_RE.sub("", text)
    text = _strip_edges(text)
    if strip_leading_to and _LEADING_TO_RE.match(text):
        # Only strip "to " when the remainder is short (verb gloss style)
        remainder = _LEADING_TO_RE.sub("", text).strip()
        if remainder and len(remainder) <= 40:
            text = remainder
    return _strip_edges(text).lower()


def is_cjk_only(text: str) -> bool:
    """True if *text* is non-empty and only CJK ideographs (no Latin/etc.)."""
    if not text:
        return False
    return bool(_CJK_ONLY_RE.match(text)) and bool(extract_cjk_chars(text))


def normalize_meaning(
    meaning: str,
    *,
    delimiters: Optional[Iterable[str]] = None,
    min_key_length: int = 2,
    strip_leading_to: bool = True,
    ignore_keys: Optional[Iterable[str]] = None,
    keep_cjk_keys: bool = True,
) -> list[str]:
    """
    Turn a Meaning field into one or more normalized synonym keys.

    Pipeline: strip HTML → lowercase (per sense) → drop POS prefixes →
    split on delimiters → clean each sense → filter by length / ignore list.
    """
    plain = strip_html(meaning or "")
    if not plain:
        return []

    delims = list(delimiters) if delimiters is not None else parse_delimiters(
        DEFAULT_SPLIT_DELIMITERS
    )
    ignore = {
        str(k).strip().lower()
        for k in (ignore_keys if ignore_keys is not None else DEFAULT_IGNORE_KEYS)
        if str(k).strip()
    }

    keys: list[str] = []
    seen: set[str] = set()
    for chunk in _split_on_delimiters(plain, delims):
        key = _clean_sense(chunk, strip_leading_to=strip_leading_to)
        if not key:
            continue
        if not keep_cjk_keys and is_cjk_only(key):
            continue
        if len(key) < max(1, int(min_key_length or 1)):
            continue
        if key in ignore:
            continue
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def normalize_from_config(meaning: str, config: dict[str, Any]) -> list[str]:
    """Normalize using knobs from merged add-on config."""
    delim_spec = str(
        config.get("meaning_split_delimiters") or DEFAULT_SPLIT_DELIMITERS
    )
    return normalize_meaning(
        meaning,
        delimiters=parse_delimiters(delim_spec),
        min_key_length=int(config.get("min_key_length", 2) or 2),
        strip_leading_to=bool(config.get("strip_leading_to", True)),
        ignore_keys=config.get("ignore_keys"),
        keep_cjk_keys=True,
    )
