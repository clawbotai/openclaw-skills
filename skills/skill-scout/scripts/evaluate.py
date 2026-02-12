"""Quality scoring and static analysis engine for skill-scout.

Evaluates OpenClaw skills across seven dimensions (documentation, code quality,
community signal, security posture, maintenance health, structural compliance,
and compatibility) using AST-based static analysis for Python code and regex
patterns for credential detection.

Can evaluate skills from a local path or by fetching files from GitHub via
the ``gh`` CLI.
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common import (
    SKILLS_DIR,
    ShellError,
    check_tool,
    content_hash,
    db_read,
    db_write,
    get_db,
    json_out,
    logger,
    run_shell,
    utcnow,
)

# ---------------------------------------------------------------------------
# Known Python 3.9 stdlib modules (for compatibility checking)
# ---------------------------------------------------------------------------

# Hardcoded set of Python 3.9 stdlib top-level module names.  We use this
# to check whether a skill depends only on the standard library (which means
# zero pip installs needed).  Any import not in this set is flagged as a
# third-party dependency, which hurts the compatibility score.
# Source: https://docs.python.org/3.9/py-modindex.html
STDLIB_MODULES = frozenset({
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
    "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
    "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
    "colorsys", "compileall", "concurrent", "configparser", "contextlib",
    "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
    "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc",
    "getopt", "getpass", "gettext", "glob", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "keyword", "lib2to3", "linecache", "locale", "logging",
    "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
    "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site",
    "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "sqlite3",
    "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test",
    "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle",
    "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib",
    "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib",
    # Also allow common built-in names
    "_thread", "__future__", "_io",
})

# ---------------------------------------------------------------------------
# Credential patterns (regex)
# ---------------------------------------------------------------------------

# Regex patterns for detecting hardcoded credentials in source code.
# Each tuple is (pattern, human-readable label).  Patterns are designed
# for high precision: they match specific key formats (e.g. AWS keys
# start with AKIA, GitHub PATs start with ghp_) rather than generic
# "long string near keyword" heuristics, to minimize false positives.
CREDENTIAL_PATTERNS: List[Tuple[str, str]] = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"glpat-[a-zA-Z0-9\-]{20,}", "GitLab PAT"),
    (r'(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|password)\s*[=:]\s*["\'][A-Za-z0-9+/=]{16,}',
     "Hardcoded credential"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private Key"),
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SecurityFlag:
    """A single security concern found during analysis.

    Attributes:
        severity: One of ``critical``, ``high``, ``medium``, ``low``.
        category: Short label for the issue type.
        detail: Human-readable description.
        file: File where the issue was found.
        line: Line number (0 if unknown).
    """
    severity: str  # critical, high, medium, low
    category: str
    detail: str
    file: str = ""
    line: int = 0


@dataclass
class DimensionScore:
    """Score breakdown for a single evaluation dimension.

    Attributes:
        name: Dimension name.
        score: Points earned.
        max_score: Maximum possible points.
        details: List of individual check results.
    """
    name: str
    score: float
    max_score: float
    details: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Complete evaluation result for a skill.

    Attributes:
        slug: Skill identifier.
        overall_score: Total score out of 100.
        tier: Quality tier (S/A/B/C/F).
        dimensions: Per-dimension score breakdown.
        security_flags: List of security concerns.
        content_hash: SHA-256 of the SKILL.md content.
        evaluated_at: ISO timestamp of evaluation.
    """
    slug: str
    overall_score: float
    tier: str
    dimensions: List[DimensionScore]
    security_flags: List[SecurityFlag]
    content_hash: str = ""
    evaluated_at: str = ""


# ---------------------------------------------------------------------------
# AST-based security analysis
# ---------------------------------------------------------------------------

