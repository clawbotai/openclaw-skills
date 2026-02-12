#!/usr/bin/env python3
"""
architect_skill.py — Autonomous multi-phase skill builder for OpenClaw.

Takes a single natural-language prompt and produces a complete, validated
OpenClaw skill directory by orchestrating four AI personas:

  Phase 1  Research      → web search + LLM synthesis
  Phase 2  Architecture  → structure selection + SKILL.md + file plan
  Phase 3  Implementation→ scaffold + code generation
  Phase 4  Validation    → quick_validate + self-correction loop

Usage:
    python architect_skill.py --prompt "Build a skill for parsing financial PDFs"

Requires:
    OPENAI_API_KEY environment variable set.
    Dependencies listed in requirements.txt (openai, pydantic, rich, duckduckgo-search).

Python 3.9+ compatible.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.status import Status
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Constants — paths to existing OpenClaw skill-creator tooling
# ---------------------------------------------------------------------------
SKILL_CREATOR_DIR = Path(
    "/opt/homebrew/lib/node_modules/openclaw/skills/skill-creator/scripts"
)
INIT_SKILL_PATH = SKILL_CREATOR_DIR / "init_skill.py"
QUICK_VALIDATE_PATH = SKILL_CREATOR_DIR / "quick_validate.py"
PACKAGE_SKILL_PATH = SKILL_CREATOR_DIR / "package_skill.py"

# ---------------------------------------------------------------------------
# Rich console (shared across all phases)
# ---------------------------------------------------------------------------
console = Console()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("architect_skill")

# =========================================================================
#  SYSTEM PROMPTS — one per AI persona
# =========================================================================

RESEARCHER_SYSTEM_PROMPT: str = textwrap.dedent("""\
    You are a **Senior Technical Researcher** with deep expertise in Python
    ecosystems, open-source libraries, and software design patterns.

    Your job:
    1. Analyse the user's skill idea together with the web-search results
       provided.
    2. Identify the **best real-world Python libraries** that solve the
       problem.  Only cite libraries that actually exist on PyPI — never
       hallucinate package names.
    3. Describe **proven design patterns** relevant to the domain.
    4. Flag **risks and edge cases** (security, performance, compatibility).
    5. Give concrete **recommendations** for building this as an OpenClaw
       skill (a self-contained directory with SKILL.md, scripts/, references/).

    Be concise, factual, and cite real library versions where possible.
""")

ARCHITECT_SYSTEM_PROMPT: str = textwrap.dedent("""\
    You are a **Principal Software Architect** specialising in the OpenClaw
    skill system.

    OpenClaw skills are self-contained directories:
        skill-name/
        ├── SKILL.md          ← YAML frontmatter (name, description) + markdown body
        ├── scripts/          ← Executable Python / Bash helpers
        ├── references/       ← Documentation loaded on demand
        └── assets/           ← Templates, images, config files

    Four canonical architecture types exist:
      • **Workflow-Based** — linear multi-step pipelines (ETL, deploy, CI).
      • **Task-Based**     — independent utility scripts triggered by context.
      • **Reference-Based** — primarily documentation with light scripting.
      • **Capabilities-Based** — wraps an external API/tool surface as skill
                                 capabilities.

    Given the research report you will:
    1. Choose the best architecture type and justify.
    2. Produce a **complete SKILL.md** with real YAML frontmatter and detailed
       markdown instructions — no TODOs or placeholders.
    3. Name the skill in hyphen-case (e.g. ``pdf-parser``).
    4. List every Python script file for ``scripts/`` with filename,
       description, and dependencies.
    5. List reference files for ``references/`` with filename and description.

    Be thorough.  The SKILL.md should be usable as-is by an OpenClaw agent.
