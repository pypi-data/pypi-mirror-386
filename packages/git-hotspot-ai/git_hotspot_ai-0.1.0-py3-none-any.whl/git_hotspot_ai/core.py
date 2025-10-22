"""Core logic for git-hotspot-ai."""

from __future__ import annotations

import dataclasses
import fnmatch
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


@dataclasses.dataclass()
class AnalyzerConfig:
    repo_path: Path
    top_selector: str
    tasks: list[str]
    since: str | None = None
    dry_run: bool = False
    ignore_patterns: list[str] | None = None
    min_commits: int = 1
    cursor_agent_path: str | None = None


@dataclasses.dataclass()
class FileHotspot:
    path: Path
    commit_count: int
    line_changes: int

    def score(self) -> float:
        return self.commit_count + 0.1 * self.line_changes


# task prompt templates for different AI tasks
TASK_PROMPTS = {
    "annotate": "请为这个文件添加详细的代码注释和文档。分析代码的功能、参数、返回值，并添加适当的注释来提高代码可读性。",
    "structure": "请分析这个文件的代码结构，识别潜在的重构机会，提出改进代码组织和架构的建议。",
    "skills": "请分析这个文件需要的技能和专业知识，识别代码中使用的技术栈、设计模式和最佳实践。",
    "performance": "请分析这个文件的性能特征，识别潜在的性能瓶颈，提出优化建议和改进方案。",
    "mvp": "请基于这个文件生成 MVP（最小可行产品）建议，分析核心功能和简化方案。",
}


