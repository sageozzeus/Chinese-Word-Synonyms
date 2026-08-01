# -*- coding: utf-8 -*-
"""Add-on identity, links, and changelog for the About settings tab.

Bump ADDON_VERSION and prepend a CHANGELOG entry whenever you ship.
After publishing on AnkiWeb, set URL_ANKIWEB to the listing URL
(e.g. https://ankiweb.net/shared/info/<id>) so AnkiWeb / Rate links appear.
"""

from __future__ import annotations

from typing import List, Tuple

ADDON_NAME = "Chinese Word Synonyms"
ADDON_VERSION = "0.1.3"
MIN_ANKI = "23.10+"
AUTHOR = "Ozzeus"
LICENSE = "MIT"

URL_GITHUB = "https://github.com/sageozzeus/Chinese-Word-Synonyms"
URL_ISSUES = URL_GITHUB + "/issues"
URL_X = "https://x.com/sageozzeus"
URL_ANKIWEB = "https://ankiweb.net/shared/info/1733540881"
# Tools → Add-ons → Get Add-ons… (same numeric id as the listing URL)
ANKIWEB_CODE = "1733540881"

# Newest first. Keep the latest entry to ~5 bullets for the About dialog.
CHANGELOG: List[Tuple[str, List[str]]] = [
    (
        "0.1.3",
        [
            "Front card: N Known Synonyms / N Total Synonyms (Known = unsuspended)",
            "Meaning delimiters in Settings (defaults include comma)",
            "Optional Extra delimiters; rebuild prompt when they change",
        ],
    ),
    (
        "0.1.2",
        [
            "Front card: N Known Synonyms / N Total Synonyms (compact)",
            "Known = unsuspended synonyms; Total = all matches",
            "Comma (,) is a default meaning delimiter (e.g. happy, glad)",
        ],
    ),
    (
        "0.1.1",
        [
            "Front card pill shows how many synonyms match (e.g. 4 Synonyms)",
            "Toggle Show synonym counts in General → Display options",
            "Full Synonyms panel still on the card back when Show only on back is on",
        ],
    ),
    (
        "0.1.0",
        [
            "Synonyms from your own deck by shared normalized meanings",
            "General and Appearance settings GUI (no JSON editing)",
            "Click a synonym to open it in the Browser",
            "Light/dark panel colors and optional custom CSS",
            "Rebuild Index from Tools → Chinese Word Synonyms…",
        ],
    ),
]
