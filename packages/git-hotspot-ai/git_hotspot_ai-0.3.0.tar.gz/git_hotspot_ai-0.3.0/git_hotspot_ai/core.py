"""
Core logic for git-hotspot-ai.

This module provides the main functionality for analyzing Git repositories to identify
code hotspots - files that have been frequently modified and are likely candidates
for refactoring, documentation, or other improvements. It integrates with AI agents
to perform various analysis tasks on the identified hotspot files.

Key features:
- Git log analysis to track file modification frequency and line changes
- Hotspot scoring algorithm based on commit count and line changes
- Integration with cursor-agent for AI-powered code analysis
- Configurable filtering and selection of top hotspot files
- Support for various analysis tasks (annotation, structure analysis, etc.)
"""

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
    """
    Configuration class for the hotspot analyzer.

    This dataclass groups the runtime parameters that control repository
    inspection and downstream AI task execution.

    Attributes:
        repo_path: Absolute or relative path pointing to the Git repository root.
        top_selector: Selection strategy for hotspots; accepts an integer string or percentage string.
        tasks: Ordered list of task identifiers to run against the selected files.
        since: Optional ISO-8601 date string passed to Git's ``--since`` flag.
        dry_run: Skip cursor-agent invocations when true while still producing a report.
        ignore_patterns: Shell-style glob patterns that skip matching files from analysis.
        min_commits: Minimum commit threshold to include a file in the hotspot list.
        cursor_agent_path: Explicit path to the cursor-agent binary; overrides environment discovery.
        force_approve: Append ``--force`` to cursor-agent when approvals should be bypassed.
        task_prompt_overrides: Mapping of task identifiers to custom prompt text.
    """
    repo_path: Path
    top_selector: str
    tasks: list[str]
    since: str | None = None
    dry_run: bool = False
    ignore_patterns: list[str] | None = None
    min_commits: int = 1
    cursor_agent_path: str | None = None
    force_approve: bool = False
    task_prompt_overrides: dict[str, str] | None = None


@dataclasses.dataclass()
class FileHotspot:
    """
    Represents a file hotspot with its modification metrics.

    This dataclass captures the activity signals required to rank files
    during hotspot analysis and supplies a scoring helper used for sorting.

    Attributes:
        path: Repository-relative file path that Git produces inside ``git log`` output.
        commit_count: Number of commits that touched the file inside the inspected window.
        line_changes: Aggregate of additions and deletions collected from ``--numstat``.

    Methods:
        score: Calculate a composite score for ranking hotspots.
    """
    path: Path
    commit_count: int
    line_changes: int

    def score(self) -> float:
        """
        Calculate the hotspot score for ranking files.

        Returns:
            float: Composite value defined as ``commit_count + 0.1 * line_changes``.
                Higher values reflect more frequent or larger changes, pushing files
                toward the top of the hotspot ordering.
        """
        return self.commit_count + 0.1 * self.line_changes


# task prompt templates for different AI analysis tasks
TASK_PROMPTS = {
    "annotate": "请为这个文件添加详细的代码注释和文档。分析代码的功能、参数、返回值，并添加适当的注释来提高代码可读性。",
    "structure": "请分析这个文件的代码结构，识别潜在的重构机会，提出改进代码组织和架构的建议。",
    "skills": "请分析这个文件需要的技能和专业知识，识别代码中使用的技术栈、设计模式和最佳实践。",
    "performance": "请分析这个文件的性能特征，识别潜在的性能瓶颈，提出优化建议和改进方案。",
    "mvp": "请基于这个文件生成 MVP（最小可行产品）建议，分析核心功能和简化方案。"
}


