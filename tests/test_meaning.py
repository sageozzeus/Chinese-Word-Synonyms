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

from chinese_word_synonyms.meaning import (  # noqa: E402
    normalize_from_config,
    normalize_meaning,
    parse_delimiters,
)


class TestParseDelimiters(unittest.TestCase):
    def test_pipe_separated(self) -> None:
        self.assertEqual(
            parse_delimiters(";|/|；|、"),
            [";", "|", "/", "；", "、"],
        )

    def test_empty_falls_back(self) -> None:
        self.assertIn(";", parse_delimiters(""))


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


if __name__ == "__main__":
    unittest.main()
