"""Unit tests for the discover module.

Tests parsing logic and data transformations without requiring network access
or external CLI tools.  All subprocess calls are avoided by testing the
pure-function parsers directly.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from discover import _parse_clawhub_search, _AWESOME_ENTRY_RE


class TestClawHubParsing(unittest.TestCase):
    """Tests for ClawHub search output parsing."""

    def test_parses_standard_output(self) -> None:
        """Standard clawhub search output should parse correctly."""
        output = (
            "- Searching\n"
            "calendar v1.0.0  Calendar  (0.520)\n"
            "feishu-calendar v1.0.2  Feishu Calendar  (0.476)\n"
            "accli v1.0.0  Apple Calendar CLI  (0.458)\n"
        )
        results = _parse_clawhub_search(output)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["slug"], "calendar")
        self.assertEqual(results[0]["version"], "1.0.0")
        self.assertEqual(results[0]["name"], "Calendar")
        self.assertAlmostEqual(results[0]["relevance"], 0.520)

    def test_skips_spinner_line(self) -> None:
        """The '- Searching' spinner line should be skipped."""
        output = "- Searching\n"
        results = _parse_clawhub_search(output)
        self.assertEqual(len(results), 0)

    def test_handles_empty_output(self) -> None:
        """Empty string should return empty list."""
        results = _parse_clawhub_search("")
        self.assertEqual(len(results), 0)

    def test_handles_multiword_names(self) -> None:
        """Skill names with multiple words should be captured fully."""
        output = "my-cool-skill v2.1.3  My Cool Skill Name  (0.999)\n"
        results = _parse_clawhub_search(output)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "My Cool Skill Name")


class TestAwesomeListParsing(unittest.TestCase):
    """Tests for awesome list regex parsing."""

    def test_matches_standard_entry(self) -> None:
        """Standard awesome list entries should match."""
        line = "- [calendar](https://github.com/openclaw/skills/tree/main/skills/0xterrybit/calendar/SKILL.md) - Calendar management"
        match = _AWESOME_ENTRY_RE.match(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "calendar")
        self.assertIn("github.com", match.group(2))
        self.assertEqual(match.group(3), "Calendar management")

    def test_no_match_on_header(self) -> None:
        """Category headers should not match the entry regex."""
        line = "### Coding Agents & IDEs"
        match = _AWESOME_ENTRY_RE.match(line)
        self.assertIsNone(match)

    def test_matches_entry_without_description(self) -> None:
        """Entries with minimal/no description should still match."""
        line = "- [my-skill](https://github.com/user/repo) -"
        match = _AWESOME_ENTRY_RE.match(line)
        self.assertIsNotNone(match)


if __name__ == "__main__":
    unittest.main()
