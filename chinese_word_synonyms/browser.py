# -*- coding: utf-8 -*-
"""Open synonym notes in the Anki Browser."""

from __future__ import annotations

from typing import Any

from aqt import dialogs, mw
from aqt.reviewer import Reviewer

CMD_PREFIX = "word_synonyms_browse:"


def open_note_in_browser(note_id: int) -> None:
    """Open Browser filtered to a single note."""
    if mw is None or mw.col is None:
        return
    # Anki passes search to search_for_terms(*search) — must be a tuple/list,
    # not a bare string (a string is unpacked character-by-character).
    dialogs.open("Browser", mw, search=(f"nid:{note_id}",))


def on_webview_js_message(
    handled: tuple[bool, Any],
    message: str,
    context: Any,
) -> tuple[bool, Any]:
    """
    Handle pycmd('word_synonyms_browse:<nid>') from the reviewer webview.
    """
    if not message.startswith(CMD_PREFIX):
        return handled
    # Only act in the reviewer (ignore other webviews)
    if context is not None and not isinstance(context, Reviewer):
        return handled
    try:
        nid = int(message[len(CMD_PREFIX) :])
    except ValueError:
        return (True, None)
    open_note_in_browser(nid)
    return (True, None)
