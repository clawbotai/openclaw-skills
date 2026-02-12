#!/usr/bin/env python3
"""
agent-orchestration / task_templates.py
========================================
Structured task prompt templates for sub-agent spawning.

Each template produces a self-contained prompt string that:
  1. Gives the sub-agent minimal, focused context
  2. Defines the task precisely
  3. Sets constraints (time, scope, don't-touch rules)
  4. Specifies an **Output Interface** — a parseable format
     the parent can extract results from programmatically

Templates use dataclasses for type-safe input validation.
All templates produce plain strings (no LLM API calls).

Design principles (from arXiv 2510.25445, Google ADK, CrewAI):
  - Each sub-agent is a specialist with a single responsibility
  - Context is explicit — sub-agents share NO memory with the parent
  - Output format is contractual — the parent MUST be able to parse it
  - Templates are composable — combine for complex workflows

Usage:
    from task_templates import CodeReviewTemplate, render
    template = CodeReviewTemplate(
        files=["src/main.py", "src/utils.py"],
        focus_areas=["security", "error handling"],
    )
    prompt = render(template)
    # Pass `prompt` to sessions_spawn(task=prompt, ...)

CLI:
    python3 task_templates.py list
    python3 task_templates.py preview code_review --files "a.py,b.py"
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Output interface format constants
# ---------------------------------------------------------------------------

# Sub-agents MUST wrap their final answer in these delimiters.
# The parent uses regex to extract the content between them.
RESULT_OPEN = "<result>"
RESULT_CLOSE = "</result>"

OUTPUT_INTERFACE_BLOCK = textwrap.dedent(f"""\
    ## Output Interface

    When you have completed the task, wrap your ENTIRE final answer
    inside these exact delimiters:

    ```
    {RESULT_OPEN}
    [Your structured output here — use JSON or Markdown as specified above]
    {RESULT_CLOSE}
    ```

    **Rules:**
    - Place the delimiters on their own lines
    - Include ONLY the final deliverable inside the tags
    - Do NOT include commentary, status updates, or tool output inside the tags
    - If the task fails, still use the tags: `{RESULT_OPEN}{{"status": "error", "reason": "..."}}{RESULT_CLOSE}`
