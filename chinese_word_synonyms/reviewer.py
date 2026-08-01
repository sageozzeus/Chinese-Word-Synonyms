# -*- coding: utf-8 -*-
"""Reviewer hooks: append Synonyms panel to the answer HTML."""

from __future__ import annotations

from typing import Any, Optional

from anki.cards import Card
from aqt import mw

from .cjk import strip_html
from .defaults import merge_config
from .indexer import (
    FALLBACK_MEANING_FIELDS,
    FALLBACK_WORD_FIELDS,
    SynonymEntry,
    get_index,
    resolve_field,
)
from .render import PANEL_JS, render_front_badge, render_panel


def _package_name() -> str:
    return __name__.split(".")[0]


def _config() -> dict[str, Any]:
    return merge_config(mw.addonManager.getConfig(_package_name()))


def _show_only_on_back(config: dict[str, Any]) -> bool:
    if "show_only_on_back" in config:
        return bool(config["show_only_on_back"])
    return bool(config.get("show_on_answer_only", True))


def _show_synonym_counts(config: dict[str, Any]) -> bool:
    return bool(config.get("show_synonym_counts", True))


def _field(config: dict[str, Any], key: str, default: str) -> str:
    fields = config.get("fields") or {}
    return (fields.get(key) or default).strip()


def _fields_from_note(
    note: Any, config: dict[str, Any]
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Return (word, meaning, note_id) using the same field resolution as the indexer."""
    wanted_word = _field(config, "word", "Word")
    wanted_meaning = _field(config, "meaning", "Meaning")
    resolved_word = resolve_field(note, wanted_word, FALLBACK_WORD_FIELDS)
    resolved_meaning = resolve_field(note, wanted_meaning, FALLBACK_MEANING_FIELDS)
    if not resolved_word or not resolved_meaning:
        return None, None, None
    word = strip_html(note[resolved_word])
    meaning = strip_html(note[resolved_meaning])
    if not word or not meaning:
        return None, None, None
    try:
        nid = int(note.id)
    except Exception:
        nid = None
    return word, meaning, nid


def _synonym_entries_for_card(card: Card) -> list[SynonymEntry]:
    idx = get_index()
    if not idx.note_count and not idx._index:
        return []

    config = _config()
    try:
        note = card.note()
    except Exception:
        return []

    word, meaning, note_id = _fields_from_note(note, config)
    if not meaning:
        return []

    return idx.synonyms_for(meaning, config, note_id=note_id, word=word or "")


def panel_html_for_card(card: Card) -> str:
    """Build Synonyms panel HTML for *card*, or "" if nothing to show."""
    entries = _synonym_entries_for_card(card)
    if not entries:
        return ""
    config = _config()
    return render_panel(entries, ui=config.get("ui"))


def front_badge_html_for_card(card: Card) -> str:
    """Known/Total summary card on the question side when the full panel is back-only."""
    entries = _synonym_entries_for_card(card)
    if not entries:
        return ""
    config = _config()
    known = sum(1 for e in entries if not e.suspended)
    return render_front_badge(known, len(entries), ui=config.get("ui"))


def on_card_will_show(html: str, card: Card, context: str) -> str:
    """
    Reliable injection: append panel HTML before Anki paints the answer.

    Prefer this over webview.eval — fade/DOM updates often wipe late eval inserts.
    """
    if context not in ("reviewAnswer", "reviewQuestion"):
        return html
    config = _config()
    if context == "reviewQuestion" and _show_only_on_back(config) and _show_synonym_counts(config):
        badge = front_badge_html_for_card(card)
        return html + badge if badge else html
    if _show_only_on_back(config) and context != "reviewAnswer":
        return html
    panel = panel_html_for_card(card)
    if not panel:
        return html
    return html + panel


def on_show_answer(card: Card) -> None:
    """Fallback inject if needed, then bind horizontal scroll arrows."""
    if mw.reviewer is None or mw.reviewer.web is None:
        return
    panel = panel_html_for_card(card)
    if panel:
        import json

        payload = json.dumps(panel)
        js = f"""
        (function() {{
          if (document.getElementById('word-synonyms-panel')) {{ return; }}
          var target = document.getElementById('qa') || document.body;
          var tmp = document.createElement('div');
          tmp.innerHTML = {payload};
          while (tmp.firstChild) {{
            var child = tmp.firstChild;
            if (child.nodeName === 'SCRIPT') {{
              tmp.removeChild(child);
              continue;
            }}
            if (child.nodeName === 'STYLE') {{ child.id = 'word-synonyms-style'; }}
            target.appendChild(child);
          }}
        }})();
        """
        mw.reviewer.web.eval(js)
    # Scripts inside card HTML are not always executed — bind via eval
    mw.reviewer.web.eval(PANEL_JS)


def on_show_question(card: Card) -> None:
    if not _show_only_on_back(_config()):
        return
    # card_will_show already appended the front Known/Total card into question HTML.
    # Only strip leftover *answer* panel injection from a prior fallback eval —
    # do not remove #word-synonyms-front-card (that would erase the front summary).
    if mw.reviewer is None or mw.reviewer.web is None:
        return
    mw.reviewer.web.eval(
        """
        (function() {
          var el = document.getElementById('word-synonyms-panel');
          if (el) { el.remove(); }
          var st = document.getElementById('word-synonyms-style');
          if (st) { st.remove(); }
          var cu = document.getElementById('word-synonyms-custom');
          if (cu) { cu.remove(); }
        })();
        """
    )