class HotspotAnalyzer:
    def __init__(self, config: AnalyzerConfig) -> None:
        self.config = config
        self.analysis_path = config.repo_path.resolve()
        self.repo_root = self._resolve_repo_root(self.analysis_path)
        self.git_cwd = self.repo_root
        self.analysis_rel = self._compute_analysis_relative_path()
        self.cursor_agent_path = self._validate_cursor_agent_path()

    # region public API
    def run(self) -> None:
        hotspots = self._collect_hotspots()
        selected = self._select_top(hotspots)
        self._print_summary(hotspots, selected)
        if not self.config.dry_run:
            self._dispatch_ai_tasks(selected)

    # endregion

    # region hotspot computation
    def _collect_hotspots(self) -> list[FileHotspot]:
        git_cmd = ["git", "log", "--numstat", "--pretty=format:%H"]
        if self.config.since:
            git_cmd.append(f"--since={self.config.since}")
        if self.analysis_rel:
            git_cmd.extend(["--", self.analysis_rel])

        result = subprocess.run(
            git_cmd,
            cwd=self.git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        commit_counts: Counter[Path] = Counter()
        line_changes: Counter[Path] = Counter()

        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.fullmatch(r"[0-9a-fA-F]{40}", stripped):
                continue

            parts = stripped.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, filename = parts
            if not filename:
                continue
            if self._should_ignore(filename):
                continue
            # filepath from git log is always repo-root relative
            rel_path = Path(filename)
            if self.analysis_rel and not rel_path.is_relative_to(self.analysis_rel):
                continue

            commit_counts[rel_path] += 1
            additions = int(added) if added.isdigit() else 0
            deletions = int(deleted) if deleted.isdigit() else 0
            line_changes[rel_path] += additions + deletions

        hotspots = [
            FileHotspot(path, commit_counts[path], line_changes[path])
            for path in commit_counts
            if commit_counts[path] >= self.config.min_commits
        ]
        hotspots.sort(key=lambda item: item.score(), reverse=True)
        return hotspots

    def _select_top(self, hotspots: list[FileHotspot]) -> list[FileHotspot]:
        if not hotspots:
            return []
        selector = self.config.top_selector.strip()
        if selector.endswith("%"):
            percentage = float(selector.rstrip("%"))
            k = max(1, int(len(hotspots) * (percentage / 100.0)))
        else:
            k = max(1, int(selector))
        return hotspots[:k]

    # endregion

    # region reporting & AI dispatch
    def _print_summary(
        self,
        hotspots: Iterable[FileHotspot],
        selected: Iterable[FileHotspot],
    ) -> None:
        print("Hotspot ranking:")
        print(f"Repo: {self.repo_root}")
        if self.analysis_rel:
            print(f"Scope: {self.analysis_rel}")
        print("=== Top Files ===")
        for idx, item in enumerate(selected, start=1):
            print(
                f"{idx:03d}. {item.path} — commits: {item.commit_count}, lines: {item.line_changes}, score: {item.score():.1f}"
            )
        if self.config.dry_run:
            print("(dry-run mode, AI tasks are skipped)")

    def _dispatch_ai_tasks(self, files: Iterable[FileHotspot]) -> None:
        for hotspot in files:
            self._handle_file(hotspot)

    def _handle_file(self, hotspot: FileHotspot) -> None:
        print(f"[AI] Processing {hotspot.path}")
        file_path = str(self.repo_root / hotspot.path)

        # process each task separately for better control and error handling
        for task in self.config.tasks:
            if task not in TASK_PROMPTS:
                print(f"Warning: Unknown task '{task}', skipping...")
                continue

            try:
                self._invoke_cursor_agent_for_task(file_path, task, hotspot)
            except Exception as e:
                print(f"Error processing task '{task}' for {hotspot.path}: {e}")

    def _invoke_cursor_agent_for_task(
        self, file_path: str, task: str, hotspot: FileHotspot
    ) -> None:
        """invoke cursor-agent for a specific task on a file"""
        prompt = self._build_task_prompt(file_path, task, hotspot)

        # construct cursor-agent command
        cmd = [
            self.cursor_agent_path,
            "--print",  # print responses to console for non-interactive use
            "--force",  # force allow commands unless explicitly denied
            prompt,
        ]

        print(f"  -> Running task: {task}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout for safety
                check=False,  # don't raise exception on non-zero exit
            )

            if result.returncode == 0:
                print(f"  ✓ Task '{task}' completed successfully")
                if result.stdout.strip():
                    print(
                        f"  Output: {result.stdout.strip()[:200]}..."
                    )  # show first 200 chars
            else:
                print(f"  ✗ Task '{task}' failed with return code {result.returncode}")
                if result.stderr.strip():
                    print(f"  Error: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print(f"  ✗ Task '{task}' timed out after 5 minutes")
        except Exception as e:
            print(f"  ✗ Task '{task}' failed with exception: {e}")

    def _build_task_prompt(
        self, file_path: str, task: str, hotspot: FileHotspot
    ) -> str:
        """build prompt for cursor-agent based on task type and file metrics"""
        base_prompt = TASK_PROMPTS[task]

        context = f"""
文件路径: {file_path}
Git 热点指标:
- 提交次数: {hotspot.commit_count}
- 代码变更行数: {hotspot.line_changes}
- 热点评分: {hotspot.score():.1f}

{base_prompt}

请分析文件 {file_path} 并提供相应的建议。
"""
        return context.strip()

    # endregion

    # region helpers
    def _should_ignore(self, filename: str) -> bool:
        patterns = self.config.ignore_patterns or []
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _resolve_repo_root(self, path: Path) -> Path:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())

    def _compute_analysis_relative_path(self) -> str | None:
        if self.analysis_path == self.repo_root:
            return None
        return str(self.analysis_path.relative_to(self.repo_root))

    def _validate_cursor_agent_path(self) -> str:
        """validate and return cursor-agent executable path"""
        # first check if provided in config
        if self.config.cursor_agent_path:
            cursor_path = self.config.cursor_agent_path
        else:
            # check environment variable
            cursor_path = os.environ.get("CURSOR_AGENT_PATH")

        if not cursor_path:
            print("Error: CURSOR_AGENT_PATH environment variable is not set!")
            print(
                "Please set the environment variable to point to your cursor-agent executable:"
            )
            print("  export CURSOR_AGENT_PATH=/path/to/cursor-agent")
            print("  # or")
            print("  export CURSOR_AGENT_PATH=$(which cursor-agent)")
            sys.exit(1)

        # check if the path exists and is executable
        cursor_path_obj = Path(cursor_path)
        if not cursor_path_obj.exists():
            print(f"Error: cursor-agent not found at: {cursor_path}")
            print("Please check your CURSOR_AGENT_PATH environment variable.")
            sys.exit(1)

        if not cursor_path_obj.is_file():
            print(f"Error: {cursor_path} is not a file")
            sys.exit(1)

        # try to verify it's actually cursor-agent by running --version
        try:
            result = subprocess.run(
                [cursor_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                print(
                    f"Warning: {cursor_path} may not be a valid cursor-agent executable"
                )
                print(f"Version check failed with return code: {result.returncode}")
        except Exception as e:
            print(f"Warning: Could not verify cursor-agent executable: {e}")

        return cursor_path

    # endregion
