"""Unit tests for the evaluate module.

Tests AST-based security analysis, regex credential detection, code metrics
extraction, and the scoring engine — all without requiring network access
or external CLIs.
"""

import sys
import unittest
from pathlib import Path
from typing import Dict

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from evaluate import (
    SecurityVisitor,
    analyze_code,
    analyze_security_ast,
    analyze_security_regex,
    _score_documentation,
    _score_code_quality,
    _score_community,
    _score_structure,
    _score_compatibility,
    _assign_tier,
)


class TestSecurityAST(unittest.TestCase):
    """Tests for AST-based security analysis."""

    def test_detects_eval_with_dynamic_arg(self) -> None:
        """eval() with a variable argument should be flagged as critical."""
        source = 'x = eval(user_input)'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.severity == "critical" and f.category == "code_execution"
                           for f in flags))

    def test_ignores_eval_with_literal(self) -> None:
        """eval() with a string literal should NOT be flagged."""
        source = 'x = eval("1 + 2")'
        flags = analyze_security_ast(source, "test.py")
        code_exec = [f for f in flags if f.category == "code_execution"]
        self.assertEqual(len(code_exec), 0)

    def test_detects_os_system(self) -> None:
        """os.system() should always be flagged as critical."""
        source = 'import os\nos.system("ls")'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "command_injection" for f in flags))

    def test_detects_subprocess_shell_true(self) -> None:
        """subprocess.run(shell=True) should be flagged."""
        source = 'import subprocess\nsubprocess.run("ls", shell=True)'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "command_injection" for f in flags))

    def test_subprocess_shell_false_ok(self) -> None:
        """subprocess.run(shell=False) should NOT be flagged."""
        source = 'import subprocess\nsubprocess.run(["ls"], shell=False)'
        flags = analyze_security_ast(source, "test.py")
        cmd_flags = [f for f in flags if f.category == "command_injection"]
        self.assertEqual(len(cmd_flags), 0)

    def test_detects_pickle_loads(self) -> None:
        """pickle.loads() should be flagged as high severity."""
        source = 'import pickle\npickle.loads(data)'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "deserialization" for f in flags))

    def test_detects_network_imports(self) -> None:
        """Import of requests/httpx/aiohttp should be flagged."""
        source = 'import requests'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "network_access" for f in flags))

    def test_handles_syntax_error(self) -> None:
        """Unparseable code should return a parse_error flag, not crash."""
        source = 'def broken(:'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "parse_error" for f in flags))

    def test_async_function_parsed(self) -> None:
        """Async functions should be analyzed without errors."""
        source = 'import os\nasync def run():\n    os.system("bad")'
        flags = analyze_security_ast(source, "test.py")
        self.assertTrue(any(f.category == "command_injection" for f in flags))


class TestSecurityRegex(unittest.TestCase):
    """Tests for regex-based credential detection."""

    def test_detects_aws_key(self) -> None:
        """AWS access key pattern should be detected."""
        source = 'aws_key = "AKIAIOSFODNN7EXAMPLE"'
        flags = analyze_security_regex(source, "test.py")
        self.assertTrue(any("AWS" in f.detail for f in flags))

    def test_detects_openai_key(self) -> None:
        """OpenAI API key pattern should be detected."""
        source = 'key = "sk-abcdefghijklmnopqrstuvwxyz1234"'
        flags = analyze_security_regex(source, "test.py")
        self.assertTrue(any("OpenAI" in f.detail for f in flags))

    def test_detects_github_pat(self) -> None:
        """GitHub PAT pattern should be detected."""
        source = 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"'
        flags = analyze_security_regex(source, "test.py")
        self.assertTrue(any("GitHub" in f.detail for f in flags))

    def test_clean_code_no_flags(self) -> None:
        """Normal code with no credentials should produce no flags."""
        source = 'x = 42\ndef hello():\n    return "world"'
        flags = analyze_security_regex(source, "test.py")
        self.assertEqual(len(flags), 0)


class TestCodeMetrics(unittest.TestCase):
    """Tests for code quality metric extraction."""

    def test_counts_functions(self) -> None:
        """Function count should include both sync and async defs."""
        source = 'def a():\n    pass\nasync def b():\n    pass'
        m = analyze_code(source)
        self.assertEqual(m.function_count, 2)

    def test_detects_docstrings(self) -> None:
        """Functions with docstrings should be counted."""
        source = 'def a():\n    """Doc."""\n    pass\ndef b():\n    pass'
        m = analyze_code(source)
        self.assertEqual(m.docstring_count, 1)

    def test_detects_type_hints(self) -> None:
        """Type-annotated arguments should be counted."""
        source = 'def a(x: int, y: str) -> bool:\n    pass'
        m = analyze_code(source)
        self.assertGreater(m.typed_args, 0)

    def test_detects_exception_handling(self) -> None:
        """Try/except blocks should set has_exception_handling."""
        source = 'try:\n    pass\nexcept:\n    pass'
        m = analyze_code(source)
        self.assertTrue(m.has_exception_handling)

    def test_counts_comments(self) -> None:
        """Comment lines should be counted."""
        source = '# comment\nx = 1\n# another'
        m = analyze_code(source)
        self.assertEqual(m.comment_lines, 2)


class TestScoring(unittest.TestCase):
    """Tests for the scoring dimension functions."""

    def test_missing_skill_md_scores_zero(self) -> None:
        """A skill without SKILL.md should score 0 in documentation."""
        files: Dict[str, str] = {"README.md": "Hello"}
        dim = _score_documentation(files)
        self.assertEqual(dim.score, 0)

    def test_full_docs_scores_high(self) -> None:
        """A skill with all documentation files should score near max."""
        files = {
            "SKILL.md": "\n".join([f"Line {i}" for i in range(150)]),
            "README.md": "Read me",
            "CHANGELOG.md": "# Changelog",
        }
        dim = _score_documentation(files)
        self.assertGreater(dim.score, 15)

    def test_community_stars_scoring(self) -> None:
        """Star counts should map to expected point ranges."""
        self.assertEqual(_score_community({"stars": 0}).score, 0)
        self.assertEqual(_score_community({"stars": 5}).score, 3)
        self.assertEqual(_score_community({"stars": 25}).score, 6)
        self.assertEqual(_score_community({"stars": 100}).score, 9)
        self.assertEqual(_score_community({"stars": 500}).score, 12)

    def test_tier_assignment(self) -> None:
        """Tier thresholds should map correctly."""
        self.assertEqual(_assign_tier(95), "S")
        self.assertEqual(_assign_tier(80), "A")
        self.assertEqual(_assign_tier(65), "B")
        self.assertEqual(_assign_tier(45), "C")
        self.assertEqual(_assign_tier(30), "F")


if __name__ == "__main__":
    unittest.main()