""")


# ---------------------------------------------------------------------------
# Template dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CodeReviewTemplate:
    """Template for code review sub-agent tasks.

    The sub-agent reviews specified files for issues in the given
    focus areas and returns structured findings.

    Attributes:
        files: List of file paths to review.
        focus_areas: Aspects to focus on (security, performance, etc.).
        severity_levels: Which severities to report (critical, high, medium, low).
        max_issues: Maximum issues to report (prevents output explosion).
        context: Optional background context about the codebase.
    """
    files: List[str]
    focus_areas: List[str] = field(default_factory=lambda: [
        "bugs", "security", "error handling", "performance",
    ])
    severity_levels: List[str] = field(default_factory=lambda: [
        "critical", "high", "medium",
    ])
    max_issues: int = 20
    context: str = ""


@dataclass
class ResearchTemplate:
    """Template for research sub-agent tasks.

    The sub-agent investigates a topic using web search and produces
    a structured research report with citations.

    Attributes:
        topic: The subject to research.
        depth: Research depth — "shallow" (quick overview), "medium"
               (key findings), "deep" (comprehensive analysis).
        questions: Specific questions to answer.
        output_format: "summary" (prose), "bullets" (key points),
                       "report" (structured with sections).
        max_sources: Maximum sources to cite.
    """
    topic: str
    depth: str = "medium"
    questions: List[str] = field(default_factory=list)
    output_format: str = "report"
    max_sources: int = 10


@dataclass
class DataExtractionTemplate:
    """Template for data extraction sub-agent tasks.

    The sub-agent processes files/content and extracts structured
    data according to a schema.

    Attributes:
        source_paths: Files or directories to process.
        extract_schema: Dict describing desired output fields.
        source_description: What the source data contains.
        output_format: "json", "csv", or "markdown_table".
        filters: Optional extraction filters.
    """
    source_paths: List[str]
    extract_schema: Dict[str, str]
    source_description: str = ""
    output_format: str = "json"
    filters: Optional[Dict[str, str]] = None


@dataclass
class ConsensusCheckTemplate:
    """Template for expert panel / consensus check sub-agent tasks.

    The sub-agent evaluates a proposal from a specific expert
    perspective and provides a structured opinion.

    Attributes:
        proposal: The design/plan/decision to evaluate.
        expert_role: The perspective to take (e.g., "security engineer").
        evaluation_criteria: Specific aspects to assess.
        context: Background information about the project.
        rating_scale: Scale for the overall verdict.
    """
    proposal: str
    expert_role: str
    evaluation_criteria: List[str] = field(default_factory=lambda: [
        "feasibility", "risks", "trade-offs", "alternatives",
    ])
    context: str = ""
    rating_scale: str = "strong_approve / approve / neutral / reject / strong_reject"


@dataclass
class DocumentationTemplate:
    """Template for documentation sub-agent tasks.

    The sub-agent generates or improves documentation for code/projects.

    Attributes:
        target_path: File or directory to document.
        doc_type: Type of docs: "readme", "api_reference", "tutorial",
                  "inline_comments", "changelog".
        style: Documentation style/standard to follow.
        existing_docs: Path to existing docs (for improvement tasks).
        audience: Target audience: "developers", "users", "operators".
    """
    target_path: str
    doc_type: str = "readme"
    style: str = "concise, practical, example-rich"
    existing_docs: Optional[str] = None
    audience: str = "developers"


@dataclass
class TestingTemplate:
    """Template for testing sub-agent tasks.

    The sub-agent writes or runs tests for specified code.

    Attributes:
        code_path: File or directory to test.
        test_framework: Testing framework to use.
        test_types: Types of tests to write/run.
        coverage_target: Minimum coverage percentage goal.
        focus_areas: Specific functionality to prioritize.
    """
    code_path: str
    test_framework: str = "pytest"
    test_types: List[str] = field(default_factory=lambda: [
        "unit", "edge_cases", "error_handling",
    ])
    coverage_target: int = 80
    focus_areas: List[str] = field(default_factory=list)


@dataclass
class RefactorTemplate:
    """Template for refactoring sub-agent tasks.

    Attributes:
        code_path: File or directory to refactor.
        goals: Refactoring objectives.
        constraints: What NOT to change (public API, behavior, etc.).
        patterns: Design patterns to apply if applicable.
    """
    code_path: str
    goals: List[str] = field(default_factory=lambda: ["readability", "maintainability"])
    constraints: List[str] = field(default_factory=lambda: [
        "preserve public API", "preserve existing behavior",
    ])
    patterns: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render(template: Any) -> str:
    """Render any template dataclass into a complete sub-agent prompt.

    Dispatches to the appropriate renderer based on template type.

    Args:
        template: A template dataclass instance.

    Returns:
        Complete prompt string ready for sessions_spawn(task=...).

    Raises:
        ValueError: If the template type is not recognized.
    """
    renderers = {
        CodeReviewTemplate: _render_code_review,
        ResearchTemplate: _render_research,
        DataExtractionTemplate: _render_data_extraction,
        ConsensusCheckTemplate: _render_consensus_check,
        DocumentationTemplate: _render_documentation,
        TestingTemplate: _render_testing,
        RefactorTemplate: _render_refactor,
    }
    renderer = renderers.get(type(template))
    if renderer is None:
        raise ValueError(f"Unknown template type: {type(template).__name__}")
    return renderer(template)


def _render_code_review(t: CodeReviewTemplate) -> str:
    """Render a code review task prompt."""
    files_list = "\n".join(f"- `{f}`" for f in t.files)
    focus = ", ".join(t.focus_areas)
    severities = ", ".join(t.severity_levels)

    context_block = ""
    if t.context:
        context_block = f"\n## Background\n{t.context}\n"

    return textwrap.dedent(f"""\
        ## Role
        You are a Senior Code Reviewer performing a focused review.

        ## Task
        Review the following files for issues related to: {focus}.
        {context_block}
        ## Files to Review
        {files_list}

        ## Constraints
        - Report only {severities} severity issues
        - Maximum {t.max_issues} issues
        - For each issue: file, line (if possible), severity, description, suggested fix
        - Do NOT modify any files — review only

        ## Expected Output Format
        Return a JSON array of findings:
        ```json
        [
          {{
            "file": "path/to/file.py",
            "line": 42,
            "severity": "high",
            "category": "security",
            "description": "SQL injection via string interpolation",
            "suggestion": "Use parameterized queries"
          }}
        ]
        ```
        If no issues found, return: `[]`

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_research(t: ResearchTemplate) -> str:
    """Render a research task prompt."""
    questions_block = ""
    if t.questions:
        q_list = "\n".join(f"- {q}" for q in t.questions)
        questions_block = f"\n## Specific Questions\n{q_list}\n"

    depth_instruction = {
        "shallow": "Quick overview — 2-3 key points, 1-2 sources.",
        "medium": "Balanced analysis — 5-7 key findings, 3-5 sources.",
        "deep": "Comprehensive deep-dive — detailed analysis with 5-10 sources.",
    }.get(t.depth, "Balanced analysis.")

    return textwrap.dedent(f"""\
        ## Role
        You are a Research Analyst conducting focused research.

        ## Task
        Research: **{t.topic}**

        ## Depth
        {depth_instruction}
        {questions_block}
        ## Constraints
        - Use web_search and web_fetch for research
        - Cite sources with URLs
        - Maximum {t.max_sources} sources
        - Focus on recent information (prefer 2025-2026)
        - Distinguish facts from opinions

        ## Expected Output Format ({t.output_format})
        Return a JSON object:
        ```json
        {{
          "topic": "{t.topic}",
          "summary": "2-3 sentence overview",
          "findings": [
            {{
              "point": "Key finding",
              "evidence": "Supporting detail",
              "source": "https://..."
            }}
          ],
          "sources": ["https://...", "https://..."],
          "confidence": "high|medium|low"
        }}
        ```

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_data_extraction(t: DataExtractionTemplate) -> str:
    """Render a data extraction task prompt."""
    paths = "\n".join(f"- `{p}`" for p in t.source_paths)
    schema = json.dumps(t.extract_schema, indent=2)

    desc_block = ""
    if t.source_description:
        desc_block = f"\n## Source Description\n{t.source_description}\n"

    filter_block = ""
    if t.filters:
        filter_block = f"\n## Filters\n```json\n{json.dumps(t.filters, indent=2)}\n```\n"

    return textwrap.dedent(f"""\
        ## Role
        You are a Data Extraction Specialist.

        ## Task
        Extract structured data from the specified sources.
        {desc_block}
        ## Sources
        {paths}

        ## Target Schema
        Extract the following fields:
        ```json
        {schema}
        ```
        {filter_block}
        ## Constraints
        - Read files using the read tool
        - Output format: {t.output_format}
        - Include ALL matching records (do not sample)
        - If a field is missing in the source, use null

        ## Expected Output Format
        Return a JSON array of extracted records matching the schema above.

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_consensus_check(t: ConsensusCheckTemplate) -> str:
    """Render a consensus/expert panel task prompt."""
    criteria = "\n".join(f"- {c}" for c in t.evaluation_criteria)

    context_block = ""
    if t.context:
        context_block = f"\n## Project Context\n{t.context}\n"

    return textwrap.dedent(f"""\
        ## Role
        You are a **{t.expert_role}** providing an expert evaluation.
        {context_block}
        ## Proposal to Evaluate
        {t.proposal}

        ## Evaluation Criteria
        Assess the proposal on:
        {criteria}

        ## Constraints
        - Stay in character as a {t.expert_role}
        - Be specific — cite concrete risks and trade-offs
        - Suggest alternatives where you see issues
        - Rate using: {t.rating_scale}

        ## Expected Output Format
        Return a JSON object:
        ```json
        {{
          "expert_role": "{t.expert_role}",
          "verdict": "approve|reject|neutral",
          "confidence": "high|medium|low",
          "assessment": {{
            "strengths": ["..."],
            "concerns": ["..."],
            "risks": ["..."],
            "alternatives": ["..."]
          }},
          "recommendation": "One paragraph summary"
        }}
        ```

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_documentation(t: DocumentationTemplate) -> str:
    """Render a documentation task prompt."""
    existing = ""
    if t.existing_docs:
        existing = f"\n## Existing Documentation\nReview and improve: `{t.existing_docs}`\n"

    return textwrap.dedent(f"""\
        ## Role
        You are a Technical Writer producing {t.doc_type} documentation.

        ## Task
        Generate {t.doc_type} documentation for: `{t.target_path}`
        {existing}
        ## Style
        {t.style}

        ## Audience
        {t.audience}

        ## Constraints
        - Read the source code/files first
        - Include real examples from the actual code
        - No placeholder text ([TODO], lorem ipsum)
        - Write the documentation to a file at the appropriate location

        ## Expected Output Format
        Return a JSON object:
        ```json
        {{
          "files_written": ["path/to/doc.md"],
          "summary": "What was documented",
          "sections": ["list", "of", "sections"]
        }}
        ```

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_testing(t: TestingTemplate) -> str:
    """Render a testing task prompt."""
    types = ", ".join(t.test_types)
    focus = "\n".join(f"- {f}" for f in t.focus_areas) if t.focus_areas else "All functionality"

    return textwrap.dedent(f"""\
        ## Role
        You are a QA Engineer writing {t.test_framework} tests.

        ## Task
        Write tests for: `{t.code_path}`

        ## Test Types
        {types}

        ## Focus Areas
        {focus}

        ## Constraints
        - Framework: {t.test_framework}
        - Target coverage: {t.coverage_target}%
        - Write tests to the standard test directory
        - Tests must be runnable: `{t.test_framework} <test_file>`
        - Include edge cases and error conditions

        ## Expected Output Format
        Return a JSON object:
        ```json
        {{
          "test_files": ["tests/test_xxx.py"],
          "test_count": 15,
          "coverage_areas": ["unit", "edge_cases"],
          "run_command": "pytest tests/"
        }}
        ```

        {OUTPUT_INTERFACE_BLOCK}
    """)


def _render_refactor(t: RefactorTemplate) -> str:
    """Render a refactoring task prompt."""
    goals = "\n".join(f"- {g}" for g in t.goals)
    constraints = "\n".join(f"- {c}" for c in t.constraints)
    patterns = "\n".join(f"- {p}" for p in t.patterns) if t.patterns else "Apply as appropriate"

    return textwrap.dedent(f"""\
        ## Role
        You are a Senior Software Engineer performing a targeted refactor.

        ## Task
        Refactor: `{t.code_path}`

        ## Goals
        {goals}

        ## Constraints (DO NOT BREAK)
        {constraints}

        ## Design Patterns
        {patterns}

        ## Process
        1. Read and understand the existing code
        2. Plan the refactor (document what changes)
        3. Apply changes
        4. Verify the code still works (run tests if they exist)

        ## Expected Output Format
        Return a JSON object:
        ```json
        {{
          "files_modified": ["path/to/file.py"],
          "changes": [
            {{"file": "...", "description": "what changed and why"}}
          ],
          "tests_passed": true,
          "summary": "Overview of refactoring"
        }}
        ```

        {OUTPUT_INTERFACE_BLOCK}
    """)


# ---------------------------------------------------------------------------
# Result parser
# ---------------------------------------------------------------------------

def parse_result(announcement: str) -> Optional[str]:
    """Extract the content between <result>...</result> tags.

    Used by the parent agent to parse sub-agent output.

    Args:
        announcement: The full sub-agent announcement text.

    Returns:
        The content between result tags, or None if not found.
    """
    import re
    pattern = re.compile(
        rf"{re.escape(RESULT_OPEN)}\s*(.*?)\s*{re.escape(RESULT_CLOSE)}",
        re.DOTALL,
    )
    match = pattern.search(announcement)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_TEMPLATE_NAMES = {
    "code_review": CodeReviewTemplate,
    "research": ResearchTemplate,
    "data_extraction": DataExtractionTemplate,
    "consensus_check": ConsensusCheckTemplate,
    "documentation": DocumentationTemplate,
    "testing": TestingTemplate,
    "refactor": RefactorTemplate,
}


def main() -> None:
    """CLI entry point for previewing task templates."""
    parser = argparse.ArgumentParser(
        prog="task_templates.py",
        description="Structured task prompt templates for sub-agent spawning.",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    # list
    subs.add_parser("list", help="List available templates")

    # preview
    p_prev = subs.add_parser("preview", help="Preview a rendered template")
    p_prev.add_argument("template", choices=list(_TEMPLATE_NAMES.keys()))
    p_prev.add_argument("--files", default="example.py",
                        help="Comma-separated file list")
    p_prev.add_argument("--topic", default="Example topic")
    p_prev.add_argument("--role", default="security engineer")
    p_prev.add_argument("--proposal", default="Example proposal")

    args = parser.parse_args()

    if args.command == "list":
        templates = []
        for name, cls in _TEMPLATE_NAMES.items():
            doc = cls.__doc__ or ""
            first_line = doc.strip().split("\n")[0] if doc else ""
            templates.append({"name": name, "description": first_line})
        print(json.dumps({"templates": templates}, indent=2))

    elif args.command == "preview":
        cls = _TEMPLATE_NAMES[args.template]
        files = [f.strip() for f in args.files.split(",")]

        # Build a sample instance based on template type
        if cls == CodeReviewTemplate:
            t = CodeReviewTemplate(files=files)
        elif cls == ResearchTemplate:
            t = ResearchTemplate(topic=args.topic)
        elif cls == DataExtractionTemplate:
            t = DataExtractionTemplate(
                source_paths=files,
                extract_schema={"name": "string", "value": "number"},
            )
        elif cls == ConsensusCheckTemplate:
            t = ConsensusCheckTemplate(
                proposal=args.proposal, expert_role=args.role,
            )
        elif cls == DocumentationTemplate:
            t = DocumentationTemplate(target_path=files[0])
        elif cls == TestingTemplate:
            t = TestingTemplate(code_path=files[0])
        elif cls == RefactorTemplate:
            t = RefactorTemplate(code_path=files[0])
        else:
            print(f"No preview handler for {args.template}", file=sys.stderr)
            sys.exit(1)

        print(render(t))


if __name__ == "__main__":
    main()
