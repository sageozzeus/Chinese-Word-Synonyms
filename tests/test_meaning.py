# -*- coding: utf-8 -*-
"""Standalone tests for meaning normalization (no Anki required).

Run: python3 -m unittest tests.test_meaning -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chinese_word_synonyms.defaults import merge_config  # noqa: E402
from chinese_word_synonyms.meaning import (  # noqa: E402
    DEFAULT_IGNORE_KEYS,
    DEFAULT_SPLIT_DELIMITERS,
    delimiters_to_spec,
    normalize_from_config,
    normalize_meaning,
    parse_delimiters,
    spec_to_ui,
)


class TestParseDelimiters(unittest.TestCase):
    def test_pipe_separated(self) -> None:
        self.assertEqual(
            parse_delimiters(";|/|；|、|,"),
            [";", "|", "/", "；", "、", ","],
        )

    def test_empty_falls_back(self) -> None:
        self.assertIn(";", parse_delimiters(""))
        self.assertIn(",", parse_delimiters(""))


class TestDelimiterSpecRoundTrip(unittest.TestCase):
    def test_default_round_trip(self) -> None:
        known, extra = spec_to_ui(DEFAULT_SPLIT_DELIMITERS)
        self.assertEqual(set(known), {";", ",", "|", "/", "；", "、"})
        self.assertEqual(extra, "")
        spec = delimiters_to_spec(known, extra)
        self.assertEqual(set(parse_delimiters(spec)), set(parse_delimiters(DEFAULT_SPLIT_DELIMITERS)))

    def test_without_pipe(self) -> None:
        spec = delimiters_to_spec([";", ","], "")
        self.assertNotIn("|", parse_delimiters(spec))
        self.assertEqual(set(parse_delimiters(spec)), {";", ","})

    def test_extra_chars(self) -> None:
        spec = delimiters_to_spec([";"], "·:")
        keys = parse_delimiters(spec)
        self.assertIn(";", keys)
        self.assertIn("·", keys)
        self.assertIn(":", keys)
        known, extra = spec_to_ui(spec)
        self.assertEqual(known, [";"])
        self.assertIn("·", extra)
        self.assertIn(":", extra)

    def test_empty_falls_back_to_default(self) -> None:
        self.assertEqual(delimiters_to_spec([], ""), DEFAULT_SPLIT_DELIMITERS)


class TestNormalizeMeaning(unittest.TestCase):
    def test_simple(self) -> None:
        self.assertEqual(normalize_meaning("happy"), ["happy"])

    def test_case_and_html(self) -> None:
        self.assertEqual(
            normalize_meaning("<b>Happy</b>"),
            ["happy"],
        )

    def test_split_senses(self) -> None:
        self.assertEqual(
            normalize_meaning("happy; glad"),
            ["happy", "glad"],
        )
        self.assertEqual(
            normalize_meaning("happy|glad/joy"),
            ["happy", "glad", "joy"],
        )
        self.assertEqual(
            normalize_meaning("快乐；happy"),
            ["快乐", "happy"],
        )
        self.assertEqual(
            normalize_meaning("happy, glad, joyful"),
            ["happy", "glad", "joyful"],
        )

    def test_pos_prefix(self) -> None:
        self.assertEqual(normalize_meaning("adj. happy"), ["happy"])
        self.assertEqual(normalize_meaning("n. happiness"), ["happiness"])
        self.assertEqual(normalize_meaning("v. to run"), ["run"])

    def test_leading_to(self) -> None:
        self.assertEqual(
            normalize_meaning("to be happy", strip_leading_to=True),
            ["be happy"],
        )
        self.assertEqual(
            normalize_meaning("to be happy", strip_leading_to=False),
            ["to be happy"],
        )

    def test_min_key_length(self) -> None:
        self.assertEqual(
            normalize_meaning("a; happy", min_key_length=2),
            ["happy"],
        )

    def test_ignore_keys(self) -> None:
        self.assertEqual(
            normalize_meaning(
                "happy; something",
                ignore_keys=["something"],
            ),
            ["happy"],
        )

    def test_default_ignores_filler_glosses(self) -> None:
        self.assertEqual(
            normalize_meaning("happy, glad, etc."),
            ["happy", "glad"],
        )
        self.assertEqual(
            normalize_meaning("sth; sb; oneself; and so on"),
            [],
        )
        self.assertEqual(
            normalize_meaning("archaic; slang; fig.; see also; mw"),
            [],
        )
        # formal / informal / dialect intentionally kept as real keys
        self.assertEqual(
            normalize_meaning("formal; informal; dialect"),
            ["formal", "informal", "dialect"],
        )

    def test_dedupe(self) -> None:
        self.assertEqual(
            normalize_meaning("happy; Happy; happy"),
            ["happy"],
        )

    def test_empty(self) -> None:
        self.assertEqual(normalize_meaning(""), [])
        self.assertEqual(normalize_meaning("   "), [])
        self.assertEqual(normalize_meaning("<br>"), [])

    def test_from_config(self) -> None:
        conf = {
            "meaning_split_delimiters": ";|/",
            "min_key_length": 2,
            "strip_leading_to": True,
            "ignore_keys": ["someone"],
        }
        self.assertEqual(
            normalize_from_config("adj. happy; someone; glad", conf),
            ["happy", "glad"],
        )


class TestMergeIgnoreKeys(unittest.TestCase):
    def test_legacy_ignore_keys_upgraded(self) -> None:
        conf = merge_config(
            {"ignore_keys": ["something", "someone", "somebody"]}
        )
        self.assertEqual(conf["ignore_keys"], list(DEFAULT_IGNORE_KEYS))
        self.assertIn("etc", conf["ignore_keys"])

    def test_custom_ignore_keys_preserved(self) -> None:
        custom = ["something", "someone", "somebody", "custom-token"]
        conf = merge_config({"ignore_keys": custom})
        self.assertEqual(conf["ignore_keys"], custom)


if __name__ == "__main__":
    unittest.main()