""")

DEVELOPER_SYSTEM_PROMPT: str = textwrap.dedent("""\
    You are a **Senior Python Developer** writing production code for an
    OpenClaw skill script.

    Rules:
    • Python 3.9+ — use ``from __future__ import annotations`` and
      ``typing.Optional[X]`` (never ``X | None``).
    • Every public function has a Google-style docstring.
    • All parameters and return types are type-hinted.
    • Graceful error handling — never let an unhandled exception crash
      silently; use ``try/except`` with informative messages.
    • Include a ``if __name__ == "__main__":`` block with ``argparse``
      when the script is meant to be invoked directly.
    • Use ``logging`` instead of bare ``print`` for diagnostics.
    • Keep imports at the top; group stdlib → third-party → local.
    • Write heavily commented code explaining *why*, not just *what*.

    You will receive a file specification (name, description, dependencies)
    and must return the **complete file contents** ready to write to disk.
""")

REVIEWER_SYSTEM_PROMPT: str = textwrap.dedent("""\
    You are a **Code Reviewer and Fixer** for OpenClaw skills.

    You will be given:
      1. The validation error output from ``quick_validate.py``.
      2. The current content of the file(s) that caused the failure.

    Your job:
      • Diagnose the root cause.
      • Return the **fixed file content** that will pass validation.
      • Explain the fix briefly.

    Common issues:
      • Missing or malformed YAML frontmatter in SKILL.md (must have ``name``
        and ``description`` keys inside ``---`` fences).
      • Missing required directories.
      • Syntax errors in Python scripts.

    Return only the corrected content — do not add commentary outside the
    structured output.
