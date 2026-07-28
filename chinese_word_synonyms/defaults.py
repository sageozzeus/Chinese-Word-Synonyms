# -*- coding: utf-8 -*-
"""Shared default config (including Appearance / UI)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_UI: dict[str, Any] = {
    "max_width": "100%",
    "border_radius_px": 12,
    "gap_em": 0.65,
    "char_size_em": 1.05,
    "word_size_em": 0.82,
    "pinyin_size_em": 0.62,
    "bg_light": "#e4ecf6",
    "bg_dark": "#2a303a",
    "border_light": "#b0b0b0",
    "border_dark": "#5a5a5a",
    "mature_light": "#2e7d32",
    "mature_dark": "#81c784",
    "suspended_light": "#c62828",
    "suspended_dark": "#ef9a9a",
    "show_shadow": True,
    "custom_css": "",
}

DEFAULT_CONFIG: dict[str, Any] = {
    "decks": [],
    "fields": {
        "word": "Word",
        "pinyin": "Pinyin",
        "meaning": "Meaning",
    },
    "max_synonyms": 12,
    "include_suspended": True,
    "candidate_min_length": 1,
    "show_only_on_back": True,
    "show_synonym_counts": True,
    "meaning_split_delimiters": ";|/|；|、",
    "min_key_length": 2,
    "strip_leading_to": True,
    "ignore_keys": ["something", "someone", "somebody"],
    "ui": deepcopy(DEFAULT_UI),
}


def merge_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Deep-merge user config onto defaults."""
    merged = deepcopy(DEFAULT_CONFIG)
    if not raw:
        return merged
    for key, value in raw.items():
        if key == "show_on_answer_only" and "show_only_on_back" not in raw:
            merged["show_only_on_back"] = bool(value)
            continue
        if key == "fields" and isinstance(value, dict):
            merged["fields"] = {**merged["fields"], **value}
        elif key == "ui" and isinstance(value, dict):
            merged["ui"] = {**merged["ui"], **value}
        elif key == "ignore_keys" and isinstance(value, list):
            merged["ignore_keys"] = [str(v) for v in value]
        else:
            merged[key] = value
    return merged


def merge_ui(raw: dict[str, Any] | None) -> dict[str, Any]:
    ui = deepcopy(DEFAULT_UI)
    if raw:
        ui.update(raw)
    return ui