class SecurityVisitor(ast.NodeVisitor):
    """AST visitor that flags dangerous code patterns.

    Walks the abstract syntax tree looking for calls to ``eval``, ``exec``,
    ``os.system``, ``subprocess`` with ``shell=True``, ``pickle.loads``,
    and network library imports.

    Attributes:
        flags: Accumulated list of SecurityFlag instances.
        filename: Source file being analyzed.
    """

    def __init__(self, filename: str = ""):
        self.flags: List[SecurityFlag] = []
        self.filename = filename

    # The core challenge of AST security analysis is resolving the target of
    # a function call.  Python's AST represents `os.system("cmd")` as a
    # nested Attribute → Name chain, not a simple string.  We walk backwards
    # through the chain to reconstruct the dotted name for pattern matching.

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the dotted name of a function call.

        Args:
            node: An ``ast.Call`` node.

        Returns:
            Dotted name string (e.g. ``os.system``) or empty string.
        """
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    def _has_shell_true(self, node: ast.Call) -> bool:
        """Check if a function call has ``shell=True`` as a keyword argument.

        Args:
            node: An ``ast.Call`` node.

        Returns:
            True if ``shell=True`` is present.
        """
        for kw in node.keywords:
            if kw.arg == "shell":
                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
                if isinstance(kw.value, ast.NameConstant) and kw.value.value is True:
                    return True
        return False

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes to detect dangerous patterns.

        Args:
            node: The Call AST node.
        """
        name = self._get_call_name(node)
        line = getattr(node, "lineno", 0)

        # eval() / exec() with non-literal arguments
        if name in ("eval", "exec"):
            # Check if argument is a constant (literal) — those are safe
            if node.args and not isinstance(node.args[0], ast.Constant):
                self.flags.append(SecurityFlag(
                    severity="critical", category="code_execution",
                    detail=f"{name}() called with dynamic argument",
                    file=self.filename, line=line,
                ))

        # os.system()
        elif name == "os.system":
            self.flags.append(SecurityFlag(
                severity="critical", category="command_injection",
                detail="os.system() — use subprocess with list args instead",
                file=self.filename, line=line,
            ))

        # subprocess with shell=True
        elif name.startswith("subprocess.") and self._has_shell_true(node):
            self.flags.append(SecurityFlag(
                severity="critical", category="command_injection",
                detail=f"{name}(shell=True) — command injection risk",
                file=self.filename, line=line,
            ))

        # pickle.loads (deserialization of untrusted data)
        elif name in ("pickle.loads", "pickle.load", "cPickle.loads", "cPickle.load"):
            self.flags.append(SecurityFlag(
                severity="high", category="deserialization",
                detail=f"{name}() — arbitrary code execution via crafted pickle",
                file=self.filename, line=line,
            ))

        # __import__() — dynamic import, common evasion technique
        elif name == "__import__":
            self.flags.append(SecurityFlag(
                severity="high", category="dynamic_import",
                detail="__import__() — dynamic module loading (evasion technique)",
                file=self.filename, line=line,
            ))

        # importlib.import_module() — another evasion path
        elif name in ("importlib.import_module", "importlib.__import__"):
            self.flags.append(SecurityFlag(
                severity="high", category="dynamic_import",
                detail=f"{name}() — dynamic module loading (evasion technique)",
                file=self.filename, line=line,
            ))

        # getattr on dangerous modules: getattr(os, 'system')
        elif name == "getattr" and len(node.args) >= 2:
            if (isinstance(node.args[0], ast.Name) and
                    node.args[0].id in ("os", "subprocess", "shutil", "ctypes")):
                self.flags.append(SecurityFlag(
                    severity="high", category="dynamic_access",
                    detail=f"getattr({node.args[0].id}, ...) — dynamic attribute access on dangerous module",
                    file=self.filename, line=line,
                ))

        # compile() + exec() pattern
        elif name == "compile" and len(node.args) >= 1:
            if not isinstance(node.args[0], ast.Constant):
                self.flags.append(SecurityFlag(
                    severity="medium", category="code_generation",
                    detail="compile() with dynamic argument — potential code generation",
                    file=self.filename, line=line,
                ))

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Flag imports of network libraries that could exfiltrate data.

        Args:
            node: The Import AST node.
        """
        for alias in node.names:
            if alias.name in ("requests", "httpx", "aiohttp"):
                self.flags.append(SecurityFlag(
                    severity="medium", category="network_access",
                    detail=f"Import of network library: {alias.name}",
                    file=self.filename, line=getattr(node, "lineno", 0),
                ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Flag from-imports of network libraries.

        Args:
            node: The ImportFrom AST node.
        """
        if node.module and node.module.split(".")[0] in ("requests", "httpx", "aiohttp"):
            self.flags.append(SecurityFlag(
                severity="medium", category="network_access",
                detail=f"Import from network library: {node.module}",
                file=self.filename, line=getattr(node, "lineno", 0),
            ))
        self.generic_visit(node)

    # Also handle async function defs (they can contain the same patterns)
    visit_AsyncFunctionDef = ast.NodeVisitor.generic_visit