""")

# =========================================================================
#  PYDANTIC MODELS — structured output schemas
# =========================================================================


class LibraryInfo(BaseModel):
    """A single recommended Python library."""
    name: str = Field(description="PyPI package name")
    version_hint: str = Field(default="", description="Recommended version constraint, e.g. '>=2.0'")
    purpose: str = Field(description="What this library does for the skill")


class ResearchReport(BaseModel):
    """Phase 1 output: synthesised research results."""
    summary: str = Field(description="One-paragraph summary of research findings")
    libraries: List[LibraryInfo] = Field(default_factory=list, description="Recommended Python libraries")
    patterns: List[str] = Field(default_factory=list, description="Relevant design patterns")
    risks: List[str] = Field(default_factory=list, description="Risks and edge cases")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")


class ScriptFileSpec(BaseModel):
    """Specification for a single script file to generate."""
    filename: str = Field(description="Filename including .py extension")
    description: str = Field(description="What this script does")
    dependencies: List[str] = Field(default_factory=list, description="PyPI packages required")


class ReferenceFileSpec(BaseModel):
    """Specification for a reference/documentation file."""
    filename: str = Field(description="Filename including extension (e.g. .md)")
    description: str = Field(description="What this reference covers")


class ArchitecturePlan(BaseModel):
    """Phase 2 output: full architecture plan for the skill."""
    skill_name: str = Field(description="Skill name in hyphen-case")
    architecture_type: str = Field(description="One of: Workflow-Based, Task-Based, Reference-Based, Capabilities-Based")
    architecture_rationale: str = Field(description="Why this architecture was chosen")
    skill_md_content: str = Field(description="Complete SKILL.md file content including YAML frontmatter")
    script_files: List[ScriptFileSpec] = Field(default_factory=list, description="Python files for scripts/")
    reference_files: List[ReferenceFileSpec] = Field(default_factory=list, description="Files for references/")


class GeneratedCode(BaseModel):
    """Phase 3 output (per file): generated source code."""
    file_path: str = Field(description="Relative path inside the skill directory, e.g. scripts/parse.py")
    code_content: str = Field(description="Complete file content")
    dependencies: List[str] = Field(default_factory=list, description="PyPI packages used by this file")


class ValidationFix(BaseModel):
    """Phase 4 output: a corrected file."""
    file_path: str = Field(description="Relative path of the fixed file inside the skill")
    fixed_content: str = Field(description="Corrected file content")
    explanation: str = Field(description="Brief explanation of what was fixed")


# =========================================================================
#  HELPER: resilient OpenAI API call with retries
# =========================================================================

def _call_openai(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_message: str,
    response_model: type,
    max_retries: int = 3,
    verbose: bool = False,
) -> Any:
    """Call the OpenAI chat-completions API with structured output (Pydantic).

    Retries on rate-limit and timeout errors with exponential back-off.

    Args:
        client: Initialised OpenAI client.
        model: Model identifier (e.g. ``gpt-4o``).
        system_prompt: System message content.
        user_message: User message content.
        response_model: Pydantic model class for ``response_format``.
        max_retries: Maximum retry attempts for transient errors.
        verbose: If True, log raw payloads.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        RuntimeError: After exhausting retries or on non-retriable errors.
    """
    # Build the JSON schema wrapper expected by OpenAI structured outputs.
    # The beta helper ``client.beta.chat.completions.parse`` handles this
    # automatically in openai>=1.40, but we keep manual support for wider
    # SDK compatibility.
    attempt = 0
    last_error: Optional[Exception] = None

    while attempt < max_retries:
        attempt += 1
        try:
            if verbose:
                logger.debug("OpenAI request attempt %d/%d  model=%s", attempt, max_retries, model)

            # Use the beta parse helper which natively accepts Pydantic models
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format=response_model,
            )

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                # Model refused or returned unparseable output
                refusal = getattr(completion.choices[0].message, "refusal", None)
                raise RuntimeError(
                    f"Model returned no structured output. Refusal: {refusal}"
                )
            return parsed

        except (RateLimitError, APITimeoutError) as exc:
            last_error = exc
            wait = 2 ** attempt
            logger.warning("Retriable API error (%s). Waiting %ds before retry…", type(exc).__name__, wait)
            time.sleep(wait)

        except APIError as exc:
            # Non-retriable API errors (auth, bad request, etc.)
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

        except Exception as exc:
            # Unexpected errors — still retry once in case of transient blip
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(1)

    raise RuntimeError(
        f"OpenAI call failed after {max_retries} attempts. Last error: {last_error}"
    )


# =========================================================================
#  PHASE 1 — Research
# =========================================================================

def phase_research(
    client: OpenAI,
    model: str,
    prompt: str,
    max_retries: int = 3,
    verbose: bool = False,
) -> ResearchReport:
    """Phase 1: search the web and synthesise a research report.

    Uses DuckDuckGo to gather context, then passes everything to the
    researcher persona.

    Args:
        client: OpenAI client.
        model: Model name.
        prompt: User's skill idea.
        max_retries: Retries for API calls.
        verbose: Extra logging.

    Returns:
        A ``ResearchReport`` with libraries, patterns, risks, recommendations.
    """
    console.print()
    console.print(Panel("[bold cyan]Phase 1 · Research[/bold cyan]", subtitle="Senior Researcher", border_style="cyan"))

    # --- Web search via DuckDuckGo -----------------------------------------
    search_results_text = ""
    try:
        from duckduckgo_search import DDGS

        with Status("[cyan]Searching the web…[/cyan]", console=console, spinner="dots"):
            ddgs = DDGS()
            # Build two queries: one broad, one Python-specific
            queries = [
                prompt,
                f"Python libraries for {prompt}",
            ]
            all_results: List[Dict[str, Any]] = []
            for query in queries:
                try:
                    results = ddgs.text(query, max_results=5)
                    all_results.extend(results)
                except Exception as search_exc:
                    logger.warning("Search query failed (%s): %s", query, search_exc)

            if all_results:
                snippets = []
                for i, r in enumerate(all_results, 1):
                    title = r.get("title", "")
                    body = r.get("body", r.get("snippet", ""))
                    href = r.get("href", r.get("link", ""))
                    snippets.append(f"{i}. [{title}]({href})\n   {body}")
                search_results_text = "\n\n".join(snippets)
            else:
                search_results_text = "(no web results returned)"

        console.print(f"  [dim]Collected {len(all_results)} search results[/dim]")

    except ImportError:
        console.print("  [yellow]⚠ duckduckgo-search not installed — skipping web search[/yellow]")
        search_results_text = "(web search unavailable — library not installed)"
    except Exception as exc:
        console.print(f"  [yellow]⚠ Web search error: {exc}[/yellow]")
        search_results_text = f"(web search error: {exc})"

    # --- LLM synthesis -----------------------------------------------------
    user_message = (
        f"## User's Skill Idea\n\n{prompt}\n\n"
        f"## Web Search Results\n\n{search_results_text}\n\n"
        "Produce a structured research report covering libraries, patterns, "
        "risks, and recommendations for building this as an OpenClaw skill."
    )

    with Status("[cyan]Synthesising research report…[/cyan]", console=console, spinner="dots"):
        report: ResearchReport = _call_openai(
            client=client,
            model=model,
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            user_message=user_message,
            response_model=ResearchReport,
            max_retries=max_retries,
            verbose=verbose,
        )

    # Display summary
    console.print(f"  [green]✓[/green] Research complete — {len(report.libraries)} libraries, "
                  f"{len(report.patterns)} patterns, {len(report.risks)} risks identified")
    if verbose:
        console.print(Panel(report.summary, title="Research Summary", border_style="dim"))

    return report


# =========================================================================
#  PHASE 2 — Architecture
# =========================================================================

def phase_architecture(
    client: OpenAI,
    model: str,
    prompt: str,
    research: ResearchReport,
    max_retries: int = 3,
    verbose: bool = False,
) -> ArchitecturePlan:
    """Phase 2: design the skill architecture.

    Uses the principal-architect persona to choose a skill structure and
    produce a full SKILL.md plus file manifest.

    Args:
        client: OpenAI client.
        model: Model name.
        prompt: Original user prompt.
        research: Phase 1 output.
        max_retries: Retries for API calls.
        verbose: Extra logging.

    Returns:
        An ``ArchitecturePlan`` with skill name, SKILL.md, and file lists.
    """
    console.print()
    console.print(Panel("[bold magenta]Phase 2 · Architecture[/bold magenta]", subtitle="Principal Architect", border_style="magenta"))

    # Serialise research into a readable block
    research_block = (
        f"## Research Report\n\n"
        f"**Summary:** {research.summary}\n\n"
        f"### Libraries\n"
        + "\n".join(f"- **{lib.name}** ({lib.version_hint}): {lib.purpose}" for lib in research.libraries)
        + f"\n\n### Patterns\n"
        + "\n".join(f"- {p}" for p in research.patterns)
        + f"\n\n### Risks\n"
        + "\n".join(f"- {r}" for r in research.risks)
        + f"\n\n### Recommendations\n"
        + "\n".join(f"- {r}" for r in research.recommendations)
    )

    user_message = (
        f"## Original Prompt\n\n{prompt}\n\n"
        f"{research_block}\n\n"
        "Design the complete OpenClaw skill. Choose the best architecture type, "
        "produce a full SKILL.md (with YAML frontmatter containing `name` and "
        "`description`), and list all script and reference files needed."
    )

    with Status("[magenta]Designing architecture…[/magenta]", console=console, spinner="dots"):
        plan: ArchitecturePlan = _call_openai(
            client=client,
            model=model,
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            user_message=user_message,
            response_model=ArchitecturePlan,
            max_retries=max_retries,
            verbose=verbose,
        )

    console.print(f"  [green]✓[/green] Skill: [bold]{plan.skill_name}[/bold]  "
                  f"Architecture: [bold]{plan.architecture_type}[/bold]")
    console.print(f"  [dim]{plan.architecture_rationale}[/dim]")
    console.print(f"  Scripts: {len(plan.script_files)}  |  References: {len(plan.reference_files)}")

    return plan


# =========================================================================
#  PHASE 3 — Implementation
# =========================================================================

def _scaffold_skill(skill_name: str, output_path: Path) -> Path:
    """Run init_skill.py to create the directory skeleton.

    Falls back to manual creation if the tool is unavailable.

    Args:
        skill_name: Hyphen-case skill name.
        output_path: Parent directory where the skill folder is created.

    Returns:
        Path to the created skill directory.
    """
    skill_dir = output_path / skill_name
    
    if INIT_SKILL_PATH.exists():
        # Use the official scaffold tool
        cmd = [
            sys.executable,
            str(INIT_SKILL_PATH),
            "--name", skill_name,
            "--output", str(output_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                console.print(f"  [green]✓[/green] Scaffolded via init_skill.py")
                return skill_dir
            else:
                logger.warning("init_skill.py failed (rc=%d): %s", result.returncode, result.stderr)
        except Exception as exc:
            logger.warning("init_skill.py invocation error: %s", exc)

    # Fallback: create the directory structure manually
    console.print("  [yellow]⚠ init_skill.py unavailable — creating structure manually[/yellow]")
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "assets").mkdir(exist_ok=True)

    # Write a minimal placeholder SKILL.md (will be overwritten immediately)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: placeholder\n---\n\n# {skill_name}\n",
        encoding="utf-8",
    )
    console.print(f"  [green]✓[/green] Skill directory created at [bold]{skill_dir}[/bold]")
    return skill_dir


def phase_implementation(
    client: OpenAI,
    model: str,
    prompt: str,
    plan: ArchitecturePlan,
    output_path: Path,
    max_retries: int = 3,
    verbose: bool = False,
) -> Path:
    """Phase 3: scaffold the skill and generate all code.

    Creates the directory, writes SKILL.md, generates each script via LLM,
    writes reference stubs, and aggregates dependencies into requirements.txt.

    Args:
        client: OpenAI client.
        model: Model name.
        prompt: Original user prompt.
        plan: Phase 2 output.
        output_path: Parent directory for the skill.
        max_retries: Retries for API calls.
        verbose: Extra logging.

    Returns:
        Path to the completed skill directory.
    """
    console.print()
    console.print(Panel("[bold green]Phase 3 · Implementation[/bold green]", subtitle="Senior Developer", border_style="green"))

    # --- Step 1: scaffold --------------------------------------------------
    skill_dir = _scaffold_skill(plan.skill_name, output_path)

    # --- Step 2: write SKILL.md --------------------------------------------
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(plan.skill_md_content, encoding="utf-8")
    console.print(f"  [green]✓[/green] SKILL.md written ({len(plan.skill_md_content)} chars)")

    # --- Step 3: generate each script file ---------------------------------
    all_dependencies: List[str] = []
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    for i, spec in enumerate(plan.script_files, 1):
        file_label = f"[{i}/{len(plan.script_files)}] {spec.filename}"
        with Status(f"[green]Generating {file_label}…[/green]", console=console, spinner="dots"):
            user_message = (
                f"## Skill Context\n\n"
                f"Skill name: {plan.skill_name}\n"
                f"Architecture: {plan.architecture_type}\n"
                f"User prompt: {prompt}\n\n"
                f"## File Specification\n\n"
                f"Filename: {spec.filename}\n"
                f"Description: {spec.description}\n"
                f"Dependencies available: {', '.join(spec.dependencies) if spec.dependencies else 'stdlib only'}\n\n"
                f"## SKILL.md (for context)\n\n"
                f"```markdown\n{plan.skill_md_content}\n```\n\n"
                f"Write the complete Python file. It must be fully functional, "
                f"type-hinted, documented, and ready for production use."
            )

            generated: GeneratedCode = _call_openai(
                client=client,
                model=model,
                system_prompt=DEVELOPER_SYSTEM_PROMPT,
                user_message=user_message,
                response_model=GeneratedCode,
                max_retries=max_retries,
                verbose=verbose,
            )

        # Write the file
        target_path = scripts_dir / spec.filename
        target_path.write_text(generated.code_content, encoding="utf-8")
        # Make scripts executable
        target_path.chmod(0o755)

        all_dependencies.extend(generated.dependencies)
        console.print(f"  [green]✓[/green] {file_label} ({len(generated.code_content)} chars, "
                      f"{len(generated.dependencies)} deps)")

    # --- Step 4: generate reference files ----------------------------------
    references_dir = skill_dir / "references"
    references_dir.mkdir(exist_ok=True)

    for i, ref in enumerate(plan.reference_files, 1):
        ref_path = references_dir / ref.filename
        # Reference files are documentation — create with description as content.
        # For .md files we generate a structured stub.
        content = f"# {ref.filename}\n\n{ref.description}\n"
        ref_path.write_text(content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Reference: {ref.filename}")

    # --- Step 5: aggregate requirements.txt --------------------------------
    # Deduplicate while preserving order
    seen: set = set()
    unique_deps: List[str] = []
    for dep in all_dependencies:
        dep_normalised = dep.strip().lower().split(">=")[0].split("==")[0].split("<")[0].split("[")[0]
        if dep_normalised and dep_normalised not in seen:
            seen.add(dep_normalised)
            unique_deps.append(dep.strip())

    if unique_deps:
        req_path = skill_dir / "requirements.txt"
        req_path.write_text("\n".join(unique_deps) + "\n", encoding="utf-8")
        console.print(f"  [green]✓[/green] requirements.txt ({len(unique_deps)} packages)")

    return skill_dir


# =========================================================================
#  PHASE 4 — Validation & Self-Correction
# =========================================================================

def _run_validation(skill_dir: Path) -> subprocess.CompletedProcess:
    """Run quick_validate.py against the skill directory.

    Args:
        skill_dir: Path to the skill directory.

    Returns:
        CompletedProcess with stdout/stderr captured.
    """
    if not QUICK_VALIDATE_PATH.exists():
        # Fallback: perform a minimal sanity check ourselves
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="SKILL.md is missing.",
            )
        content = skill_md.read_text(encoding="utf-8")
        # Check for YAML frontmatter
        if not content.startswith("---"):
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="SKILL.md must start with YAML frontmatter (--- fence).",
            )
        # Check for name and description in frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="SKILL.md YAML frontmatter is malformed (missing closing ---).",
            )
        frontmatter = parts[1]
        if "name:" not in frontmatter:
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="SKILL.md frontmatter missing 'name' field.",
            )
        if "description:" not in frontmatter:
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="SKILL.md frontmatter missing 'description' field.",
            )
        # Check scripts directory exists
        if not (skill_dir / "scripts").is_dir():
            return subprocess.CompletedProcess(
                args=["fallback-validate"],
                returncode=1,
                stdout="",
                stderr="scripts/ directory is missing.",
            )
        # Basic Python syntax check on all .py files
        for py_file in (skill_dir / "scripts").glob("*.py"):
            try:
                compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")
            except SyntaxError as syn_err:
                return subprocess.CompletedProcess(
                    args=["fallback-validate"],
                    returncode=1,
                    stdout="",
                    stderr=f"Syntax error in {py_file.name}: {syn_err}",
                )
        return subprocess.CompletedProcess(
            args=["fallback-validate"],
            returncode=0,
            stdout="Validation passed (fallback checker).",
            stderr="",
        )

    # Use the official validator
    cmd = [sys.executable, str(QUICK_VALIDATE_PATH), str(skill_dir)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def phase_validation(
    client: OpenAI,
    model: str,
    skill_dir: Path,
    max_retries: int = 3,
    verbose: bool = False,
) -> bool:
    """Phase 4: validate the skill and self-correct on failure.

    Runs validation, and if it fails, asks the reviewer persona to fix
    the problematic files.  Retries up to ``max_retries`` times.

    Args:
        client: OpenAI client.
        model: Model name.
        skill_dir: Path to the generated skill directory.
        max_retries: Maximum fix-and-retry cycles.
        verbose: Extra logging.

    Returns:
        True if validation passes, False if all retries exhausted.
    """
    console.print()
    console.print(Panel("[bold yellow]Phase 4 · Validation[/bold yellow]", subtitle="Code Reviewer", border_style="yellow"))

    for attempt in range(1, max_retries + 1):
        with Status(f"[yellow]Running validation (attempt {attempt}/{max_retries})…[/yellow]",
                     console=console, spinner="dots"):
            try:
                result = _run_validation(skill_dir)
            except subprocess.TimeoutExpired:
                console.print(f"  [red]✗ Validation timed out (attempt {attempt})[/red]")
                continue
            except Exception as exc:
                console.print(f"  [red]✗ Validation error: {exc}[/red]")
                continue

        if result.returncode == 0:
            console.print(f"  [green]✓ Validation passed![/green]")
            return True

        # Validation failed — extract the error
        error_output = (result.stderr or result.stdout or "Unknown validation error").strip()
        console.print(f"  [red]✗ Validation failed (attempt {attempt}): {error_output}[/red]")

        if attempt >= max_retries:
            break

        # --- Self-correction via reviewer persona -------------------------
        # Read the files that might need fixing
        skill_md_content = ""
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md_content = skill_md_path.read_text(encoding="utf-8")

        # Gather script contents for context
        script_contents: Dict[str, str] = {}
        scripts_path = skill_dir / "scripts"
        if scripts_path.is_dir():
            for py_file in scripts_path.glob("*.py"):
                script_contents[f"scripts/{py_file.name}"] = py_file.read_text(encoding="utf-8")

        files_context = f"### SKILL.md\n```\n{skill_md_content}\n```\n\n"
        for fpath, fcontent in script_contents.items():
            files_context += f"### {fpath}\n```python\n{fcontent}\n```\n\n"

        user_message = (
            f"## Validation Error\n\n```\n{error_output}\n```\n\n"
            f"## Current Skill Files\n\n{files_context}\n"
            "Fix the file that caused the validation error. Return the corrected content."
        )

        with Status("[yellow]Requesting fix from reviewer…[/yellow]", console=console, spinner="dots"):
            try:
                fix: ValidationFix = _call_openai(
                    client=client,
                    model=model,
                    system_prompt=REVIEWER_SYSTEM_PROMPT,
                    user_message=user_message,
                    response_model=ValidationFix,
                    max_retries=max_retries,
                    verbose=verbose,
                )
            except RuntimeError as exc:
                console.print(f"  [red]✗ Reviewer LLM call failed: {exc}[/red]")
                continue

        # Apply the fix
        fix_target = skill_dir / fix.file_path
        fix_target.parent.mkdir(parents=True, exist_ok=True)
        fix_target.write_text(fix.fixed_content, encoding="utf-8")
        console.print(f"  [yellow]⟳ Applied fix to {fix.file_path}: {fix.explanation}[/yellow]")

    console.print(Panel(
        "[bold red]Validation failed after all retries.[/bold red]\n"
        "The skill was generated but may have issues. Please review manually.",
        border_style="red",
    ))
    return False


# =========================================================================
#  SUMMARY — final report
# =========================================================================

def _print_summary(
    skill_dir: Path,
    plan: ArchitecturePlan,
    validation_passed: bool,
    elapsed: float,
) -> None:
    """Print a rich summary table of the generated skill.

    Args:
        skill_dir: Path to the skill directory.
        plan: The architecture plan used.
        validation_passed: Whether validation succeeded.
        elapsed: Total wall-clock time in seconds.
    """
    console.print()

    table = Table(title="🏗️  Skill Generation Summary", border_style="bold blue", show_lines=True)
    table.add_column("Property", style="bold", width=20)
    table.add_column("Value", min_width=40)

    table.add_row("Skill Name", plan.skill_name)
    table.add_row("Architecture", plan.architecture_type)
    table.add_row("Location", str(skill_dir))
    table.add_row("Scripts", ", ".join(s.filename for s in plan.script_files) or "(none)")
    table.add_row("References", ", ".join(r.filename for r in plan.reference_files) or "(none)")

    status_text = "[green]✓ PASSED[/green]" if validation_passed else "[red]✗ FAILED[/red]"
    table.add_row("Validation", status_text)
    table.add_row("Time", f"{elapsed:.1f}s")

    console.print(table)

    # List all files
    console.print("\n[bold]Generated files:[/bold]")
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(skill_dir)
            size = path.stat().st_size
            console.print(f"  📄 {rel}  [dim]({size} bytes)[/dim]")
    console.print()


# =========================================================================
#  MAIN PIPELINE
# =========================================================================

def run_pipeline(
    prompt: str,
    output_path: str = "./skills",
    model: str = "gpt-4o",
    max_retries: int = 3,
    verbose: bool = False,
) -> None:
    """Execute the full four-phase skill generation pipeline.

    This is the main entry point for programmatic use.

    Args:
        prompt: Natural-language description of the desired skill.
        output_path: Parent directory where the skill folder will be created.
        model: OpenAI model to use.
        max_retries: Max retries for API calls and validation.
        verbose: Enable verbose logging.

    Raises:
        RuntimeError: On fatal errors (missing API key, etc.).
    """
    start_time = time.time()

    # --- Pre-flight checks -------------------------------------------------
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please export it before running this script."
        )

    output_dir = Path(output_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialise the OpenAI client
    client = OpenAI(api_key=api_key)

    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold white]🧠 OpenClaw Skill Architect[/bold white]\n\n"
        f'[dim]Prompt:[/dim] "{prompt}"\n'
        f"[dim]Model:[/dim] {model}  [dim]Output:[/dim] {output_dir}",
        border_style="bold blue",
    ))

    # --- Phase 1: Research -------------------------------------------------
    research = phase_research(
        client=client,
        model=model,
        prompt=prompt,
        max_retries=max_retries,
        verbose=verbose,
    )

    # --- Phase 2: Architecture ---------------------------------------------
    plan = phase_architecture(
        client=client,
        model=model,
        prompt=prompt,
        research=research,
        max_retries=max_retries,
        verbose=verbose,
    )

    # --- Phase 3: Implementation -------------------------------------------
    skill_dir = phase_implementation(
        client=client,
        model=model,
        prompt=prompt,
        plan=plan,
        output_path=output_dir,
        max_retries=max_retries,
        verbose=verbose,
    )

    # --- Phase 4: Validation -----------------------------------------------
    validation_passed = phase_validation(
        client=client,
        model=model,
        skill_dir=skill_dir,
        max_retries=max_retries,
        verbose=verbose,
    )

    # --- Summary -----------------------------------------------------------
    elapsed = time.time() - start_time
    _print_summary(skill_dir, plan, validation_passed, elapsed)

    if validation_passed:
        console.print("[bold green]✅ Skill generated successfully![/bold green]\n")
    else:
        console.print("[bold yellow]⚠️  Skill generated with validation warnings. Review manually.[/bold yellow]\n")


# =========================================================================
#  CLI ENTRY POINT
# =========================================================================

def main() -> None:
    """Parse CLI arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        prog="architect_skill",
        description="Autonomous multi-phase OpenClaw skill generator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python architect_skill.py --prompt "Build a skill for parsing financial PDFs"
              python architect_skill.py --prompt "Web scraping toolkit" --model gpt-4o-mini --verbose
              python architect_skill.py --prompt "Docker management" --output-path /tmp/skills
        """),
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="Natural-language description of the skill to build.",
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o).",
    )
    parser.add_argument(
        "--output-path", "-o",
        default="./skills",
        help="Parent directory for the generated skill (default: ./skills).",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries for API calls and validation (default: 3).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output.",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        run_pipeline(
            prompt=args.prompt,
            output_path=args.output_path,
            model=args.model,
            max_retries=args.max_retries,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except RuntimeError as exc:
        console.print(Panel(f"[bold red]Fatal error:[/bold red] {exc}", border_style="red"))
        sys.exit(1)
    except Exception as exc:
        console.print(Panel(
            f"[bold red]Unexpected error:[/bold red] {exc}\n\n"
            f"[dim]{traceback.format_exc()}[/dim]",
            border_style="red",
        ))
        sys.exit(1)


if __name__ == "__main__":
    main()