class HotspotAnalyzer:
    """
    Main analyzer class for identifying and processing Git code hotspots.
    
    This class orchestrates the entire hotspot analysis process, from collecting
    Git log data to dispatching AI tasks on the most active files. It provides
    a clean separation between data collection, analysis, and AI task execution.
    
    Attributes:
        config: Configuration object containing analysis parameters
        analysis_path: Resolved path to the analysis target
        repo_root: Root directory of the Git repository
        git_cwd: Working directory for Git commands
        analysis_rel: Relative path from repo root to analysis target
        cursor_agent_path: Validated path to cursor-agent executable
    """
    
    def __init__(self, config: AnalyzerConfig) -> None:
        """
        Initialize the hotspot analyzer with the given configuration.

        Args:
            config: Fully populated ``AnalyzerConfig`` instance controlling runtime behavior.

        Raises:
            SystemExit: When cursor-agent validation cannot confirm an executable path.
        """
        # store raw configuration for later use
        self.config = config
        # resolve analysis target to absolute path to avoid relative path ambiguity
        self.analysis_path = config.repo_path.resolve()
        # locate repository root using Git metadata to ensure correctness
        self.repo_root = self._resolve_repo_root(self.analysis_path)
        # git commands operate from repo root for consistent path handling
        self.git_cwd = self.repo_root
        # compute path of analysis target relative to repository root for filtering
        self.analysis_rel = self._compute_analysis_relative_path()
        # verify cursor-agent availability immediately to fail fast if misconfigured
        self.cursor_agent_path = self._validate_cursor_agent_path()

    # region public API
    def run(self) -> None:
        """
        Execute the complete hotspot analysis workflow.

        The method coordinates data collection, selection, reporting, and optional
        AI execution sequentially. Each stage relies on helper methods so that the
        control flow remains easy to audit.

        Returns:
            None.
        """
        hotspots = self._collect_hotspots()
        selected = self._select_top(hotspots)
        self._print_summary(hotspots, selected)
        if not self.config.dry_run:
            self._dispatch_ai_tasks(selected)

    # endregion

    # region hotspot computation
    def _collect_hotspots(self) -> list[FileHotspot]:
        """
        Collect hotspot data by analyzing Git log information.

        Returns:
            list[FileHotspot]: Sorted list (descending score) of hotspots discovered
                inside the repository scope.

        Raises:
            subprocess.CalledProcessError: Propagated when Git cannot execute successfully.
        """
        # construct git log command with numstat for line change data
        git_cmd = ["git", "log", "--numstat", "--pretty=format:%H"]

        if self.config.since:
            git_cmd.append(f"--since={self.config.since}")

        if self.analysis_rel:
            git_cmd.extend(["--", self.analysis_rel])

        # execute git command in repository root
        result = subprocess.run(
            git_cmd,
            cwd=self.git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        # counters to track file statistics
        commit_counts: Counter[Path] = Counter()
        line_changes: Counter[Path] = Counter()

        # process git log output line by line
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # skip commit hash lines
            if re.fullmatch(r"[0-9a-fA-F]{40}", stripped):
                continue

            # parse numstat format: additions\tdeletions\tfilename
            parts = stripped.split("\t")
            if len(parts) != 3:
                continue
            added, deleted, filename = parts
            if not filename:
                continue
            # apply ignore patterns before spending time on conversions
            if self._should_ignore(filename):
                continue
            # filepath from git log is always repo-root relative
            rel_path = Path(filename)
            # filter by analysis scope if specified
            if self.analysis_rel and not rel_path.is_relative_to(self.analysis_rel):
                continue

            # increment commit count for this file
            commit_counts[rel_path] += 1
            # safely parse line change numbers; binary diffs use '-' which should be treated as zero
            additions = int(added) if added.isdigit() else 0
            deletions = int(deleted) if deleted.isdigit() else 0
            line_changes[rel_path] += additions + deletions

        # create hotspot objects and filter by minimum commits
        hotspots = [
            FileHotspot(path, commit_counts[path], line_changes[path])
            for path in commit_counts
            if commit_counts[path] >= self.config.min_commits
        ]
        # sort by score in descending order so downstream selection remains simple
        hotspots.sort(key=lambda item: item.score(), reverse=True)
        return hotspots

    def _select_top(self, hotspots: list[FileHotspot]) -> list[FileHotspot]:
        """
        Select the top N files based on the configured selector.
        
        Args:
            hotspots: List of all hotspots sorted by score.

        Returns:
            list[FileHotspot]: Selection of hotspots derived from ``top_selector``.

        Raises:
            ValueError: If the selector cannot be parsed into a valid count
                or percentage value
        """
        if not hotspots:
            return []
        selector = self.config.top_selector.strip()
        if not selector:
            raise ValueError("top_selector must not be empty")

        if selector.endswith("%"):
            # percentage-based selection with explicit validation
            percentage_value = selector.rstrip("%")
            try:
                percentage = float(percentage_value)
            except ValueError as exc:
                raise ValueError(
                    f"invalid percentage selector: '{selector}'"
                ) from exc
            if percentage <= 0:
                raise ValueError("percentage selector must be positive")
            selection_size = int(len(hotspots) * (percentage / 100.0))
        else:
            # absolute number selection with explicit validation
            try:
                selection_size = int(selector)
            except ValueError as exc:
                raise ValueError(
                    f"invalid numeric selector: '{selector}'"
                ) from exc
            if selection_size <= 0:
                raise ValueError("numeric selector must be positive")

        if selection_size < 1:
            selection_size = 1
        if selection_size > len(hotspots):
            selection_size = len(hotspots)
        return hotspots[:selection_size]

    # endregion

    # region reporting & AI dispatch
    def _print_summary(
        self,
        hotspots: list[FileHotspot],
        selected: list[FileHotspot],
    ) -> None:
        """Display a detailed summary of the analysis results.

        Args:
            hotspots: Complete hotspot ranking generated from git history.
            selected: Subset of hotspots chosen for AI task execution.

        Returns:
            None.
        """
        print("=" * 80)
        print("🔥 Git Hotspot Analysis Report")
        print("=" * 80)
        print(f"📁 Repository: {self.repo_root}")
        if self.analysis_rel:
            print(f"📂 Analysis Scope: {self.analysis_rel}")
        if self.config.since:
            print(f"📅 Time Filter: since {self.config.since}")
        if self.config.ignore_patterns:
            print(f"🚫 Ignored Patterns: {', '.join(self.config.ignore_patterns)}")
        print(f"📊 Minimum Commits: {self.config.min_commits}")
        print()
        
        # show complete data collection summary
        print("📈 Data Collection Summary:")
        print(f"   • Total files analyzed: {len(hotspots)}")
        print(f"   • Files selected for AI analysis: {len(selected)}")
        print(f"   • Selection criteria: {self.config.top_selector}")
        print()
        
        # show all hotspot files with detailed metrics
        if hotspots:
            print("📋 Complete Hotspot Ranking:")
            print("-" * 80)
            print(f"{'Rank':<6} {'File Path':<50} {'Commits':<8} {'Lines':<10} {'Score':<8}")
            print("-" * 80)
            
            for idx, item in enumerate(hotspots, start=1):
                # highlight selected files in the table for quick scanning
                marker = "🎯" if item in selected else "  "
                print(f"{marker}{idx:>3}. {str(item.path):<50} {item.commit_count:>6} {item.line_changes:>8} {item.score():>6.1f}")
            print("-" * 80)
        
        # show selected files for AI analysis
        if selected:
            print()
            print("🎯 Selected Files for AI Analysis:")
            print("-" * 60)
            for idx, item in enumerate(selected, start=1):
                print(f"{idx:>3}. {item.path}")
                print(f"     📊 Metrics: {item.commit_count} commits, {item.line_changes} line changes, score: {item.score():.1f}")
            print("-" * 60)
        
        # show task information
        if not self.config.dry_run and selected:
            print()
            print("🤖 AI Tasks to Execute:")
            for task in self.config.tasks:
                try:
                    task_desc = self._resolve_task_prompt(task)
                except KeyError:
                    task_desc = "task prompt not defined"
                print(f"   • {task}: {task_desc[:60]}...")
        
        if self.config.dry_run:
            print()
            print("🔍 (Dry-run mode: AI tasks will be skipped)")
        
        print("=" * 80)

    def _dispatch_ai_tasks(self, files: list[FileHotspot]) -> None:
        """
        Dispatch AI analysis tasks for the selected hotspot files.
        
        This method orchestrates the execution of all configured AI tasks
        on each selected hotspot file. It provides detailed progress tracking
        and error handling to ensure robust execution even if individual
        tasks fail.
        
        Args:
            files: List of hotspot files to process with AI tasks
        """
        if not files:
            print("\n⚠️  No files selected for AI analysis.")
            return
        
        total_files = len(files)
        total_tasks = len(self.config.tasks) * total_files
        
        print(f"\n🚀 Starting AI Analysis...")
        print(f"📊 Progress Overview: {total_files} files × {len(self.config.tasks)} tasks = {total_tasks} total operations")
        print("=" * 80)
        
        completed_tasks = 0
        
        # process each file with all configured tasks
        for file_idx, hotspot in enumerate(files, 1):
            print(f"\n📄 Processing File {file_idx}/{total_files}: {hotspot.path}")
            print(f"   📊 File Metrics: {hotspot.commit_count} commits, {hotspot.line_changes} line changes, score: {hotspot.score():.1f}")
            
            file_tasks_completed = 0
            file_tasks_total = len(self.config.tasks)
            
            # execute each task for the current file
            for task_idx, task in enumerate(self.config.tasks, 1):
                if not self._has_task_prompt(task):
                    print(f"   ⚠️  Task {task_idx}/{file_tasks_total}: Unknown task '{task}', skipping...")
                    continue
                
                print(f"   🤖 Task {task_idx}/{file_tasks_total}: {task}")
                
                try:
                    success = self._invoke_cursor_agent_for_task(str(self.repo_root / hotspot.path), task, hotspot)
                    if success:
                        file_tasks_completed += 1
                        completed_tasks += 1
                        print(f"      ✅ Completed successfully")
                    else:
                        print(f"      ❌ Failed")
                except Exception as e:
                    print(f"      💥 Error: {e}")
                
                # show overall progress; protect against division by zero indirectly by checking total_tasks earlier
                progress_pct = (completed_tasks / total_tasks) * 100
                print(f"      📈 Overall Progress: {completed_tasks}/{total_tasks} ({progress_pct:.1f}%)")
            
            # file completion summary
            file_success_rate = (file_tasks_completed / file_tasks_total) * 100 if file_tasks_total > 0 else 0
            print(f"   📋 File Summary: {file_tasks_completed}/{file_tasks_total} tasks completed ({file_success_rate:.1f}%)")
        
        # final summary
        print("\n" + "=" * 80)
        print("🎉 AI Analysis Complete!")
        final_success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        print(f"📊 Final Results: {completed_tasks}/{total_tasks} tasks completed ({final_success_rate:.1f}%)")
        print("=" * 80)


    def _invoke_cursor_agent_for_task(self, file_path: str, task: str, hotspot: FileHotspot) -> bool:
        """
        Invoke cursor-agent for a specific task on a file.

        Args:
            file_path: Absolute path string for the file passed to cursor-agent.
            task: Task identifier expected to exist inside ``TASK_PROMPTS``.
            hotspot: Metrics instance providing contextual information for the prompt.

        Returns:
            bool: ``True`` when cursor-agent exits successfully, ``False`` otherwise.
        """
        
        prompt = self._build_task_prompt(file_path, task, hotspot)
        
        # construct cursor-agent command
        cmd = [
            self.cursor_agent_path,
            "--print",  # print responses to console for non-interactive use
        ]
        
        # add --force flag only if explicitly requested and allowed
        if self.config.force_approve:
            cmd.append("--force")
        
        cmd.append(prompt)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout for safety
                check=False  # don't raise exception on non-zero exit
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    # show a preview of the output so the operator can skim without opening separate tools
                    output_preview = result.stdout.strip()[:150]
                    if len(result.stdout.strip()) > 150:
                        output_preview += "..."
                    print(f"      💬 Output: {output_preview}")
                return True
            else:
                if result.stderr.strip():
                    error_msg = result.stderr.strip()[:100]
                    if len(result.stderr.strip()) > 100:
                        error_msg += "..."
                    print(f"      🚨 Error (code {result.returncode}): {error_msg}")
                return False
                    
        except subprocess.TimeoutExpired:
            print(f"      ⏰ Task timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"      💥 Exception: {str(e)[:100]}")
            return False

    def _build_task_prompt(self, file_path: str, task: str, hotspot: FileHotspot) -> str:
        """
        Build a comprehensive prompt for cursor-agent based on task type and file metrics.

        Args:
            file_path: Absolute path string to include inside the AI context block.
            task: Key that maps to the stored Chinese-language instructions.
            hotspot: Activity data to embed inside the generated prompt.

        Returns:
            str: Fully formatted prompt string assembled for cursor-agent consumption.
        """
        base_prompt = self._resolve_task_prompt(task)
        
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

    def _resolve_task_prompt(self, task: str) -> str:
        """resolve prompt text for a task identifier."""
        overrides = self.config.task_prompt_overrides or {}
        if task in overrides:
            return overrides[task]
        if task in TASK_PROMPTS:
            return TASK_PROMPTS[task]
        raise KeyError(task)

    def _has_task_prompt(self, task: str) -> bool:
        """check whether a prompt is defined for the given task."""
        overrides = self.config.task_prompt_overrides or {}
        if task in overrides:
            return True
        return task in TASK_PROMPTS

    # endregion

    # region helpers
    def _should_ignore(self, filename: str) -> bool:
        """
        Check if a filename should be ignored based on configured patterns.

        Args:
            filename: Repo-relative path string extracted from ``git log`` output.

        Returns:
            bool: ``True`` when any ignore pattern matches the file, otherwise ``False``.
        """
        patterns = self.config.ignore_patterns or []
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def _resolve_repo_root(self, path: Path) -> Path:
        """
        Resolve the Git repository root directory from a given path.
        
        Args:
            path: Path within the repository to start from.

        Returns:
            Path: Repository root produced by ``git rev-parse --show-toplevel``.

        Raises:
            subprocess.CalledProcessError: If the path is not within a Git repository
        """
        # rely on git metadata instead of manual parent traversal to avoid false positives
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())

    def _compute_analysis_relative_path(self) -> str | None:
        """
        Compute the relative path from repository root to analysis target.
        
        Returns:
            str | None: Relative subpath when restricting analysis, otherwise ``None``.
        """
        if self.analysis_path == self.repo_root:
            return None
        return str(self.analysis_path.relative_to(self.repo_root))

    def _validate_cursor_agent_path(self) -> str:
        """Validate and return cursor-agent executable path.

        Returns:
            str: Verified file-system path pointing to the cursor-agent executable.

        Raises:
            SystemExit: When the path cannot be discovered or verified as a file.
        """
        # first check if provided in config
        if self.config.cursor_agent_path:
            cursor_path = self.config.cursor_agent_path
        else:
            # check environment variable
            cursor_path = os.environ.get("CURSOR_AGENT_PATH")
        
        if not cursor_path:
            print("Error: CURSOR_AGENT_PATH environment variable is not set!")
            print("Please set the environment variable to point to your cursor-agent executable:")
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
                check=False
            )
            if result.returncode != 0:
                print(f"Warning: {cursor_path} may not be a valid cursor-agent executable")
                print(f"Version check failed with return code: {result.returncode}")
        except Exception as e:
            print(f"Warning: Could not verify cursor-agent executable: {e}")
        
        return cursor_path

    # endregion
