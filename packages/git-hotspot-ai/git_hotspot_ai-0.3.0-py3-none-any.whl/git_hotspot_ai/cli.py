"""Command-line entrypoint for git-hotspot-ai."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import HotspotAnalyzer, AnalyzerConfig


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
        default="annotate,structure,skills,performance,mvp",
        help="Comma-separated AI tasks: annotate,structure,skills,performance,mvp",
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
        "--task-prompt",
        action="append",
        metavar="TASK=TEXT",
        help="Override default prompt for a task (format: task=custom text). Can be repeated.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    raw_prompt_overrides = args.task_prompt if args.task_prompt else []
    task_prompt_overrides: dict[str, str] = {}

    for item in raw_prompt_overrides:
        if "=" not in item:
            parser.error(f"invalid task prompt override (missing '='): {item}")
        task_name, prompt_text = item.split("=", 1)
        task_name = task_name.strip()
        prompt_text = prompt_text.strip()
        if not task_name:
            parser.error("task prompt override requires a non-empty task name")
        if not prompt_text:
            parser.error(f"task prompt override for '{task_name}' requires non-empty text")
        task_prompt_overrides[task_name] = prompt_text

    cfg = AnalyzerConfig(
        repo_path=args.repo,
        top_selector=args.top,
        tasks=[task.strip() for task in args.tasks.split(",") if task.strip()],
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
