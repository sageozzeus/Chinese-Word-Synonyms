# -*- coding: utf-8 -*-
"""Add-on identity, links, and changelog for the About settings tab.

Bump ADDON_VERSION and prepend a CHANGELOG entry whenever you ship.
After publishing on AnkiWeb, set URL_ANKIWEB to the listing URL
(e.g. https://ankiweb.net/shared/info/<id>) so AnkiWeb / Rate links appear.
"""

from __future__ import annotations

from typing import List, Tuple

ADDON_NAME = "Chinese Word Synonyms"
ADDON_VERSION = "0.1.0"
MIN_ANKI = "23.10+"
AUTHOR = "Ozzeus"
LICENSE = "MIT"

URL_GITHUB = "https://github.com/sageozzeus/Chinese-Word-Synonyms"
URL_ISSUES = URL_GITHUB + "/issues"
URL_X = "https://x.com/sageozzeus"
# Set after AnkiWeb publish, e.g. "https://ankiweb.net/shared/info/<id>"
URL_ANKIWEB = ""

# Newest first. Keep the latest entry to ~5 bullets for the About dialog.
CHANGELOG: List[Tuple[str, List[str]]] = [
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