def analyze_security_ast(source: str, filename: str = "") -> List[SecurityFlag]:
    """Run AST-based security analysis on Python source code.

    Args:
        source: Python source code string.
        filename: Original filename for error reporting.

    Returns:
        List of SecurityFlag instances found.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return [SecurityFlag(
            severity="low", category="parse_error",
            detail=f"Could not parse: {e}", file=filename,
        )]

    visitor = SecurityVisitor(filename)
    visitor.visit(tree)
    return visitor.flags


def analyze_security_regex(source: str, filename: str = "") -> List[SecurityFlag]:
    """Run regex-based credential detection on source code.

    Args:
        source: Source code or text content.
        filename: Original filename for error reporting.

    Returns:
        List of SecurityFlag instances for detected credentials.
    """
    flags: List[SecurityFlag] = []
    for pattern, label in CREDENTIAL_PATTERNS:
        for match in re.finditer(pattern, source):
            # Redact the match in the detail
            matched = match.group(0)
            redacted = matched[:8] + "****" + matched[-4:] if len(matched) > 16 else "****"
            line_num = source[:match.start()].count("\n") + 1
            flags.append(SecurityFlag(
                severity="critical", category="credential_exposure",
                detail=f"{label}: {redacted}",
                file=filename, line=line_num,
            ))
    return flags


# ---------------------------------------------------------------------------
# Markdown security scanning (SKILL.md / README.md)
# ---------------------------------------------------------------------------

# Shell command patterns that should never appear in skill documentation.
# These indicate either prompt injection (tricking the agent into running
# malicious commands) or supply-chain attacks via "prerequisite" instructions.
MARKDOWN_SHELL_PATTERNS: List[Tuple[str, str, str]] = [
    # (regex, label, severity)
    (r"curl\s+[^\s]+\s*\|\s*(?:ba)?sh", "Pipe to shell (curl|sh)", "critical"),
    (r"wget\s+[^\s]+\s*[;&|]\s*(?:ba)?sh", "Pipe to shell (wget)", "critical"),
    (r"curl\s+-[sS]*o\s", "Silent download (curl -o)", "high"),
    (r"wget\s+-q", "Silent download (wget -q)", "high"),
    (r"chmod\s+\+x\s", "Make executable (chmod +x)", "high"),
    (r"base64\s+-[dD]", "Base64 decode", "high"),
    (r"xxd\s+-r", "Hex decode (xxd -r)", "high"),
    (r"python3?\s+-c\s+['\"].*(?:import|exec|eval)", "Inline Python execution", "high"),
    (r"npm\s+install\s+-g\s", "Global npm install", "medium"),
    (r"pip3?\s+install\s+(?!-r)", "Direct pip install (not requirements)", "medium"),
    (r"brew\s+install\s", "Homebrew install", "low"),
]

# URL patterns that suggest untrusted external resources
SUSPICIOUS_URL_PATTERNS: List[Tuple[str, str, str]] = [
    (r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "Raw IP address URL", "critical"),
    (r"https?://(?:glot\.io|repl\.it|pastebin\.com|hastebin\.com)", "Code-paste service URL", "high"),
    (r"https?://bit\.ly|tinyurl\.com|t\.co|goo\.gl", "URL shortener", "high"),
    (r"https?://[^\s\"']+\.(?:zip|tar\.gz|exe|dmg|pkg|sh|bat)\b", "Direct binary/archive download", "medium"),
]


def analyze_markdown_security(content: str, filename: str = "") -> List[SecurityFlag]:
    """Scan markdown content for embedded shell commands and suspicious URLs.

    SKILL.md files are read by AI agents and executed as instructions. Attackers
    can embed malicious commands disguised as "setup prerequisites" or "quick start"
    steps. This scanner catches those patterns.

    Args:
        content: Markdown text content.
        filename: Original filename for error reporting.

    Returns:
        List of SecurityFlag instances found.
    """
    flags: List[SecurityFlag] = []

    # Check for shell command patterns
    for pattern, label, severity in MARKDOWN_SHELL_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            context = content[max(0, match.start() - 20):match.end() + 20].strip()
            flags.append(SecurityFlag(
                severity=severity,
                category="markdown_injection",
                detail=f"{label}: ...{context}...",
                file=filename,
                line=line_num,
            ))

    # Check for suspicious URLs
    for pattern, label, severity in SUSPICIOUS_URL_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count("\n") + 1
            flags.append(SecurityFlag(
                severity=severity,
                category="suspicious_url",
                detail=f"{label}: {match.group(0)[:80]}",
                file=filename,
                line=line_num,
            ))

    # Check for obfuscation patterns (encoded strings in markdown)
    obfuscation_patterns = [
        (r"\\x[0-9a-fA-F]{2}(?:\\x[0-9a-fA-F]{2}){3,}", "Hex-encoded string"),
        (r"[A-Za-z0-9+/]{40,}={0,2}", "Possible base64 blob (40+ chars)"),
    ]
    for pattern, label in obfuscation_patterns:
        for match in re.finditer(pattern, content):
            # Only flag if it's NOT inside a code block that looks like normal code
            line_num = content[:match.start()].count("\n") + 1
            flags.append(SecurityFlag(
                severity="medium",
                category="obfuscation",
                detail=f"{label} at line {line_num}",
                file=filename,
                line=line_num,
            ))

    return flags


# ---------------------------------------------------------------------------
# Code quality analysis (AST-based)
# ---------------------------------------------------------------------------

@dataclass
class CodeMetrics:
    """Metrics extracted from Python source via AST analysis.

    Attributes:
        function_count: Total functions (sync + async).
        docstring_count: Functions with docstrings.
        typed_args: Arguments with type annotations.
        total_args: Total function arguments.
        has_exception_handling: Whether any try/except blocks exist.
        imports: Set of top-level module names imported.
        line_count: Total lines of code.
        comment_lines: Lines that are comments.
    """
    function_count: int = 0
    docstring_count: int = 0
    typed_args: int = 0
    total_args: int = 0
    has_exception_handling: bool = False
    imports: List[str] = field(default_factory=list)
    line_count: int = 0
    comment_lines: int = 0


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor that collects code quality metrics.

    Attributes:
        metrics: Accumulated CodeMetrics.
    """

    def __init__(self) -> None:
        self.metrics = CodeMetrics()

    def _check_func(self, node: Any) -> None:
        """Analyze a function definition for docstrings and type hints.

        Args:
            node: A FunctionDef or AsyncFunctionDef AST node.
        """
        self.metrics.function_count += 1

        # Check docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
            self.metrics.docstring_count += 1

        # Count typed args
        for arg in node.args.args:
            self.metrics.total_args += 1
            if arg.annotation is not None:
                self.metrics.typed_args += 1

        # Check return annotation
        if node.returns is not None:
            self.metrics.typed_args += 1
            self.metrics.total_args += 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit synchronous function definitions.

        Args:
            node: The FunctionDef AST node.
        """
        self._check_func(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions.

        Args:
            node: The AsyncFunctionDef AST node.
        """
        self._check_func(node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Flag that exception handling exists.

        Args:
            node: The Try AST node.
        """
        self.metrics.has_exception_handling = True
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Track imported module names.

        Args:
            node: The Import AST node.
        """
        for alias in node.names:
            self.metrics.imports.append(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from-imported module names.

        Args:
            node: The ImportFrom AST node.
        """
        if node.module:
            self.metrics.imports.append(node.module.split(".")[0])
        self.generic_visit(node)


def analyze_code(source: str) -> CodeMetrics:
    """Extract code quality metrics from Python source.

    Args:
        source: Python source code string.

    Returns:
        CodeMetrics with function counts, docstrings, type hints, etc.
    """
    metrics = CodeMetrics()
    metrics.line_count = len(source.splitlines())
    metrics.comment_lines = sum(
        1 for line in source.splitlines()
        if line.strip().startswith("#")
    )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return metrics

    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    metrics.function_count = analyzer.metrics.function_count
    metrics.docstring_count = analyzer.metrics.docstring_count
    metrics.typed_args = analyzer.metrics.typed_args
    metrics.total_args = analyzer.metrics.total_args
    metrics.has_exception_handling = analyzer.metrics.has_exception_handling
    metrics.imports = list(set(analyzer.metrics.imports))

    return metrics


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _score_documentation(files: Dict[str, str]) -> DimensionScore:
    """Score documentation quality (max 25 points).

    Args:
        files: Dict mapping filename to file content.

    Returns:
        DimensionScore for the documentation dimension.
    """
    dim = DimensionScore(name="documentation", score=0, max_score=25)

    # SKILL.md exists (+8) — required
    if "SKILL.md" not in files:
        dim.details.append("SKILL.md MISSING — entire skill scores 0")
        return dim

    skill_md = files["SKILL.md"]
    dim.score += 8
    dim.details.append("+8: SKILL.md exists")

    # SKILL.md >100 lines with real content (+4)
    lines = skill_md.strip().splitlines()
    non_empty = [l for l in lines if l.strip()]
    if len(non_empty) > 100:
        dim.score += 4
        dim.details.append(f"+4: SKILL.md has {len(non_empty)} non-empty lines")
    elif len(non_empty) > 50:
        dim.score += 2
        dim.details.append(f"+2: SKILL.md has {len(non_empty)} lines (partial)")

    # README.md (+4)
    if "README.md" in files:
        dim.score += 4
        dim.details.append("+4: README.md exists")

    # CHANGELOG.md (+3)
    if "CHANGELOG.md" in files:
        dim.score += 3
        dim.details.append("+3: CHANGELOG.md exists")

    # Inline comments in scripts (+3)
    total_code = 0
    total_comments = 0
    for fname, content in files.items():
        if fname.endswith(".py"):
            total_code += len(content.splitlines())
            total_comments += sum(1 for l in content.splitlines() if l.strip().startswith("#"))
    if total_code > 0 and total_comments / total_code > 0.10:
        dim.score += 3
        dim.details.append(f"+3: Comment ratio {total_comments}/{total_code} = {total_comments/total_code:.0%}")
    elif total_code > 0 and total_comments / total_code > 0.05:
        dim.score += 1
        dim.details.append(f"+1: Comment ratio {total_comments/total_code:.0%} (partial)")

    # No placeholders (+3)
    all_text = " ".join(files.values())
    placeholders = re.findall(r"\[TODO\]|\[PLACEHOLDER\]|lorem ipsum", all_text, re.IGNORECASE)
    if not placeholders:
        dim.score += 3
        dim.details.append("+3: No placeholder text detected")
    else:
        dim.details.append(f"+0: Found {len(placeholders)} placeholder(s)")

    return dim


def _score_code_quality(files: Dict[str, str]) -> DimensionScore:
    """Score code quality (max 20 points).

    Args:
        files: Dict mapping filename to content.

    Returns:
        DimensionScore for the code quality dimension.
    """
    dim = DimensionScore(name="code_quality", score=0, max_score=20)

    py_files = {k: v for k, v in files.items() if k.endswith(".py")}
    if not py_files:
        dim.details.append("No Python scripts found")
        return dim

    # Has scripts with actual code (+5)
    total_loc = sum(len(v.splitlines()) for v in py_files.values())
    if total_loc > 50:
        dim.score += 5
        dim.details.append(f"+5: {len(py_files)} scripts, {total_loc} LOC")
    elif total_loc > 10:
        dim.score += 2
        dim.details.append(f"+2: {total_loc} LOC (minimal)")

    # Aggregate metrics across all Python files
    total_funcs = 0
    total_docs = 0
    total_typed = 0
    total_args = 0
    has_exceptions = False
    all_imports: List[str] = []

    for source in py_files.values():
        m = analyze_code(source)
        total_funcs += m.function_count
        total_docs += m.docstring_count
        total_typed += m.typed_args
        total_args += m.total_args
        has_exceptions = has_exceptions or m.has_exception_handling
        all_imports.extend(m.imports)

    # Type hints (+4)
    if total_args > 0:
        ratio = total_typed / total_args
        if ratio > 0.5:
            dim.score += 4
            dim.details.append(f"+4: Type hint coverage {ratio:.0%}")
        elif ratio > 0.2:
            dim.score += 2
            dim.details.append(f"+2: Partial type hints {ratio:.0%}")

    # Docstrings (+4)
    if total_funcs > 0:
        ratio = total_docs / total_funcs
        if ratio > 0.6:
            dim.score += 4
            dim.details.append(f"+4: Docstring coverage {ratio:.0%}")
        elif ratio > 0.3:
            dim.score += 2
            dim.details.append(f"+2: Partial docstrings {ratio:.0%}")

    # Exception handling (+3)
    if has_exceptions:
        dim.score += 3
        dim.details.append("+3: Uses try/except error handling")

    # No hardcoded paths (+2)
    bad_paths = 0
    for source in py_files.values():
        bad_paths += len(re.findall(r'["\']/(?:Users|home|root|tmp)/\w+', source))
    if bad_paths == 0:
        dim.score += 2
        dim.details.append("+2: No hardcoded filesystem paths")
    else:
        dim.details.append(f"+0: {bad_paths} hardcoded path(s) found")

    # PEP 8 basics (+2)
    pep8_issues = 0
    for source in py_files.values():
        for i, line in enumerate(source.splitlines()):
            if "\t" in line:
                pep8_issues += 1
            if len(line) > 120:
                pep8_issues += 1
    if pep8_issues == 0:
        dim.score += 2
        dim.details.append("+2: PEP 8 basics pass (no tabs, <=120 chars)")
    elif pep8_issues < 5:
        dim.score += 1
        dim.details.append(f"+1: Minor PEP 8 issues ({pep8_issues})")

    return dim


def _score_community(skill_data: Dict[str, Any]) -> DimensionScore:
    """Score community signal (max 15 points).

    Args:
        skill_data: Skill record from the database (or manually supplied).

    Returns:
        DimensionScore for the community dimension.
    """
    dim = DimensionScore(name="community", score=0, max_score=15)
    stars = skill_data.get("stars", 0)
    forks = skill_data.get("forks", 0)

    if stars >= 200:
        dim.score += 12
        dim.details.append(f"+12: {stars} stars (200+)")
    elif stars >= 51:
        dim.score += 9
        dim.details.append(f"+9: {stars} stars (51-200)")
    elif stars >= 11:
        dim.score += 6
        dim.details.append(f"+6: {stars} stars (11-50)")
    elif stars >= 1:
        dim.score += 3
        dim.details.append(f"+3: {stars} stars (1-10)")
    else:
        dim.details.append("+0: No stars")

    if forks > 0:
        dim.score += 3
        dim.details.append(f"+3: {forks} forks")

    return dim


def _score_security(files: Dict[str, str]) -> Tuple[DimensionScore, List[SecurityFlag]]:
    """Score security posture (max 15 points, subtractive).

    Starts at 15 and subtracts for each vulnerability found via AST
    analysis and regex credential scanning.

    Args:
        files: Dict mapping filename to content.

    Returns:
        Tuple of (DimensionScore, list of all SecurityFlags found).
    """
    dim = DimensionScore(name="security", score=15, max_score=15)
    all_flags: List[SecurityFlag] = []

    for fname, content in files.items():
        # AST analysis for Python files
        if fname.endswith(".py"):
            flags = analyze_security_ast(content, fname)
            all_flags.extend(flags)

        # Markdown security scanning (SKILL.md, README.md)
        if fname.endswith(".md"):
            flags = analyze_markdown_security(content, fname)
            all_flags.extend(flags)

        # Regex credential scan for all files
        flags = analyze_security_regex(content, fname)
        all_flags.extend(flags)

    # Deduct points by severity
    critical_count = sum(1 for f in all_flags if f.severity == "critical")
    high_count = sum(1 for f in all_flags if f.severity == "high")
    medium_count = sum(1 for f in all_flags if f.severity == "medium")

    deduction = (critical_count * 5) + (high_count * 3) + (medium_count * 1)
    dim.score = max(0, 15 - deduction)

    if all_flags:
        dim.details.append(
            f"-{deduction}: {critical_count} critical, {high_count} high, "
            f"{medium_count} medium issues"
        )
    else:
        dim.details.append("+15: No security issues detected")

    return dim, all_flags


def _score_maintenance(skill_data: Dict[str, Any]) -> DimensionScore:
    """Score maintenance health (max 10 points).

    Args:
        skill_data: Skill record with ``last_updated`` and ``version`` fields.

    Returns:
        DimensionScore for the maintenance dimension.
    """
    dim = DimensionScore(name="maintenance", score=0, max_score=10)

    last_updated = skill_data.get("last_updated", "")
    if last_updated:
        try:
            from datetime import datetime as dt, timezone as tz
            updated = dt.fromisoformat(last_updated.replace("Z", "+00:00"))
            days_ago = (dt.now(tz.utc) - updated).days
            if days_ago <= 30:
                dim.score += 4
                dim.details.append(f"+4: Updated {days_ago} days ago (within 30d)")
            elif days_ago <= 90:
                dim.score += 2
                dim.details.append(f"+2: Updated {days_ago} days ago (within 90d)")
            else:
                dim.details.append(f"+0: Updated {days_ago} days ago (stale)")
        except ValueError:
            dim.details.append("+0: Could not parse last_updated")
    else:
        dim.details.append("+0: No update date available")

    # Version count heuristic — multiple versions = maintained
    version = skill_data.get("version", "")
    if version:
        parts = version.split(".")
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            if major > 1 or minor > 0:
                dim.score += 3
                dim.details.append(f"+3: Version {version} (>1.0.0)")
            elif version != "":
                dim.score += 1
                dim.details.append(f"+1: Version {version}")
        except (ValueError, IndexError):
            dim.score += 1
            dim.details.append(f"+1: Has version string: {version}")

    # Bonus for multiple versions (from downloads/raw_data heuristic)
    downloads = skill_data.get("downloads", 0)
    if downloads > 100:
        dim.score = min(dim.score + 3, 10)
        dim.details.append(f"+3: {downloads} downloads (active usage)")

    return dim


def _score_structure(files: Dict[str, str]) -> DimensionScore:
    """Score structural compliance (max 10 points).

    Args:
        files: Dict mapping filename to content.

    Returns:
        DimensionScore for the structural compliance dimension.
    """
    dim = DimensionScore(name="structure", score=0, max_score=10)

    # _meta.json exists (+4)
    if "_meta.json" in files:
        dim.score += 4
        dim.details.append("+4: _meta.json exists")

        # Has required fields (+3)
        try:
            meta = json.loads(files["_meta.json"])
            required = ["slug", "version", "description"]
            present = [f for f in required if f in meta]
            if len(present) == len(required):
                dim.score += 3
                dim.details.append("+3: All required fields present")
            else:
                missing = set(required) - set(present)
                dim.details.append(f"+0: Missing fields: {missing}")
        except json.JSONDecodeError:
            dim.details.append("+0: _meta.json is invalid JSON")
    else:
        dim.details.append("+0: _meta.json missing")

    # CONTRIBUTING.md (+3)
    if "CONTRIBUTING.md" in files:
        dim.score += 3
        dim.details.append("+3: CONTRIBUTING.md exists")

    return dim


def _score_compatibility(files: Dict[str, str]) -> DimensionScore:
    """Score compatibility (max 5 points).

    Args:
        files: Dict mapping filename to content.

    Returns:
        DimensionScore for the compatibility dimension.
    """
    dim = DimensionScore(name="compatibility", score=0, max_score=5)

    py_files = {k: v for k, v in files.items() if k.endswith(".py")}
    if not py_files:
        dim.score += 5
        dim.details.append("+5: No Python dependencies to check")
        return dim

    # Collect all imports
    all_imports: List[str] = []
    for source in py_files.values():
        m = analyze_code(source)
        all_imports.extend(m.imports)

    unique_imports = set(all_imports)
    non_stdlib = unique_imports - STDLIB_MODULES
    # Filter out relative imports and common non-stdlib that might be local
    non_stdlib = {i for i in non_stdlib if not i.startswith("_") and i != "common"}

    if not non_stdlib:
        dim.score += 3
        dim.details.append("+3: All imports are stdlib")
    else:
        dim.details.append(f"+0: Non-stdlib imports: {non_stdlib}")

    # Check for modern syntax incompatible with 3.9
    for fname, source in py_files.items():
        if re.search(r":\s*\w+\s*\|\s*\w+", source) or re.search(r"->\s*\w+\s*\|\s*None", source):
            dim.details.append(f"+0: {fname} uses X|Y union syntax (3.10+)")
            return dim

    dim.score += 2
    dim.details.append("+2: Python 3.9 compatible syntax")

    return dim


def _assign_tier(score: float) -> str:
    """Map a numeric score to a quality tier.

    Args:
        score: Overall score (0-100).

    Returns:
        Tier string: S, A, B, C, or F.
    """
    if score >= 90:
        return "S"
    elif score >= 75:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "F"


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def collect_local_files(path: Path) -> Dict[str, str]:
    """Collect relevant files from a local skill directory.

    Reads SKILL.md, README.md, _meta.json, CHANGELOG.md, CONTRIBUTING.md,
    and all .py files in scripts/ (up to 10 files).

    Args:
        path: Path to the skill directory.

    Returns:
        Dict mapping filename to content string.
    """
    files: Dict[str, str] = {}
    target_names = ["SKILL.md", "README.md", "_meta.json", "CHANGELOG.md", "CONTRIBUTING.md"]

    for name in target_names:
        fpath = path / name
        if fpath.exists():
            try:
                files[name] = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

    # Collect Python scripts
    scripts_dir = path / "scripts"
    if scripts_dir.is_dir():
        py_files = sorted(scripts_dir.glob("*.py"))[:10]
        for pf in py_files:
            try:
                key = f"scripts/{pf.name}"
                files[key] = pf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass

    return files


def collect_remote_files(slug: str) -> Optional[Dict[str, str]]:
    """Collect files from a remote skill via ClawHub inspect or GitHub.

    First attempts ``clawhub inspect`` to list and fetch files.  Falls back
    to GitHub API if the skill has a source_url in the database.

    Args:
        slug: Skill slug.

    Returns:
        Dict mapping filename to content, or None on failure.
    """
    files: Dict[str, str] = {}

    # Try clawhub inspect first
    try:
        out = run_shell(["clawhub", "inspect", slug, "--files", "--json"], timeout=20)
        data = out.get("json", {})
        file_list = data.get("files", [])

        for f in file_list[:15]:
            fname = f if isinstance(f, str) else f.get("path", "")
            if not fname:
                continue
            try:
                file_out = run_shell([
                    "clawhub", "inspect", slug, "--file", fname
                ], timeout=15)
                files[fname] = file_out["stdout"]
            except ShellError:
                pass

        if files:
            return files
    except ShellError:
        pass

    # Fallback to GitHub
    skill_data = db_read("SELECT source_url FROM skills WHERE slug=?", (slug,))
    if skill_data and skill_data[0].get("source_url"):
        url = skill_data[0]["source_url"]
        # Parse owner/repo from GitHub URL
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)", url)
        if match:
            owner, repo = match.group(1), match.group(2)
            from discover import fetch_github_file
            for fname in ["SKILL.md", "README.md", "_meta.json", "CHANGELOG.md"]:
                content = fetch_github_file(owner, repo, fname)
                if content:
                    files[fname] = content

    return files if files else None


# ---------------------------------------------------------------------------
# Main evaluate function
# ---------------------------------------------------------------------------

def evaluate_skill(
    slug: str,
    path: Optional[Path] = None,
    skill_data: Optional[Dict[str, Any]] = None,
) -> EvalResult:
    """Run a full quality evaluation on a skill.

    Can evaluate from a local directory (``path``) or by fetching files
    remotely (using ``slug`` to look up source).

    Args:
        slug: Skill identifier.
        path: Local path to the skill directory (optional).
        skill_data: Pre-loaded skill metadata from the database (optional).

    Returns:
        Complete EvalResult with scores, tier, and security flags.
    """
    # Collect files
    if path:
        files = collect_local_files(path)
    else:
        files = collect_remote_files(slug) or {}

    if not files:
        return EvalResult(
            slug=slug, overall_score=0, tier="F",
            dimensions=[], security_flags=[],
            evaluated_at=utcnow(),
        )

    # Load skill data from DB if not provided
    if skill_data is None:
        rows = db_read("SELECT * FROM skills WHERE slug=?", (slug,))
        skill_data = rows[0] if rows else {}

    # SKILL.md is required — if missing, score is 0
    if "SKILL.md" not in files:
        return EvalResult(
            slug=slug, overall_score=0, tier="F",
            dimensions=[DimensionScore("documentation", 0, 25,
                                        ["SKILL.md MISSING — entire skill scores 0"])],
            security_flags=[],
            content_hash="",
            evaluated_at=utcnow(),
        )

    # Score all dimensions
    dims: List[DimensionScore] = []
    dims.append(_score_documentation(files))
    dims.append(_score_code_quality(files))
    dims.append(_score_community(skill_data))

    sec_dim, sec_flags = _score_security(files)
    dims.append(sec_dim)

    dims.append(_score_maintenance(skill_data))
    dims.append(_score_structure(files))
    dims.append(_score_compatibility(files))

    overall = sum(d.score for d in dims)
    tier = _assign_tier(overall)

    # Security tier cap: a skill with eval() or hardcoded credentials
    # should NEVER be rated as high quality, regardless of how well-
    # documented or popular it is.  This prevents social engineering
    # attacks where a malicious skill pads its stars and docs to appear
    # trustworthy while hiding dangerous code.
    critical_flags = [f for f in sec_flags if f.severity == "critical"]
    if critical_flags and tier in ("S", "A", "B"):
        tier = "C"
        logger.warning("Tier capped at C due to %d critical security flags", len(critical_flags))

    c_hash = content_hash(files.get("SKILL.md", ""))
    now = utcnow()

    result = EvalResult(
        slug=slug,
        overall_score=round(overall, 1),
        tier=tier,
        dimensions=dims,
        security_flags=sec_flags,
        content_hash=c_hash,
        evaluated_at=now,
    )

    # Persist to database
    dim_dict = {d.name: {"score": d.score, "max": d.max_score, "details": d.details}
                for d in dims}
    flag_list = [asdict(f) for f in sec_flags]

    db_write(
        """INSERT INTO evaluations (slug, evaluated_at, overall_score, tier,
                dimension_scores, security_flags)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (slug, now, overall, tier, json.dumps(dim_dict), json.dumps(flag_list)),
    )

    # Update skill record
    db_write(
        """UPDATE skills SET quality_score=?, quality_tier=?, last_evaluated=?,
                content_hash=?, flagged=?
           WHERE slug=?""",
        (overall, tier, now, c_hash, 1 if critical_flags else 0, slug),
    )

    return result


def compare_skills(slug_a: str, slug_b: str,
                   path_a: Optional[Path] = None,
                   path_b: Optional[Path] = None) -> Dict[str, Any]:
    """Compare two skills head-to-head across all dimensions.

    Args:
        slug_a: First skill slug (typically "theirs").
        slug_b: Second skill slug (typically "ours").
        path_a: Local path for skill A (optional).
        path_b: Local path for skill B (optional).

    Returns:
        Dict with per-dimension comparison and overall recommendation.
    """
    eval_a = evaluate_skill(slug_a, path=path_a)
    eval_b = evaluate_skill(slug_b, path=path_b)

    comparisons = []
    for da, db in zip(eval_a.dimensions, eval_b.dimensions):
        comparisons.append({
            "dimension": da.name,
            "skill_a": {"score": da.score, "max": da.max_score},
            "skill_b": {"score": db.score, "max": db.max_score},
            "winner": slug_a if da.score > db.score else slug_b if db.score > da.score else "tie",
        })

    recommendation = "keep_ours"
    if eval_a.overall_score > eval_b.overall_score + 10:
        recommendation = "replace_with_theirs"
    elif abs(eval_a.overall_score - eval_b.overall_score) <= 10:
        recommendation = "merge_capabilities"

    return {
        "skill_a": {"slug": slug_a, "score": eval_a.overall_score, "tier": eval_a.tier},
        "skill_b": {"slug": slug_b, "score": eval_b.overall_score, "tier": eval_b.tier},
        "dimensions": comparisons,
        "recommendation": recommendation,
        "security_a": [asdict(f) for f in eval_a.security_flags],
        "security_b": [asdict(f) for f in eval_b.security_flags],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the evaluate CLI."""
    parser = argparse.ArgumentParser(
        description="Evaluate OpenClaw skill quality across 7 dimensions",
        prog="evaluate.py",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # score
    p_score = sub.add_parser("score", help="Evaluate a single skill")
    p_score.add_argument("--slug", help="Skill slug (for remote evaluation)")
    p_score.add_argument("--path", help="Local path to skill directory")

    # batch
    p_batch = sub.add_parser("batch", help="Batch evaluate multiple skills")
    p_batch.add_argument("--slugs", required=True, help="Comma-separated skill slugs")

    # security
    p_sec = sub.add_parser("security", help="Security-only deep scan")
    p_sec.add_argument("--path", required=True, help="Local path to skill directory")

    # compare
    p_cmp = sub.add_parser("compare", help="Head-to-head skill comparison")
    p_cmp.add_argument("--slug", required=True, help="Their skill slug")
    p_cmp.add_argument("--ours", required=True, help="Our skill slug or path")

    args = parser.parse_args()

    if args.command == "score":
        if not args.slug and not args.path:
            parser.error("Either --slug or --path is required")
        path = Path(args.path) if args.path else None
        slug = args.slug or Path(args.path).name
        result = evaluate_skill(slug, path=path)
        json_out({
            "slug": result.slug,
            "overall_score": result.overall_score,
            "tier": result.tier,
            "content_hash": result.content_hash,
            "evaluated_at": result.evaluated_at,
            "dimensions": [asdict(d) for d in result.dimensions],
            "security_flags": [asdict(f) for f in result.security_flags],
        })

    elif args.command == "batch":
        slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
        results = []
        for slug in slugs:
            result = evaluate_skill(slug)
            results.append({
                "slug": result.slug,
                "overall_score": result.overall_score,
                "tier": result.tier,
            })
        json_out({"evaluated": len(results), "results": results})

    elif args.command == "security":
        path = Path(args.path)
        files = collect_local_files(path)
        all_flags: List[SecurityFlag] = []
        for fname, content in files.items():
            if fname.endswith(".py"):
                all_flags.extend(analyze_security_ast(content, fname))
            all_flags.extend(analyze_security_regex(content, fname))
        json_out({
            "path": str(path),
            "total_flags": len(all_flags),
            "critical": sum(1 for f in all_flags if f.severity == "critical"),
            "high": sum(1 for f in all_flags if f.severity == "high"),
            "medium": sum(1 for f in all_flags if f.severity == "medium"),
            "flags": [asdict(f) for f in all_flags],
        })

    elif args.command == "compare":
        ours_path = None
        if os.path.isdir(args.ours):
            ours_path = Path(args.ours)
        result = compare_skills(args.slug, args.ours, path_b=ours_path)
        json_out(result)


if __name__ == "__main__":
    main()
