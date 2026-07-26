# -*- coding: utf-8 -*-
"""Build and query the normalized-meaning → notes inverted index."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from aqt import mw
from aqt.utils import showInfo, tooltip

from .cjk import cjk_length, extract_cjk_chars, strip_html
from .defaults import merge_config
from .meaning import normalize_from_config

# Tried when the configured word field is missing from a note type
FALLBACK_WORD_FIELDS = (
    "Word",
    "Hanzi",
    "Expression",
    "Chinese",
    "汉字",
    "漢字",
    "Simplified",
    "Vocabulary",
    "Vocab",
    "Character",
    "Characters",
    "Front",
)

FALLBACK_MEANING_FIELDS = (
    "Meaning",
    "Definition",
    "English",
    "Gloss",
    "Translation",
    "含义",
    "释义",
    "Back",
)


def _addon_package() -> str:
    return __name__.split(".")[0]


@dataclass
class SynonymEntry:
    note_id: int
    word: str
    pinyin: str
    meaning: str
    meaning_keys: list[str]
    suspended: bool
    mature: bool = False


@dataclass
class BuildStats:
    scanned: int = 0
    indexed: int = 0
    keys: int = 0
    skip_no_word_field: int = 0
    skip_no_meaning_field: int = 0
    skip_empty_word: int = 0
    skip_empty_meaning: int = 0
    skip_no_keys: int = 0
    missing_word_models: set[str] = field(default_factory=set)
    missing_meaning_models: set[str] = field(default_factory=set)
    used_word_field: str = ""
    used_meaning_field: str = ""
    resolved_word_fields: set[str] = field(default_factory=set)
    resolved_meaning_fields: set[str] = field(default_factory=set)


class SynonymIndex:
    """In-memory inverted index: normalized meaning key → synonym entries."""

    def __init__(self) -> None:
        self._index: dict[str, list[SynonymEntry]] = {}
        self._by_note: dict[int, SynonymEntry] = {}
        self.note_count: int = 0
        self.key_count: int = 0
        self.last_stats: BuildStats = BuildStats()

    def clear(self) -> None:
        self._index = {}
        self._by_note = {}
        self.note_count = 0
        self.key_count = 0

    def build(self, config: dict[str, Any], *, show_progress: bool = True) -> BuildStats:
        """Scan the collection and rebuild the index from scratch."""
        stats = BuildStats()
        col = mw.col
        if col is None:
            self.last_stats = stats
            return stats

        fields = config.get("fields") or {}
        word_field = (fields.get("word") or "Word").strip()
        pinyin_field = (fields.get("pinyin") or "Pinyin").strip()
        meaning_field = (fields.get("meaning") or "Meaning").strip()
        deck_names: list[str] = list(config.get("decks") or [])
        stats.used_word_field = word_field
        stats.used_meaning_field = meaning_field

        note_ids = self._find_note_ids(deck_names)
        stats.scanned = len(note_ids)
        active_nids = self._nids_with_active_card()
        mature_nids = self._nids_with_mature_card()
        new_index: dict[str, list[SynonymEntry]] = defaultdict(list)
        seen_per_key: dict[str, set[int]] = defaultdict(set)
        by_note: dict[int, SynonymEntry] = {}
        indexed_notes = 0

        total = len(note_ids)
        if show_progress and total:
            mw.progress.start(label="Building word synonyms…", max=total)

        try:
            for i, nid in enumerate(note_ids):
                if show_progress and total and i % 200 == 0:
                    mw.progress.update(
                        label=f"Building word synonyms… ({i}/{total})",
                        value=i,
                    )

                try:
                    note = col.get_note(nid)
                except Exception:
                    continue

                resolved_word = resolve_field(note, word_field, FALLBACK_WORD_FIELDS)
                if not resolved_word:
                    model_name = note.note_type()["name"]
                    stats.missing_word_models.add(model_name)
                    stats.skip_no_word_field += 1
                    continue

                stats.resolved_word_fields.add(resolved_word)
                word = strip_html(note[resolved_word])
                if not word:
                    stats.skip_empty_word += 1
                    continue

                resolved_meaning = resolve_field(
                    note, meaning_field, FALLBACK_MEANING_FIELDS
                )
                if not resolved_meaning:
                    model_name = note.note_type()["name"]
                    stats.missing_meaning_models.add(model_name)
                    stats.skip_no_meaning_field += 1
                    continue

                stats.resolved_meaning_fields.add(resolved_meaning)
                meaning = strip_html(note[resolved_meaning])
                if not meaning:
                    stats.skip_empty_meaning += 1
                    continue

                meaning_keys = normalize_from_config(meaning, config)
                if not meaning_keys:
                    stats.skip_no_keys += 1
                    continue

                pinyin = ""
                rp = resolve_field(note, pinyin_field)
                if rp:
                    pinyin = strip_html(note[rp])

                suspended = nid not in active_nids
                mature = (not suspended) and (nid in mature_nids)
                entry = SynonymEntry(
                    note_id=nid,
                    word=word,
                    pinyin=pinyin,
                    meaning=meaning,
                    meaning_keys=list(meaning_keys),
                    suspended=suspended,
                    mature=mature,
                )
                by_note[nid] = entry

                for key in meaning_keys:
                    if nid in seen_per_key[key]:
                        continue
                    seen_per_key[key].add(nid)
                    new_index[key].append(entry)

                indexed_notes += 1
        finally:
            if show_progress and total:
                mw.progress.finish()

        for _key, entries in new_index.items():
            entries.sort(key=self._sort_key)

        self._index = dict(new_index)
        self._by_note = by_note
        self.note_count = indexed_notes
        self.key_count = len(self._index)
        stats.indexed = indexed_notes
        stats.keys = self.key_count
        self.last_stats = stats
        return stats

    def synonyms_for(
        self,
        meaning: str,
        config: dict[str, Any],
        *,
        note_id: Optional[int] = None,
        word: str = "",
    ) -> list[SynonymEntry]:
        """
        Return synonym entries that share at least one normalized meaning key.

        Current note / identical headword excluded. Flat list (MVP: one group).
        """
        if not meaning or not self._index:
            return []

        keys = normalize_from_config(meaning, config)
        if not keys:
            return []

        include_suspended = bool(config.get("include_suspended", True))
        max_synonyms = int(config.get("max_synonyms", 12) or 12)
        min_len = int(config.get("candidate_min_length", 1) or 0)

        current_word = strip_html(word) if word else ""
        current_cjk = "".join(extract_cjk_chars(current_word, unique=False))

        seen_nids: set[int] = set()
        seen_headwords: set[str] = set()
        filtered: list[SynonymEntry] = []

        for key in keys:
            candidates = self._index.get(key) or []
            for entry in candidates:
                if note_id is not None and entry.note_id == note_id:
                    continue
                if entry.note_id in seen_nids:
                    continue
                if current_word and entry.word == current_word:
                    continue
                entry_cjk = "".join(extract_cjk_chars(entry.word, unique=False))
                if current_cjk and entry_cjk and entry_cjk == current_cjk:
                    continue
                # Deduplicate identical headword CJK across different notes
                if entry_cjk and entry_cjk in seen_headwords:
                    continue
                if not include_suspended and entry.suspended:
                    continue
                if min_len and cjk_length(entry.word) < min_len:
                    continue
                seen_nids.add(entry.note_id)
                if entry_cjk:
                    seen_headwords.add(entry_cjk)
                filtered.append(entry)

        filtered.sort(key=self._sort_key)
        if len(filtered) > max_synonyms:
            filtered = filtered[:max_synonyms]
        return filtered

    @staticmethod
    def _sort_key(entry: SynonymEntry) -> tuple:
        # Mature first, then young/learning, suspended last; then shorter words
        if entry.suspended:
            status = 2
        elif entry.mature:
            status = 0
        else:
            status = 1
        return (status, cjk_length(entry.word), entry.word)

    @staticmethod
    def _find_note_ids(deck_names: list[str]) -> list[int]:
        col = mw.col
        assert col is not None

        if not deck_names:
            # Empty find_notes("") returns [] on some Anki builds — use SQL.
            try:
                ids = col.db.list("select id from notes")
                if ids:
                    return list(ids)
            except Exception:
                pass
            for query in ("*", "deck:*", ""):
                try:
                    ids = list(col.find_notes(query))
                    if ids:
                        return ids
                except Exception:
                    continue
            return []

        note_ids: set[int] = set()
        for name in deck_names:
            name = name.strip()
            if not name:
                continue
            note_ids.update(SynonymIndex._note_ids_for_deck(name))

        return list(note_ids)

    @staticmethod
    def _note_ids_for_deck(name: str) -> list[int]:
        """Resolve note IDs for one deck name (search, then SQL by deck id)."""
        col = mw.col
        assert col is not None
        safe = name.replace('"', '\\"')
        for query in (f'deck:"{safe}"', f"deck:{safe}"):
            try:
                ids = list(col.find_notes(query))
                if ids:
                    return ids
            except Exception:
                continue

        did = None
        try:
            did = col.decks.id(name, create=False)
        except Exception:
            if hasattr(col.decks, "id_for_name"):
                try:
                    did = col.decks.id_for_name(name)
                except Exception:
                    did = None
        if not did:
            return []
        try:
            return list(
                col.db.list(
                    "select distinct nid from cards where did = ? or odid = ?",
                    did,
                    did,
                )
            )
        except Exception:
            return []

    @staticmethod
    def _nids_with_active_card() -> set[int]:
        """Note IDs that have at least one non-suspended card (queue != -1)."""
        col = mw.col
        assert col is not None
        try:
            return set(col.db.list("select distinct nid from cards where queue != -1"))
        except Exception:
            return set()

    @staticmethod
    def _nids_with_mature_card() -> set[int]:
        """Note IDs with at least one active mature card (review, ivl >= 21 days)."""
        col = mw.col
        assert col is not None
        try:
            return set(
                col.db.list(
                    "select distinct nid from cards "
                    "where queue != -1 and type = 2 and ivl >= 21"
                )
            )
        except Exception:
            return set()


def resolve_field(
    note: Any,
    wanted: str,
    fallbacks: tuple[str, ...] = (),
) -> Optional[str]:
    """Match field by exact name, then case-insensitive, then fallbacks."""
    if not wanted and not fallbacks:
        return None
    try:
        keys = list(note.keys())
    except Exception:
        return None
    if wanted in keys:
        return wanted
    lower_map = {k.lower(): k for k in keys}
    if wanted:
        hit = lower_map.get(wanted.lower())
        if hit:
            return hit
    for name in fallbacks:
        if name in keys:
            return name
        hit = lower_map.get(name.lower())
        if hit:
            return hit
    return None


_index: Optional[SynonymIndex] = None


def get_index() -> SynonymIndex:
    global _index
    if _index is None:
        _index = SynonymIndex()
    return _index


def _format_stats(stats: BuildStats) -> str:
    from .about_meta import ADDON_NAME

    return (
        f"{ADDON_NAME}: indexed {stats.indexed} notes, {stats.keys} meaning keys"
    )


def _explain_zero(stats: BuildStats, config: dict[str, Any]) -> None:
    """Show a clear dialog when nothing was indexed."""
    decks = config.get("decks") or []
    deck_line = "all decks" if not decks else ", ".join(decks[:5])
    fields = config.get("fields") or {}
    word_field = fields.get("word", "Word")
    meaning_field = fields.get("meaning", "Meaning")

    lines = [
        "No notes were indexed.",
        "",
        f"Scanned: {stats.scanned} notes ({deck_line})",
        f"Configured word field: “{word_field}”",
        f"Configured meaning field: “{meaning_field}”",
        f"Skipped — word field missing: {stats.skip_no_word_field}",
        f"Skipped — meaning field missing: {stats.skip_no_meaning_field}",
        f"Skipped — empty word: {stats.skip_empty_word}",
        f"Skipped — empty meaning: {stats.skip_empty_meaning}",
        f"Skipped — no usable meaning keys: {stats.skip_no_keys}",
    ]
    if stats.missing_word_models:
        models = ", ".join(sorted(stats.missing_word_models)[:8])
        lines.append(f"Note types without word field: {models}")
    if stats.missing_meaning_models:
        models = ", ".join(sorted(stats.missing_meaning_models)[:8])
        lines.append(f"Note types without meaning field: {models}")
    if stats.resolved_word_fields:
        used = ", ".join(sorted(stats.resolved_word_fields))
        lines.append(f"Word fields actually used: {used}")
    if stats.resolved_meaning_fields:
        used = ", ".join(sorted(stats.resolved_meaning_fields))
        lines.append(f"Meaning fields actually used: {used}")
    lines.extend(
        [
            "",
            "Fix: Tools → Chinese Word Synonyms…",
            "Set Word / Hanzi and Meaning to the fields that hold",
            "your headword and English/definition text,",
            "then Rebuild Index on the General tab.",
        ]
    )
    showInfo("\n".join(lines))


def rebuild_index(*, show_progress: bool = True, notify: bool = True) -> None:
    """Rebuild the global index from current config."""
    if mw.col is None:
        return
    config = merge_config(mw.addonManager.getConfig(_addon_package()))
    idx = get_index()
    stats = idx.build(config, show_progress=show_progress)
    if notify:
        tooltip(_format_stats(stats), period=4000)
        if stats.indexed == 0:
            _explain_zero(stats, config)
