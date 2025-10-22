"""Command-line entrypoint for git-hotspot-ai."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import HotspotAnalyzer, AnalyzerConfig


DEFAULT_TASKS = [
    "annotate",
    "structure",
    "skills",
    "performance",
    "mvp",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-hotspot-ai",
        description="Analyze git hotspots and trigger AI post-processing.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to the target git repository (default: current directory)",
    )
    parser.add_argument(
        "--top",
        type=str,
        default="10%",
        help="Top percentage or count of hotspot files (e.g. '10%%' or '25').",
    )
    parser.add_argument(
        "--tasks",
        type=str,
        default=None,
        help="Comma-separated AI tasks: annotate,structure,skills,performance,mvp",
    )
    parser.add_argument(
        "--task",
        action="append",
        dest="task_list",
        metavar="TASK",
        help="Add a single AI task. Can be repeated to specify multiple tasks.",
    )
    parser.add_argument(
        "--all-tasks",
        action="store_true",
        help="Run all available AI tasks (equivalent to default behavior).",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Optional git --since filter (e.g. '6 months ago').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print hotspot ranking without invoking AI agents.",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        default="",
        help="Comma-separated glob patterns to ignore (e.g. 'tests/*,docs/*').",
    )
    parser.add_argument(
        "--min-commits",
        type=int,
        default=1,
        help="Minimum commit count for a file to be considered (default: 1).",
    )
    parser.add_argument(
        "--cursor-agent-path",
        type=str,
        default=None,
        help="Path to cursor-agent executable (overrides CURSOR_AGENT_PATH env var).",
    )
    parser.add_argument(
        "--force-approve",
        action="store_true",
        help="Use --force flag with cursor-agent (auto-approve all commands).",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt text for all tasks (overrides default prompts).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # first determine configured tasks
    configured_tasks: list[str] = []

    if args.task_list:
        for entry in args.task_list:
            cleaned = entry.strip()
            if cleaned:
                configured_tasks.append(cleaned)

    if args.tasks:
        for entry in args.tasks.split(","):
            cleaned = entry.strip()
            if cleaned:
                configured_tasks.append(cleaned)

    if not configured_tasks or args.all_tasks:
        configured_tasks = DEFAULT_TASKS.copy()

    # handle prompt overrides
    task_prompt_overrides: dict[str, str] = {}

    # handle custom prompt for all tasks
    if args.prompt:
        # apply custom prompt to all configured tasks
        for task in configured_tasks:
            task_prompt_overrides[task] = args.prompt

    cfg = AnalyzerConfig(
        repo_path=args.repo,
        top_selector=args.top,
        tasks=configured_tasks,
        since=args.since,
        dry_run=args.dry_run,
        ignore_patterns=[pat.strip() for pat in args.ignore.split(",") if pat.strip()],
        min_commits=max(1, args.min_commits),
        cursor_agent_path=args.cursor_agent_path,
        force_approve=args.force_approve,
        task_prompt_overrides=task_prompt_overrides if task_prompt_overrides else None,
    )

    analyzer = HotspotAnalyzer(cfg)
    analyzer.run()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
