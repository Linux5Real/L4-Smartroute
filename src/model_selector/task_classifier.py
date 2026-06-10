from __future__ import annotations

import re


TASK_TYPES = {
    "simple_edit",
    "bugfix",
    "debugging",
    "multi_file_refactor",
    "architecture",
    "test_generation",
    "docs",
    "review",
    "long_context_analysis",
    "agentic_implementation",
    "frontend_ui",
    "backend_systems",
    "math_science",
}

TASK_PATTERNS: dict[str, tuple[str, ...]] = {
    "architecture": (
        "architecture",
        "design",
        "schema",
        "migration",
        "api contract",
        "data model",
        "system",
    ),
    "debugging": (
        "debug",
        "diagnose",
        "traceback",
        "stack trace",
        "root cause",
        "flaky",
        "crash",
        "exception",
    ),
    "bugfix": (
        "bug",
        "fix",
        "broken",
        "failing",
        "regression",
        "error",
        "issue",
    ),
    "multi_file_refactor": (
        "refactor",
        "rewrite",
        "restructure",
        "migrate",
        "split",
        "extract",
        "cross-cutting",
        "multiple files",
    ),
    "test_generation": (
        "test",
        "pytest",
        "coverage",
        "unit test",
        "integration test",
        "e2e",
    ),
    "review": (
        "review",
        "audit",
        "security",
        "risk",
        "inspect",
        "regression check",
    ),
    "docs": (
        "docs",
        "readme",
        "documentation",
        "comment",
        "explain",
        "changelog",
        "copy",
    ),
    "long_context_analysis": (
        "summarize",
        "analyse all",
        "analyze all",
        "whole codebase",
        "entire project",
        "large context",
        "graphify",
        "map the codebase",
    ),
    "agentic_implementation": (
        "build",
        "implement",
        "create",
        "add feature",
        "end-to-end",
        "full workflow",
        "ship",
    ),
    "frontend_ui": (
        "frontend",
        "ui",
        "ux",
        "react",
        "next.js",
        "component",
        "css",
        "responsive",
        "layout",
        "design system",
    ),
    "backend_systems": (
        "backend",
        "api",
        "server",
        "database",
        "postgres",
        "auth",
        "queue",
        "cache",
        "endpoint",
        "middleware",
    ),
    "math_science": (
        "math",
        "physics",
        "science",
        "scientific",
        "proof",
        "algorithm",
        "optimization",
        "statistics",
        "probability",
    ),
    "simple_edit": (
        "typo",
        "rename",
        "small",
        "quick",
        "one line",
        "single file",
        "format",
    ),
}

COMPLEXITY_HINTS = {
    "low": {"simple_edit": 2, "docs": 1},
    "medium": {"bugfix": 1, "test_generation": 1, "agentic_implementation": 1},
    "high": {"multi_file_refactor": 2, "architecture": 1, "debugging": 1, "backend_systems": 1},
    "critical": {"architecture": 2, "multi_file_refactor": 1, "review": 1, "backend_systems": 1},
}


def classify_task(
    prompt: str = "",
    *,
    complexity: str | None = None,
    files_affected: int = 0,
    communities_crossed: int = 0,
) -> str:
    """Classify a task into a stable routing label for model selection."""
    text = prompt.lower()
    text = re.sub(r"\s+", " ", text)
    scores = {task: 0 for task in TASK_TYPES}

    for task, patterns in TASK_PATTERNS.items():
        for pattern in patterns:
            if pattern in text:
                scores[task] += 3 if " " in pattern else 2

    if complexity in COMPLEXITY_HINTS:
        for task, points in COMPLEXITY_HINTS[complexity].items():
            scores[task] += points

    if files_affected >= 8 or communities_crossed >= 3:
        scores["multi_file_refactor"] += 2
        scores["long_context_analysis"] += 1
    elif 0 < files_affected <= 2 and communities_crossed <= 1:
        scores["simple_edit"] += 1

    if not prompt.strip() and files_affected:
        return "review"

    priority = [
        "architecture",
        "debugging",
        "multi_file_refactor",
        "review",
        "backend_systems",
        "frontend_ui",
        "math_science",
        "agentic_implementation",
        "bugfix",
        "test_generation",
        "long_context_analysis",
        "docs",
        "simple_edit",
    ]
    best = max(priority, key=lambda task: (scores[task], -priority.index(task)))
    return best if scores[best] > 0 else "agentic_implementation"
